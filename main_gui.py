"""
Traffic Monitoring System - Main Entry Point
Modern AI-powered traffic monitoring with enhanced UI

Features:
- Real-time vehicle detection using YOLOv8
- Live camera and video file support
- Vehicle counting and tracking
- Parked vehicle detection
- Session data export to CSV
- Modern, user-friendly interface with CustomTkinter

Usage:
    python main_gui.py
"""

from ui import TrafficMonitorApp


def main():
    """Launch the Traffic Monitoring System"""
    app = TrafficMonitorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
