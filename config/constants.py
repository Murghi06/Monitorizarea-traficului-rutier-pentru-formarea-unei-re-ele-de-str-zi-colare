"""
Configuration constants for Traffic Monitoring System
"""

# Vehicle detection classes
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

# Color map for different vehicle types (BGR format)
COLOR_MAP = {
    'car': (0, 255, 0),
    'motorcycle': (255, 0, 0),
    'bus': (0, 0, 255),
    'truck': (255, 255, 0),
    'parked': (128, 128, 128)
}

# Detection and tracking thresholds
CONFIDENCE_THRESHOLD = 0.35  # Lowered to detect more vehicles
DISTANCE_THRESHOLD = 150
MAX_DISAPPEARED_FRAMES = 45  # Base value (adjusted by tracker based on SKIP_FRAMES)
PARKED_THRESHOLD = 200
MOVEMENT_THRESHOLD = 15

# UI Theme colors
THEME_COLORS = {
    'primary': '#1a1a2e',
    'secondary': '#16213e',
    'accent': '#0f3460',
    'success': '#06d6a0',
    'warning': '#ffd166',
    'danger': '#ef476f',
    'info': '#118ab2',
    'text': '#edf2f4',
    'text_secondary': '#8d99ae',
    'sidebar': '#0b0c10',
    'card_bg': '#1f2833',
    'hover': '#45a29e'
}

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_BUFFER_SIZE = 1

# Model settings
YOLO_MODEL = 'yolov8n.pt'
YOLO_IMGSZ = 640

# Performance optimization settings
SKIP_FRAMES = 2  # Process every Nth frame (1=all, 2=every 2nd, 3=every 3rd)
USE_GPU = True  # Enable GPU acceleration if available (auto-detects)
PROCESS_RESIZE_WIDTH = 1280  # Resize width for detection (0 = no resize)
DISPLAY_RESIZE_WIDTH = 960  # Display width
DISPLAY_RESIZE_HEIGHT = 540  # Display height

# Data file
DATA_FILE = 'traffic_data.csv'
