import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

# ====== MODEL PATH ======
model_path = os.path.join(os.getcwd(), "pose_landmarker_full.task")

BaseOptions = python.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions
VisionRunningMode = vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO
)

landmarker = PoseLandmarker.create_from_options(options)

# ====== VIDEO SOURCE ======
video_path = "test_video.mp4"  # change filename if needed
cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
frame_number = 0

fall_counter = 0
FALL_THRESHOLD = int(fps * 1)  # 1 second duration

def calculate_angle(a, b):
    angle = np.arctan2(b[1] - a[1], b[0] - a[0])
    return np.degrees(angle)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    timestamp = int((frame_number / fps) * 1000)  # milliseconds
    frame_number += 1

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = landmarker.detect_for_video(mp_image, timestamp)

    if result.pose_landmarks:
        landmarks = result.pose_landmarks[0]

        # LEFT SHOULDER (11), LEFT HIP (23)
        shoulder = [landmarks[11].x, landmarks[11].y]
        hip = [landmarks[23].x, landmarks[23].y]

        angle = abs(calculate_angle(shoulder, hip))

        # ===== Fall Logic =====
        if angle < 30:   # near horizontal
            fall_counter += 1
        else:
            fall_counter = 0

        if fall_counter > FALL_THRESHOLD:
            cv2.putText(frame, "FALL DETECTED",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3)

        # Draw skeleton
        for lm in landmarks:
            h, w, _ = frame.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, (0,255,0), -1)

    cv2.imshow("Video Fall Detection", frame)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()