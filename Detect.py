import cv2
from ultralytics import YOLO
import pandas as pd
from datetime import datetime
import numpy as np
from collections import defaultdict
import os

class TrafficMonitor:
    def __init__(self, video1_path):
        """
        Initialize the traffic monitoring system
        
        Args:
            video_path: Path to video file or 0 for webcam
        """
        self.video_path = video_path
        self.model = YOLO('yolov8n.pt')  # Load YOLOv8 nano model (fastest)
        
        # Vehicle categories we're tracking
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle', 
            5: 'bus',
            7: 'truck'
        }
        
        # Counters for each vehicle type
        self.vehicle_counts = defaultdict(int)
        
        # Tracking variables
        self.tracked_objects = {}
        self.next_object_id = 0
        self.max_disappeared = 30
        
    def calculate_centroid(self, box):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    def update_tracking(self, detections):
        """
        Update object tracking to avoid counting the same vehicle multiple times
        
        Args:
            detections: List of detected vehicle bounding boxes
        """
        if len(detections) == 0:
            # Mark missing objects
            for obj_id in list(self.tracked_objects.keys()):
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracked_objects[obj_id]
            return []
        
        current_centroids = [self.calculate_centroid(det['box']) for det in detections]
        
        # If no existing objects, register all as new
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
        
        # Match current detections to existing tracked objects
        object_ids = list(self.tracked_objects.keys())
        object_centroids = [self.tracked_objects[obj_id]['centroid'] for obj_id in object_ids]
        
        # Calculate distances between all pairs
        distances = np.zeros((len(object_centroids), len(current_centroids)))
        for i, obj_centroid in enumerate(object_centroids):
            for j, curr_centroid in enumerate(current_centroids):
                distances[i][j] = np.linalg.norm(
                    np.array(obj_centroid) - np.array(curr_centroid)
                )
        
        # Match objects based on minimum distance
        matched_objects = set()
        matched_detections = set()
        new_objects = []
        
        # Sort by distance and match
        for _ in range(min(len(object_ids), len(current_centroids))):
            min_idx = np.unravel_index(distances.argmin(), distances.shape)
            if distances[min_idx] < 100:  # Distance threshold
                obj_id = object_ids[min_idx[0]]
                self.tracked_objects[obj_id]['centroid'] = current_centroids[min_idx[1]]
                self.tracked_objects[obj_id]['disappeared'] = 0
                matched_objects.add(min_idx[0])
                matched_detections.add(min_idx[1])
                distances[min_idx[0], :] = np.inf
                distances[:, min_idx[1]] = np.inf
        
        # Mark unmatched objects as disappeared
        for i, obj_id in enumerate(object_ids):
            if i not in matched_objects:
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracked_objects[obj_id]
        
        # Register new objects
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
    
    def process_video(self):
        """Main processing loop for video analysis"""
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {self.video_path}")
            return
        
        print("Processing video... Press 'q' to quit, 's' to save current data")
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Run detection every frame (you can skip frames for speed: frame_count % 2 == 0)
            results = self.model(frame, verbose=False)
            
            # Extract vehicle detections
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Only process vehicles with good confidence
                    if class_id in self.vehicle_classes and confidence > 0.5:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        detections.append({
                            'box': (x1, y1, x2, y2),
                            'class': self.vehicle_classes[class_id],
                            'confidence': confidence
                        })
            
            # Update tracking and count new vehicles
            new_objects = self.update_tracking(detections)
            self.count_new_vehicles(new_objects)
            
            # Draw bounding boxes and labels
            for det in detections:
                x1, y1, x2, y2 = map(int, det['box'])
                label = f"{det['class']}: {det['confidence']:.2f}"
                
                # Different colors for different vehicle types
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
            
            # Display counts on frame
            y_offset = 30
            
            for vehicle_type in ['car', 'motorcycle', 'bus', 'truck']:
                count = self.vehicle_counts[vehicle_type]
                cv2.putText(frame, f"{vehicle_type.capitalize()}: {count}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                           (255, 255, 255), 2)
                y_offset += 30
            
            # Show frame
            cv2.imshow('Traffic Monitor', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                self.save_data()
                print("Data saved!")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save final data
        self.save_data()
        print("\nProcessing complete!")
        self.display_summary()
    
    def save_data(self):
        """Save current counts to CSV file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_entry = {
            'Timestamp': timestamp,
            'Cars': self.vehicle_counts['car'],
            'Motorcycles': self.vehicle_counts['motorcycle'],
            'Buses': self.vehicle_counts['bus'],
            'Trucks': self.vehicle_counts['truck'],
            'Total': sum(self.vehicle_counts.values())
        }
        
        # Append to CSV
        filename = 'traffic_data.csv'
        df = pd.DataFrame([data_entry])
        
        if os.path.exists(filename):
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, mode='w', header=True, index=False)
    
    def display_summary(self):
        """Display summary of current session"""
        print("\n" + "="*50)
        print("TRAFFIC MONITORING SUMMARY")
        print("="*50)
        print(f"\nVehicle Counts:")
        print(f"  Cars: {self.vehicle_counts['car']}")
        print(f"  Motorcycles: {self.vehicle_counts['motorcycle']}")
        print(f"  Buses: {self.vehicle_counts['bus']}")
        print(f"  Trucks: {self.vehicle_counts['truck']}")
        print(f"  Total: {sum(self.vehicle_counts.values())}")
        print("="*50)

# Example usage
if __name__ == "__main__":
    print("Traffic Monitoring System")
    print("1. Monitor video file")
    print("2. Monitor live camera")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == '1':
        video_path = input("Enter video file path (or press Enter for 'video.mp4'): ")
        if not video_path:
            video_path = 'video.mp4'
        
        monitor = TrafficMonitor(video_path)
        monitor.process_video()
    
    elif choice == '2':
        monitor = TrafficMonitor(0)  # 0 = webcam
        monitor.process_video()
    
    else:
        print("Invalid choice!")