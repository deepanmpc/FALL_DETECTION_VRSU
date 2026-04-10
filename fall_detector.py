import cv2
import numpy as np
import math
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
from config import active_config
from alerts import send_alerts_async
from logger import log_event

class FallDetector:
    def __init__(self, config=None):
        self.config = config or active_config
        self.tracked_persons = {}
        self.next_person_id = 1
        self.MAX_DISTANCE = 150
        
        base_options = python.BaseOptions(model_asset_path=self.config["model_path"])
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=5
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def reset(self):
        """Resets the tracking state."""
        self.tracked_persons = {}
        self.next_person_id = 1

    def get_status(self, person_id):
        """Returns the current state dict for a specific person."""
        return self.tracked_persons.get(person_id)

    def process_frame(self, frame, timestamp_ms):
        """
        Main entry point for processing a video frame.
        Detects poses, assigns IDs, tracks logic, and overlays visualization.
        """
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        result = self.landmarker.detect_for_video(mp_image, int(timestamp_ms))
        
        current_frame_centroids = []
        if result.pose_landmarks:
            for landmarks in result.pose_landmarks:
                min_x = min([lm.x * w for lm in landmarks])
                max_x = max([lm.x * w for lm in landmarks])
                min_y = min([lm.y * h for lm in landmarks])
                max_y = max([lm.y * h for lm in landmarks])
                bbox_area = (max_x - min_x) * (max_y - min_y)
                
                # Distance normalization: Ignore if too small/far
                if bbox_area < self.config["min_bbox_area"]:
                    continue
                    
                cx = sum([lm.x * w for lm in landmarks]) / len(landmarks)
                cy = sum([lm.y * h for lm in landmarks]) / len(landmarks)
                current_frame_centroids.append(((cx, cy), landmarks, bbox_area, min_x, max_x, min_y, max_y))

        updated_tracked_persons = {}
        
        for centroid, landmarks, bbox_area, min_x, max_x, min_y, max_y in current_frame_centroids:
            best_match_id = None
            best_match_dist = float('inf')
            
            for person_id, state in self.tracked_persons.items():
                dist = math.dist(centroid, state["centroid"])
                if dist < best_match_dist and dist < self.MAX_DISTANCE:
                    best_match_dist = dist
                    best_match_id = person_id
                    
            if best_match_id is not None:
                state = self.tracked_persons.pop(best_match_id)
                state["centroid"] = centroid
                updated_tracked_persons[best_match_id] = state
            else:
                updated_tracked_persons[self.next_person_id] = {
                    "centroid": centroid,
                    "fall_counter": 0,
                    "status": "NORMAL",
                    "nose_y_history": [],
                    "confidence_score": 0.0,
                    "fallen_time": None,
                    "stumble_time": None,
                    "last_state_change_time": time.time()
                }
                best_match_id = self.next_person_id
                self.next_person_id += 1
                
            state = updated_tracked_persons[best_match_id]
            old_status = state["status"]
            
            l_shoulder = [landmarks[11].x, landmarks[11].y]
            r_shoulder = [landmarks[12].x, landmarks[12].y]
            l_hip = [landmarks[23].x, landmarks[23].y]
            r_hip = [landmarks[24].x, landmarks[24].y]

            shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
            hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]

            dy = abs(shoulder[1] - hip[1])
            dx = abs(shoulder[0] - hip[0])
            
            angle = 90.0 if dy == 0 else np.degrees(np.arctan(dx / dy))

            # Head Velocity tracking
            nose_y = landmarks[0].y
            state["nose_y_history"].append(nose_y)
            if len(state["nose_y_history"]) > 10:
                state["nose_y_history"].pop(0)

            velocity = 0.0
            if len(state["nose_y_history"]) >= 2:
                velocity = state["nose_y_history"][-1] - state["nose_y_history"][-2]

            # Distance normalization logic on thresholds
            area_factor = max(1.0, 50000.0 / max(bbox_area, 1.0))
            dynamic_fall_angle = self.config["fall_angle_threshold"] + (area_factor * 5)
            dynamic_about_to_fall = self.config["about_to_fall_threshold"] + (area_factor * 2)

            if angle > dynamic_fall_angle:
                state["fall_counter"] += 1
                base_confidence = 0.5
                if velocity > self.config["head_velocity_threshold"]:
                    base_confidence += 0.3
                state["confidence_score"] = min(1.0, base_confidence)

                if state["fall_counter"] > self.config["fall_frame_threshold"] and state["confidence_score"] > self.config["confidence_threshold"]:
                    if state["fallen_time"] is None:
                        state["fallen_time"] = timestamp_ms
                    
                    time_since_fall = (timestamp_ms - state["fallen_time"]) / 1000.0
                    
                    # Activity Disambiguation: Floor Activity
                    l_wrist_y = landmarks[15].y
                    r_wrist_y = landmarks[16].y
                    l_hip_y = landmarks[23].y
                    r_hip_y = landmarks[24].y
                    
                    wrists_below_hips = (l_wrist_y > l_hip_y) and (r_wrist_y > r_hip_y)
                    
                    if wrists_below_hips and time_since_fall < 3.0:
                        state["status"] = "FLOOR_ACTIVITY"
                    else:
                        if state["status"] != "FALLEN":
                            state["status"] = "FALLEN"
                            # Trigger Alerts
                            snapshot_path = f"fall_snapshot_{best_match_id}_{int(timestamp_ms)}.jpg"
                            cv2.imwrite(snapshot_path, frame)
                            send_alerts_async(best_match_id, timestamp_ms, snapshot_path)
                else:
                    state["status"] = "ABOUT_TO_FALL"
            elif angle > dynamic_about_to_fall:
                state["fall_counter"] = 0 
                if state["status"] not in ["FALLEN", "FLOOR_ACTIVITY"]:
                    state["status"] = "ABOUT_TO_FALL"
                state["confidence_score"] = 0.3
            else:
                state["fall_counter"] = 0
                state["confidence_score"] = 0.0
                
                # Activity Disambiguation: Stumble vs Normal
                if state["status"] in ["FALLEN", "FLOOR_ACTIVITY"]:
                    if state["fallen_time"] is not None and ((timestamp_ms - state["fallen_time"]) / 1000.0) < 5.0:
                        state["status"] = "STUMBLE"
                        state["stumble_time"] = timestamp_ms
                    else:
                        state["status"] = "NORMAL"
                elif state["status"] == "STUMBLE":
                    if state["stumble_time"] is not None and ((timestamp_ms - state["stumble_time"]) / 1000.0) > 3.0:
                        state["status"] = "NORMAL"
                else:
                    state["status"] = "NORMAL"
                    
                if state["status"] not in ["STUMBLE", "FALLEN", "FLOOR_ACTIVITY"]:
                    state["fallen_time"] = None
                    
            # Log transition events
            new_status = state["status"]
            if old_status != new_status:
                duration = time.time() - state.get("last_state_change_time", time.time())
                log_event(time.time(), best_match_id, new_status, angle, state["confidence_score"], duration, int(timestamp_ms))
                state["last_state_change_time"] = time.time()
                
            state["landmarks"] = landmarks
            state["bbox"] = (min_x, max_x, min_y, max_y)

        self.tracked_persons = updated_tracked_persons

        # Draw overlays
        for person_id, state in self.tracked_persons.items():
            if "landmarks" not in state:
                continue
            landmarks = state["landmarks"]
            min_x, max_x, min_y, max_y = state["bbox"]
            
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 3, (0,255,0), -1)
                
            cv2.rectangle(frame, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (255, 0, 0), 2)
            
            color = (0, 255, 0)
            display_text = f"ID: {person_id} - {state['status']} (Conf: {state['confidence_score']:.2f})"
            
            if state["status"] == "ABOUT_TO_FALL":
                color = (0, 255, 255)
            elif state["status"] == "FLOOR_ACTIVITY":
                color = (255, 165, 0)
            elif state["status"] == "STUMBLE":
                color = (255, 255, 0)
            elif state["status"] == "FALLEN":
                color = (0, 0, 255)
                display_text = f"ID: {person_id} - FALL DETECTED (Conf: {state['confidence_score']:.2f})"
                    
            cv2.putText(frame, display_text, (int(min_x), int(min_y) - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
        return frame
