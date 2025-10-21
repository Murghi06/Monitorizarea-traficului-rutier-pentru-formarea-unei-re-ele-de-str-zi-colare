"""
Optimized Traffic Monitoring System - Final Version
Detects and counts vehicles (cars, motorcycles, buses, trucks) from video files or live camera
Optimized for speed and accuracy
"""

import cv2
from ultralytics import YOLO
import pandas as pd
from datetime import datetime
import numpy as np
from collections import defaultdict
import os
from pathlib import Path

class TrafficMonitor:
    """Highly optimized traffic monitoring class"""
    
    # Class constants - Fine-tuned for best performance
    VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
    COLOR_MAP = {
        'car': (0, 255, 0),
        'motorcycle': (255, 0, 0),
        'bus': (0, 0, 255),
        'truck': (255, 255, 0),
        'parked': (128, 128, 128)
    }
    CONFIDENCE_THRESHOLD = 0.45  # Slightly lower for better detection
    DISTANCE_THRESHOLD = 150  # Increased for better tracking across frames
    MAX_DISAPPEARED_FRAMES = 45  # Increased to handle longer occlusions
    PARKED_THRESHOLD = 200  # Reduced to ~6-7 seconds (faster parked detection)
    MOVEMENT_THRESHOLD = 15  # Reduced for more sensitive movement detection
    
    def __init__(self, source, is_live=False, model_path='yolov8n.pt'):
        """Initialize traffic monitoring system"""
        self.source = source
        self.is_live = is_live
        self.model_path = model_path
        
        # Initialize counters and tracking
        self.vehicle_counts = defaultdict(int)
        self.tracked_objects = {}
        self.next_object_id = 0
        self.session_start = datetime.now()
        
        # Performance optimization
        self.frame_counter = 0
        self.model = None
        
        # Cache for faster drawing
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
    
    def _load_model(self):
        """Load YOLO model with warm-up"""
        if self.model is not None:
            return
            
        try:
            print("Loading YOLOv8 model...")
            self.model = YOLO(self.model_path)
            self.model.fuse()  # Fuse layers for faster inference
            
            # Warm-up with smaller frame for speed
            print("Warming up model...")
            dummy = np.zeros((384, 640, 3), dtype=np.uint8)
            self.model(dummy, verbose=False, imgsz=640)
            
            print("✓ Model ready!")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    @staticmethod
    def calculate_centroid(box):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    @staticmethod
    def calculate_distance(p1, p2):
        """Fast distance calculation"""
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def update_tracking(self, detections):
        """Optimized object tracking with duplicate prevention"""
        if not detections:
            return self._handle_no_detections()
        
        current_centroids = [self.calculate_centroid(det['box']) for det in detections]
        
        if not self.tracked_objects:
            return self._register_new_objects(detections, current_centroids)
        
        return self._match_and_update(detections, current_centroids)
    
    def _handle_no_detections(self):
        """Handle case when no vehicles detected"""
        for obj_id in list(self.tracked_objects.keys()):
            self.tracked_objects[obj_id]['disappeared'] += 1
            if self.tracked_objects[obj_id]['disappeared'] > self.MAX_DISAPPEARED_FRAMES:
                del self.tracked_objects[obj_id]
        return []
    
    def _register_new_objects(self, detections, centroids):
        """Register new objects"""
        new_objects = []
        for i, det in enumerate(detections):
            self.tracked_objects[self.next_object_id] = {
                'centroid': centroids[i],
                'disappeared': 0,
                'class': det['class'],
                'counted': False,
                'stationary_frames': 0,
                'is_parked': False,
                'total_movement': 0
            }
            new_objects.append(self.next_object_id)
            self.next_object_id += 1
        return new_objects
    
    def _match_and_update(self, detections, current_centroids):
        """Match current detections to tracked objects - optimized"""
        object_ids = list(self.tracked_objects.keys())
        object_centroids = [self.tracked_objects[oid]['centroid'] for oid in object_ids]
        
        # Fast distance matrix using numpy
        obj_array = np.array(object_centroids)
        curr_array = np.array(current_centroids)
        
        distances = np.zeros((len(object_centroids), len(current_centroids)))
        for i in range(len(obj_array)):
            distances[i] = np.sqrt(np.sum((curr_array - obj_array[i])**2, axis=1))
        
        matched_objects = set()
        matched_detections = set()
        new_objects = []
        
        # Greedy matching
        for _ in range(min(len(object_ids), len(current_centroids))):
            min_idx = np.unravel_index(distances.argmin(), distances.shape)
            
            if distances[min_idx] < self.DISTANCE_THRESHOLD:
                obj_id = object_ids[min_idx[0]]
                obj = self.tracked_objects[obj_id]
                old_centroid = obj['centroid']
                new_centroid = current_centroids[min_idx[1]]
                
                movement = self.calculate_distance(old_centroid, new_centroid)
                
                # Update object
                obj['centroid'] = new_centroid
                obj['disappeared'] = 0
                obj['total_movement'] += movement
                
                # Parked detection
                if movement < self.MOVEMENT_THRESHOLD:
                    obj['stationary_frames'] += 1
                else:
                    was_parked = obj['is_parked']
                    obj['stationary_frames'] = 0
                    obj['is_parked'] = False
                    
                    # Count if was parked and now moving
                    if was_parked and not obj['counted']:
                        self.vehicle_counts[obj['class']] += 1
                        obj['counted'] = True
                        if self.is_live:
                            print(f"✓ {obj['class'].capitalize()} (was parked, now moving)! Total: {self.vehicle_counts[obj['class']]}")
                
                if obj['stationary_frames'] > self.PARKED_THRESHOLD:
                    obj['is_parked'] = True
                
                matched_objects.add(min_idx[0])
                matched_detections.add(min_idx[1])
                distances[min_idx[0], :] = np.inf
                distances[:, min_idx[1]] = np.inf
        
        # Handle unmatched objects
        for i, obj_id in enumerate(object_ids):
            if i not in matched_objects:
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.MAX_DISAPPEARED_FRAMES:
                    del self.tracked_objects[obj_id]
        
        # Check for rediscovery before creating new objects
        for i in range(len(current_centroids)):
            if i not in matched_detections:
                is_rediscovery = False
                
                for obj_id, obj in list(self.tracked_objects.items()):
                    if obj['disappeared'] > 0 and obj['disappeared'] <= self.MAX_DISAPPEARED_FRAMES:
                        distance = self.calculate_distance(obj['centroid'], current_centroids[i])
                        if distance < self.DISTANCE_THRESHOLD * 1.5:
                            obj['centroid'] = current_centroids[i]
                            obj['disappeared'] = 0
                            is_rediscovery = True
                            break
                
                if not is_rediscovery:
                    self.tracked_objects[self.next_object_id] = {
                        'centroid': current_centroids[i],
                        'disappeared': 0,
                        'class': detections[i]['class'],
                        'counted': False,
                        'stationary_frames': 0,
                        'is_parked': False,
                        'total_movement': 0
                    }
                    new_objects.append(self.next_object_id)
                    self.next_object_id += 1
        
        return new_objects
    
    def count_new_vehicles(self, new_object_ids):
        """Count newly detected vehicles immediately"""
        for obj_id in new_object_ids:
            obj = self.tracked_objects.get(obj_id)
            if obj and not obj['counted'] and not obj['is_parked']:
                self.vehicle_counts[obj['class']] += 1
                obj['counted'] = True
                if self.is_live:
                    print(f"✓ {obj['class'].capitalize()} detected! Total: {self.vehicle_counts[obj['class']]}")
    
    def process_frame(self, frame):
        """Process single frame with optimizations"""
        self.frame_counter += 1
        
        # Run detection with optimized settings
        results = self.model(frame, verbose=False, conf=self.CONFIDENCE_THRESHOLD, imgsz=640)
        
        # Extract detections
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id in self.VEHICLE_CLASSES:
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    detections.append({
                        'box': (x1, y1, x2, y2),
                        'class': self.VEHICLE_CLASSES[class_id],
                        'confidence': confidence
                    })
        
        # Update tracking
        new_objects = self.update_tracking(detections)
        self.count_new_vehicles(new_objects)
        
        # Draw annotations
        frame = self._draw_annotations(frame, detections)
        
        return frame
    
    def _draw_annotations(self, frame, detections):
        """Optimized drawing with all info"""
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = map(int, det['box'])
            centroid = self.calculate_centroid(det['box'])
            
            # Check if parked
            is_parked = False
            for obj in self.tracked_objects.values():
                if self.calculate_distance(obj['centroid'], centroid) < 50:
                    is_parked = obj['is_parked']
                    break
            
            if is_parked:
                label = f"{det['class']}: PARKED"
                color = self.COLOR_MAP['parked']
                thickness = 1
            else:
                label = f"{det['class']}: {det['confidence']:.2f}"
                color = self.COLOR_MAP[det['class']]
                thickness = 2
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Label background for readability
            (label_w, label_h), _ = cv2.getTextSize(label, self.font, 0.5, 2)
            cv2.rectangle(frame, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), self.font, 0.5, (0, 0, 0), 2)
        
        # Info panel
        self._draw_info_panel(frame)
        
        return frame
    
    def _draw_info_panel(self, frame):
        """Draw optimized info panel"""
        panel_height = 180 if self.is_live else 150
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (320, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        y = 28
        mode = "LIVE CAMERA" if self.is_live else "VIDEO FILE"
        cv2.putText(frame, mode, (10, y), self.font, 0.7, (255, 255, 255), 2)
        y += 32
        
        if self.is_live:
            duration = str(datetime.now() - self.session_start).split('.')[0]
            cv2.putText(frame, f"Time: {duration}", (10, y), self.font, 0.5, (200, 200, 200), 1)
            y += 28
        
        # Vehicle counts
        for vehicle_type in ['car', 'motorcycle', 'bus', 'truck']:
            count = self.vehicle_counts[vehicle_type]
            color = self.COLOR_MAP[vehicle_type]
            cv2.putText(frame, f"{vehicle_type.capitalize()}: {count}", 
                       (10, y), self.font, 0.6, color, 2)
            y += 28
        
        total = sum(self.vehicle_counts.values())
        cv2.putText(frame, f"TOTAL: {total}", (10, y), self.font, 0.7, (255, 255, 255), 2)
    
    def reset_counts(self):
        """Reset all counters and timer"""
        self.vehicle_counts = defaultdict(int)
        self.tracked_objects = {}
        self.next_object_id = 0
        self.session_start = datetime.now()  # Reset timer
        self.frame_counter = 0
        print("\n✓ Counters and timer reset!")
    
    def start_monitoring(self):
        """Main monitoring loop"""
        cap = self._initialize_capture()
        if cap is None:
            return
        
        self._load_model()
        self._print_controls()
        
        paused = False
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame = self.process_frame(frame)
                else:
                    h, w = frame.shape[:2]
                    cv2.putText(frame, "PAUSED", (w//2 - 100, h//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                
                cv2.imshow('Traffic Monitor', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.save_data()
                    print("✓ Data saved!")
                elif key == ord('r') and self.is_live:
                    self.reset_counts()
                elif key == ord('p') and self.is_live:
                    paused = not paused
                    print(f"✓ {'PAUSED' if paused else 'RESUMED'}")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.save_data()
            self.display_summary()
    
    def _initialize_capture(self):
        """Initialize video capture optimized for speed"""
        print("Opening camera..." if self.is_live else "Opening video...")
        
        if self.is_live:
            # Try fastest backends
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                cap = cv2.VideoCapture(self.source, backend)
                if cap.isOpened():
                    break
        else:
            cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            print(f"Error: Could not open {'camera' if self.is_live else 'video'}")
            return None
        
        if self.is_live:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FPS, 30)
            ret, _ = cap.read()
            if not ret:
                print("Error: Could not read from camera")
                return None
        
        print("✓ Ready!")
        return cap
    
    def _print_controls(self):
        """Print controls"""
        print("\n" + "="*60)
        print(f"TRAFFIC MONITORING - {'LIVE' if self.is_live else 'VIDEO'}")
        print("="*60)
        print("Controls:")
        print("  'q' - Quit and save")
        print("  's' - Save data")
        if self.is_live:
            print("  'r' - Reset counters")
            print("  'p' - Pause/Resume")
        print("="*60 + "\n")
    
    def save_data(self):
        """Save data to CSV"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = str(datetime.now() - self.session_start).split('.')[0]
        
        data = {
            'Timestamp': timestamp,
            'Source': 'Live Camera' if self.is_live else 'Video File',
            'Duration': duration,
            'Cars': self.vehicle_counts['car'],
            'Motorcycles': self.vehicle_counts['motorcycle'],
            'Buses': self.vehicle_counts['bus'],
            'Trucks': self.vehicle_counts['truck'],
            'Total': sum(self.vehicle_counts.values())
        }
        
        filename = 'traffic_data.csv'
        df = pd.DataFrame([data])
        
        if Path(filename).exists():
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, mode='w', header=True, index=False)
    
    def display_summary(self):
        """Display session summary"""
        duration = str(datetime.now() - self.session_start).split('.')[0]
        
        print("\n" + "="*50)
        print("SESSION SUMMARY")
        print("="*50)
        print(f"Source: {'Live Camera' if self.is_live else 'Video File'}")
        print(f"Duration: {duration}")
        print(f"\nVehicle Counts:")
        print(f"  Cars: {self.vehicle_counts['car']}")
        print(f"  Motorcycles: {self.vehicle_counts['motorcycle']}")
        print(f"  Buses: {self.vehicle_counts['bus']}")
        print(f"  Trucks: {self.vehicle_counts['truck']}")
        print(f"  Total: {sum(self.vehicle_counts.values())}")
        print("="*50)
        print(f"Data saved to: traffic_data.csv\n")


def main():
    """Main entry point"""
    print("="*60)
    print("TRAFFIC MONITORING SYSTEM - OPTIMIZED")
    print("="*60)
    print("\nSelect mode:")
    print("1 - Video file")
    print("2 - Live camera")
    
    choice = input("\nChoice (1/2): ").strip()
    
    try:
        if choice == '1':
            video_path = input("Video path (Enter for 'video.mp4'): ").strip() or 'video.mp4'
            
            if not Path(video_path).exists():
                print(f"Error: '{video_path}' not found!")
                return
            
            monitor = TrafficMonitor(video_path, is_live=False)
            monitor.start_monitoring()
        
        elif choice == '2':
            monitor = TrafficMonitor(0, is_live=True)  # Default to camera 0
            monitor.start_monitoring()
        
        else:
            print("Invalid choice!")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()