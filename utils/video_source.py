"""
Video source handling utilities
"""

import cv2
from config.constants import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_BUFFER_SIZE


class VideoSource:
    """Handles video capture from different sources"""
    
    def __init__(self, source, is_live=False):
        self.source = source
        self.is_live = is_live
        self.cap = None
        self.resolution = (0, 0)  # Will be set when video opens
    
    def open(self):
        """Open video source with hardware acceleration"""
        if self.is_live:
            # Try different backends for live camera
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                self.cap = cv2.VideoCapture(self.source, backend)
                if self.cap.isOpened():
                    break
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFER_SIZE)
        else:
            # For video files, try hardware-accelerated backends
            self.cap = cv2.VideoCapture(self.source)
            
            if self.cap.isOpened():
                # Try to enable hardware acceleration
                try:
                    self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                except:
                    pass  # If not supported, continue with software decode
                
                # Minimize buffering for responsive playback
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Get video resolution if opened successfully
        if self.cap and self.cap.isOpened():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.resolution = (width, height)
        
        return self.cap.isOpened() if self.cap else False
    
    def get_resolution(self):
        """Get video resolution as (width, height)"""
        return self.resolution
    
    def get_fps(self):
        """Get video frame rate"""
        if self.cap and self.cap.isOpened():
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0
    
    def read(self):
        """Read frame from video source"""
        if self.cap and self.cap.isOpened():
            return self.cap.read()
        return False, None
    
    def release(self):
        """Release video source"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def is_opened(self):
        """Check if video source is open"""
        return self.cap is not None and self.cap.isOpened()
