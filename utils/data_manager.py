"""
Data handling utilities
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from config.constants import DATA_FILE


class DataManager:
    """Manages data saving and loading"""
    
    @staticmethod
    def save_session_data(vehicle_counts, session_start, is_live):
        """Save monitoring session data to CSV with proper column alignment"""
        if sum(vehicle_counts.values()) == 0:
            return None
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = str(datetime.now() - session_start).split('.')[0] if session_start else "00:00:00"
        
        # Column structure aligned to requirements:
        # A: Timestamp, B: Source, C: Time Monitored, D: Cars, E: Motorcycles, F: Buses, G: Trucks, H: Total
        data = {
            'Timestamp': [timestamp],                              # Column A (1)
            'Source': ['Live Camera' if is_live else 'Video File'], # Column B (2)
            'Processing Time': [duration],                          # Column C (3)
            'Cars': [vehicle_counts.get('car', 0)],               # Column D (4)
            'Motorcycles': [vehicle_counts.get('motorcycle', 0)], # Column E (5)
            'Buses': [vehicle_counts.get('bus', 0)],              # Column F (6)
            'Trucks': [vehicle_counts.get('truck', 0)],           # Column G (7)
            'Total': [sum(vehicle_counts.values())]               # Column H (8)
        }
        
        df = pd.DataFrame(data)
        
        if Path(DATA_FILE).exists():
            df.to_csv(DATA_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(DATA_FILE, mode='w', header=True, index=False)
        
        return DATA_FILE
    
    @staticmethod
    def load_historical_data():
        """Load historical monitoring data"""
        if Path(DATA_FILE).exists():
            return pd.read_csv(DATA_FILE)
        return None
