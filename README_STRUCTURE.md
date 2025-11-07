# Traffic Monitoring System - Modern UI

## 📋 Overview

A modern, AI-powered traffic monitoring system with an enhanced user interface built using CustomTkinter. The application features real-time vehicle detection, tracking, and counting using YOLOv8.

## ✨ Features

- 🎨 **Modern UI**: Beautiful, dark-themed interface with CustomTkinter
- 🚗 **Vehicle Detection**: Real-time detection of cars, motorcycles, buses, and trucks
- 📹 **Multiple Sources**: Support for live camera and video files
- 📊 **Statistics Dashboard**: Real-time vehicle counting with visual cards
- 🅿️ **Parked Vehicle Detection**: Identifies and marks stationary vehicles
- 💾 **Data Export**: Saves session data to CSV for analysis
- ⏸️ **Pause/Resume**: Control monitoring with pause functionality
- 🔄 **Reset Counters**: Clear statistics without restarting

## 🏗️ Project Structure

```
├── config/                 # Configuration constants
│   ├── __init__.py
│   └── constants.py       # Theme colors, detection parameters
│
├── core/                   # Core detection and tracking logic
│   ├── __init__.py
│   ├── detector.py        # YOLO-based vehicle detection
│   └── tracker.py         # Vehicle tracking and counting
│
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── components.py      # Reusable UI components
│   └── main_window.py     # Main application window
│
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── data_manager.py    # CSV data handling
│   └── video_source.py    # Video capture management
│
├── DetectV5_Code_GUI.py   # Enhanced main script (uses new modules)
├── main_gui.py            # Alternative entry point
└── README_STRUCTURE.md    # This file
```

## 🚀 Getting Started

### Prerequisites

```bash
pip install customtkinter opencv-python ultralytics pandas pillow numpy
```

### Running the Application

**Option 1: Using the enhanced script**
```bash
python DetectV5_Code_GUI.py
```

**Option 2: Using the standalone launcher**
```bash
python main_gui.py
```

## 🎮 Usage

1. **Select a Video Source**
   - Click "📹 Live Camera" to use your webcam
   - Click "📁 Video File" to select a video file

2. **Start Monitoring**
   - Click "▶ Start Monitoring" to begin detection
   - The AI model will load automatically

3. **Control Playback**
   - Use "⏸ Pause" to pause/resume monitoring
   - Click "⏹ Stop Monitoring" to end the session

4. **Manage Data**
   - Click "🔄 Reset Counters" to clear statistics
   - Click "💾 Save Data" to export to CSV

## 🎨 UI Components

### Stats Cards
- **Cars**: Green highlight for detected cars
- **Motorcycles**: Red highlight for motorcycles
- **Buses**: Blue highlight for buses
- **Trucks**: Yellow highlight for trucks
- **Total**: Aggregated count of all vehicles

### Video Display
- Real-time video feed with bounding boxes
- Color-coded vehicle detection
- Parked vehicle indicators (gray boxes)

### Status Bar
- Real-time status updates
- Color-coded indicators (success/warning/danger/info)

## ⚙️ Configuration

Edit `config/constants.py` to customize:

- **Detection Parameters**: Confidence threshold, tracking settings
- **Theme Colors**: Customize the UI color scheme
- **Camera Settings**: Resolution, buffer size
- **Model Settings**: YOLO model selection

## 📊 Data Export

Session data is automatically saved to `traffic_data.csv` with:
- Timestamp
- Source type (Live Camera/Video File)
- Session duration
- Vehicle counts by type
- Total vehicle count

## 🛠️ Maintenance

### Adding New Vehicle Types

1. Update `VEHICLE_CLASSES` in `config/constants.py`
2. Add color mapping in `COLOR_MAP`
3. Update UI to add new stat card in `ui/main_window.py`

### Customizing Theme

Edit the `THEME_COLORS` dictionary in `config/constants.py`:
```python
THEME_COLORS = {
    'primary': '#1a1a2e',      # Main background
    'secondary': '#16213e',     # Secondary background
    'accent': '#0f3460',        # Accent color
    'success': '#06d6a0',       # Success actions
    'warning': '#ffd166',       # Warning states
    'danger': '#ef476f',        # Danger/stop actions
    # ... more colors
}
```

### Extending Functionality

The modular structure makes it easy to:
- Add new detection models (modify `core/detector.py`)
- Implement new tracking algorithms (modify `core/tracker.py`)
- Add export formats (extend `utils/data_manager.py`)
- Create new UI components (add to `ui/components.py`)

## 🐛 Troubleshooting

**Model Loading Issues**
- Ensure YOLOv8 model file (`yolov8n.pt`) is accessible
- Check internet connection (first run downloads the model)

**Camera Not Opening**
- Verify camera permissions
- Try different camera indices (0, 1, 2)
- Check if another application is using the camera

**Performance Issues**
- Lower the video resolution in `config/constants.py`
- Use a lighter YOLO model (yolov8n.pt is recommended)
- Close other resource-intensive applications

## 📝 License

This project is part of a hackathon submission for school street safety monitoring.

## 👥 Contributors

Developed for the School Street Traffic Safety Initiative

---

**Note**: The old implementation remains in `DetectV5_Code_GUI.py` as `TrafficMonitorGUI_Legacy` for reference purposes.
