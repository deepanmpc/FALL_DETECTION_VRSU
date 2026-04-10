import cv2
import time
from fall_detector import FallDetector

def main():
    # Instantiate the class-based detector
    detector = FallDetector()
    cap = cv2.VideoCapture(0)
    
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Calculate real elapsed timestamp in milliseconds
        timestamp_ms = int((time.time() - start_time) * 1000)

        processed_frame = detector.process_frame(frame, timestamp_ms)

        cv2.imshow("Live Fall Detection", processed_frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
