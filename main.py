#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the rPPG Heart Rate Monitoring Application.

This module initializes the application, handles camera selection and launches
the main monitoring window.
"""

import sys
import cv2
from PyQt6 import QtWidgets
from ui.main_window import MainWindow
from camera_selector import CameraSelector


def start_application():
    """
    Initialize and launch the application.
    
    This function:
    1. Sets up the Qt application environment
    2. Shows the camera selection dialog
    3. Verifies camera accessibility
    4. Launches the main application window
    
    Returns:
        int: Application exit code
    """
    try:
        # Initialize Qt application
        app = QtWidgets.QApplication(sys.argv)
        
        # Show camera selection dialog
        selected_camera = select_camera()
        if selected_camera is None:
            print("Camera selection was canceled.")
            return 0
            
        # Verify camera is accessible before launching main application
        if not verify_camera_accessibility(selected_camera):
            return 1
            
        # Launch main application window
        window = MainWindow(camera_index=selected_camera)
        window.show()
        
        # Start application event loop
        return app.exec()
        
    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {e}")
        QtWidgets.QMessageBox.critical(None, "Application Error", f"An error occurred: {e}")
        return 1


def select_camera():
    """
    Show camera selection dialog and get user's camera choice.
    
    Returns:
        int or None: Selected camera index or None if canceled
    """
    selector = CameraSelector()
    if selector.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return selector.get_selected_camera()
    return None


def verify_camera_accessibility(camera_index):
    """
    Check if the selected camera can be opened.
    
    Args:
        camera_index (int): Camera device index to check
        
    Returns:
        bool: True if camera is accessible, False otherwise
    """
    test_cap = cv2.VideoCapture(camera_index)
    if test_cap.isOpened():
        test_cap.release()
        return True
    else:
        # Show error message if camera cannot be accessed
        QtWidgets.QMessageBox.critical(
            None, 
            "Camera Error", 
            f"Could not open camera {camera_index}. Please check your connection and try again."
        )
        return False


if __name__ == "__main__":
    sys.exit(start_application())
