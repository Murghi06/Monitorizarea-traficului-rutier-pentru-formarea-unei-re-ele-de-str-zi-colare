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
    
    def open(self):
        """Open video source"""
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
            self.cap = cv2.VideoCapture(self.source)
        
        return self.cap.isOpened() if self.cap else False
    
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
