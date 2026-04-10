#!/bin/bash

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Define blue color for the CLI interface
BLUE='\033[0;34m'
NC='\033[0m' # No Color

while true; do
    clear
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}             Fall Detection System CLI Menu           ${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}  1. Real-time Fall Detection (Webcam)                ${NC}"
    echo -e "${BLUE}  2. Video File Fall Detection                        ${NC}"
    echo -e "${BLUE}  3. Run Tests                                        ${NC}"
    echo -e "${BLUE}  4. Exit                                             ${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo -ne "${BLUE}Select an option (1-4): ${NC}"
    read -r choice

    case $choice in
        1)
            echo -e "\n${BLUE}Starting Real-time Fall Detection...${NC}"
            python3 main.py
            echo -e "\n${BLUE}Press Enter to return to the menu...${NC}"
            read -r
            ;;
        2)
            echo -e "\n${BLUE}Starting Video File Fall Detection...${NC}"
            python3 video_fall_detection.py
            echo -e "\n${BLUE}Press Enter to return to the menu...${NC}"
            read -r
            ;;
        3)
            echo -e "\n${BLUE}Running Test Suite...${NC}"
            python3 -m pytest test_fall_detector.py
            echo -e "\n${BLUE}Press Enter to return to the menu...${NC}"
            read -r
            ;;
        4)
            echo -e "\n${BLUE}Exiting the application. Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${BLUE}Invalid option selected. Please choose between 1 and 4.${NC}"
            echo -e "${BLUE}Press Enter to try again...${NC}"
            read -r
            ;;
    esac
done
