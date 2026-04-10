import os
# Suppress noisy TensorFlow and glog INFO/WARNING logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

import cv2
import time
from fall_detector import FallDetector

def main():
    print("Initializing AI models... (this takes a moment)")
    # Instantiate the class-based detector
    detector = FallDetector()
    
    print("Booting up webcam...")
    # Using CAP_AVFOUNDATION fixes the slow camera startup delay heavily present on maxOS
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    
    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return

    start_time = time.time()

    print("\n=============================================")
    print("       REAL-TIME DETECTION ACTIVE            ")
    print(" >> PRESS 'q' in the video window to EXIT << ")
    print(" >> Or press Ctrl+C in this terminal         ")
    print("=============================================\n")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Calculate real elapsed timestamp in milliseconds
            timestamp_ms = int((time.time() - start_time) * 1000)

            # Process the frame
            processed_frame = detector.process_frame(frame, timestamp_ms)

            # Make the exit command visually clear on the screen as well
            cv2.putText(processed_frame, "Press 'Q' to Exit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Display the resulting frame
            cv2.imshow("Live Fall Detection", processed_frame)
            
            # Using waitKey(1) instead of waitKey(10) to make keypress more responsive
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n'q' pressed. Exiting...")
                break
                
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting gracefully...")
        
    finally:
        # Guarantee cleanup happens no matter how we exit
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
