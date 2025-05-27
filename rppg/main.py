import sys
from PyQt6 import QtWidgets
from rppg.camera_selector import CameraSelector 
from rppg.ui.main_window import MainWindow

# --- BUNGKUS LOGIKA UTAMA KE DALAM FUNGSI main() ---
def main():
    """
    Initializes and runs the rPPG Heart Rate Monitor application.
    This function sets up the QApplication, handles camera selection,
    and displays the main window.
    """
    app = QtWidgets.QApplication(sys.argv)
    
    # Initialize CameraSelector dialog
    selector = CameraSelector()
    
    # Show the camera selection dialog and check if accepted
    if selector.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        selected_camera = selector.get_selected_camera()
        
        # Create and show the main application window
        window = MainWindow(camera_index=selected_camera)
        window.show()
        
        # Start the Qt event loop
        sys.exit(app.exec())
    else:
        # If camera selection is cancelled, exit the application
        print("Camera selection cancelled. Exiting application.")
        sys.exit(0)

if __name__ == "__main__":
    # This block ensures that main() is called when rppg/main.py is executed directly.
    # When imported by run.py, this block is skipped, and run.py calls main() directly.
    main()
