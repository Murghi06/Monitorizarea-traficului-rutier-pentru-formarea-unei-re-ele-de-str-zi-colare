"""
Performance Configuration Tool
Quick tool to adjust optimization settings
"""

import re
from pathlib import Path


def read_constants():
    """Read current configuration"""
    config_path = Path("config/constants.py")
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract current values
    skip_frames = int(re.search(r'SKIP_FRAMES\s*=\s*(\d+)', content).group(1))
    use_gpu = re.search(r'USE_GPU\s*=\s*(True|False)', content).group(1) == 'True'
    
    return content, skip_frames, use_gpu


def write_constants(content):
    """Write updated configuration"""
    config_path = Path("config/constants.py")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    print("=" * 70)
    print("  Traffic Monitoring System - Performance Configuration")
    print("=" * 70)
    print()
    
    try:
        content, current_skip, current_gpu = read_constants()
        
        print("Current Settings:")
        print(f"  SKIP_FRAMES: {current_skip}")
        print(f"  USE_GPU: {current_gpu}")
        print()
        print("-" * 70)
        print()
        
        # Configure SKIP_FRAMES
        print("Frame Skipping Configuration")
        print("  1 = Process every frame (slowest, most accurate)")
        print("  2 = Process every 2nd frame (recommended, 2x faster)")
        print("  3 = Process every 3rd frame (3x faster, good for live camera)")
        print("  4 = Process every 4th frame (4x faster, may miss fast vehicles)")
        print()
        
        skip_input = input(f"Enter SKIP_FRAMES value (1-5) [{current_skip}]: ").strip()
        
        if skip_input:
            new_skip = int(skip_input)
            if new_skip < 1 or new_skip > 5:
                print("❌ Invalid value. Must be between 1 and 5.")
                return
        else:
            new_skip = current_skip
        
        # Configure GPU
        print()
        print("GPU Acceleration Configuration")
        print("  True = Enable GPU if available (much faster)")
        print("  False = Use CPU only")
        print()
        
        gpu_input = input(f"Enable GPU acceleration? (y/n) [{'y' if current_gpu else 'n'}]: ").strip().lower()
        
        if gpu_input:
            new_gpu = gpu_input == 'y'
        else:
            new_gpu = current_gpu
        
        # Update configuration
        content = re.sub(r'SKIP_FRAMES\s*=\s*\d+', f'SKIP_FRAMES = {new_skip}', content)
        content = re.sub(r'USE_GPU\s*=\s*(True|False)', f'USE_GPU = {new_gpu}', content)
        
        write_constants(content)
        
        print()
        print("=" * 70)
        print("✓ Configuration updated successfully!")
        print()
        print(f"  SKIP_FRAMES: {current_skip} → {new_skip}")
        print(f"  USE_GPU: {current_gpu} → {new_gpu}")
        print()
        
        # Expected performance
        if new_skip == 1:
            speed = "1x (baseline)"
        else:
            speed = f"~{new_skip}x faster"
        
        if new_gpu:
            speed += " + GPU boost (5-10x if GPU available)"
        
        print(f"Expected speed improvement: {speed}")
        print()
        print("⚠ Restart the application for changes to take effect.")
        print("=" * 70)
        
    except FileNotFoundError:
        print("❌ Error: config/constants.py not found!")
        print("   Make sure you're running this from the project root directory.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
