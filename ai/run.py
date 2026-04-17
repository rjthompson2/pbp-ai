from ultralytics import YOLO
import cv2
import os
import json

# CONFIG
MODEL_PATH = "ai/model/yolov8n.pt"
VIDEO_PATH = input("Enter video path: ")

output_video = "data/ml_output/" + VIDEO_PATH.split("/")[-1] + "_annotated.mp4"

DATASET_DIR = "data/testing_data"
IMG_DIR = f"{DATASET_DIR}/images"
LBL_DIR = f"{DATASET_DIR}/labels"

STATE_PATH = "data/annotations/state.json"

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(LBL_DIR, exist_ok=True)
os.makedirs("ml_output", exist_ok=True)

# LOAD STATE
if os.path.exists(STATE_PATH):
    with open(STATE_PATH, "r") as f:
        state = json.load(f)
else:
    state = {}

# LOAD MODEL
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

out = cv2.VideoWriter(
    output_video,
    cv2.VideoWriter_fourcc(*"mp4v"),
    fps,
    (width, height)
)

frame_id = 0

# PROCESS VIDEO
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_name = f"frame_{frame_id:06d}.jpg"

    # ----------------------------
    # SKIP IF ALREADY ANNOTATED
    # ----------------------------
    if frame_name in state:
        print(f"Skipping {frame_name} (already annotated)")
        frame_id += 1
        continue

    results = model(frame, imgsz=320, conf=0.25)
    r = results[0]
    annotated = r.plot()

    # SAVE IMAGE ONLY IF NEW
    img_path = os.path.join(IMG_DIR, frame_name)
    cv2.imwrite(img_path, frame)

    # SAVE LABELS
    label_path = os.path.join(LBL_DIR, f"frame_{frame_id:06d}.txt")

    boxes_out = []

    with open(label_path, "w") as f:
        if r.boxes is not None:
            for box in r.boxes:
                cls = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                w = (x2 - x1) / width
                h = (y2 - y1) / height

                f.write(f"{cls} {x_center} {y_center} {w} {h}\n")

                boxes_out.append({
                    "class": cls,
                    "bbox": [x1, y1, x2, y2]
                })

    # UPDATE STATE (mark as auto-labeled)
    state[frame_name] = {
        "boxes": boxes_out,
        "auto_labeled": True
    }

    # SAVE STATE EVERY FRAME (safe for crash recovery)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    # VIDEO OUTPUT
    out.write(annotated)

    # LIVE PREVIEW
    cv2.imshow("YOLO Output", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    frame_id += 1

cap.release()
out.release()
cv2.destroyAllWindows()

print("Done. Dataset + state updated.")