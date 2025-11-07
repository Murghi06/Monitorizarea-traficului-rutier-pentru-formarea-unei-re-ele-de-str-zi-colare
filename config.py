"""
Configuration file for Traffic Monitoring System
Contains all constants and configuration parameters
"""

# Vehicle detection settings
VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

# Color mapping for different vehicle types
COLOR_MAP = {
    'car': (0, 255, 0),
    'motorcycle': (255, 0, 0),
    'bus': (0, 0, 255),
    'truck': (255, 255, 0),
    'parked': (128, 128, 128)
}

# Detection thresholds
CONFIDENCE_THRESHOLD = 0.45
DISTANCE_THRESHOLD = 150
MAX_DISAPPEARED_FRAMES = 45
PARKED_THRESHOLD = 200
MOVEMENT_THRESHOLD = 15

# Video settings
DEFAULT_FRAME_WIDTH = 640
DEFAULT_FRAME_HEIGHT = 480
BUFFER_SIZE = 1
YOLO_IMAGE_SIZE = 640

# GUI settings
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 750
RIGHT_PANEL_WIDTH = 320

# File settings
DEFAULT_CSV_FILENAME = 'traffic_data.csv'
YOLO_MODEL_PATH = 'yolov8n.pt'

# Modern UI Colors
UI_COLORS = {
    'primary_bg': '#0f1419',
    'secondary_bg': '#16213e',
    'card_bg': '#1a1a2e',
    'accent_blue': '#3498db',
    'accent_purple': '#9b59b6',
    'accent_green': '#27ae60',
    'accent_orange': '#f39c12',
    'accent_red': '#e74c3c',
    'text_primary': '#eef5ff',
    'text_secondary': '#b0b8c4',
    'text_muted': '#8e95a3'
}
