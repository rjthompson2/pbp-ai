import os
import json
import shutil
from ultralytics import YOLO
from tqdm import tqdm
from collections import defaultdict
from PIL import Image

STATE_JSON = "./data/annotations/state.json"
IMAGES_DIR = "./data/training_data"

YOLO_DIR = "./data_yolo"
IMG_OUT = os.path.join(YOLO_DIR, "images")
LBL_OUT = os.path.join(YOLO_DIR, "labels")

os.makedirs(IMG_OUT + "/train", exist_ok=True)
os.makedirs(IMG_OUT + "/val", exist_ok=True)
os.makedirs(LBL_OUT + "/train", exist_ok=True)
os.makedirs(LBL_OUT + "/val", exist_ok=True)

# LOAD STATE.JSON
with open(STATE_JSON) as f:
    state = json.load(f)

# BUILD CLASS MAP
classes = set()

for img_data in state.values():
    for b in img_data.get("boxes", []):
        classes.add(b["class"])

classes = sorted(list(classes))
class_map = {c: i for i, c in enumerate(classes)}

# SPLIT IMAGES
all_images = list(state.items())

train_size = int(0.8 * len(all_images))

train_items = all_images[:train_size]
val_items = all_images[train_size:]

# CONVERT
def convert(items, split):
    for img_name, data in tqdm(items, desc=f"Converting {split}"):

        img_path = os.path.join(IMAGES_DIR, img_name)

        if not os.path.exists(img_path):
            continue

        try:
            with Image.open(img_path) as im:
                w_img, h_img = im.size
        except:
            continue

        # copy image
        dst_img = os.path.join(IMG_OUT, split, img_name)
        if not os.path.exists(dst_img):
            shutil.copy(img_path, dst_img)

        boxes = data.get("boxes", [])

        # skip unannotated images
        if len(boxes) == 0:
            continue

        label_path = os.path.join(
            LBL_OUT,
            split,
            os.path.splitext(img_name)[0] + ".txt"
        )

        with open(label_path, "w") as f:
            wrote = False

            for b in boxes:
                x1, y1, x2, y2 = b["bbox"]
                cls = class_map[b["class"]]

                # convert to YOLO format
                x_center = ((x1 + x2) / 2) / w_img
                y_center = ((y1 + y2) / 2) / h_img
                w = (x2 - x1) / w_img
                h = (y2 - y1) / h_img

                f.write(f"{cls} {x_center} {y_center} {w} {h}\n")
                wrote = True

        if not wrote:
            os.remove(label_path)

# RUN
convert(train_items, "train")
convert(val_items, "val")

# DATA.YAML
yaml_path = os.path.join(YOLO_DIR, "data.yaml")

with open(yaml_path, "w") as f:
    f.write(f"path: {YOLO_DIR}\n")
    f.write("train: images/train\n")
    f.write("val: images/val\n")
    f.write("names:\n")
    for i, c in enumerate(classes):
        f.write(f"  {i}: {c}\n")

# TRAIN
model = YOLO("yolov8n.pt")

model.train(
    data=yaml_path,
    epochs=5,
    imgsz=320,
    batch=8,
    workers=4
)