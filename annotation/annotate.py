import os
import re
import json
import hashlib
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk

annotation_path = "data/annotations/"
os.makedirs(annotation_path, exist_ok=True)


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
        tk.Button(self.sidebar, text="Save", command=self.save_file).pack(fill=tk.X)

        #CLASSES
        self.class_list = self.load_classes()
        self.class_visible = {c: True for c in self.class_list}
        if not self.class_list:
            self.class_list = ["person", "car", "dog", "cat"]
            self.class_visible = {
                "person": True,
                "car": True,
                "dog": True,
                "cat": True
            }

        self.selected_class = tk.StringVar(value=self.class_list[0])


        self.class_vars = {}
        self.visible_vars = {}
        tk.Label(self.sidebar, text="Classes").pack()

        self.selected_class = tk.StringVar(value=self.class_list[0] if self.class_list else "")

        self.add_tag_btn = tk.Button(self.sidebar, text="Add Tag", command=self.add_tag)
        self.add_tag_btn.pack(fill=tk.X)

        self.refresh_class_box()


        # DATA
        self.images = []
        self.index = 0
        self.img = None
        self.tk_img = None
        self.scale = 1.0

        self.current_boxes = []
        self.current_path = None

        self.image_boxes = []

        # DRAW STATE
        self.start_x = 0
        self.start_y = 0
        self.active_rect = None
        self.active_box = None

        self.drag_data = {"x": 0, "y": 0}

        # EVENTS
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.zoom)
        
        self.root.bind("<BackSpace>", lambda e: self.delete_box())
        self.root.bind("<Escape>", lambda e: self.cancel_draw())
        self.root.bind("d", lambda e: self.next_image())
        self.root.bind("a", lambda e: self.prev_image())

        # STATE
        self.state_file = annotation_path + "state.json"
        self.state = self.load_state()
        self.selected_box = None

        # IMAGE LABEL
        self.image_label = tk.Label(self.sidebar, text="", wraplength=200)
        self.image_label.pack(fill=tk.X)

        # JUMP TO IMAGE
        jump_frame = tk.Frame(self.sidebar)
        jump_frame.pack(fill=tk.X, pady=5)

        tk.Label(jump_frame, text="Go to image #").pack()

        # input validation
        vcmd = (self.root.register(self.only_int), "%P")

        self.jump_entry = tk.Entry(
            jump_frame,
            validate="key",
            validatecommand=vcmd
        )
        self.jump_entry.pack(fill=tk.X)
        self.jump_entry.bind("<Return>", lambda e: self.jump_to_image())

        tk.Button(
            jump_frame,
            text="Jump",
            command=self.jump_to_image
        ).pack(fill=tk.X)

    #DEBUG TOOl
    def debug_key(self, event):
        print("KEY PRESSED:", event.keysym)

    # STATE
    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}

    def save_state_file(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def get_image_hash(self, path):
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    # CLASSES
    def load_classes(self):
        path = annotation_path + "classes.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return []

    def save_classes(self):
        with open(annotation_path + "classes.json", "w") as f:
            json.dump(self.class_list, f, indent=2)

    def add_tag(self):
        tag = simpledialog.askstring("Add Tag", "Enter new class name:")
        if tag and tag.strip() not in self.class_list:
            self.class_list.append(tag.strip())
            self.save_classes()
            self.refresh_class_box()

    def refresh_class_box(self):
        if hasattr(self, "class_ui_rows"):
            for widget in self.class_ui_rows:
                widget.destroy()

        self.class_ui_rows = []

        # ensure selection exists
        if self.class_list and not self.selected_class.get():
            self.selected_class.set(self.class_list[0])

        for c in self.class_list:
            row = tk.Frame(self.sidebar)
            row.pack(fill=tk.X, anchor="w")
            self.class_ui_rows.append(row)

            # visibility toggle
            var = self.class_vars.get(c, tk.BooleanVar(value=True))
            self.class_vars[c] = var

            tk.Checkbutton(
                row,
                variable=var,
                command=self.redraw_boxes
            ).pack(side=tk.LEFT)

            # selection button
            rb = tk.Radiobutton(
                row,
                text=c,
                variable=self.selected_class,
                value=c,
                indicatoron=0,   # makes it act like a button
                width=12
            )
            rb.pack(side=tk.LEFT, anchor="w")

        # Rebuild button
        self.add_tag_btn.destroy()
        self.add_tag_btn = tk.Button(self.sidebar, text="Add Tag", command=self.add_tag)
        self.add_tag_btn.pack(fill=tk.X)


    # def select_class(self, event):
    #     sel = self.class_box.curselection()
    #     if sel:
    #         self.selected_class.set(self.class_list[sel[0]])

    # LOAD IMAGES
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        def natural_sort_key(path):
            name = os.path.basename(path)
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split(r'(\d+)', name)]

        self.images = sorted(
            [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".png", ".jpeg"))
            ],
            key=natural_sort_key
        )

        self.index = 0
        self.load_image()

    def load_image(self):
        if not self.images or self.index >= len(self.images):
            return

        self.canvas.delete("all")
        self.current_boxes = []
        self.selected_box = None

        self.current_path = self.images[self.index]
        key = os.path.basename(self.current_path)

        self.image_label.config(
            text=f"{key} ({self.index+1}/{len(self.images)})"
        )

        self.img = Image.open(self.current_path)
        self.render_image()

        saved = self.state.get(key)

        # ALWAYS load full dataset into image_boxes
        self.image_boxes = saved["boxes"] if saved else []

        # render only visible ones
        for box in self.image_boxes:
            if self.class_vars.get(box["class"], tk.BooleanVar(value=True)).get():
                self.create_box(box)

    def render_image(self):
        if self.img is None:
            return

        w, h = self.img.size
        img = self.img.resize((int(w * self.scale), int(h * self.scale)))

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    # DRAW NEW BOX
    def on_press(self, event):
        # detect item under cursor
        clicked = self.canvas.find_closest(event.x, event.y)

        if clicked:
            item = clicked[0]

            # verify it's actually a rectangle we created
            for b in self.current_boxes:
                if b["rect"] == item:
                    # Block selection if class is hidden
                    if not self.class_vars.get(b["class"], tk.BooleanVar(value=True)).get():
                        return

                    self.selected_box = b
                    self.dragging = True
                    self.drag_start = (event.x, event.y)
                    self.highlight_box(b)
                    return

        # otherwise start drawing
        self.selected_box = None
        self.dragging = False

        self.start_x, self.start_y = event.x, event.y

        self.active_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2
        )

    def on_drag(self, event):
        # MOVE BOX
        if self.dragging and self.selected_box:
            dx = (event.x - self.drag_start[0]) / self.scale
            dy = (event.y - self.drag_start[1]) / self.scale

            x1, y1, x2, y2 = self.selected_box["bbox"]
            new_bbox = [x1 + dx, y1 + dy, x2 + dx, y2 + dy]

            # update UI copy
            self.selected_box["bbox"] = new_bbox

            # update source of truth
            self.selected_box["ref"]["bbox"] = new_bbox

            cx1, cy1 = self.image_to_canvas(x1 + dx, y1 + dy)
            cx2, cy2 = self.image_to_canvas(x2 + dx, y2 + dy)

            self.canvas.coords(self.selected_box["rect"], cx1, cy1, cx2, cy2)

            self.drag_start = (event.x, event.y)
            return

        # DRAW BOX
        if self.active_rect:
            self.canvas.coords(
                self.active_rect,
                self.start_x, self.start_y,
                event.x, event.y
            )

    def on_release(self, event):
        self.dragging = False

        if self.active_rect:
            x1, y1 = self.canvas_to_image(self.start_x, self.start_y)
            x2, y2 = self.canvas_to_image(event.x, event.y)

            # protects against misclicks
            if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
                return

            box = {
                "bbox": [x1, y1, x2, y2],
                "class": self.selected_class.get()
            }

            # remove temporary red box
            self.canvas.delete(self.active_rect)

            # add to BOTH:
            self.image_boxes.append(box)
            self.create_box(box)

            self.active_rect = None

    #TOGGLE BOXES (SHOW/HIDE)
    def redraw_boxes(self):
        if self.img is None:
            return

        self.canvas.delete("all")
        self.render_image()

        self.current_boxes = []

        for b in self.image_boxes:
            visible = self.class_vars.get(b["class"], tk.BooleanVar(value=True)).get()

            if visible:
                self.create_box(b)

    # BOX LOGIC
    def create_box(self, box):
        x1, y1, x2, y2 = box["bbox"]

        cx1, cy1 = self.image_to_canvas(x1, y1)
        cx2, cy2 = self.image_to_canvas(x2, y2)

        rect = self.canvas.create_rectangle(
            cx1, cy1, cx2, cy2,
            outline="green",
            width=2
        )

        obj = {
            "rect": rect,
            "bbox": box["bbox"],
            "class": box["class"],
            "ref": box
        }

        self.current_boxes.append(obj)

        self.canvas.tag_bind(rect, "<ButtonPress-1>", self.select_box)

    def highlight_box(self, box):
        # reset all boxes to green
        for b in self.current_boxes:
            self.canvas.itemconfig(b["rect"], outline="green", width=2)

        # highlight selected box
        self.canvas.itemconfig(box["rect"], outline="yellow", width=3)

    # SELECT + DRAG
    def select_box(self, rect_id, event=None):
        if event is None:
            return
            
        rect_id = self.canvas.find_closest(event.x, event.y)[0]

        for b in self.current_boxes:
            if b["rect"] == rect_id:
                self.selected_box = b
                self.highlight_box(b)
                break

    def drag_box(self, event):
        dx = (event.x - self.drag_data["x"]) / self.scale
        dy = (event.y - self.drag_data["y"]) / self.scale

        x1, y1, x2, y2 = self.active_box["bbox"]

        self.active_box["bbox"] = [x1 + dx, y1 + dy, x2 + dx, y2 + dy]

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

        cx1, cy1 = self.image_to_canvas(x1 + dx, y1 + dy)
        cx2, cy2 = self.image_to_canvas(x2 + dx, y2 + dy)

        self.canvas.coords(self.active_box["rect"], cx1, cy1, cx2, cy2)

    # DELETE / CANCEL
    def delete_box(self):
        if self.selected_box is None:
            return

        target = self.selected_box

        # remove from source of truth
        self.image_boxes.remove(target["ref"])

        # redraw everything (safe + consistent)
        self.redraw_boxes()

        self.selected_box = None

    def cancel_draw(self):
        if self.active_rect:
            self.canvas.delete(self.active_rect)
            self.active_rect = None

    # UTIL
    def canvas_to_image(self, x, y):
        return x / self.scale, y / self.scale

    def image_to_canvas(self, x, y):
        return x * self.scale, y * self.scale

    def zoom(self, event):
        self.scale *= 1.1 if event.delta > 0 else 0.9
        self.canvas.delete("all")
        self.render_image()

        old = self.current_boxes.copy()
        self.current_boxes = []

        for b in old:
            self.create_box(b)

    def jump_to_image(self):
        if not self.images:
            return

        try:
            idx = int(self.jump_entry.get()) - 1
        except ValueError:
            print("Invalid index")
            return

        # clamp to valid range
        idx = max(0, min(idx, len(self.images) - 1))

        # save current annotations first
        self.save_all_states()

        self.index = idx
        self.load_image()

    def only_int(self, value_if_allowed):
        if value_if_allowed == "":
            return True  # allow clearing field

        return value_if_allowed.isdigit()

    # NAV
    def next_image(self):
        self.save_state_file()
        if self.index < len(self.images) - 1:
            self.index += 1
            self.load_image()

    def prev_image(self):
        self.save_state_file()
        if self.index > 0:
            self.index -= 1
            self.load_image()

    # SAVE
    def save_all_states(self):
        if not self.current_path:
            return

        key = os.path.basename(self.current_path)

        self.state[key] = {
            "boxes": self.image_boxes,
            "hash": self.get_image_hash(self.current_path)
        }

        self.save_state_file()

    def save_file(self):
        self.save_all_states()
        print("File saved")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()