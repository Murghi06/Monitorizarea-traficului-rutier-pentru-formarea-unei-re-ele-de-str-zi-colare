"""
Traffic Monitoring System - GUI Version
Modern interface with Tkinter
"""

import cv2
from ultralytics import YOLO
import pandas as pd
from datetime import datetime
import numpy as np
from collections import defaultdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading

class TrafficMonitorGUI:
    """GUI wrapper for Traffic Monitor"""
    
    # Class constants
    VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
    COLOR_MAP = {
        'car': (0, 255, 0),
        'motorcycle': (255, 0, 0),
        'bus': (0, 0, 255),
        'truck': (255, 255, 0),
        'parked': (128, 128, 128)
    }
    CONFIDENCE_THRESHOLD = 0.45
    DISTANCE_THRESHOLD = 150
    MAX_DISAPPEARED_FRAMES = 45
    PARKED_THRESHOLD = 200
    MOVEMENT_THRESHOLD = 15
    
    def __init__(self, root):
        """Initialize GUI"""
        self.root = root
        self.root.title("Traffic Monitoring System")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # Variables
        self.is_monitoring = False
        self.is_paused = False
        self.video_source = None
        self.is_live = False
        self.cap = None
        self.model = None
        
        # Monitoring variables
        self.vehicle_counts = defaultdict(int)
        self.tracked_objects = {}
        self.next_object_id = 0
        self.session_start = None
        self.frame_counter = 0
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Create GUI layout"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🚗 Traffic Monitoring System", 
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Video display
        left_panel = tk.Frame(main_container, bg="#ecf0f1", relief=tk.RIDGE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        video_label = tk.Label(left_panel, text="Video Feed", font=("Arial", 12, "bold"), bg="#ecf0f1")
        video_label.pack(pady=5)
        
        self.video_canvas = tk.Label(left_panel, bg="black")
        self.video_canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Right panel - Controls and stats
        right_panel = tk.Frame(main_container, bg="#ecf0f1", relief=tk.RIDGE, bd=2, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Source selection
        source_frame = tk.LabelFrame(right_panel, text="Source Selection", font=("Arial", 11, "bold"), bg="#ecf0f1", padx=10, pady=10)
        source_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            source_frame, 
            text="📹 Live Camera", 
            command=self.start_live_camera,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            source_frame, 
            text="📁 Select Video File", 
            command=self.select_video_file,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        ).pack(fill=tk.X, pady=5)
        
        # Controls
        control_frame = tk.LabelFrame(right_panel, text="Controls", font=("Arial", 11, "bold"), bg="#ecf0f1", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = tk.Button(
            control_frame, 
            text="▶ Start", 
            command=self.toggle_monitoring,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.start_btn.pack(fill=tk.X, pady=5)
        
        self.pause_btn = tk.Button(
            control_frame, 
            text="⏸ Pause", 
            command=self.toggle_pause,
            bg="#f39c12",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.pause_btn.pack(fill=tk.X, pady=5)
        
        tk.Button(
            control_frame, 
            text="🔄 Reset Counters", 
            command=self.reset_counts,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            control_frame, 
            text="💾 Save Data", 
            command=self.save_data,
            bg="#16a085",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        ).pack(fill=tk.X, pady=5)
        
        # Statistics
        stats_frame = tk.LabelFrame(right_panel, text="Vehicle Counts", font=("Arial", 11, "bold"), bg="#ecf0f1", padx=10, pady=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_labels = {}
        for vehicle_type in ['car', 'motorcycle', 'bus', 'truck', 'total']:
            frame = tk.Frame(stats_frame, bg="#ecf0f1")
            frame.pack(fill=tk.X, pady=3)
            
            label = tk.Label(
                frame,
                text=f"{vehicle_type.capitalize()}:",
                font=("Arial", 10, "bold"),
                bg="#ecf0f1",
                width=12,
                anchor="w"
            )
            label.pack(side=tk.LEFT)
            
            count_label = tk.Label(
                frame,
                text="0",
                font=("Arial", 12, "bold"),
                bg="#ecf0f1",
                fg="#2c3e50"
            )
            count_label.pack(side=tk.RIGHT)
            self.stats_labels[vehicle_type] = count_label
        
        # Timer
        self.timer_label = tk.Label(
            stats_frame,
            text="Duration: 00:00:00",
            font=("Arial", 10),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        self.timer_label.pack(pady=(10, 0))
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready. Select a video source to begin.",
            font=("Arial", 9),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def start_live_camera(self):
        """Start live camera monitoring"""
        self.video_source = 0
        self.is_live = True
        self.start_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Live camera selected. Click Start to begin monitoring.")
        messagebox.showinfo("Camera Selected", "Live camera ready! Click 'Start' to begin monitoring.")
    
    def select_video_file(self):
        """Select video file"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.video_source = file_path
            self.is_live = False
            self.start_btn.config(state=tk.NORMAL)
            self.status_label.config(text=f"Video selected: {Path(file_path).name}")
            messagebox.showinfo("Video Selected", f"Video loaded: {Path(file_path).name}\nClick 'Start' to begin.")
    
    def toggle_monitoring(self):
        """Start/stop monitoring"""
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start monitoring thread"""
        if self.video_source is None:
            messagebox.showerror("Error", "Please select a video source first!")
            return
        
        # Load model if not loaded
        if self.model is None:
            self.status_label.config(text="Loading YOLO model... Please wait.")
            self.root.update()
            try:
                self.model = YOLO('yolov8n.pt')
                self.model.fuse()
                # Warm-up
                dummy = np.zeros((384, 640, 3), dtype=np.uint8)
                self.model(dummy, verbose=False, imgsz=640)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model: {e}")
                return
        
        # Open video source
        try:
            if self.is_live:
                for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                    self.cap = cv2.VideoCapture(self.video_source, backend)
                    if self.cap.isOpened():
                        break
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
                self.cap = cv2.VideoCapture(self.video_source)
            
            if not self.cap.isOpened():
                raise Exception("Could not open video source")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open video source: {e}")
            return
        
        self.is_monitoring = True
        self.session_start = datetime.now()
        self.start_btn.config(text="⏹ Stop", bg="#e74c3c")
        self.pause_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Monitoring active...")
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start timer update
        self.update_timer()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.cap:
            self.cap.release()
        self.start_btn.config(text="▶ Start", bg="#27ae60")
        self.pause_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Monitoring stopped.")
        self.save_data()
    
    def toggle_pause(self):
        """Pause/resume monitoring"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="▶ Resume", bg="#27ae60")
            self.status_label.config(text="Monitoring paused.")
        else:
            self.pause_btn.config(text="⏸ Pause", bg="#f39c12")
            self.status_label.config(text="Monitoring active...")
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            if not self.is_paused:
                ret, frame = self.cap.read()
                if not ret:
                    self.root.after(0, self.stop_monitoring)
                    break
                
                # Process frame
                frame = self.process_frame(frame)
                
                # Display frame
                self.display_frame(frame)
                
                # Update stats
                self.root.after(0, self.update_stats)
    
    def process_frame(self, frame):
        """Process frame for vehicle detection"""
        self.frame_counter += 1
        
        # Run detection
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
        frame = self.draw_annotations(frame, detections)
        
        return frame
    
    def update_tracking(self, detections):
        """Update object tracking"""
        if not detections:
            for obj_id in list(self.tracked_objects.keys()):
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.MAX_DISAPPEARED_FRAMES:
                    del self.tracked_objects[obj_id]
            return []
        
        current_centroids = [self.calculate_centroid(det['box']) for det in detections]
        
        if not self.tracked_objects:
            return self.register_new_objects(detections, current_centroids)
        
        return self.match_and_update(detections, current_centroids)
    
    @staticmethod
    def calculate_centroid(box):
        """Calculate center of box"""
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    @staticmethod
    def calculate_distance(p1, p2):
        """Calculate distance between points"""
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def register_new_objects(self, detections, centroids):
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
    
    def match_and_update(self, detections, current_centroids):
        """Match detections to tracked objects"""
        object_ids = list(self.tracked_objects.keys())
        object_centroids = [self.tracked_objects[oid]['centroid'] for oid in object_ids]
        
        obj_array = np.array(object_centroids)
        curr_array = np.array(current_centroids)
        
        distances = np.zeros((len(object_centroids), len(current_centroids)))
        for i in range(len(obj_array)):
            distances[i] = np.sqrt(np.sum((curr_array - obj_array[i])**2, axis=1))
        
        matched_objects = set()
        matched_detections = set()
        new_objects = []
        
        for _ in range(min(len(object_ids), len(current_centroids))):
            min_idx = np.unravel_index(distances.argmin(), distances.shape)
            
            if distances[min_idx] < self.DISTANCE_THRESHOLD:
                obj_id = object_ids[min_idx[0]]
                obj = self.tracked_objects[obj_id]
                old_centroid = obj['centroid']
                new_centroid = current_centroids[min_idx[1]]
                
                movement = self.calculate_distance(old_centroid, new_centroid)
                
                obj['centroid'] = new_centroid
                obj['disappeared'] = 0
                obj['total_movement'] += movement
                
                if movement < self.MOVEMENT_THRESHOLD:
                    obj['stationary_frames'] += 1
                else:
                    was_parked = obj['is_parked']
                    obj['stationary_frames'] = 0
                    obj['is_parked'] = False
                    
                    if was_parked and not obj['counted']:
                        self.vehicle_counts[obj['class']] += 1
                        obj['counted'] = True
                
                if obj['stationary_frames'] > self.PARKED_THRESHOLD:
                    obj['is_parked'] = True
                
                matched_objects.add(min_idx[0])
                matched_detections.add(min_idx[1])
                distances[min_idx[0], :] = np.inf
                distances[:, min_idx[1]] = np.inf
        
        for i, obj_id in enumerate(object_ids):
            if i not in matched_objects:
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.MAX_DISAPPEARED_FRAMES:
                    del self.tracked_objects[obj_id]
        
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
        """Count new vehicles"""
        for obj_id in new_object_ids:
            obj = self.tracked_objects.get(obj_id)
            if obj and not obj['counted'] and not obj['is_parked']:
                self.vehicle_counts[obj['class']] += 1
                obj['counted'] = True
    
    def draw_annotations(self, frame, detections):
        """Draw boxes and labels"""
        for det in detections:
            x1, y1, x2, y2 = map(int, det['box'])
            centroid = self.calculate_centroid(det['box'])
            
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
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame
    
    def display_frame(self, frame):
        """Display frame in GUI"""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (640, 480))
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        self.video_canvas.imgtk = imgtk
        self.video_canvas.configure(image=imgtk)
    
    def update_stats(self):
        """Update statistics display"""
        self.stats_labels['car'].config(text=str(self.vehicle_counts['car']))
        self.stats_labels['motorcycle'].config(text=str(self.vehicle_counts['motorcycle']))
        self.stats_labels['bus'].config(text=str(self.vehicle_counts['bus']))
        self.stats_labels['truck'].config(text=str(self.vehicle_counts['truck']))
        self.stats_labels['total'].config(text=str(sum(self.vehicle_counts.values())))
    
    def update_timer(self):
        """Update timer display"""
        if self.is_monitoring and self.session_start:
            duration = datetime.now() - self.session_start
            duration_str = str(duration).split('.')[0]
            self.timer_label.config(text=f"Duration: {duration_str}")
            self.root.after(1000, self.update_timer)
    
    def reset_counts(self):
        """Reset all counts"""
        if messagebox.askyesno("Reset", "Reset all counters?"):
            self.vehicle_counts = defaultdict(int)
            self.tracked_objects = {}
            self.next_object_id = 0
            self.frame_counter = 0
            self.session_start = datetime.now()
            self.update_stats()
            self.status_label.config(text="Counters reset.")
    
    def save_data(self):
        """Save data to CSV"""
        if sum(self.vehicle_counts.values()) == 0:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = str(datetime.now() - self.session_start).split('.')[0] if self.session_start else "00:00:00"
        
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
        
        messagebox.showinfo("Saved", f"Data saved to {filename}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TrafficMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()