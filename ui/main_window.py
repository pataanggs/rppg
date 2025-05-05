import time
from PyQt6 import QtWidgets, QtCore, QtGui
import cv2
from threads.video_thread import VideoThread
from sound import setup_alarm_sound, toggle_alarm_sound
from ui.components import HeartRateDisplay
import numpy as np
from ui.settings_dialog import SettingsDialog
from ui.styles import Colors, Fonts, StyleSheets, Layout, apply_stylesheet, get_heart_rate_color

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.initUI()
        self.setup_video()
        self.is_muted = False
        setup_alarm_sound(self)

    def initUI(self):
        self.setWindowTitle("rPPG Heart Rate Monitor")
        self.setGeometry(100, 100, 1000, 700)
        
        # Apply main window style
        apply_stylesheet(self, StyleSheets.get_main_window_style)
        
        # Main widget and layout
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()  # Change to horizontal layout
        
        # Left panel for video
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setContentsMargins(Layout.MARGIN, Layout.MARGIN, Layout.MARGIN, Layout.MARGIN)
        
        # Create video display with fixed aspect ratio
        self.video_label = QtWidgets.QLabel()
        self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(Layout.VIDEO_MIN_WIDTH, Layout.VIDEO_MIN_HEIGHT)
        self.video_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        
        # Face detection status indicator
        self.face_status = QtWidgets.QLabel("No face detected")
        apply_stylesheet(self.face_status, StyleSheets.get_status_label_style("warning"))
        
        left_panel.addWidget(self.video_label, 1)
        left_panel.addWidget(self.face_status)
        
        # Right panel for stats and controls
        right_panel = QtWidgets.QVBoxLayout()
        right_panel.setContentsMargins(Layout.MARGIN, Layout.MARGIN, Layout.MARGIN, Layout.MARGIN)
        
        # App title and description
        title_label = QtWidgets.QLabel("rPPG Heart Rate Monitor")
        apply_stylesheet(title_label, StyleSheets.get_title_label_style)
        description = QtWidgets.QLabel(
            "Remote photoplethysmography (rPPG) measures heart rate\n"
            "by analyzing subtle color changes in facial skin."
        )
        description.setWordWrap(True)
        
        # Create heart rate display
        self.hr_display = HeartRateDisplay()
        self.hr_display.set_color(Colors.HR_NORMAL)
        
        # Create status label with more info
        self.status_label = QtWidgets.QLabel("Waiting for face detection...")
        apply_stylesheet(self.status_label, StyleSheets.STATUS_LABEL)
        
        # Add record button 
        self.record_button = QtWidgets.QPushButton("Start Recording")
        apply_stylesheet(self.record_button, StyleSheets.get_button_style)
        self.record_button.clicked.connect(self.toggle_recording)
        self.is_recording = False
        
        # Add export button
        self.export_button = QtWidgets.QPushButton("Export Data")
        apply_stylesheet(self.export_button, StyleSheets.get_button_style)
        self.export_button.clicked.connect(self.export_data)
        
        # Add items to right panel
        right_panel.addWidget(title_label)
        right_panel.addWidget(description)
        right_panel.addWidget(self.hr_display)
        right_panel.addWidget(self.status_label)
        
        # Button layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.export_button)
        right_panel.addLayout(button_layout)
        
        # Add stretcher to push everything up
        right_panel.addStretch()
        
        # Add panels to main layout
        main_layout.addLayout(left_panel, 3)  # Video takes 3/5 of width
        main_layout.addLayout(right_panel, 2)  # Controls take 2/5 of width
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create toolbar and actions
        self._setup_toolbar()

    def setup_video(self):
        self.video_thread = VideoThread(camera_index=self.camera_index)
        self.video_thread.frame_update.connect(self.update_frame)
        self.video_thread.hr_update.connect(self.update_heart_rate)
        self.video_thread.face_detected.connect(self.update_face_status)
        self.video_thread.start()
    
    def update_frame(self, frame):
        qt_img = self.convert_cv_to_qt(frame)
        self.video_label.setPixmap(qt_img)
    
    def update_heart_rate(self, hr):
        """Update displayed heart rate and handle alerts."""
        # Update the heart rate display with the new value
        self.hr_display.set_heart_rate(hr)
        
        # Set the color based on the heart rate value
        hr_color = get_heart_rate_color(hr)
        self.hr_display.set_color(hr_color)
        
        # Record data if recording is enabled
        if hasattr(self, 'is_recording') and self.is_recording:
            if not hasattr(self, 'recorded_data'):
                self.recorded_data = []
            self.recorded_data.append((time.time(), hr))
        
        # Check if heart rate is outside normal range for alerts
        if hr < 50 or hr > 100:
            status_text = f"Warning: Abnormal heart rate ({hr:.1f} BPM)"
            if hr < 50:
                alert_type = "bradycardia"
            else:
                alert_type = "tachycardia"
                
            self.status_label.setText(f"{status_text} - Possible {alert_type}")
            apply_stylesheet(self.status_label, StyleSheets.get_status_label_style("danger"))
            
            # Play alarm if not muted
            if not self.is_muted and hasattr(self, 'alarm_sound'):
                self.alarm_sound.play()
                
        elif hr < 60 or hr > 90:
            self.status_label.setText(f"Caution: Heart rate ({hr:.1f} BPM) outside ideal range")
            apply_stylesheet(self.status_label, StyleSheets.get_status_label_style("warning"))
            
            # Stop alarm if playing
            if hasattr(self, 'alarm_sound') and self.alarm_sound.alarm_playing:
                self.alarm_sound.stop()
                
        else:
            self.status_label.setText(f"Normal heart rate: {hr:.1f} BPM")
            apply_stylesheet(self.status_label, StyleSheets.get_status_label_style("normal"))
            
            # Stop alarm if playing
            if hasattr(self, 'alarm_sound') and self.alarm_sound.alarm_playing:
                self.alarm_sound.stop()
    
    def convert_cv_to_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        return QtGui.QPixmap.fromImage(qt_image)
    
    def closeEvent(self, event):
        self.video_thread.stop()

    def _setup_toolbar(self):
        """Set up the application toolbar."""
        toolbar = QtWidgets.QToolBar()
        self.addToolBar(toolbar)
        
        # Mute button
        self.mute_button = QtWidgets.QToolButton()
        sound_icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_MediaVolume)
        self.mute_button.setIcon(sound_icon)
        self.mute_button.setToolTip("Toggle alarm sound (currently ON)")
        self.mute_button.clicked.connect(lambda: toggle_alarm_sound(self))
        toolbar.addWidget(self.mute_button)
        
        # Settings button
        settings_button = QtWidgets.QToolButton()
        settings_icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView)
        settings_button.setIcon(settings_icon)
        settings_button.setToolTip("Settings")
        settings_button.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_button)

    def toggle_recording(self):
        """Toggle recording of heart rate data."""
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.setText("Stop Recording")
            self.recorded_data = []
            self.record_start_time = time.time()
            self.status_label.setText("Recording heart rate data...")
        else:
            self.record_button.setText("Start Recording")
            self.status_label.setText(f"Recorded {len(self.recorded_data)} data points.")

    def export_data(self):
        """Export recorded heart rate data to CSV."""
        if not hasattr(self, 'recorded_data') or not self.recorded_data:
            QtWidgets.QMessageBox.warning(self, "Export Error", "No data available to export.")
            return
            
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Heart Rate Data", "", "CSV Files (*.csv)")
            
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write("timestamp,heart_rate\n")
                    for timestamp, hr in self.recorded_data:
                        file.write(f"{timestamp},{hr}\n")
                QtWidgets.QMessageBox.information(self, "Export Successful", 
                                                f"Data exported to {file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")

    def show_settings(self):
        """Show settings dialog and apply settings if accepted."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Apply settings to the video thread
            settings = {
                'window_size': dialog.window_size.value(),
                'min_hr': dialog.min_normal.value(),
                'max_hr': dialog.max_normal.value(),
                'show_face_rect': dialog.show_face_rect.isChecked(),
                'show_bpm_on_frame': dialog.show_bpm.isChecked()
            }
            self.video_thread.set_settings(settings)
            QtWidgets.QMessageBox.information(self, "Settings Applied", 
                                             "Settings have been applied successfully.")

    def update_face_status(self, face_detected):
        """Update the face detection status indicator."""
        if face_detected:
            self.face_status.setText("Face Detected")
            apply_stylesheet(self.face_status, StyleSheets.get_status_label_style("normal"))
        else:
            self.face_status.setText("No Face Detected")
            apply_stylesheet(self.face_status, StyleSheets.get_status_label_style("warning"))