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
CONFIDENCE_THRESHOLD = 0.45  # Baseline for 1080p (adjusted to reduce false positives)
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
SKIP_FRAMES = 3  # Process every Nth frame (1=all, 2=every 2nd, 3=every 3rd)
USE_GPU = True  # Enable GPU acceleration if available (auto-detects)
PROCESS_RESIZE_WIDTH = 1280  # Resize width for detection (0 = no resize)
DISPLAY_RESIZE_WIDTH = 960  # Display width
DISPLAY_RESIZE_HEIGHT = 540  # Display height

# Data file
DATA_FILE = 'traffic_data.csv'


# Resolution-based parameter scaling
def get_scaled_parameters(video_width, video_height):
    """
    Calculate scaled detection parameters based on video resolution.
    Reference resolution: 1920x1080 (1080p) - baseline for current config
    
    Args:
        video_width: Width of the input video
        video_height: Height of the input video
    
    Returns:
        dict: Scaled parameters for detection and tracking
    """
    # Reference resolution (1080p) - our baseline
    REFERENCE_WIDTH = 1920
    REFERENCE_HEIGHT = 1080
    
    # Calculate resolution scale factor (based on total pixel count)
    reference_pixels = REFERENCE_WIDTH * REFERENCE_HEIGHT
    video_pixels = video_width * video_height
    scale_factor = (video_pixels / reference_pixels) ** 0.5  # Square root for more balanced scaling
    
    # Base parameters (optimized for 1080p to achieve ~125 vehicle count)
    base_confidence = 0.45  # Increased from 0.35 to reduce over-counting
    base_distance = 150
    base_movement = 15
    
    # Scale parameters
    # Lower resolution → need HIGHER confidence (fewer false positives from low detail)
    # Higher resolution → can use LOWER confidence (more detail available)
    scaled_confidence = base_confidence + (1.0 - scale_factor) * 0.15  # Increase threshold for lower res
    scaled_confidence = max(0.30, min(0.70, scaled_confidence))  # Clamp between 0.30 and 0.70
    
    # Distance threshold scales with resolution (fewer pixels = closer tracking needed)
    scaled_distance = base_distance * scale_factor
    scaled_distance = max(50, min(300, scaled_distance))  # Clamp between 50 and 300
    
    # Movement threshold also scales with resolution
    scaled_movement = base_movement * scale_factor
    scaled_movement = max(5, min(30, scaled_movement))  # Clamp between 5 and 30
    
    return {
        'confidence_threshold': round(scaled_confidence, 2),
        'distance_threshold': int(scaled_distance),
        'movement_threshold': int(scaled_movement),
        'scale_factor': round(scale_factor, 2),
        'resolution_class': _get_resolution_class(video_width, video_height)
    }


def _get_resolution_class(width, height):
    """Classify video resolution for logging/debugging"""
    pixels = width * height
    if pixels >= 1920 * 1080:
        return "1080p+"
    elif pixels >= 1280 * 720:
        return "720p"
    elif pixels >= 640 * 480:
        return "480p"
    else:
        return "low"
