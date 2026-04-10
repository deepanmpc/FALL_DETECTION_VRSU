import cv2
from fall_detector import FallDetector
import os

def main():
    # Instantiate the class-based detector
    detector = FallDetector()
    video_path = "test_video.mp4"
    
    # Graceful fallback if video doesn't exist
    if not os.path.exists(video_path):
        print(f"Warning: {video_path} not found. Please provide a valid video file.")
        return

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
        
    frame_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_ms = int((frame_number / fps) * 1000)
        frame_number += 1

        processed_frame = detector.process_frame(frame, timestamp_ms)

        cv2.imshow("Video Fall Detection", processed_frame)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
