"""
Traffic Monitoring System - Main Entry Point
Modern interface with CustomTkinter for monitoring traffic and counting vehicles
"""
import customtkinter as ctk
from ui.main_window import TrafficMonitorGUI


def main():
    """Main entry point for the application"""
    root = ctk.CTk()
    app = TrafficMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
