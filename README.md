# Fall Detection System (VRSU)

A real-time fall detection application leveraging MediaPipe's Pose Landmarker to monitor human posture and detect potential falls from both live webcam feeds and recorded video files.

## 🚀 Features

- **Real-time Webcam Detection**: Monitor live video streams for immediate fall detection (`main.py`).
- **Video Analysis**: Process pre-recorded video files (`test_video.mp4`) with advanced detection logic (`video_fall_detection.py`).
- **Posture Monitoring**: Calculates the lean angle from the vertical to determine stability.
- **Multi-state Alerts**:
  - `NORMAL`: Upright posture.
  - `ABOUT TO FALL`: Detected unstable angle (30-60 degrees).
  - `FALL DETECTED`: Horizontal posture detected for a sustained period.
  - `CAUTION: Extended Fall`: Alert for falls lasting longer than 10 seconds.
- **Skeleton Visualization**: Overlays pose landmarks on the video for debugging and visual confirmation.

## 🛠️ Requirements

- Python 3.x
- OpenCV (`cv2`)
- NumPy
- MediaPipe

## 📥 Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/deepanmpc/FALL_DETECTION_VRSU.git
    cd FALL_DETECTION_VRSU
    ```

2.  **Install dependencies**:
    ```bash
    pip install opencv-python numpy mediapipe
    ```

3.  **Download the Pose Model**:
    The system requires the `pose_landmarker_full.task` model. You can download it from [Google's MediaPipe models](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task) and place it in the project root.

## 🏃 Usage

### Live Webcam Detection
Run the `main.py` script to start monitoring via your default webcam:
```bash
python main.py
```

### Video File Detection
To analyze a video file, ensure it is named `test_video.mp4` (or update the path in the script) and run:
```bash
python video_fall_detection.py
```

## ⚖️ How it Works

The system calculates the angle between the shoulders and hips relative to the vertical axis. 
- An angle near **0°** indicates an upright person.
- An angle exceeding **60°** for a specific number of frames triggers a **FALL DETECTED** alert.
- The video processing script uses a dynamic threshold based on the video's FPS for better accuracy.
