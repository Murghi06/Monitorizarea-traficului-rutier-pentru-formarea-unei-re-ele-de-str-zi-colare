@echo off
echo ========================================
echo Traffic Monitoring System - Dependency Installer
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install dependencies
echo Installing required packages...
echo.

echo [1/7] Installing OpenCV...
python -m pip install opencv-python

echo [2/7] Installing Ultralytics (YOLO)...
python -m pip install ultralytics

echo [3/7] Installing Pandas...
python -m pip install pandas

echo [4/7] Installing NumPy...
python -m pip install numpy

echo [5/7] Installing Pillow...
python -m pip install pillow

echo [6/7] Installing CustomTkinter...
python -m pip install customtkinter

echo [7/7] Installing additional dependencies...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo All dependencies have been installed successfully.
echo You can now run the application using: python main.py
echo.
pause
