import pytest
import numpy as np
import time
import cv2
from unittest.mock import MagicMock, patch
from fall_detector import FallDetector

class MockLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def create_synthetic_landmarks(pose_type="normal"):
    """Generates synthetic MediaPipe landmarks for specific posture scenarios."""
    landmarks = [MockLandmark(0.5, 0.5) for _ in range(33)]
    
    if pose_type == "normal":
        # Upright posture
        landmarks[11] = MockLandmark(0.4, 0.2) # shoulders
        landmarks[12] = MockLandmark(0.6, 0.2)
        landmarks[23] = MockLandmark(0.45, 0.6) # hips
        landmarks[24] = MockLandmark(0.55, 0.6)
        landmarks[0] = MockLandmark(0.5, 0.1) # nose
        landmarks[15] = MockLandmark(0.3, 0.4) # wrists above hips
        landmarks[16] = MockLandmark(0.7, 0.4)
    elif pose_type == "fallen":
        # Horizontal posture (angle > 60 degrees)
        landmarks[11] = MockLandmark(0.2, 0.8) # shoulders
        landmarks[12] = MockLandmark(0.2, 0.9)
        landmarks[23] = MockLandmark(0.7, 0.85) # hips
        landmarks[24] = MockLandmark(0.7, 0.95)
        landmarks[0] = MockLandmark(0.1, 0.9) # nose dropped rapidly
        landmarks[15] = MockLandmark(0.3, 0.8) # wrists
        landmarks[16] = MockLandmark(0.3, 0.9)
    elif pose_type == "floor_activity":
        # Horizontal posture but wrists are below hips
        landmarks[11] = MockLandmark(0.2, 0.8)
        landmarks[12] = MockLandmark(0.2, 0.9)
        landmarks[23] = MockLandmark(0.7, 0.85)
        landmarks[24] = MockLandmark(0.7, 0.95)
        landmarks[0] = MockLandmark(0.1, 0.9)
        landmarks[15] = MockLandmark(0.8, 0.9) # wrists below hips (y > hip_y)
        landmarks[16] = MockLandmark(0.8, 0.99)
        
    return landmarks

@pytest.fixture
def detector():
    # Mock the MediaPipe model loading since we only test logic
    with patch('mediapipe.tasks.python.vision.PoseLandmarker.create_from_options'):
        # Pass a mock config for fast tests
        config = {
            "model_path": "dummy.task",
            "fall_angle_threshold": 60.0,
            "about_to_fall_threshold": 30.0,
            "fall_frame_threshold": 5,
            "confidence_threshold": 0.6,
            "head_velocity_threshold": 0.01,
            "alert_cooldown_seconds": 60,
            "min_bbox_area": 100,
            "log_path": "test_fall_events.csv",
            "db_path": "test_fall_events.db"
        }
        detector = FallDetector(config=config)
        return detector

def test_angle_calculation_and_confidence(detector):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    mock_result = MagicMock()
    mock_result.pose_landmarks = [create_synthetic_landmarks("fallen")]
    detector.landmarker.detect_for_video = MagicMock(return_value=mock_result)
    
    # Process frames to hit FALLEN state
    for i in range(25):
        detector.process_frame(frame, i * 33)
        
    status = detector.get_status(1)
    assert status is not None
    assert status["status"] == "FALLEN"
    assert status["confidence_score"] >= 0.6

def test_state_transitions(detector):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    mock_result = MagicMock()
    
    # 1. NORMAL
    mock_result.pose_landmarks = [create_synthetic_landmarks("normal")]
    detector.landmarker.detect_for_video = MagicMock(return_value=mock_result)
    detector.process_frame(frame, 0)
    assert detector.get_status(1)["status"] == "NORMAL"
    
    # 2. FALLEN
    mock_result.pose_landmarks = [create_synthetic_landmarks("fallen")]
    for i in range(1, 25):
        detector.process_frame(frame, i * 33)
    assert detector.get_status(1)["status"] == "FALLEN"
    
    # 3. STUMBLE (recovers quickly)
    mock_result.pose_landmarks = [create_synthetic_landmarks("normal")]
    detector.process_frame(frame, 10 * 33)
    assert detector.get_status(1)["status"] == "STUMBLE"

def test_floor_activity_disambiguation(detector):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_result = MagicMock()
    
    # Wrists are positioned below hips, indicating floor activity instead of a fall
    mock_result.pose_landmarks = [create_synthetic_landmarks("floor_activity")]
    detector.landmarker.detect_for_video = MagicMock(return_value=mock_result)
    
    for i in range(25):
        detector.process_frame(frame, i * 33)
        
    status = detector.get_status(1)
    assert status["status"] == "FLOOR_ACTIVITY"

@patch('alerts._send_sms')
@patch('alerts._send_email')
def test_alert_throttle_logic(mock_email, mock_sms, detector):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    mock_result = MagicMock()
    mock_result.pose_landmarks = [create_synthetic_landmarks("fallen")]
    detector.landmarker.detect_for_video = MagicMock(return_value=mock_result)
    
    # Clear alert tracking global dict
    import alerts
    alerts.last_alert_time.clear()
    
    # Trigger first fall
    for i in range(25):
        detector.process_frame(frame, i * 33)
        
    assert mock_sms.called
    assert mock_email.called
    
    mock_sms.reset_mock()
    mock_email.reset_mock()
    
    # Reset tracking state but keep alert throttle dictionary intact
    detector.reset()
    
    # Trigger fall again within cooldown window
    for i in range(25):
        detector.process_frame(frame, (i + 25) * 33)
        
    # Should be throttled, so alerts shouldn't be fired again
    assert not mock_sms.called
    assert not mock_email.called
