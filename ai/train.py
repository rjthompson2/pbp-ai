# import torch
# from torch.utils.data import DataLoader
# from rfdetr import RFDETRBase
# from rfdetr.datasets import build_dataset
# from types import SimpleNamespace

# # Setup
# device = "cuda" if torch.cuda.is_available() else "cpu"

# # Dataset
# dataset = build_dataset(
#     image_set="train",
#     args=SimpleNamespace(
#         coco_path="./data",
#         dataset_file="coco",
#         multi_scale=False,
#         masks=False,
#         cache_mode=False,
#         expanded_scales=False,
#         do_random_resize_via_padding=False,
#         patch_size=16,
#         num_windows=0,
#     ),
#     resolution=256
# )

# dataloader = DataLoader(
#     dataset,
#     batch_size=1,
#     shuffle=True,
#     collate_fn=lambda x: tuple(zip(*x))  # REQUIRED for DETR-style models
# )

# # Model
# num_classes = 2 # CHANGE THIS
# model = RFDETRBase(num_classes=num_classes, device=device)

# # Optional: load pretrained weights
# # model.load_state_dict(torch.load("rf-detr-base.pth"))

# # Optimizer
# optimizer = torch.optim.AdamW(model.model.model.parameters(), lr=1e-4)

# # Training loop
# num_epochs = 1

# for epoch in range(num_epochs):
#     model.train(
#         dataset_dir="./data",
#         dataset_file="coco",
#         num_workers=2,
#         resolution=280,
#         skip_val=True
#     )
#     total_loss = 0

#     for images, targets in dataloader:
#         images = [img.to(device) for img in images]
#         targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

#         outputs = model(images, targets)

#         # RF-DETR returns a dict of losses
#         loss_dict = outputs
#         loss = sum(loss_dict.values())

#         optimizer.zero_grad()
#         loss.backward()
#         optimizer.step()

#         total_loss += loss.item()

#     print(f"Epoch {epoch} Loss: {total_loss:.4f}")

#     torch.save(model.state_dict(), f"ai/model/model_epoch_{epoch}.pth")

import os
import json
import shutil
from ultralytics import YOLO
from tqdm import tqdm
import random
from PIL import Image
from collections import defaultdict

# PATHS
COCO_JSON = "./data/annotations/coco_annotations.json"
IMAGES_DIR = "./data/training_data"

YOLO_DIR = "./data_yolo"
IMAGES_OUT = os.path.join(YOLO_DIR, "images")
LABELS_OUT = os.path.join(YOLO_DIR, "labels")

os.makedirs(IMAGES_OUT + "/train", exist_ok=True)
os.makedirs(IMAGES_OUT + "/val", exist_ok=True)
os.makedirs(LABELS_OUT + "/train", exist_ok=True)
os.makedirs(LABELS_OUT + "/val", exist_ok=True)

# LOAD COCO
with open(COCO_JSON) as f:
    coco = json.load(f)

images = coco["images"]
annotations = coco["annotations"]
categories = coco["categories"]

# Shuffle images for random training and validation
random.seed(42)
random.shuffle(images)

# Map image_id → image info
image_map = {img["id"]: img for img in images}

# Map category_id → 0-based index
cat_map = {cat["id"]: i for i, cat in enumerate(categories)}

# SIMPLE TRAIN/VAL SPLIT
split_index = int(0.8 * len(images))
train_images = images[:split_index]
val_images = images[split_index:]

train_ids = set(img["id"] for img in train_images)
val_ids = set(img["id"] for img in val_images)

# CONVERT COCO → YOLO
def convert_annotations(image_list, split):
    for img in tqdm(image_list, desc=f"Converting {split}"):
        img_id = img["id"]
        file_name = img["file_name"]

        # inside function
        img_path = os.path.join(IMAGES_DIR, file_name)

        try:
            with Image.open(img_path) as im:
                width, height = im.size
        except Exception as e:
            print(f"Error reading image {img_path}: {e}")
            continue

        src_path = os.path.join(IMAGES_DIR, file_name)
        dst_path = os.path.join(IMAGES_OUT, split, file_name)

        if not os.path.exists(src_path):
            print(f"Missing image: {src_path}")
            continue

        if not os.path.exists(dst_path):
            shutil.copy(src_path, dst_path)

        label_name = os.path.splitext(file_name)[0] + ".txt"
        label_path = os.path.join(LABELS_OUT, split, label_name)

        ann_map = defaultdict(list)

        for ann in annotations:
            ann_map[ann["image_id"]].append(ann)

        with open(label_path, "w") as f:
            for ann in ann_map[img_id]:
                x, y, w, h = ann["bbox"]
                class_id = cat_map[ann["category_id"]]

                x_center = (x + w / 2) / width
                y_center = (y + h / 2) / height
                w /= width
                h /= height

                f.write(f"{class_id} {x_center} {y_center} {w} {h}\n")

# Run conversion
convert_annotations(train_images, "train")
convert_annotations(val_images, "val")

# CREATE data.yaml
yaml_path = os.path.join(YOLO_DIR, "data.yaml")

with open(yaml_path, "w") as f:
    f.write(f"path: {YOLO_DIR}\n")
    f.write("train: images/train\n")
    f.write("val: images/val\n")
    f.write("names:\n")
    for i, cat in enumerate(categories):
        f.write(f"  {i}: {cat['name']}\n")

# TRAIN YOLO
model = YOLO("ai/model/yolov8n.pt")  # lightweight model

model.train(
    data=yaml_path,
    epochs=3,
    imgsz=320,
    batch=8,
    workers=4,
    verbose=True
)