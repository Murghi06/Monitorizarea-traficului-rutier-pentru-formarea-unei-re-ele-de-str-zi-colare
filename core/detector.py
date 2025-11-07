"""
Vehicle detection module
Handles YOLO model and detection processing
"""

import cv2
import numpy as np
from ultralytics import YOLO
from config.constants import VEHICLE_CLASSES, CONFIDENCE_THRESHOLD, YOLO_MODEL, YOLO_IMGSZ, COLOR_MAP


class VehicleDetector:
    """Handles vehicle detection using YOLO"""
    
    def __init__(self):
        self.model = None
        
    def load_model(self):
        """Load and prepare YOLO model"""
        if self.model is None:
            self.model = YOLO(YOLO_MODEL)
            self.model.fuse()
            # Warm-up inference
            dummy = np.zeros((384, 640, 3), dtype=np.uint8)
            self.model(dummy, verbose=False, imgsz=YOLO_IMGSZ)
    
    def detect(self, frame):
        """
        Detect vehicles in frame
        Returns list of detections with box, class, and confidence
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        results = self.model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD, imgsz=YOLO_IMGSZ)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id in VEHICLE_CLASSES:
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
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
