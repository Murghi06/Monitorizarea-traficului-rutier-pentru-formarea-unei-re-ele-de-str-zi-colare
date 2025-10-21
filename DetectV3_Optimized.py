import cv2
from ultralytics import YOLO
import pandas as pd
from datetime import datetime
import numpy as np
from collections import defaultdict
import os
from pathlib import Path

class TrafficMonitor:
    """Main traffic monitoring class with optimized performance"""
    
    # Class constants
    VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
    COLOR_MAP = {
        'car': (0, 255, 0),
        'motorcycle': (255, 0, 0),
        'bus': (0, 0, 255),
        'truck': (255, 255, 0)
    }
    CONFIDENCE_THRESHOLD = 0.5
    DISTANCE_THRESHOLD = 100
    MAX_DISAPPEARED_FRAMES = 30
    
    def __init__(self, source, is_live=False, model_path='yolov8n.pt'):
        """
        Initialize traffic monitoring system
        
        Args:
            source: Video file path or camera index (0 for webcam)
            is_live: True for live camera, False for video file
            model_path: Path to YOLO model file
        """
        self.source = source
        self.is_live = is_live
        self.model_path = model_path
        
        # Initialize counters and tracking
        self.vehicle_counts = defaultdict(int)
        self.tracked_objects = {}
        self.next_object_id = 0
        self.session_start = datetime.now()
        
        # Performance settings
        self.frame_skip = 2 if is_live else 1  # Skip frames for live camera
        self.frame_counter = 0
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model with error handling"""
        try:
            print("Loading YOLOv8 model...")
            self.model = YOLO(self.model_path)
            print("✓ Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("The model will be downloaded automatically on first run.")
            raise
    
    @staticmethod
    def calculate_centroid(box):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    @staticmethod
    def calculate_distance(point1, point2):
        """Calculate Euclidean distance between two points"""
        return np.linalg.norm(np.array(point1) - np.array(point2))
    
    def update_tracking(self, detections):
        """
        Update object tracking with optimized matching algorithm
        
        Args:
            detections: List of detected vehicle bounding boxes
            
        Returns:
            List of newly detected object IDs
        """
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
        """Register all detections as new objects"""
        new_objects = []
        for i, det in enumerate(detections):
            self.tracked_objects[self.next_object_id] = {
                'centroid': centroids[i],
                'disappeared': 0,
                'class': det['class'],
                'counted': False
            }
            new_objects.append(self.next_object_id)
            self.next_object_id += 1
        return new_objects
    
    def _match_and_update(self, detections, current_centroids):
        """Match current detections to existing tracked objects"""
        object_ids = list(self.tracked_objects.keys())
        object_centroids = [self.tracked_objects[oid]['centroid'] for oid in object_ids]
        
        # Build distance matrix
        distances = np.zeros((len(object_centroids), len(current_centroids)))
        for i, obj_cent in enumerate(object_centroids):
            for j, curr_cent in enumerate(current_centroids):
                distances[i][j] = self.calculate_distance(obj_cent, curr_cent)
        
        # Match objects
        matched_objects = set()
        matched_detections = set()
        new_objects = []
        
        # Hungarian algorithm simplified: greedy matching
        for _ in range(min(len(object_ids), len(current_centroids))):
            min_idx = np.unravel_index(distances.argmin(), distances.shape)
            
            if distances[min_idx] < self.DISTANCE_THRESHOLD:
                obj_id = object_ids[min_idx[0]]
                self.tracked_objects[obj_id]['centroid'] = current_centroids[min_idx[1]]
                self.tracked_objects[obj_id]['disappeared'] = 0
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
        
        # Register new detections
        for i in range(len(current_centroids)):
            if i not in matched_detections:
                self.tracked_objects[self.next_object_id] = {
                    'centroid': current_centroids[i],
                    'disappeared': 0,
                    'class': detections[i]['class'],
                    'counted': False
                }
                new_objects.append(self.next_object_id)
                self.next_object_id += 1
        
        return new_objects
    
    def count_new_vehicles(self, new_object_ids):
        """Count newly detected vehicles"""
        for obj_id in new_object_ids:
            obj = self.tracked_objects.get(obj_id)
            if obj and not obj['counted']:
                vehicle_class = obj['class']
                self.vehicle_counts[vehicle_class] += 1
                obj['counted'] = True
                if self.is_live:
                    print(f"✓ {vehicle_class.capitalize()} detected! Total: {self.vehicle_counts[vehicle_class]}")
    
    def process_frame(self, frame):
        """
        Process a single frame for vehicle detection
        
        Args:
            frame: Video frame to process
            
        Returns:
            Processed frame with annotations
        """
        self.frame_counter += 1
        
        # Skip frames for performance
        if self.frame_counter % self.frame_skip != 0:
            return self._draw_info_panel(frame)
        
        # Run YOLO detection
        results = self.model(frame, verbose=False, conf=self.CONFIDENCE_THRESHOLD)
        
        # Extract vehicle detections
        detections = self._extract_detections(results)
        
        # Update tracking and count
        new_objects = self.update_tracking(detections)
        self.count_new_vehicles(new_objects)
        
        # Draw annotations
        frame = self._draw_detections(frame, detections)
        frame = self._draw_info_panel(frame)
        
        return frame
    
    def _extract_detections(self, results):
        """Extract vehicle detections from YOLO results"""
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if class_id in self.VEHICLE_CLASSES and confidence > self.CONFIDENCE_THRESHOLD:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    detections.append({
                        'box': (x1, y1, x2, y2),
                        'class': self.VEHICLE_CLASSES[class_id],
                        'confidence': confidence
                    })
        return detections
    
    def _draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame"""
        for det in detections:
            x1, y1, x2, y2 = map(int, det['box'])
            label = f"{det['class']}: {det['confidence']:.2f}"
            color = self.COLOR_MAP.get(det['class'], (255, 255, 255))
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return frame
    
    def _draw_info_panel(self, frame):
        """Draw information panel on frame"""
        info_height = 200 if self.is_live else 160
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (300, info_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        y = 25
        mode = "LIVE" if self.is_live else "VIDEO"
        cv2.putText(frame, f"{mode} MONITORING", (10, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 30
        
        if self.is_live:
            duration = str(datetime.now() - self.session_start).split('.')[0]
            cv2.putText(frame, f"Duration: {duration}", (10, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y += 25
        
        for vehicle_type in ['car', 'motorcycle', 'bus', 'truck']:
            count = self.vehicle_counts[vehicle_type]
            color = self.COLOR_MAP[vehicle_type]
            cv2.putText(frame, f"{vehicle_type.capitalize()}: {count}", 
                       (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y += 25
        
        total = sum(self.vehicle_counts.values())
        cv2.putText(frame, f"TOTAL: {total}", (10, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def reset_counts(self):
        """Reset all counters and start new session"""
        self.vehicle_counts = defaultdict(int)
        self.tracked_objects = {}
        self.next_object_id = 0
        self.session_start = datetime.now()
        print("\n✓ Counters reset! New session started.")
    
    def start_monitoring(self):
        """Start monitoring process"""
        cap = self._initialize_capture()
        if cap is None:
            return
        
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
                    cv2.putText(frame, "PAUSED", 
                               (frame.shape[1]//2 - 100, frame.shape[0]//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                
                cv2.imshow('Traffic Monitor', frame)
                
                # Handle key presses
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
        """Initialize video capture with error handling"""
        print("Opening camera..." if self.is_live else "Opening video file...")
        cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            print(f"Error: Could not open {'camera' if self.is_live else 'video file'}")
            return None
        
        print("✓ Ready!")
        
        if self.is_live:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        return cap
    
    def _print_controls(self):
        """Print control instructions"""
        print("\n" + "="*60)
        print(f"TRAFFIC MONITORING - {'LIVE CAMERA' if self.is_live else 'VIDEO FILE'}")
        print("="*60)
        print("Controls:")
        print("  'q' - Quit and save")
        print("  's' - Save current data")
        if self.is_live:
            print("  'r' - Reset counters")
            print("  'p' - Pause/Resume")
        print("="*60 + "\n")
    
    def save_data(self):
        """Save current counts to CSV"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = str(datetime.now() - self.session_start).split('.')[0]
        
        data_entry = {
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
        df = pd.DataFrame([data_entry])
        
        if Path(filename).exists():
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, mode='w', header=True, index=False)
    
    def display_summary(self):
        """Display monitoring session summary"""
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
    """Main entry point for the application"""
    print("="*60)
    print("TRAFFIC MONITORING SYSTEM")
    print("="*60)
    print("\nSelect monitoring mode:")
    print("1 - Monitor video file")
    print("2 - Monitor live camera")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    try:
        if choice == '1':
            video_path = input("Enter video file path (or press Enter for 'video.mp4'): ").strip()
            video_path = video_path or 'video.mp4'
            
            if not Path(video_path).exists():
                print(f"Error: Video file '{video_path}' not found!")
                return
            
            monitor = TrafficMonitor(video_path, is_live=False)
            monitor.start_monitoring()
        
        elif choice == '2':
            camera_input = input("Enter camera number (default: 0): ").strip()
            camera_index = int(camera_input) if camera_input else 0
            
            monitor = TrafficMonitor(camera_index, is_live=True)
            monitor.start_monitoring()
        
        else:
            print("Invalid choice!")
    
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()