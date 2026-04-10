import os
import subprocess
import yaml
import sys

# Define ANSI escape codes for coloring terminal output
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
NC = '\033[0m' # No Color

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"{BLUE}======================================================{NC}")
    print(f"{BLUE}             Fall Detection PyCLI System              {NC}")
    print(f"{BLUE}======================================================{NC}")

def run_realtime():
    print(f"\n{CYAN}Starting Real-time Fall Detection...{NC}")
    subprocess.run([sys.executable, "main.py"])

def run_video():
    print(f"\n{CYAN}Starting Video File Fall Detection...{NC}")
    video_path = input(f"{YELLOW}Enter the path to the video file (leave empty for default 'test_video.mp4'): {NC}").strip()
    
    cmd = [sys.executable, "video_fall_detection.py"]
    if video_path:
        cmd.append(video_path)
        
    print(f"{CYAN}Running video detection process...{NC}")
    subprocess.run(cmd)

def run_tests():
    print(f"\n{CYAN}Running Test Suite...{NC}")
    subprocess.run([sys.executable, "-m", "pytest", "test_fall_detector.py"])

def modify_config():
    config_file = "config.yaml"
    if not os.path.exists(config_file):
        print(f"{RED}Config file {config_file} not found!{NC}")
        input(f"\n{BLUE}Press Enter to return...{NC}")
        return

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            
        print(f"\n{CYAN}--- Current Configuration Settings ---{NC}")
        keys = list(config.keys())
        for i, key in enumerate(keys):
            print(f"{i+1}. {key}: {config[key]}")
        print(f"{len(keys)+1}. Cancel / Return")
        
        choice = input(f"\n{YELLOW}Select a parameter to modify (1-{len(keys)+1}): {NC}").strip()
        
        if not choice:
            return
            
        try:
            choice = int(choice)
            if choice == len(keys) + 1:
                return
            if 1 <= choice <= len(keys):
                selected_key = keys[choice-1]
                current_val = config[selected_key]
                new_val = input(f"{YELLOW}Enter new value for {selected_key} (current: {current_val}): {NC}").strip()
                
                if new_val:
                    # Try to cast to proper type based on original type
                    if isinstance(current_val, int):
                        config[selected_key] = int(new_val)
                    elif isinstance(current_val, float):
                        config[selected_key] = float(new_val)
                    else:
                        config[selected_key] = new_val
                        
                    with open(config_file, "w") as f:
                        yaml.dump(config, f)
                    print(f"{GREEN}Successfully updated {selected_key} to {new_val}!{NC}")
                else:
                    print(f"{YELLOW}No changes made.{NC}")
            else:
                print(f"{RED}Invalid option selected.{NC}")
        except ValueError:
            print(f"{RED}Invalid input. Please enter a number or valid value.{NC}")
            
    except Exception as e:
        print(f"{RED}Error modifying config: {e}{NC}")
    
    input(f"\n{BLUE}Press Enter to return...{NC}")

def main():
    while True:
        clear_screen()
        print_header()
        print(f"{BLUE}  1. Real-time Fall Detection (Webcam){NC}")
        print(f"{BLUE}  2. Video File Fall Detection{NC}")
        print(f"{BLUE}  3. Run Tests{NC}")
        print(f"{BLUE}  4. Show/Modify Configuration{NC}")
        print(f"{BLUE}  5. Exit{NC}")
        print(f"{BLUE}======================================================{NC}")
        
        choice = input(f"{BLUE}Select an option (1-5): {NC}").strip()
        
        if choice == '1':
            run_realtime()
        elif choice == '2':
            run_video()
        elif choice == '3':
            run_tests()
        elif choice == '4':
            modify_config()
        elif choice == '5':
            print(f"\n{GREEN}Exiting. Goodbye!{NC}")
            break
        else:
            print(f"\n{RED}Invalid option selected.{NC}")
            input(f"{BLUE}Press Enter to continue...{NC}")

if __name__ == "__main__":
    main()
