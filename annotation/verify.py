import os
import json
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw

class COCOViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("COCO Annotation Viewer")

        # Canvas
        self.canvas = tk.Canvas(root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Controls
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(fill=tk.X)

        tk.Button(self.btn_frame, text="Load COCO JSON", command=self.load_coco).pack(side=tk.LEFT)

        # Data
        self.images = []
        self.annotations = {}
        self.categories = {}
        self.image_index = 0

        self.tk_img = None
        self.img = None

        # Keyboard
        root.bind("d", lambda e: self.next_image())
        root.bind("a", lambda e: self.prev_image())

    # LOAD COCO
    def load_coco(self):
        json_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not json_path:
            return

        with open(json_path, "r") as f:
            data = json.load(f)

        # categories
        self.categories = {
            c["id"]: c["name"] for c in data.get("categories", [])
        }

        # images
        self.images = data.get("images", [])

        # annotations grouped by image_id
        self.annotations = {}
        for ann in data.get("annotations", []):
            img_id = ann["image_id"]
            self.annotations.setdefault(img_id, []).append(ann)

        self.image_index = 0
        self.show_image()

    # SHOW IMAGE
    def show_image(self):
        if not self.images:
            return

        img_info = self.images[self.image_index]

        img_path = self.find_image(img_info["file_name"])
        if not img_path:
            print("Missing image:", img_info["file_name"])
            return

        try:
            self.img = Image.open(img_path).convert("RGB")
        except Exception as e:
            print("Skipping bad image:", img_path, e)
            return

        draw = ImageDraw.Draw(self.img)

        img_id = img_info["id"]
        anns = self.annotations.get(img_id, [])

        for ann in anns:
            x, y, w, h = ann["bbox"]
            x2, y2 = x + w, y + h

            draw.rectangle([x, y, x2, y2], outline="red", width=3)

            cat_id = ann["category_id"]
            label = self.categories.get(cat_id, str(cat_id))

            draw.text((x, y), label, fill="yellow")

        # resize for display
        display = self.img.resize((900, 700))
        self.tk_img = ImageTk.PhotoImage(display)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        self.root.title(f"Image {self.image_index+1}/{len(self.images)}")

    # FIND IMAGE
    def find_image(self, filename):
        # assumes images are in same folder or subfolders
        for root, _, files in os.walk("."):
            if filename in files:
                return os.path.join(root, filename)
        return None

    # NAVIGATION
    def next_image(self):
        if self.image_index < len(self.images) - 1:
            self.image_index += 1
            self.show_image()

    def prev_image(self):
        if self.image_index > 0:
            self.image_index -= 1
            self.show_image()


if __name__ == "__main__":
    root = tk.Tk()
    app = COCOViewer(root)
    root.mainloop()