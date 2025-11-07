"""
Modern Traffic Monitoring GUI
Using CustomTkinter for enhanced visuals
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import threading
from datetime import datetime
from pathlib import Path

from config.constants import THEME_COLORS, SKIP_FRAMES, DISPLAY_RESIZE_WIDTH, DISPLAY_RESIZE_HEIGHT
from core import VehicleDetector, VehicleTracker
from utils import DataManager, VideoSource
from ui.components import StatsCard, ModernButton, VideoDisplay, StatusBar, InfoCard


class TrafficMonitorApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Traffic Monitoring System")
        self.geometry("1400x800")
        self.minsize(1000, 600)  # Set minimum window size
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Application state
        self.is_monitoring = False
        self.is_paused = False
        self.video_source = None
        self.is_live = False
        self.current_video = None
        self.session_start = None
        self.frame_counter = 0
        self.processed_frames = 0  # Frames actually processed by AI
        self.last_processed_frame = None  # Cache for display
        
        # Initialize components
        self.detector = VehicleDetector()
        self.tracker = VehicleTracker()
        self.data_manager = DataManager()
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface"""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create sidebar
        self._create_sidebar()
        
        # Create main content
        self._create_main_content()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_sidebar(self):
        """Create sidebar with controls"""
        sidebar = ctk.CTkFrame(
            self,
            width=320,
            corner_radius=0,
            fg_color=THEME_COLORS['sidebar']
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(30, 20))
        
        title_label = ctk.CTkLabel(
            logo_frame,
            text="🚗 Traffic Monitor",
            font=("Segoe UI", 24, "bold"),
            text_color=THEME_COLORS['text']
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="AI-Powered Vehicle Detection",
            font=("Segoe UI", 11),
            text_color=THEME_COLORS['text_secondary']
        )
        subtitle_label.pack()
        
        # Separator
        separator1 = ctk.CTkFrame(sidebar, height=2, fg_color=THEME_COLORS['accent'])
        separator1.pack(fill="x", padx=20, pady=20)
        
        # Source Selection Section
        source_label = ctk.CTkLabel(
            sidebar,
            text="📂 Video Source",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME_COLORS['text'],
            anchor="w"
        )
        source_label.pack(fill="x", padx=20, pady=(0, 15))
        
        self.live_cam_btn = ModernButton(
            sidebar,
            text="Live Camera",
            icon="📹",
            command=self._start_live_camera,
            style="secondary"
        )
        self.live_cam_btn.pack(fill="x", padx=20, pady=5)
        
        self.video_file_btn = ModernButton(
            sidebar,
            text="Video File",
            icon="📁",
            command=self._select_video_file,
            style="secondary"
        )
        self.video_file_btn.pack(fill="x", padx=20, pady=5)
        
        # Separator
        separator2 = ctk.CTkFrame(sidebar, height=2, fg_color=THEME_COLORS['accent'])
        separator2.pack(fill="x", padx=20, pady=20)
        
        # Controls Section
        controls_label = ctk.CTkLabel(
            sidebar,
            text="🎮 Controls",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME_COLORS['text'],
            anchor="w"
        )
        controls_label.pack(fill="x", padx=20, pady=(0, 15))
        
        self.start_btn = ModernButton(
            sidebar,
            text="Start Monitoring",
            icon="▶",
            command=self._toggle_monitoring,
            style="success"
        )
        self.start_btn.pack(fill="x", padx=20, pady=5)
        self.start_btn.configure(state="disabled")
        
        self.pause_btn = ModernButton(
            sidebar,
            text="Pause",
            icon="⏸",
            command=self._toggle_pause,
            style="warning"
        )
        self.pause_btn.pack(fill="x", padx=20, pady=5)
        self.pause_btn.configure(state="disabled")
        
        self.reset_btn = ModernButton(
            sidebar,
            text="Reset Counters",
            icon="🔄",
            command=self._reset_counters,
            style="secondary"
        )
        self.reset_btn.pack(fill="x", padx=20, pady=5)
        
        self.save_btn = ModernButton(
            sidebar,
            text="Save Data",
            icon="💾",
            command=self._save_data,
            style="primary"
        )
        self.save_btn.pack(fill="x", padx=20, pady=5)
        
        # Separator
        separator3 = ctk.CTkFrame(sidebar, height=2, fg_color=THEME_COLORS['accent'])
        separator3.pack(fill="x", padx=20, pady=20)
        
        # Session Info
        session_label = ctk.CTkLabel(
            sidebar,
            text="⏱️ Session Info",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME_COLORS['text'],
            anchor="w"
        )
        session_label.pack(fill="x", padx=20, pady=(0, 15))
        
        # Timer
        self.timer_label = ctk.CTkLabel(
            sidebar,
            text="Duration: 00:00:00",
            font=("Segoe UI", 13),
            text_color=THEME_COLORS['text_secondary']
        )
        self.timer_label.pack(fill="x", padx=20, pady=5)
        
        # Frames processed
        self.frames_label = ctk.CTkLabel(
            sidebar,
            text="Frames: 0",
            font=("Segoe UI", 13),
            text_color=THEME_COLORS['text_secondary']
        )
        self.frames_label.pack(fill="x", padx=20, pady=5)
    
    def _create_main_content(self):
        """Create main content area"""
        main_container = ctk.CTkFrame(
            self,
            fg_color=THEME_COLORS['primary'],
            corner_radius=0
        )
        main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Stats section
        stats_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        stats_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        # Create stat cards
        self.car_card = StatsCard(stats_frame, "Cars", "🚗")
        self.car_card.grid(row=0, column=0, padx=8, pady=0, sticky="ew")
        
        self.motorcycle_card = StatsCard(stats_frame, "Motorcycles", "🏍️")
        self.motorcycle_card.grid(row=0, column=1, padx=8, pady=0, sticky="ew")
        
        self.bus_card = StatsCard(stats_frame, "Buses", "🚌")
        self.bus_card.grid(row=0, column=2, padx=8, pady=0, sticky="ew")
        
        self.truck_card = StatsCard(stats_frame, "Trucks", "🚚")
        self.truck_card.grid(row=0, column=3, padx=8, pady=0, sticky="ew")
        
        self.total_card = StatsCard(stats_frame, "Total", "📊")
        self.total_card.grid(row=0, column=4, padx=8, pady=0, sticky="ew")
        
        # Video display
        self.video_display = VideoDisplay(main_container)
        self.video_display.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        self.video_label = self.video_display.get_video_label()
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.set_status("Ready. Select a video source to begin.", "info")
    
    def _start_live_camera(self):
        """Start live camera monitoring"""
        self.video_source = 0
        self.is_live = True
        self.start_btn.configure(state="normal")
        self.status_bar.set_status("Live camera selected. Click Start to begin.", "success")
        messagebox.showinfo("Camera Selected", "Live camera ready! Click 'Start' to begin monitoring.")
    
    def _select_video_file(self):
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
            self.start_btn.configure(state="normal")
            filename = Path(file_path).name
            self.status_bar.set_status(f"Video selected: {filename}", "success")
            messagebox.showinfo("Video Selected", f"Video loaded: {filename}\nClick 'Start' to begin.")
    
    def _toggle_monitoring(self):
        """Start/stop monitoring"""
        if not self.is_monitoring:
            self._start_monitoring()
        else:
            self._stop_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring process"""
        if self.video_source is None:
            messagebox.showerror("Error", "Please select a video source first!")
            return
        
        # Load model
        self.status_bar.set_status("Loading AI model... Please wait.", "warning")
        self.update()
        
        try:
            self.detector.load_model()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {e}")
            self.status_bar.set_status("Failed to load model.", "danger")
            return
        
        # Open video source
        self.current_video = VideoSource(self.video_source, self.is_live)
        if not self.current_video.open():
            messagebox.showerror("Error", "Failed to open video source!")
            self.status_bar.set_status("Failed to open video source.", "danger")
            return
        
        # Update state
        self.is_monitoring = True
        self.session_start = datetime.now()
        self.frame_counter = 0
        
        # Update UI
        self.start_btn.configure(text="⏹  Stop Monitoring", fg_color=THEME_COLORS['danger'])
        self.pause_btn.configure(state="normal")
        self.live_cam_btn.configure(state="disabled")
        self.video_file_btn.configure(state="disabled")
        self.status_bar.set_status("Monitoring active...", "success")
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start timer
        self._update_timer()
    
    def _stop_monitoring(self):
        """Stop monitoring process"""
        self.is_monitoring = False
        
        if self.current_video:
            self.current_video.release()
        
        # Update UI
        self.start_btn.configure(text="▶  Start Monitoring", fg_color=THEME_COLORS['success'])
        self.pause_btn.configure(state="disabled")
        self.live_cam_btn.configure(state="normal")
        self.video_file_btn.configure(state="normal")
        self.status_bar.set_status("Monitoring stopped.", "info")
        
        # Save data
        self._save_data()
    
    def _toggle_pause(self):
        """Pause/resume monitoring"""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.configure(text="▶  Resume", fg_color=THEME_COLORS['success'])
            self.status_bar.set_status("Monitoring paused.", "warning")
        else:
            self.pause_btn.configure(text="⏸  Pause", fg_color=THEME_COLORS['warning'])
            self.status_bar.set_status("Monitoring active...", "success")
    
    def _monitoring_loop(self):
        """Main monitoring loop with frame skipping optimization"""
        import time
        
        while self.is_monitoring:
            if not self.is_paused:
                ret, frame = self.current_video.read()
                
                if not ret:
                    self.after(0, self._stop_monitoring)
                    break
                
                self.frame_counter += 1
                
                # Process every Nth frame based on SKIP_FRAMES setting
                if self.frame_counter % SKIP_FRAMES == 0:
                    # Process this frame
                    self.processed_frames += 1
                    processed_frame = self._process_frame(frame.copy())
                    self.last_processed_frame = processed_frame
                    
                    # Display processed frame
                    self.after(0, lambda f=processed_frame: self._display_frame(f))
                    
                    # Update stats every 5 processed frames to reduce GUI overhead
                    if self.processed_frames % 5 == 0:
                        self.after(0, self._update_stats)
                        self.after(0, lambda: self.frames_label.configure(
                            text=f"Frames: {self.frame_counter} (Processed: {self.processed_frames})"
                        ))
                else:
                    # Skip AI processing, but still display last processed frame
                    if self.last_processed_frame is not None and self.frame_counter % 2 == 0:
                        self.after(0, lambda f=self.last_processed_frame: self._display_frame(f))
            else:
                # Paused - wait a bit
                time.sleep(0.1)
    
    def _process_frame(self, frame):
        """Process frame for vehicle detection"""
        # Detect vehicles
        detections = self.detector.detect(frame)
        
        # Update tracking
        new_objects = self.tracker.update(detections)
        self.tracker.count_new_vehicles(new_objects)
        
        # Draw annotations
        frame = self.detector.draw_detections(frame, detections, self.tracker)
        
        return frame
    
    def _display_frame(self, frame):
        """Display frame in GUI with dynamic resizing to fit container"""
        # Convert color space
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get current container size
        container_width = self.video_label.winfo_width()
        container_height = self.video_label.winfo_height()
        
        # Use default size if container not yet rendered (initial display)
        if container_width <= 1 or container_height <= 1:
            container_width = DISPLAY_RESIZE_WIDTH
            container_height = DISPLAY_RESIZE_HEIGHT
        
        # Calculate aspect ratios
        frame_aspect = frame.shape[1] / frame.shape[0]  # width / height
        container_aspect = container_width / container_height
        
        # Determine resize dimensions to fill container while maintaining aspect ratio
        if frame_aspect > container_aspect:
            # Frame is wider - fit to width
            new_width = container_width
            new_height = int(container_width / frame_aspect)
        else:
            # Frame is taller - fit to height
            new_height = container_height
            new_width = int(container_height * frame_aspect)
        
        # Resize frame for display using fast interpolation
        frame_resized = cv2.resize(
            frame_rgb, 
            (new_width, new_height),
            interpolation=cv2.INTER_LINEAR  # Faster than INTER_CUBIC
        )
        
        # Convert to PIL Image then CTkImage
        pil_image = Image.fromarray(frame_resized)
        ctk_image = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=(new_width, new_height)
        )
        
        # Update display
        self.video_label.configure(image=ctk_image)
        self.video_label.image = ctk_image  # Keep reference
    
    def _update_stats(self):
        """Update statistics display"""
        counts = self.tracker.get_counts()
        
        self.car_card.update_value(counts.get('car', 0))
        self.motorcycle_card.update_value(counts.get('motorcycle', 0))
        self.bus_card.update_value(counts.get('bus', 0))
        self.truck_card.update_value(counts.get('truck', 0))
        self.total_card.update_value(self.tracker.get_total_count())
    
    def _update_timer(self):
        """Update timer display"""
        if self.is_monitoring and self.session_start:
            duration = datetime.now() - self.session_start
            duration_str = str(duration).split('.')[0]
            self.timer_label.configure(text=f"Duration: {duration_str}")
            self.after(1000, self._update_timer)
    
    def _reset_counters(self):
        """Reset all counters"""
        if messagebox.askyesno("Reset Counters", "Are you sure you want to reset all counters?"):
            self.tracker.reset()
            self.frame_counter = 0
            self.processed_frames = 0
            self.session_start = datetime.now()
            self._update_stats()
            self.frames_label.configure(text="Frames: 0 (Processed: 0)")
            self.status_bar.set_status("Counters reset.", "info")
    
    def _save_data(self):
        """Save monitoring data to CSV"""
        counts = self.tracker.get_counts()
        
        if self.tracker.get_total_count() == 0:
            return
        
        filename = self.data_manager.save_session_data(counts, self.session_start, self.is_live)
        
        if filename:
            messagebox.showinfo("Data Saved", f"Session data saved to {filename}")
            self.status_bar.set_status(f"Data saved to {filename}", "success")


def main():
    """Main entry point"""
    app = TrafficMonitorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
