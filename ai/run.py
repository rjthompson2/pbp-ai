from ultralytics import YOLO
import cv2
import os

# CONFIG
MODEL_PATH = "ai/model/yolov8n.pt"
VIDEO_PATH = input("Enter video path")

output_video = "ml_output/"+VIDEO_PATH.split("/")[-1]+"annotated.mp4"
DATASET_DIR = "auto_dataset"

IMG_DIR = f"{DATASET_DIR}/images"
LBL_DIR = f"{DATASET_DIR}/labels"

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(LBL_DIR, exist_ok=True)

# LOAD MODEL
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

width = int(cap.get(3))
height = int(cap.get(4))
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

    results = model(frame, imgsz=320, conf=0.25)

    r = results[0]
    annotated = r.plot()

    # SAVE IMAGE
    img_path = os.path.join(IMG_DIR, f"frame_{frame_id:06d}.jpg")
    cv2.imwrite(img_path, frame)

    # SAVE LABELS (YOLO format)
    label_path = os.path.join(LBL_DIR, f"frame_{frame_id:06d}.txt")

    with open(label_path, "w") as f:
        if r.boxes is not None:
            for box in r.boxes:
                cls = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # convert to YOLO format
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                w = (x2 - x1) / width
                h = (y2 - y1) / height

                f.write(f"{cls} {x_center} {y_center} {w} {h}\n")

    # SAVE VIDEO OUTPUT
    out.write(annotated)

    # OPTIONAL: live preview
    cv2.imshow("YOLO Output", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    frame_id += 1

cap.release()
out.release()
cv2.destroyAllWindows()

print("Done. Dataset + video saved.")