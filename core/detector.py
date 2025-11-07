"""
Vehicle detection module
Handles YOLO model and detection processing
"""

import cv2
import numpy as np
from ultralytics import YOLO
from config.constants import (
    VEHICLE_CLASSES, CONFIDENCE_THRESHOLD, YOLO_MODEL, YOLO_IMGSZ, 
    COLOR_MAP, USE_GPU, PROCESS_RESIZE_WIDTH
)


class VehicleDetector:
    """Handles vehicle detection using YOLO"""
    
    def __init__(self):
        self.model = None
        self.device = 'cpu'
        self.use_half = False
        
    def load_model(self):
        """Load and prepare YOLO model with GPU support"""
        if self.model is None:
            self.model = YOLO(YOLO_MODEL)
            
            # Enable GPU if available and requested
            if USE_GPU:
                try:
                    import torch
                    if torch.cuda.is_available():
                        self.device = '0'  # First GPU
                        self.use_half = True  # FP16 for faster inference
                        self.model.to('cuda')
                        print("✓ GPU acceleration enabled")
                    else:
                        self.device = 'cpu'
                        print("⚠ GPU not available, using CPU")
                except ImportError:
                    self.device = 'cpu'
                    print("⚠ PyTorch CUDA not available, using CPU")
            else:
                self.device = 'cpu'
                print("ℹ GPU acceleration disabled in settings")
            
            # Fuse model layers for faster inference
            self.model.fuse()
            
            # Warm-up inference
            dummy = np.zeros((384, 640, 3), dtype=np.uint8)
            self.model.predict(dummy, verbose=False, imgsz=YOLO_IMGSZ, device=self.device)
    
    def detect(self, frame):
        """
        Detect vehicles in frame with optimizations
        Returns list of detections with box, class, and confidence
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Optimize frame size for faster processing
        original_height, original_width = frame.shape[:2]
        
        if PROCESS_RESIZE_WIDTH > 0 and original_width > PROCESS_RESIZE_WIDTH:
            scale = PROCESS_RESIZE_WIDTH / original_width
            new_width = PROCESS_RESIZE_WIDTH
            new_height = int(original_height * scale)
            frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            scale_back = original_width / new_width
        else:
            frame_resized = frame
            scale_back = 1.0
        
        # Run detection with optimizations
        results = self.model.predict(
            frame_resized, 
            verbose=False, 
            conf=CONFIDENCE_THRESHOLD, 
            imgsz=YOLO_IMGSZ,
            device=self.device,
            half=self.use_half,  # Use FP16 if GPU available
            max_det=100  # Limit detections for speed
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id in VEHICLE_CLASSES:
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Scale coordinates back if we resized
                    if scale_back != 1.0:
                        x1, y1, x2, y2 = x1 * scale_back, y1 * scale_back, x2 * scale_back, y2 * scale_back
                    
                    detections.append({
                        'box': (x1, y1, x2, y2),
                        'class': VEHICLE_CLASSES[class_id],
                        'confidence': confidence
                    })
        
        return detections
    
    @staticmethod
    def draw_detections(frame, detections, tracker):
        """Draw bounding boxes and labels on frame"""
        for det in detections:
            x1, y1, x2, y2 = map(int, det['box'])
            centroid = tracker.calculate_centroid(det['box'])
            
            # Check if vehicle is parked
            is_parked = tracker.is_object_parked(centroid)
            
            if is_parked:
                label = f"{det['class']}: PARKED"
                color = COLOR_MAP['parked']
                thickness = 1
            else:
                label = f"{det['class']}: {det['confidence']:.2f}"
                color = COLOR_MAP[det['class']]
                thickness = 2
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame
