import os
import json
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk

annotation_path = "data/annotations/"

class AnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Annotation Tool")

        # CANVAS
        self.canvas = tk.Canvas(root, cursor="cross", bg="black")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # SIDEBAR
        self.sidebar = tk.Frame(root, width=220)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(self.sidebar, text="Load Folder", command=self.load_folder).pack(fill=tk.X)
        tk.Button(self.sidebar, text="Save COCO", command=self.save_coco).pack(fill=tk.X)

        tk.Label(self.sidebar, text="Classes").pack()

        self.class_list = self.load_classes()
        if not self.class_list:
            self.class_list = ["person", "car", "dog", "cat"]

        self.selected_class = tk.StringVar(value=self.class_list[0])

        self.class_box = tk.Listbox(self.sidebar)
        self.class_box.pack(fill=tk.X)
        self.class_box.bind("<<ListboxSelect>>", self.select_class)

        tk.Button(self.sidebar, text="Add Tag", command=self.add_tag).pack(fill=tk.X)

        self.refresh_class_box()

        # DATA
        self.images = []
        self.index = 0
        self.img = None
        self.tk_img = None
        self.scale = 1.0

        self.annotations = {}
        self.current_boxes = []
        self.current_path = None

        # DRAW STATE
        self.start_x = None
        self.start_y = None
        self.active_rect = None
        self.active_box = None

        self.drag_data = {"x": 0, "y": 0}

        # EVENTS
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.zoom)

        root.bind("d", lambda e: self.next_image())
        root.bind("a", lambda e: self.prev_image())
        root.bind("<Delete>", lambda e: self.delete_box())

    # ZOOM COORD CONVERSION
    def canvas_to_image(self, x, y):
        return x / self.scale, y / self.scale

    def image_to_canvas(self, x, y):
        return x * self.scale, y * self.scale

    # CLASSES
    def load_classes(self):
        path = annotation_path+"classes.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return []

    def save_classes(self):
        os.makedirs(annotation_path, exist_ok=True)
        with open(annotation_path+"classes.json", "w") as f:
            json.dump(self.class_list, f, indent=2)

    def add_tag(self):
        tag = simpledialog.askstring("Add Tag", "Enter new class name:")
        if not tag:
            return

        tag = tag.strip()
        if tag and tag not in self.class_list:
            self.class_list.append(tag)
            self.save_classes()
            self.refresh_class_box()

    def refresh_class_box(self):
        self.class_box.delete(0, tk.END)
        for c in self.class_list:
            self.class_box.insert(tk.END, c)

        self.class_box.selection_set(0)
        self.selected_class.set(self.class_list[0])

    def select_class(self, event):
        sel = self.class_box.curselection()
        if sel:
            self.selected_class.set(self.class_list[sel[0]])

    # LOAD IMAGES
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.images = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ]

        self.index = 0
        self.load_image()

    def load_image(self):
        self.canvas.delete("all")

        self.current_boxes = []
        self.active_box = None

        self.current_path = self.images[self.index]

        self.img = Image.open(self.current_path)
        self.render_image()

        if self.current_path in self.annotations:
            for box in self.annotations[self.current_path]:
                self.draw_box(box)

    def render_image(self):
        w, h = self.img.size
        img = self.img.resize((int(w * self.scale), int(h * self.scale)))

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    # DRAW BOX
    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y

        self.active_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2
        )

    def on_drag(self, event):
        if self.active_rect:
            self.canvas.coords(
                self.active_rect,
                self.start_x, self.start_y, event.x, event.y
            )

    def on_release(self, event):
        if not self.active_rect:
            return

        x1, y1 = self.canvas_to_image(self.start_x, self.start_y)
        x2, y2 = self.canvas_to_image(event.x, event.y)

        box = {
            "rect": self.active_rect,
            "bbox": [x1, y1, x2, y2],
            "class": self.selected_class.get()
        }

        self.current_boxes.append(box)
        self.bind_box(box)

        self.active_rect = None

    # DRAG
    def bind_box(self, box):
        rect = box["rect"]

        def select(e):
            self.active_box = box
            self.drag_data["x"] = e.x
            self.drag_data["y"] = e.y

        def move(e):
            dx = (e.x - self.drag_data["x"]) / self.scale
            dy = (e.y - self.drag_data["y"]) / self.scale

            x1, y1, x2, y2 = box["bbox"]

            x1 += dx
            y1 += dy
            x2 += dx
            y2 += dy

            box["bbox"] = [x1, y1, x2, y2]

            cx1, cy1 = self.image_to_canvas(x1, y1)
            cx2, cy2 = self.image_to_canvas(x2, y2)

            self.canvas.coords(rect, cx1, cy1, cx2, cy2)

            self.drag_data["x"] = e.x
            self.drag_data["y"] = e.y

        self.canvas.tag_bind(rect, "<Button-1>", select)
        self.canvas.tag_bind(rect, "<B1-Motion>", move)

    # DRAW EXISTING BOX
    def draw_box(self, box):
        x1, y1, x2, y2 = box["bbox"]

        cx1, cy1 = self.image_to_canvas(x1, y1)
        cx2, cy2 = self.image_to_canvas(x2, y2)

        rect = self.canvas.create_rectangle(
            cx1, cy1, cx2, cy2,
            outline="green",
            width=2
        )

        new_box = {
            "rect": rect,
            "bbox": box["bbox"],
            "class": box["class"]
        }

        self.current_boxes.append(new_box)
        self.bind_box(new_box)

    # DELETE
    def delete_box(self):
        if not self.active_box:
            return

        self.canvas.delete(self.active_box["rect"])
        self.current_boxes.remove(self.active_box)
        self.active_box = None

    # ZOOM
    def zoom(self, event):
        if event.delta > 0:
            self.scale *= 1.1
        else:
            self.scale *= 0.9

        self.canvas.delete("all")
        self.render_image()

        # redraw boxes correctly
        boxes_copy = self.current_boxes.copy()
        self.current_boxes = []

        for box in boxes_copy:
            self.draw_box(box)

    # NAVIGATION
    def next_image(self):
        self.save_all_states()
        if self.index < len(self.images) - 1:
            self.index += 1
            self.load_image()

    def prev_image(self):
        self.save_all_states()
        if self.index > 0:
            self.index -= 1
            self.load_image()

    def save_all_states(self):
        if not self.current_path:
            return

        self.annotations[self.current_path] = [
            {
                "bbox": b["bbox"],
                "class": b["class"]
            }
            for b in self.current_boxes
        ]

    # COCO EXPORT
    def save_coco(self):
        self.save_all_states()

        coco = {"images": [], "annotations": [], "categories": []}
        cats = self.class_list

        for i, c in enumerate(cats):
            coco["categories"].append({"id": i + 1, "name": c})

        ann_id = 1

        for i, img_path in enumerate(self.images):
            coco["images"].append({
                "id": i,
                "file_name": os.path.basename(img_path)
            })

            boxes = self.annotations.get(img_path, [])

            for b in boxes:
                x1, y1, x2, y2 = b["bbox"]

                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)

                coco["annotations"].append({
                    "id": ann_id,
                    "image_id": i,
                    "category_id": cats.index(b["class"]) + 1,
                    "bbox": [x1, y1, x2 - x1, y2 - y1],
                    "area": (x2 - x1) * (y2 - y1),
                    "iscrowd": 0
                })

                ann_id += 1

        os.makedirs(annotation_path, exist_ok=True)

        img_name = img_path.split("/")[-1]
        with open(annotation_path+f"instances_{img_name}.json", "w") as f:
            json.dump(coco, f, indent=2)

        print("Saved COCO file ✔")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()