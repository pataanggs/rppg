import sys
from PyQt6 import QtWidgets
from ui.main_window import MainWindow
from threads.video_thread import VideoThread
import cv2


class CameraSelector(QtWidgets.QDialog):
    """Dialog to allow user to select a camera from available options."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Camera")
        self.setGeometry(300, 300, 300, 100)
        self._setup_ui()

    def _setup_ui(self):
        """Sets up UI components of the CameraSelector."""
        layout = QtWidgets.QVBoxLayout()

        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.addItem("Default Camera", 0)
        self._populate_camera_list()

        layout.addWidget(QtWidgets.QLabel("Select camera:"))
        layout.addWidget(self.camera_combo)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | 
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def _populate_camera_list(self):
        """Adds available camera options to the dropdown."""
        for i in range(1, 5):  # Check for a few cameras (expandable)
            self.camera_combo.addItem(f"Camera {i}", i)

    def get_selected_camera(self):
        """Returns the selected camera index."""
        return self.camera_combo.currentData()


def start_application():
    """Main application entry point."""
    try:
        app = QtWidgets.QApplication(sys.argv)
        selected_camera = get_selected_camera_from_user()
        if selected_camera is not None:
            # Test camera availability before creating the main window
            test_cap = cv2.VideoCapture(selected_camera)
            if test_cap.isOpened():
                test_cap.release()
                window = MainWindow(camera_index=selected_camera)
                window.show()
                sys.exit(app.exec())
            else:
                QtWidgets.QMessageBox.critical(
                    None, 
                    "Camera Error", 
                    f"Could not open camera {selected_camera}. Please check your connection and try again."
                )
                sys.exit(1)
        else:
            print("Camera selection was canceled.")
            sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        QtWidgets.QMessageBox.critical(None, "Application Error", f"An error occurred: {e}")
        sys.exit(1)


def get_selected_camera_from_user():
    """Handles the camera selection dialog and returns the selected camera."""
    selector = CameraSelector()
    if selector.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return selector.get_selected_camera()
    return None


if __name__ == "__main__":
    start_application()
