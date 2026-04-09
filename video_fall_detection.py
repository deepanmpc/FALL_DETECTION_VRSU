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
FALL_THRESHOLD = int(fps * 0.2)  # Reduced latency
LONG_FALL_THRESHOLD = int(fps * 10) # 10 seconds duration

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

        # Get coordinates for both sides to improve accuracy
        l_shoulder = [landmarks[11].x, landmarks[11].y]
        r_shoulder = [landmarks[12].x, landmarks[12].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        r_hip = [landmarks[24].x, landmarks[24].y]

        # Calculate midpoints
        shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]

        # Calculate lean angle from vertical (0 degrees = upright, 90 degrees = horizontal)
        dy = abs(shoulder[1] - hip[1])
        dx = abs(shoulder[0] - hip[0])
        
        # Use arctan(dx/dy) for angle from vertical
        if dy == 0:
            angle = 90.0
        else:
            angle = np.degrees(np.arctan(dx / dy))

        # ===== Fall Logic =====
        # Thresholds:
        # 30-60 degrees: About to fall / Unstable
        # > 60 degrees: Fallen

        if angle > 60:
            fall_counter += 1
            status = "FALLEN"
        elif angle > 30:
            fall_counter = 0  # Reset fall counter as they haven't fully fallen yet
            status = "ABOUT_TO_FALL"
        else:
            fall_counter = 0
            status = "NORMAL"

        if status == "ABOUT_TO_FALL":
             cv2.putText(frame, "ABOUT TO FALL", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 255), 3) # Yellow

        if fall_counter > FALL_THRESHOLD:
            cv2.putText(frame, "FALL DETECTED",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3) # Red
            
            if fall_counter > LONG_FALL_THRESHOLD:
                cv2.putText(frame, "CAUTION: Extended Fall",
                        (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 128, 255),
                        2)

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