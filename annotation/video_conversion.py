import cv2
import os
import json

# CONFIG
VIDEO_DIR = "data/testing_data"
OUTPUT_DIR = "data/training_data"
PROCESSED_FILE = "annotation/processed_videos.json"

FPS = 1
WIDTH = 640

os.makedirs(OUTPUT_DIR, exist_ok=True)

# LOAD PROCESSED LIST
if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE, "r") as f:
        processed_videos = set(json.load(f))
else:
    processed_videos = set()

# PROCESS VIDEOS
video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]

for video_name in video_files:

    if video_name in processed_videos:
        print(f"Skipping (already processed): {video_name}")
        continue

    print(f"Processing: {video_name}")

    video_path = os.path.join(VIDEO_DIR, video_name)
    cap = cv2.VideoCapture(video_path)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / FPS)

    frame_count = 0
    saved_count = 0

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            h, w, _ = frame.shape
            new_height = int((WIDTH / w) * h)
            frame_resized = cv2.resize(frame, (WIDTH, new_height))

            filename = os.path.join(
                OUTPUT_DIR, video_name+f"frame_{saved_count:04d}.jpg"
            )
            cv2.imwrite(filename, frame_resized)

            saved_count += 1

        frame_count += 1

    cap.release()

    print(f"Saved {saved_count} frames for {video_name}")

    # mark as processed
    processed_videos.add(video_name)

    # save immediately (safe if crash happens later)
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed_videos), f, indent=2)

print("Done.")