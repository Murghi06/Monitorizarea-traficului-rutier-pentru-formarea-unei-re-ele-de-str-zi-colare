import cv2
from ultralytics import YOLO
import pandas as pd
from datetime import datetime
import numpy as np
from collections import defaultdict
import os

class TrafficMonitor:
    def __init__(self, source, is_live=False):
        """
        Initialize traffic monitoring
        
        Args:
            source: Video file path or camera index (0 for webcam)
            is_live: True if using live camera, False for video file
        """
        self.source = source
        self.is_live = is_live
        self.model = YOLO('yolov8n.pt')
        
        # Vehicle categories
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle', 
            5: 'bus',
            7: 'truck'
        }
        
        # Counters
        self.vehicle_counts = defaultdict(int)
        
        # Tracking
        self.tracked_objects = {}
        self.next_object_id = 0
        self.max_disappeared = 30
        
        # Session tracking
        self.session_start = datetime.now()
        
    def calculate_centroid(self, box):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    def update_tracking(self, detections):
        """Update object tracking"""
        if len(detections) == 0:
            for obj_id in list(self.tracked_objects.keys()):
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracked_objects[obj_id]
            return []
        
        current_centroids = [self.calculate_centroid(det['box']) for det in detections]
        
        if len(self.tracked_objects) == 0:
            new_objects = []
            for i, det in enumerate(detections):
                self.tracked_objects[self.next_object_id] = {
                    'centroid': current_centroids[i],
                    'disappeared': 0,
                    'class': det['class'],
                    'counted': False
                }
                new_objects.append(self.next_object_id)
                self.next_object_id += 1
            return new_objects
        
        object_ids = list(self.tracked_objects.keys())
        object_centroids = [self.tracked_objects[obj_id]['centroid'] for obj_id in object_ids]
        
        distances = np.zeros((len(object_centroids), len(current_centroids)))
        for i, obj_centroid in enumerate(object_centroids):
            for j, curr_centroid in enumerate(current_centroids):
                distances[i][j] = np.linalg.norm(
                    np.array(obj_centroid) - np.array(curr_centroid)
                )
        
        matched_objects = set()
        matched_detections = set()
        new_objects = []
        
        for _ in range(min(len(object_ids), len(current_centroids))):
            min_idx = np.unravel_index(distances.argmin(), distances.shape)
            if distances[min_idx] < 100:
                obj_id = object_ids[min_idx[0]]
                self.tracked_objects[obj_id]['centroid'] = current_centroids[min_idx[1]]
                self.tracked_objects[obj_id]['disappeared'] = 0
                matched_objects.add(min_idx[0])
                matched_detections.add(min_idx[1])
                distances[min_idx[0], :] = np.inf
                distances[:, min_idx[1]] = np.inf
        
        for i, obj_id in enumerate(object_ids):
            if i not in matched_objects:
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracked_objects[obj_id]
        
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
            if not self.tracked_objects[obj_id]['counted']:
                vehicle_class = self.tracked_objects[obj_id]['class']
                self.vehicle_counts[vehicle_class] += 1
                self.tracked_objects[obj_id]['counted'] = True
                if self.is_live:
                    print(f"✓ New {vehicle_class} detected! Total: {self.vehicle_counts[vehicle_class]}")
    
    def reset_counts(self):
        """Reset all counters and start new session"""
        self.vehicle_counts = defaultdict(int)
        self.tracked_objects = {}
        self.next_object_id = 0
        self.session_start = datetime.now()
        print("\n✓ Counters reset! New session started.")
    
    def start_monitoring(self):
        """Start monitoring (video or live camera)"""
        cap = cv2.VideoCapture(self.source)
        
        if not cap.isOpened():
            if self.is_live:
                print(f"Error: Could not open camera {self.source}")
                print("Try changing camera index to 1 or 2 if you have multiple cameras")
            else:
                print(f"Error: Could not open video file {self.source}")
            return
        
        # Set camera resolution for live mode
        if self.is_live:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        source_type = "LIVE CAMERA" if self.is_live else "VIDEO FILE"
        print("\n" + "="*60)
        print(f"TRAFFIC MONITORING STARTED - {source_type}")
        print("="*60)
        print("Controls:")
        print("  'q' - Quit and save data")
        print("  's' - Save current data (continues monitoring)")
        if self.is_live:
            print("  'r' - Reset counters (start new session)")
            print("  'p' - Pause/Resume")
        print("="*60 + "\n")
        
        paused = False
        frame_skip = 0
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    if self.is_live:
                        print("Error reading from camera")
                    break
                
                frame_skip += 1
                
                # Process frame
                if frame_skip % 1 == 0:  # Process every frame
                    results = self.model(frame, verbose=False)
                    
                    detections = []
                    for result in results:
                        boxes = result.boxes
                        for box in boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            
                            if class_id in self.vehicle_classes and confidence > 0.5:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                detections.append({
                                    'box': (x1, y1, x2, y2),
                                    'class': self.vehicle_classes[class_id],
                                    'confidence': confidence
                                })
                    
                    new_objects = self.update_tracking(detections)
                    self.count_new_vehicles(new_objects)
                    
                    # Draw detections
                    for det in detections:
                        x1, y1, x2, y2 = map(int, det['box'])
                        label = f"{det['class']}: {det['confidence']:.2f}"
                        
                        color_map = {
                            'car': (0, 255, 0),
                            'motorcycle': (255, 0, 0),
                            'bus': (0, 0, 255),
                            'truck': (255, 255, 0)
                        }
                        color = color_map.get(det['class'], (255, 255, 255))
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label, (x1, y1 - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Draw info panel
                info_height = 200 if self.is_live else 160
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (300, info_height), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                
                # Display info
                y_offset = 25
                mode_text = "LIVE" if self.is_live else "VIDEO"
                cv2.putText(frame, f"{mode_text} MONITORING", (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 30
                
                # Session duration
                if self.is_live:
                    duration = datetime.now() - self.session_start
                    duration_str = str(duration).split('.')[0]
                    cv2.putText(frame, f"Duration: {duration_str}", (10, y_offset), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                    y_offset += 25
                
                # Vehicle counts
                for vehicle_type in ['car', 'motorcycle', 'bus', 'truck']:
                    count = self.vehicle_counts[vehicle_type]
                    color_map = {
                        'car': (0, 255, 0),
                        'motorcycle': (255, 0, 0),
                        'bus': (0, 0, 255),
                        'truck': (255, 255, 0)
                    }
                    color = color_map[vehicle_type]
                    cv2.putText(frame, f"{vehicle_type.capitalize()}: {count}", 
                               (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                               color, 2)
                    y_offset += 25
                
                # Total
                total = sum(self.vehicle_counts.values())
                cv2.putText(frame, f"TOTAL: {total}", (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            else:
                cv2.putText(frame, "PAUSED", (frame.shape[1]//2 - 100, frame.shape[0]//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
            
            cv2.imshow('Traffic Monitor', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nStopping monitoring...")
                break
            elif key == ord('s'):
                self.save_data()
                print("✓ Data saved to traffic_data.csv")
            elif key == ord('r') and self.is_live:
                self.reset_counts()
            elif key == ord('p') and self.is_live:
                paused = not paused
                status = "PAUSED" if paused else "RESUMED"
                print(f"✓ Monitoring {status}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save final data
        self.save_data()
        self.display_summary()
    
    def save_data(self):
        """Save current counts to CSV"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_entry = {
            'Timestamp': timestamp,
            'Source': 'Live Camera' if self.is_live else 'Video File',
            'Session_Duration': str(datetime.now() - self.session_start).split('.')[0],
            'Cars': self.vehicle_counts['car'],
            'Motorcycles': self.vehicle_counts['motorcycle'],
            'Buses': self.vehicle_counts['bus'],
            'Trucks': self.vehicle_counts['truck'],
            'Total': sum(self.vehicle_counts.values())
        }
        
        filename = 'traffic_data.csv'
        df = pd.DataFrame([data_entry])
        
        if os.path.exists(filename):
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, mode='w', header=True, index=False)
    
    def display_summary(self):
        """Display session summary"""
        duration = datetime.now() - self.session_start
        print("\n" + "="*50)
        print("SESSION SUMMARY")
        print("="*50)
        print(f"Source: {'Live Camera' if self.is_live else 'Video File'}")
        print(f"Duration: {str(duration).split('.')[0]}")
        print(f"\nVehicle Counts:")
        print(f"  Cars: {self.vehicle_counts['car']}")
        print(f"  Motorcycles: {self.vehicle_counts['motorcycle']}")
        print(f"  Buses: {self.vehicle_counts['bus']}")
        print(f"  Trucks: {self.vehicle_counts['truck']}")
        print(f"  Total: {sum(self.vehicle_counts.values())}")
        print("="*50)
        print("Data saved to: traffic_data.csv\n")

# Main menu
if __name__ == "__main__":
    print("="*60)
    print("TRAFFIC MONITORING SYSTEM")
    print("="*60)
    print("\nSelect monitoring mode:")
    print("1 - Monitor video file")
    print("2 - Monitor live camera")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        video_path = input("Enter video file path (or press Enter for 'video.mp4'): ").strip()
        if not video_path:
            video_path = 'video.mp4'
        
        monitor = TrafficMonitor(video_path, is_live=False)
        monitor.start_monitoring()
    
    elif choice == '2':
        camera_choice = input("Enter camera number (0 for default webcam, 1 for external): ").strip()
        
        if camera_choice == '':
            camera_index = 0
        else:
            try:
                camera_index = int(camera_choice)
            except:
                print("Invalid input, using default camera (0)")
                camera_index = 0
        
        monitor = TrafficMonitor(camera_index, is_live=True)
        monitor.start_monitoring()
    
    else:
        print("Invalid choice!")