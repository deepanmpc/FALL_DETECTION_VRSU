import cv2
from flask import Flask, Response, jsonify, send_from_directory, request
from fall_detector import FallDetector
import time
import logger
import os
import threading
import numpy as np

app = Flask(__name__, static_folder='web_dashboard')

# Global Fall Detector Instance
detector = FallDetector()

# Global stream state
active_mode = None
target_video_path = "test_video.mp4"
latest_processed_frame = None

status_cache = {
    "status": "NORMAL",
    "angle": 90.0,
    "velocity": 0.0,
    "confidence": 0.0
}

def camera_worker_thread():
    """ Dedicated background thread to handle macOS VideoCapture thread-safety """
    global active_mode, target_video_path, latest_processed_frame, status_cache
    
    cap = None
    current_mode = None
    
    # Create a nice placeholder frame so the web stream doesn't crash on boot
    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(placeholder, "CONNECTING...", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    latest_processed_frame = placeholder
    
    while True:
        # State swap detection
        if current_mode != active_mode:
            if cap is not None:
                cap.release()
                cap = None
            
            detector.reset()
            current_mode = active_mode
            
            if current_mode == 'realtime':
                cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
            elif current_mode == 'video':
                cap = cv2.VideoCapture(target_video_path)
            else:
                cv2.putText(placeholder, "STREAM INACTIVE", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
                latest_processed_frame = placeholder

        # If we have no active feed, sleep
        if current_mode is None or cap is None or not cap.isOpened():
            time.sleep(0.1)
            continue
            
        ret, frame = cap.read()
        if not ret:
            if current_mode == "video":
                # Auto-loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                time.sleep(0.1)
            continue

        # AI Processing
        timestamp_ms = int(time.time() * 1000)
        processed_frame = detector.process_frame(frame, timestamp_ms)
        
        # Telemetry extraction
        if len(detector.tracked_persons) > 0:
            pid = list(detector.tracked_persons.keys())[0]
            state = detector.tracked_persons[pid]
            status_cache["status"] = state["status"]
            status_cache["confidence"] = state["confidence_score"] * 100
            status_cache["angle"] = state.get("angle", 0.0)
            status_cache["velocity"] = state.get("velocity", 0.0)
        else:
            status_cache["status"] = "NORMAL"
            status_cache["confidence"] = 0.0
            
        latest_processed_frame = processed_frame
        time.sleep(0.01) # Small sleep to yield CPU

# Boot the isolated camera thread
cam_thread = threading.Thread(target=camera_worker_thread, daemon=True)
cam_thread.start()


def generate_frames():
    global latest_processed_frame
    while True:
        if latest_processed_frame is not None:
            # Safely encode the latest physical frame
            ret, buffer = cv2.imencode('.jpg', latest_processed_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05) # ~20 FPS limit for the web stream

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    return jsonify(status_cache)

@app.route('/api/logs')
def get_logs():
    try:
        logs = logger.query_recent_falls(hours=24)
        formatted = []
        for row in logs:
            formatted.append({
                "id": row[0],
                "timestamp": row[1],
                "person_id": row[2],
                "event_type": row[3],
                "angle": row[4],
                "confidence": row[5],
                "duration": row[6]
            })
        return jsonify(formatted[:15])
    except Exception as e:
        return jsonify([])

@app.route('/api/control', methods=['POST'])
def control():
    global active_mode, target_video_path
    data = request.json
    mode = data.get('mode')
    
    if mode == 'realtime':
        active_mode = "realtime"
        return jsonify({"success": True, "message": "Camera Feed Request Sent"})
        
    elif mode == 'video':
        user_path = data.get('path', 'test_video.mp4')
        if not os.path.exists(user_path):
            return jsonify({"success": False, "message": f"Error: File {user_path} not found!"})
        target_video_path = user_path
        active_mode = "video"
        return jsonify({"success": True, "message": f"Video Feed '{user_path}' Request Sent"})
        
    elif mode == 'stop':
        active_mode = None
        return jsonify({"success": True, "message": "Feed Stopped"})
        
    return jsonify({"success": False, "message": "Invalid control mode"})

if __name__ == '__main__':
    print("====================================")
    print(" LARA VISION WEB SERVER STARTING... ")
    print(" Available on: http://localhost:5005")
    print("====================================")
    
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['GLOG_minloglevel'] = '2'
    
    app.run(host='0.0.0.0', port=5005, threaded=True)
