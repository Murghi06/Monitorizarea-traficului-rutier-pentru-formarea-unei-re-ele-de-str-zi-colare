# Migration Guide - Old to New UI

## 🔄 Migrating from Old to New Interface

This guide helps you transition from the old Tkinter implementation to the new CustomTkinter version.

## Quick Start

### Old Way
```python
python DetectV5_Code_GUI.py  # Used old TrafficMonitorGUI class
```

### New Way
```python
python DetectV5_Code_GUI.py  # Now uses new TrafficMonitorApp
# OR
python main_gui.py            # Alternative launcher
```

The file `DetectV5_Code_GUI.py` has been updated to use the new modular system automatically!

## What Changed?

### 1. Dependencies
**New requirement:**
```bash
pip install customtkinter
```

All other dependencies remain the same.

### 2. Entry Point

**Before:**
```python
from DetectV5_Code_GUI import TrafficMonitorGUI

root = tk.Tk()
app = TrafficMonitorGUI(root)
root.mainloop()
```

**After:**
```python
from ui import TrafficMonitorApp

app = TrafficMonitorApp()  # No need to create Tk() root
app.mainloop()
```

### 3. Functionality Mapping

All features from the old version are preserved:

| Old Feature | New Feature | Status |
|-------------|-------------|--------|
| Live Camera | 📹 Live Camera button | ✅ Same |
| Video File | 📁 Video File button | ✅ Same |
| Start/Stop | ▶ Start/⏹ Stop Monitoring | ✅ Enhanced |
| Pause | ⏸ Pause button | ✅ Enhanced |
| Reset Counters | 🔄 Reset Counters | ✅ Same |
| Save Data | 💾 Save Data | ✅ Same |
| Vehicle Counts | Stat Cards | ✅ Enhanced |
| Timer | Duration display | ✅ Enhanced |
| Status Bar | Color-coded status | ✅ Enhanced |

## Configuration Changes

### Before: Hardcoded Values
```python
class TrafficMonitorGUI:
    CONFIDENCE_THRESHOLD = 0.45
    # ... buried in class definition
```

### After: Centralized Config
```python
# Edit config/constants.py
CONFIDENCE_THRESHOLD = 0.45
DISTANCE_THRESHOLD = 150
# ... all in one place
```

## Customization Guide

### Changing Theme Colors

**File:** `config/constants.py`

```python
THEME_COLORS = {
    'primary': '#1a1a2e',      # Your color here
    'success': '#06d6a0',       # Your color here
    # ...
}
```

### Modifying Detection Parameters

**File:** `config/constants.py`

```python
CONFIDENCE_THRESHOLD = 0.45    # 0.0 to 1.0
DISTANCE_THRESHOLD = 150       # pixels
PARKED_THRESHOLD = 200         # frames
MOVEMENT_THRESHOLD = 15        # pixels
```

### Adding New Vehicle Types

**1. Update config** (`config/constants.py`):
```python
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck',
    8: 'bicycle',  # New type
}

COLOR_MAP = {
    # ...existing colors...
    'bicycle': (255, 165, 0),  # Orange
}
```

**2. Update UI** (`ui/main_window.py` in `_create_main_content`):
```python
self.bicycle_card = StatsCard(stats_frame, "Bicycles", "🚲")
self.bicycle_card.grid(row=0, column=5, padx=8, pady=0, sticky="ew")
```

**3. Update stats** (`ui/main_window.py` in `_update_stats`):
```python
self.bicycle_card.update_value(counts.get('bicycle', 0))
```

## Code Organization

### Old Structure
```
DetectV5_Code_GUI.py (600+ lines)
  └── Everything in one file
```

### New Structure
```
config/
  └── constants.py          ← All configuration
core/
  ├── detector.py           ← YOLO detection logic
  └── tracker.py            ← Tracking algorithms
ui/
  ├── components.py         ← Reusable UI components
  └── main_window.py        ← Main application
utils/
  ├── data_manager.py       ← Data export
  └── video_source.py       ← Video handling
```

## Extending the Application

### Adding a New UI Component

**File:** `ui/components.py`

```python
class MyCustomWidget(ctk.CTkFrame):
    """Your custom widget"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # Your widget code here
```

Then use it in `ui/main_window.py`:
```python
from ui.components import MyCustomWidget

# In _setup_ui or similar method:
my_widget = MyCustomWidget(parent_frame)
my_widget.pack()
```

### Adding Data Export Formats

**File:** `utils/data_manager.py`

```python
class DataManager:
    @staticmethod
    def export_to_json(vehicle_counts, session_start, is_live):
        """Export session data to JSON"""
        import json
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'counts': dict(vehicle_counts),
            # ... your data structure
        }
        
        with open('traffic_data.json', 'w') as f:
            json.dump(data, f, indent=2)
```

### Customizing Detection Algorithm

**File:** `core/detector.py`

```python
class VehicleDetector:
    def detect(self, frame):
        # Modify detection logic here
        # Or use a different model
        pass
```

## Backward Compatibility

The old `TrafficMonitorGUI` class is preserved as `TrafficMonitorGUI_Legacy` in `DetectV5_Code_GUI.py`.

To use the old version:
```python
from DetectV5_Code_GUI import TrafficMonitorGUI_Legacy
import tkinter as tk

root = tk.Tk()
app = TrafficMonitorGUI_Legacy(root)
root.mainloop()
```

However, we recommend using the new version for:
- Better user experience
- Easier maintenance
- Modern appearance
- Future updates

## Data Compatibility

✅ **CSV files are fully compatible** between old and new versions!

Both save to `traffic_data.csv` with the same format:
```csv
Timestamp,Source,Duration,Cars,Motorcycles,Buses,Trucks,Total
2025-11-07 14:30:00,Live Camera,00:05:23,42,5,2,3,52
```

## Troubleshooting

### "Module 'customtkinter' not found"
```bash
pip install customtkinter
```

### "Cannot import TrafficMonitorApp"
Make sure you're running from the project root directory where the `ui/`, `core/`, etc. folders are located.

### Colors Look Wrong
Check that you're using the dark theme:
```python
# This is set automatically in main_window.py
ctk.set_appearance_mode("dark")
```

### Performance Issues
The new UI has the same performance as the old one. If you experience issues:
1. Check your YOLO model size
2. Reduce video resolution in `config/constants.py`
3. Close other applications

## Getting Help

1. Check `README_STRUCTURE.md` for architecture overview
2. Read `IMPROVEMENTS.md` for detailed changes
3. Run `python QUICKSTART.py` for a quick guide
4. Examine the inline comments in the code

## Summary

✅ **All features preserved**
✅ **Better organization**
✅ **Modern interface**
✅ **Easy to customize**
✅ **Old code preserved for reference**

The migration is seamless - just run the same file and enjoy the new interface!
