import cv2
from PyQt6 import QtWidgets, QtCore, QtGui

class CameraSelector(QtWidgets.QDialog):
    """Dialog for selecting a camera device with real-time preview."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Camera Device")
        self.setFixedSize(600, 550)  # Sedikit menambah tinggi jendela untuk ruang lebih

        # Initialize camera variables
        self.current_camera_index = None
        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_preview)

        # Main layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)  # Mengatur jarak antar elemen

        # Title
        title = QtWidgets.QLabel("Select Your Camera")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instruction
        instruction = QtWidgets.QLabel("Choose a camera device from the list below")
        instruction.setStyleSheet("font-size: 14px; color: #666;")
        instruction.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)

        # Camera preview
        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("border: 2px solid #ccc; border-radius: 8px; background-color: #000;")
        self.camera_label.setFixedSize(400, 200)
        layout.addWidget(self.camera_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Spacer untuk jarak tambahan setelah preview
        layout.addSpacing(15)

        # Camera selection dropdown
        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #ccc;
                padding: 5px;
            }
        """)
        self.camera_combo.setFixedWidth(350)  # Memperlebar dropdown
        self.camera_combo.currentIndexChanged.connect(self.switch_camera)
        layout.addWidget(self.camera_combo, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Spacer untuk jarak tambahan setelah dropdown
        layout.addSpacing(15)

        # Select button
        self.select_button = QtWidgets.QPushButton("Select This Camera")
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.select_button.setFixedWidth(250)  # Memperlebar tombol
        self.select_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.select_button.clicked.connect(self.accept)
        layout.addWidget(self.select_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Spacer untuk jarak tambahan setelah tombol
        layout.addSpacing(15)

        # Status
        self.status_label = QtWidgets.QLabel("Found 0 camera(s)")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.populate_cameras()

    def populate_cameras(self):
        """Populate the camera dropdown with available devices."""
        self.camera_combo.clear()
        index = 0
        while True:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                break
            cap.release()
            device_name = f"Camera {index}"
            self.camera_combo.addItem(device_name, index)
            index += 1
        self.status_label.setText(f"Found {index} camera(s)")
        if index > 0:
            self.switch_camera()

    def switch_camera(self):
        """Switch to the selected camera and start preview."""
        # Stop previous camera if running
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Get the selected camera index
        index = self.camera_combo.currentData()
        if index is None:
            self.camera_label.setText("No camera selected")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            return

        # Open the new camera
        self.current_camera_index = index
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self.timer.start(33)  # Update every ~33ms (30 FPS)
        else:
            self.camera_label.setText("Camera not available")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.cap = None

    def update_preview(self):
        """Update the preview for the selected camera in real-time."""
        if self.cap is None or not self.cap.isOpened():
            self.camera_label.setText("Camera not available")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.timer.stop()
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            image = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(self.camera_label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.camera_label.setPixmap(scaled_pixmap)
        else:
            self.camera_label.setText("Unable to load camera preview")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.timer.stop()

    def get_selected_camera(self):
        """Return the index of the selected camera."""
        return self.camera_combo.currentData()

    def closeEvent(self, event):
        """Ensure the camera is released when the dialog is closed."""
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        event.accept() 