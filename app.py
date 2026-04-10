import cv2
from flask import Flask, Response, jsonify, send_from_directory, request
from fall_detector import FallDetector
import time
import logger
import os

app = Flask(__name__, static_folder='web_dashboard')

# Global Fall Detector Instance
detector = FallDetector()

# Global stream state
cap = None
active_mode = None
status_cache = {
    "status": "NORMAL",
    "angle": 90.0,
    "velocity": 0.0,
    "confidence": 0.0
}

def generate_frames():
    global cap, active_mode, status_cache
    while True:
        if cap is None or not cap.isOpened():
            time.sleep(0.1)
            continue
            
        ret, frame = cap.read()
        if not ret:
            # If video ends, loop it automatically
            if active_mode == "video":
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                time.sleep(0.1)
                continue

        timestamp_ms = int(time.time() * 1000)
        
        # Process frame
        processed_frame = detector.process_frame(frame, timestamp_ms)
        
        # Push live metrics up to HTML Status API
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
            
        # Encode Frame to JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        
        # Boundary generator stream for MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

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
        return jsonify(formatted[:15])  # Return the latest 15 events
    except Exception as e:
        return jsonify([])

@app.route('/api/control', methods=['POST'])
def control():
    global cap, active_mode
    data = request.json
    mode = data.get('mode')
    
    # Cleanup previous instances
    if cap is not None:
        cap.release()
        
    detector.reset()
    status_cache["status"] = "NORMAL"
    status_cache["confidence"] = 0.0
    
    if mode == 'realtime':
        # Fast cam startup for macOS
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        active_mode = "realtime"
        return jsonify({"success": True, "message": "Camera Feed Started"})
        
    elif mode == 'video':
        video_path = data.get('path', 'test_video.mp4')
        if not os.path.exists(video_path):
            return jsonify({"success": False, "message": f"Error: File {video_path} not found!"})
        cap = cv2.VideoCapture(video_path)
        active_mode = "video"
        return jsonify({"success": True, "message": f"Video Feed '{video_path}' Started"})
        
    elif mode == 'stop':
        active_mode = None
        cap = None
        return jsonify({"success": True, "message": "Feed Stopped"})
        
    return jsonify({"success": False, "message": "Invalid control mode"})

if __name__ == '__main__':
    print("====================================")
    print(" LARA VISION WEB SERVER STARTING... ")
    print(" Available on: http://localhost:5005")
    print("====================================")
    
    # Disable spammy CV logs
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['GLOG_minloglevel'] = '2'
    
    app.run(host='0.0.0.0', port=5005, threaded=True)
