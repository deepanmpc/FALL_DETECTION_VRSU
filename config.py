import yaml
import os

def load_config(config_file="config.yaml"):
    config = {
        "model_path": "pose_landmarker_full.task",
        "fall_angle_threshold": 60.0,
        "about_to_fall_threshold": 30.0,
        "fall_frame_threshold": 15,
        "confidence_threshold": 0.7,
        "head_velocity_threshold": 0.015,
        "alert_cooldown_seconds": 60,
        "min_bbox_area": 5000,
        "log_path": "fall_events.csv",
        "db_path": "fall_events.db"
    }
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                loaded = yaml.safe_load(f)
                if loaded:
                    config.update(loaded)
            except Exception as e:
                print(f"Error reading {config_file}: {e}")
                
    # Environment variable overrides
    for key in config.keys():
        env_val = os.environ.get(key.upper())
        if env_val is not None:
            # Type cast based on default type
            if isinstance(config[key], int):
                config[key] = int(env_val)
            elif isinstance(config[key], float):
                config[key] = float(env_val)
            else:
                config[key] = env_val
                
    print("--- Active Configuration ---")
    for k, v in config.items():
        print(f"{k}: {v}")
    print("----------------------------")
    
    return config

active_config = load_config()
