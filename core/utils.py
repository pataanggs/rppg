"""
Utility Functions for rPPG Heart Rate Monitoring Application

This module provides utility functions for the application, including image
conversion between OpenCV and PyQt6 formats, color transformations, and other
helper functions.
"""

import cv2
import numpy as np
from PyQt6 import QtGui, QtCore
import time


def convert_cv_qt(cv_img, target_width=None, target_height=None, keep_aspect_ratio=True):
    """
    Convert an OpenCV BGR image to a QPixmap for display in PyQt6.

    This function handles the conversion between OpenCV's BGR format and
    PyQt's RGB format, optionally resizing the image while maintaining
    aspect ratio if requested.

    Args:
        cv_img (np.ndarray): OpenCV image in BGR format
        target_width (int, optional): Desired width for the output QPixmap
        target_height (int, optional): Desired height for the output QPixmap
        keep_aspect_ratio (bool): Whether to maintain aspect ratio when resizing.
                                 Defaults to True.

    Returns:
        QtGui.QPixmap: Converted QPixmap ready to be displayed in a PyQt widget

    Raises:
        ValueError: If input image is None or not a numpy array
    """
    if cv_img is None or not isinstance(cv_img, (np.ndarray, )):
        raise ValueError("Invalid input image for conversion.")

    # Convert BGR to RGB
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w

    # Create QImage
    q_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
    pixmap = QtGui.QPixmap.fromImage(q_image)

    # Resize if target size provided
    if target_width and target_height:
        mode = QtCore.Qt.AspectRatioMode.KeepAspectRatio if keep_aspect_ratio else QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
        pixmap = pixmap.scaled(target_width, target_height, aspectRatioMode=mode)

    return pixmap


def extract_roi_mean(frame, roi_mask):
    """
    Extract the mean color values from a region of interest in an image.
    
    Args:
        frame (np.ndarray): Input video frame
        roi_mask (np.ndarray): Binary mask indicating the region of interest
    
    Returns:
        tuple: Mean (R, G, B) values from the region
        
    Raises:
        ValueError: If frame or mask dimensions don't match
    """
    if frame is None or roi_mask is None:
        return None
        
    if frame.shape[:2] != roi_mask.shape[:2]:
        raise ValueError("Frame and ROI mask dimensions must match")
    
    # Apply mask and compute average color
    masked = cv2.bitwise_and(frame, frame, mask=roi_mask)
    
    # Avoid division by zero
    mask_pixels = np.sum(roi_mask)
    if mask_pixels == 0:
        return None
        
    # Calculate mean color values
    r_mean = np.sum(masked[:, :, 2]) / mask_pixels
    g_mean = np.sum(masked[:, :, 1]) / mask_pixels
    b_mean = np.sum(masked[:, :, 0]) / mask_pixels
    
    return (r_mean, g_mean, b_mean)


class FPSCounter:
    """A class to calculate and track frames per second."""
    
    def __init__(self, avg_frames=30):
        """
        Initialize FPS counter.
        
        Args:
            avg_frames (int): Number of frames to average for FPS calculation
        """
        self.prev_time = time.time()
        self.frame_times = []
        self.avg_frames = avg_frames
        
    def update(self):
        """
        Update frame time information.
        Call this method on each new frame.
        """
        current_time = time.time()
        delta = current_time - self.prev_time
        self.frame_times.append(delta)
        
        # Keep only the most recent frames for averaging
        if len(self.frame_times) > self.avg_frames:
            self.frame_times.pop(0)
            
        self.prev_time = current_time
        
    def get_fps(self):
        """
        Calculate the current frames per second.
        
        Returns:
            float: Current FPS based on recent frame times
        """
        if not self.frame_times:
            return 0.0
            
        avg_time = sum(self.frame_times) / len(self.frame_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0.0
        return fps 