import os
import time
import cv2  # Impor cv2 untuk menggunakan cv2.flip
from PyQt6 import QtWidgets, QtCore, QtMultimedia, QtGui
from threads.video_thread import VideoThread, rppg_signal, time_data
from plot_canvas import MplCanvas
from signal_processing import bandpass_filter, calculate_heart_rate, calculate_respiration_rate
from utils import convert_cv_qt
from sound import setup_alarm_sound, toggle_alarm_sound
from ui.components import create_video_container, create_vital_cards, create_status_bar, create_exit_dialog
from ui.styles import STYLESHEET, VIDEO_CONTAINER_STYLE, STATUS_BAR_STYLE, BUTTON_STYLE

class MainWindow(QtWidgets.QMainWindow):
    """Main window for real-time rPPG and respiration monitoring."""
    FRAME_RATE = 30
    HR_LOW_THRESHOLD = 50
    HR_HIGH_THRESHOLD = 120

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.thread = None
        self.alarm_playing = False
        self.is_muted = False
        self.frame_times = []
        self.last_frame_time = time.time()
        self.blink_state = False
        self.is_mirrored = False

        self.setup_ui()
        self.setup_timers()
        setup_alarm_sound(self)

    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Real-Time rPPG & Respiration Monitoring')
        self.setMinimumSize(1200, 800)

        # Central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setStyleSheet(STYLESHEET)
        self.setCentralWidget(central_widget)

        # Create components
        self.video_container, self.video_label, self.rec_indicator, self.status_icon, \
        self.status_text, self.fps_label, self.face_status, self.landmark_btn, self.bbox_btn = create_video_container()
        self.canvas, self.hr_card, self.rr_card, self.hr_label, self.rr_label = create_vital_cards()
        self.status_bar, self.status_indicator, self.status_label, self.mute_button, \
        self.start_button, self.exit_button = create_status_bar()

        self.mirror_button = QtWidgets.QPushButton("Mirror Camera")
        self.mirror_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;  /* Biru untuk status inactive */
                color: white;
                border-radius: 5px;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1E88E5;  /* Biru sedikit lebih gelap saat hover */
            }
        """)
        self.mirror_button.setFixedSize(120, 30)
        self.mirror_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.mirror_button.clicked.connect(self.toggle_mirror)

        # Set maximum size for video label to control zoom and leave space for mirror button
        self.video_label.setMaximumSize(600, 400)
        self.video_container.setMaximumHeight(420)

        # Layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Top section (video and vitals)
        top_layout = QtWidgets.QHBoxLayout()

        # Video wrapper with mirror button
        video_wrapper = QtWidgets.QWidget()
        video_wrapper.setStyleSheet("border-radius: 10px; background: #fff; padding: 5px;")
        video_layout = QtWidgets.QVBoxLayout(video_wrapper)
        video_layout.addWidget(self.video_container)
        video_layout.addSpacing(10)
        video_layout.addWidget(self.mirror_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(video_wrapper, 1)

        # Vital signs section
        vital_wrapper = QtWidgets.QVBoxLayout()
        vital_wrapper.addWidget(self.hr_card)
        vital_wrapper.addWidget(self.rr_card)
        vital_wrapper.setSpacing(10)
        top_layout.addLayout(vital_wrapper, 1)

        # Plot section
        plot_wrapper = QtWidgets.QWidget()
        plot_wrapper.setStyleSheet("border-radius: 10px; background: #fff; padding: 5px;")
        plot_layout = QtWidgets.QVBoxLayout(plot_wrapper)
        plot_layout.addWidget(self.canvas)
        top_layout.addWidget(plot_wrapper, 2)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.status_bar)

        # Connect buttons
        self.start_button.clicked.connect(self.toggle_capture)
        self.exit_button.clicked.connect(self.close_app)
        self.mute_button.clicked.connect(lambda: toggle_alarm_sound(self))
        self.landmark_btn.clicked.connect(self.toggle_landmarks)
        self.bbox_btn.clicked.connect(self.toggle_bounding_box)

    def setup_timers(self):
        """Initialize timers for plot and indicator updates."""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.blink_timer = QtCore.QTimer()
        self.blink_timer.timeout.connect(self._blink_rec_indicator)

    def _blink_rec_indicator(self):
        """Blink the recording indicator."""
        self.blink_state = not self.blink_state
        self.rec_indicator.setStyleSheet(
            "background-color: #f44336; border-radius: 5px;" if self.blink_state else
            "background-color: transparent; border-radius: 5px;"
        )

    def toggle_capture(self):
        """Start or stop video capture."""
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.timer.stop()
            self.blink_timer.stop()
            self.start_button.setText("Start Monitoring")
            self.start_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
            self.status_icon.setStyleSheet("background-color: #9e9e9e; border-radius: 5px;")
            self.status_text.setText("Camera not active")
            self.status_indicator.setStyleSheet("background-color: #9e9e9e; border-radius: 4px;")
            self.status_label.setText("Status: Ready")
            self.status_label.setStyleSheet("color: #555; font-size: 13px;")
        else:
            self.thread = VideoThread(camera_index=self.camera_index)
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.start()
            self.timer.start(1000 // self.FRAME_RATE)
            self.blink_timer.start(500)
            if self.thread.show_landmarks:
                self.landmark_btn.setStyleSheet(BUTTON_STYLE["landmark_active"])
            if self.thread.show_bounding_box:
                self.bbox_btn.setStyleSheet(BUTTON_STYLE["bbox_active"])
            self.start_button.setText("Stop Monitoring")
            self.start_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))
            self.status_icon.setStyleSheet("background-color: #4CAF50; border-radius: 5px;")
            self.status_text.setText("Camera active - Monitoring")
            self.status_indicator.setStyleSheet("background-color: #4CAF50; border-radius: 4px;")
            self.status_label.setText("Status: Monitoring active")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 13px; font-weight: bold;")

    @QtCore.pyqtSlot()
    def update_plot(self):
        """Update rPPG and respiration plots."""
        if len(rppg_signal) <= 30:
            return

        filtered_rppg = bandpass_filter(rppg_signal, 0.7, 4, self.FRAME_RATE)
        filtered_resp = bandpass_filter(rppg_signal, 0.1, 0.5, self.FRAME_RATE)

        hr = calculate_heart_rate(filtered_rppg, self.FRAME_RATE)
        rr = calculate_respiration_rate(filtered_resp, self.FRAME_RATE)

        # Update vital signs
        if self.HR_LOW_THRESHOLD <= hr <= self.HR_HIGH_THRESHOLD:
            self.hr_label.setStyleSheet("color: #4CAF50; font-size: 28px; font-weight: bold;")
            if self.alarm_playing:
                self.alarm_sound.stop()
                self.alarm_playing = False
            self.status_indicator.setStyleSheet("background-color: #4CAF50; border-radius: 4px;")
            self.status_label.setText("Status: Monitoring active")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 13px; font-weight: bold;")
        else:
            self.hr_label.setStyleSheet("color: #f44336; font-size: 28px; font-weight: bold;")
            if not self.is_muted and not self.alarm_playing and os.path.exists(self.alarm_sound.source().toLocalFile()):
                self.alarm_sound.play()
                self.alarm_playing = True
            warning_text = f"WARNING: Heart rate abnormal ({hr:.1f} BPM)"
            if self.is_muted:
                warning_text += " (Alarm Muted)"
            self.status_indicator.setStyleSheet("background-color: #f44336; border-radius: 4px;")
            self.status_label.setText(warning_text)
            self.status_label.setStyleSheet("color: #f44336; font-size: 13px; font-weight: bold;")

        self.hr_label.setText(f"{hr:.1f} BPM")
        self.rr_label.setText(f"{rr:.1f} BPM")

        # Update plots
        min_len = min(len(time_data), len(filtered_rppg))
        time_array = list(time_data)[-min_len:]
        rppg_array = filtered_rppg[-min_len:]
        resp_array = filtered_resp[-min_len:]

        self.canvas.line_rppg.set_data(time_array, rppg_array)
        self.canvas.line_resp.set_data(time_array, resp_array)
        self.canvas.ax1.relim()
        self.canvas.ax1.autoscale_view()
        self.canvas.ax2.relim()
        self.canvas.ax2.autoscale_view()
        self.canvas.draw()

    @QtCore.pyqtSlot(object, bool)
    def update_image(self, cv_img, face_detected):
        """Update video display and FPS."""
        current_time = time.time()
        self.frame_times.append(current_time - self.last_frame_time)
        self.last_frame_time = current_time

        if len(self.frame_times) > 30:
            self.frame_times.pop(0)

        if self.frame_times:
            fps = 1.0 / (sum(self.frame_times) / len(self.frame_times))
            self.fps_label.setText(f"{fps:.1f} FPS")

        self.face_status.setText("Face Detected" if face_detected else "No Face")
        self.face_status.setStyleSheet(
            "color: #4CAF50; font-size: 12px; font-weight: bold;" if face_detected else
            "color: #ff6b6b; font-size: 12px; font-weight: bold;"
        )

        # Log frame size for debugging
        if cv_img is not None:
            print(f"Frame received: shape={cv_img.shape}")
        else:
            print("Frame is None")

        # Mirror image if enabled
        if self.is_mirrored and cv_img is not None:
            cv_img = cv2.flip(cv_img, 1)

        # Convert and display the frame
        if cv_img is not None:
            try:
                # Ensure video_label has a valid size
                if self.video_label.width() > 0 and self.video_label.height() > 0:
                    qt_img = convert_cv_qt(cv_img, self.video_label.width(), self.video_label.height())
                    if qt_img.isNull():
                        print("QPixmap is null after conversion")
                    else:
                        self.video_label.setPixmap(qt_img)
                        print("Frame displayed successfully")
                else:
                    print(f"Invalid video_label size: width={self.video_label.width()}, height={self.video_label.height()}")
            except Exception as e:
                print(f"Error displaying frame: {str(e)}")
        else:
            print("Cannot display frame: cv_img is None")

    def close_app(self):
        """Close the application."""
        self.close()

    def closeEvent(self, event):
        """Handle window close event with custom dialog."""
        dialog = create_exit_dialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if self.thread and self.thread.isRunning():
                self.thread.stop()
                self.alarm_sound.stop()
            event.accept()
        else:
            event.ignore()

    def toggle_landmarks(self):
        """Toggle facial landmarks display."""
        if self.thread and self.thread.isRunning():
            self.thread.toggle_landmarks()
            self.landmark_btn.setStyleSheet(
                BUTTON_STYLE["landmark_active"] if self.thread.show_landmarks else
                BUTTON_STYLE["landmark_inactive"]
            )

    def toggle_bounding_box(self):
        """Toggle face bounding box display."""
        if self.thread and self.thread.isRunning():
            self.thread.toggle_bounding_box()
            self.bbox_btn.setStyleSheet(
                BUTTON_STYLE["bbox_active"] if self.thread.show_bounding_box else
                BUTTON_STYLE["bbox_inactive"]
            )

    def toggle_mirror(self):
        """Toggle mirror effect for camera feed."""
        self.is_mirrored = not self.is_mirrored
        self.mirror_button.setStyleSheet(
            """
            QPushButton {
                background-color: #42A5F5;  /* Biru lebih terang untuk status active */
                color: white;
                border-radius: 5px;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            """ if self.is_mirrored else
            """
            QPushButton {
                background-color: #2196F3;  /* Biru untuk status inactive */
                color: white;
                border-radius: 5px;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            """
        )
        self.mirror_button.setText("Mirror Camera")  # Pastikan teks tetap sama