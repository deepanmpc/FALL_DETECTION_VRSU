import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Download pose model file first:
# https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task

model_path = "pose_landmarker_full.task"

BaseOptions = python.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions
VisionRunningMode = vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO
)

landmarker = PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)  # Use 0 for webcam, or provide video file path")

fall_counter = 0
FALL_THRESHOLD = 15

def calculate_angle(a, b):
    angle = np.arctan2(b[1] - a[1], b[0] - a[0])
    return np.degrees(angle)

frame_timestamp = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = landmarker.detect_for_video(mp_image, frame_timestamp)
    frame_timestamp += 1

    if result.pose_landmarks:
        landmarks = result.pose_landmarks[0]

        shoulder = [landmarks[11].x, landmarks[11].y]
        hip = [landmarks[23].x, landmarks[23].y]

        angle = abs(calculate_angle(shoulder, hip))

        if angle < 30:
            fall_counter += 1
        else:
            fall_counter = 0

        if fall_counter > FALL_THRESHOLD:
            cv2.putText(frame, "FALL DETECTED", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 3)

    cv2.imshow("Fall Detection", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()