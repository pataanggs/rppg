import time
from PyQt6 import QtWidgets, QtCore, QtGui
import cv2
from threads.video_thread import VideoThread
from sound import setup_alarm_sound, toggle_alarm_sound
from ui.components import HeartRateDisplay, HeartRateGraph, ProgressCircleWidget
import numpy as np
from ui.settings_dialog import SettingsDialog
from ui.styles import Colors, Fonts, StyleSheets, Layout, apply_stylesheet, get_heart_rate_color
import csv
import os
from datetime import datetime

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        # Setup data storage
        self.hr_data = []
        self.hr_timestamps = []
        self.max_data_points = 300  # Store last 5 minutes at 1Hz
        self.initUI()
        self.setup_video()
        self.is_muted = False
        setup_alarm_sound(self)

    def initUI(self):
        self.setWindowTitle("rPPG Heart Rate Monitor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application icon
        self.setWindowIcon(self._create_heart_icon())
        
        # Apply modern styling with a dark theme for better contrast
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f5c2e7;
            }
            QPushButton:pressed {
                background-color: #cba6f7;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QToolBar {
                background-color: #181825;
                border-bottom: 1px solid #313244;
                spacing: 12px;
                padding: 8px 6px;
            }
            QToolButton {
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
            QToolButton:hover {
                background-color: #313244;
            }
            QToolButton:pressed {
                background-color: #45475a;
            }
            QStatusBar {
                background-color: #181825;
                color: #a6adc8;
                border-top: 1px solid #313244;
                font-size: 12px;
                padding: 4px;
            }
            QComboBox {
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px 14px;
                background-color: #313244;
                color: #cdd6f4;
                min-height: 24px;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: url(ui/assets/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox:hover {
                border-color: #45475a;
                background-color: #45475a;
            }
        """)
        
        # Main widget and layout
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Top section for video and heart rate
        top_section = QtWidgets.QHBoxLayout()
        top_section.setSpacing(30)
        
        # Left panel for video
        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setSpacing(20)
        
        # Create video display with premium design
        self.video_container = QtWidgets.QWidget()
        self.video_container.setObjectName("videoContainer")
        self.video_container.setStyleSheet("""
            #videoContainer {
                background-color: #181825;
                border-radius: 16px;
                border: 1px solid #313244;
            }
        """)
        
        video_layout = QtWidgets.QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(3, 3, 3, 3)
        
        self.video_label = QtWidgets.QLabel()
        self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(Layout.VIDEO_MIN_WIDTH, Layout.VIDEO_MIN_HEIGHT)
        self.video_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, 
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.video_label.setStyleSheet("border-radius: 14px;")
        
        # Add placeholder image or text
        placeholder = QtGui.QPixmap(480, 360)
        placeholder.fill(QtGui.QColor("#1a1b26"))
        placeholder_painter = QtGui.QPainter(placeholder)
        placeholder_painter.setPen(QtGui.QColor("#6c7086"))
        placeholder_painter.setFont(QtGui.QFont("Segoe UI", 14))
        placeholder_painter.drawText(placeholder.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Connecting to camera...")
        placeholder_painter.end()
        self.video_label.setPixmap(placeholder)
        
        video_layout.addWidget(self.video_label)
        
        # Face detection status with modern design
        face_status_container = QtWidgets.QWidget()
        face_status_container.setStyleSheet("""
            background-color: #181825;
            border-radius: 10px;
            border: 1px solid #313244;
        """)
        face_status_layout = QtWidgets.QHBoxLayout(face_status_container)
        face_status_layout.setContentsMargins(16, 12, 16, 12)
        face_status_layout.setSpacing(14)
        
        self.face_status_icon = QtWidgets.QLabel()
        self.face_status_icon.setFixedSize(22, 22)
        self.set_face_status_icon(False)
        
        self.face_status = QtWidgets.QLabel("No face detected")
        self.face_status.setStyleSheet("""
            color: #fab387;
            font-weight: bold;
            font-size: 14px;
        """)
        
        status_separator = QtWidgets.QFrame()
        status_separator.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        status_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        status_separator.setStyleSheet("color: #313244;")
        
        # Add quality label
        quality_label = QtWidgets.QLabel("Signal Quality:")
        quality_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        
        # Enhanced signal quality indicator
        self.signal_quality = ProgressCircleWidget()
        self.signal_quality.setValue(0)
        
        face_status_layout.addWidget(self.face_status_icon)
        face_status_layout.addWidget(self.face_status)
        face_status_layout.addStretch()
        face_status_layout.addWidget(status_separator)
        face_status_layout.addWidget(quality_label)
        face_status_layout.addWidget(self.signal_quality)
        
        # Add video and status to left panel
        left_panel.addWidget(self.video_container, 1)
        left_panel.addWidget(face_status_container)
        
        # Right panel with enhanced card design
        right_panel_container = QtWidgets.QWidget()
        right_panel_container.setObjectName("rightPanel")
        right_panel_container.setStyleSheet("""
            #rightPanel {
                background-color: #181825;
                border-radius: 16px;
                border: 1px solid #313244;
            }
        """)
        
        right_panel = QtWidgets.QVBoxLayout(right_panel_container)
        right_panel.setContentsMargins(30, 30, 30, 30)
        right_panel.setSpacing(25)
        
        # App title with modern branding
        header_layout = QtWidgets.QHBoxLayout()
        
        # Create heart logo
        heart_logo_container = QtWidgets.QWidget()
        heart_logo_container.setFixedSize(44, 44)
        heart_logo_layout = QtWidgets.QVBoxLayout(heart_logo_container)
        heart_logo_layout.setContentsMargins(0, 0, 0, 0)
        
        self.heart_logo = QtWidgets.QLabel()
        heart_pixmap = self._create_heart_pixmap(36, "#f38ba8")
        self.heart_logo.setPixmap(heart_pixmap)
        self.heart_logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        heart_logo_layout.addWidget(self.heart_logo)
        
        title_label = QtWidgets.QLabel("rPPG Heart Rate Monitor")
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #f5c2e7;
        """)
        
        header_layout.addWidget(heart_logo_container)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Enhanced description with better typography
        description = QtWidgets.QLabel(
            "Remote photoplethysmography (rPPG) analyzes subtle color changes in facial skin to measure heart rate non-invasively using only a standard camera."
        )
        description.setStyleSheet("""
            color: #a6adc8;
            font-size: 14px;
            line-height: 1.5;
        """)
        description.setWordWrap(True)
        
        # Create heart rate display with premium design
        self.hr_display = HeartRateDisplay()
        self.hr_display.set_color(Colors.HR_NORMAL)
        
        # Enhanced status container
        status_container = QtWidgets.QWidget()
        status_container.setStyleSheet("""
            background-color: #313244;
            border-radius: 10px;
            padding: 4px;
        """)
        status_layout = QtWidgets.QHBoxLayout(status_container)
        status_layout.setContentsMargins(16, 14, 16, 14)
        
        status_icon = QtWidgets.QLabel()
        info_pixmap = self._create_icon_pixmap("info", 22, "#89b4fa")
        status_icon.setPixmap(info_pixmap)
        
        self.status_label = QtWidgets.QLabel("Waiting for face detection...")
        self.status_label.setStyleSheet("""
            color: #cdd6f4;
            font-size: 14px;
            font-weight: 500;
        """)
        
        status_layout.addWidget(status_icon)
        status_layout.addWidget(self.status_label, 1)
        
        # Better spacing for buttons
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(20)
        
        self.record_button = QtWidgets.QPushButton(" Start Recording")
        self.record_button.setIcon(self._create_icon_from_name("media-record"))
        self.record_button.clicked.connect(self.toggle_recording)
        self.is_recording = False
        
        self.export_button = QtWidgets.QPushButton(" Export Data")
        self.export_button.setIcon(self._create_icon_from_name("document-save"))
        self.export_button.clicked.connect(self.export_data)
        
        button_layout.addWidget(self.record_button)
        button_layout.addWidget(self.export_button)
        
        # Add stats panel
        stats_container = QtWidgets.QWidget()
        stats_container.setStyleSheet("""
            background-color: #313244;
            border-radius: 10px;
        """)
        stats_layout = QtWidgets.QHBoxLayout(stats_container)
        
        # Session duration
        session_stats = QtWidgets.QVBoxLayout()
        session_label = QtWidgets.QLabel("Session")
        session_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.session_time = QtWidgets.QLabel("00:00")
        self.session_time.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        session_stats.addWidget(session_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        session_stats.addWidget(self.session_time, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Data points collected
        datapoints_stats = QtWidgets.QVBoxLayout()
        datapoints_label = QtWidgets.QLabel("Data Points")
        datapoints_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.datapoints_count = QtWidgets.QLabel("0")
        self.datapoints_count.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        datapoints_stats.addWidget(datapoints_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        datapoints_stats.addWidget(self.datapoints_count, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Average HR
        avg_hr_stats = QtWidgets.QVBoxLayout()
        avg_hr_label = QtWidgets.QLabel("Avg HR")
        avg_hr_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.avg_hr = QtWidgets.QLabel("--")
        self.avg_hr.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        avg_hr_stats.addWidget(avg_hr_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        avg_hr_stats.addWidget(self.avg_hr, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        stats_layout.addLayout(session_stats)
        stats_layout.addLayout(datapoints_stats)
        stats_layout.addLayout(avg_hr_stats)
        
        # Add items to right panel
        right_panel.addLayout(header_layout)
        right_panel.addWidget(description)
        right_panel.addWidget(self.hr_display)
        right_panel.addWidget(status_container)
        right_panel.addWidget(button_container)
        right_panel.addWidget(stats_container)
        right_panel.addStretch()
        
        # Add panels to top section
        top_section.addLayout(left_panel, 3)  # Video takes 3/5 of width
        top_section.addWidget(right_panel_container, 2)  # Controls take 2/5 of width
        
        # Enhanced graph section
        graph_container = QtWidgets.QWidget()
        graph_container.setObjectName("graphContainer")
        graph_container.setStyleSheet("""
            #graphContainer {
                background-color: #181825;
                border-radius: 16px;
                border: 1px solid #313244;
            }
        """)
        
        graph_section = QtWidgets.QVBoxLayout(graph_container)
        graph_section.setContentsMargins(24, 24, 24, 24)
        graph_section.setSpacing(20)
        
        # Enhanced header for the graph
        graph_header = QtWidgets.QHBoxLayout()
        
        chart_icon = QtWidgets.QLabel()
        chart_pixmap = self._create_icon_pixmap("chart", 22, "#f38ba8")
        chart_icon.setPixmap(chart_pixmap)
        
        graph_title = QtWidgets.QLabel("Heart Rate History")
        graph_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #f5c2e7;
        """)
        
        graph_header.addWidget(chart_icon)
        graph_header.addWidget(graph_title)
        graph_header.addStretch()
        
        # Enhanced time range selector with better styling
        time_range_label = QtWidgets.QLabel("Time Range:")
        time_range_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        
        self.time_range_combo = QtWidgets.QComboBox()
        self.time_range_combo.addItem("Last 1 minute", 60)
        self.time_range_combo.addItem("Last 3 minutes", 180)
        self.time_range_combo.addItem("Last 5 minutes", 300)
        self.time_range_combo.setCurrentIndex(1)  # Default 3 minutes
        self.time_range_combo.setFixedWidth(150)
        self.time_range_combo.setStyleSheet("""
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 6px 8px;
            font-size: 13px;
            color: #cdd6f4;
        """)
        self.time_range_combo.currentIndexChanged.connect(self.update_time_range)
        
        graph_header.addWidget(time_range_label)
        graph_header.addWidget(self.time_range_combo)
        
        # Add controls to manipulate the graph
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Add zoom controls
        zoom_out_btn = QtWidgets.QToolButton()
        zoom_out_btn.setIcon(self._create_icon_from_name("zoom-out"))
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.setStyleSheet("""
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 6px;
        """)
        
        zoom_in_btn = QtWidgets.QToolButton()
        zoom_in_btn.setIcon(self._create_icon_from_name("zoom-in"))
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.setStyleSheet("""
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 6px;
        """)
        
        controls_layout.addWidget(zoom_out_btn)
        controls_layout.addWidget(zoom_in_btn)
        
        graph_header.addLayout(controls_layout)
        
        # Create heart rate graph widget with better styling
        self.hr_graph = HeartRateGraph()
        self.hr_graph.setMinimumHeight(220)
        
        graph_section.addLayout(graph_header)
        graph_section.addWidget(self.hr_graph)
        
        # Add both sections to main layout
        main_layout.addLayout(top_section, 3)  # Top section takes 3/4 of height
        main_layout.addWidget(graph_container, 1)  # Graph takes 1/4 of height
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create enhanced toolbar
        self._setup_toolbar()
        
        # Add status bar with more information
        self.statusBar().showMessage("Ready - Waiting for camera initialization")
        
        # Add session timer
        self.session_timer = QtCore.QTimer()
        self.session_timer.timeout.connect(self._update_session_time)
        self.session_start_time = time.time()
        self.session_timer.start(1000)  # Update every second
        
        # Add enhanced shadow effect to containers
        for widget in [self.video_container, right_panel_container, graph_container, face_status_container]:
            shadow = QtWidgets.QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setColor(QtGui.QColor(0, 0, 0, 45))
            shadow.setOffset(0, 4)
            widget.setGraphicsEffect(shadow)

    def setup_video(self):
        self.video_thread = VideoThread(camera_index=self.camera_index)
        self.video_thread.frame_update.connect(self.update_frame)
        self.video_thread.hr_update.connect(self.update_heart_rate)
        self.video_thread.face_detected.connect(self.update_face_status)
        self.video_thread.signal_quality_update.connect(self.update_signal_quality)
        self.video_thread.start()
    
    def update_frame(self, frame):
        qt_img = self.convert_cv_to_qt(frame)
        self.video_label.setPixmap(qt_img)
        
    def update_heart_rate(self, hr_data):
        """Update heart rate value and graph."""
        hr, is_valid = hr_data
        
        # Store the data but don't update widgets directly
        self._current_hr = hr
        self._hr_valid = is_valid
        
        # Schedule update for the next event loop cycle to break potential recursion
        QtCore.QTimer.singleShot(0, self._do_heart_rate_update)

    def _do_heart_rate_update(self):
        """Actually perform the heart rate update after deferring to break recursion."""
        if not hasattr(self, '_current_hr'):
            return

        hr = self._current_hr
        is_valid = self._hr_valid
        
        # Update the heart rate display
        if is_valid:
            self.hr_display.set_heart_rate(hr)
            
            # Set color based on heart rate value
            hr_color = get_heart_rate_color(hr)
            self.hr_display.set_color(hr_color)
            
            # Update status message based on heart rate
            if hr < 60:
                status_text = f"Low heart rate detected: {hr:.1f} BPM"
                self.status_label.setStyleSheet("color: #fab387; font-weight: bold;")
            elif hr > 100:
                status_text = f"High heart rate detected: {hr:.1f} BPM"
                self.status_label.setStyleSheet("color: #f38ba8; font-weight: bold;")
            else:
                status_text = f"Normal heart rate: {hr:.1f} BPM"
                self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
                
            self.status_label.setText(status_text)
            
            # Record data point if we're recording
            if hasattr(self, 'is_recording') and self.is_recording:
                current_time = time.time()
                self.recorded_data.append((current_time, hr))
                
            # Add data to history
            current_time = time.time()
            self.hr_data.append(hr)
            self.hr_timestamps.append(current_time)
            
            # Limit the data points stored
            if len(self.hr_data) > self.max_data_points:
                self.hr_data.pop(0)
                self.hr_timestamps.pop(0)
                
            # Update the graph if we have enough data points
            if len(self.hr_data) > 1:
                self.hr_graph.update_graph(self.hr_data, self.hr_timestamps)
        else:
            self.status_label.setText("Calculating heart rate...")
            self.status_label.setStyleSheet("color: #cdd6f4;")
    
    def convert_cv_to_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        
        # Create rounded pixmap
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        return pixmap
    
    def closeEvent(self, event):
        self.video_thread.stop()
        # Prompt to save data if recording
        if hasattr(self, 'is_recording') and self.is_recording and hasattr(self, 'recorded_data') and len(self.recorded_data) > 0:
            reply = QtWidgets.QMessageBox.question(
                self, 'Save Data', 
                'Would you like to save the recorded heart rate data before exiting?',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.export_data()

    def _setup_toolbar(self):
        """Set up the application toolbar with modern icons."""
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 12px;
                padding: 6px;
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
            QToolButton {
                border-radius: 6px;
                padding: 6px;
            }
            QToolButton:hover {
                background-color: #313244;
            }
            QToolButton:pressed {
                background-color: #45475a;
            }
        """)
        self.addToolBar(toolbar)
        
        # Add toolbar title
        title_label = QtWidgets.QLabel("  rPPG Monitor")
        title_label.setStyleSheet("font-weight: bold; color: #f5c2e7; font-size: 15px;")
        toolbar.addWidget(title_label)
        
        # Add spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, 
                             QtWidgets.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Mute button with custom icon
        self.mute_button = QtWidgets.QToolButton()
        self.mute_button.setIcon(self._create_icon_from_name("audio-volume-high"))
        self.mute_button.setToolTip("Toggle alarm sound (currently ON)")
        self.mute_button.clicked.connect(lambda: toggle_alarm_sound(self))
        toolbar.addWidget(self.mute_button)
        
        # Settings button with custom icon
        settings_button = QtWidgets.QToolButton()
        settings_button.setIcon(self._create_icon_from_name("preferences-system"))
        settings_button.setToolTip("Settings")
        settings_button.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_button)
        
        # Clear data button with custom icon
        clear_button = QtWidgets.QToolButton()
        clear_button.setIcon(self._create_icon_from_name("edit-clear-all"))
        clear_button.setToolTip("Clear Graph Data")
        clear_button.clicked.connect(self.clear_graph_data)
        toolbar.addWidget(clear_button)

    def toggle_recording(self):
        """Toggle recording of heart rate data."""
        self.is_recording = not self.is_recording
        
        if self.is_recording:
            self.record_button.setText(" Stop Recording")
            self.record_button.setIcon(self._create_icon_from_name("media-playback-stop"))
            self.record_button.setStyleSheet("""
                background-color: #f38ba8;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
            """)
            self.recorded_data = []
            self.statusBar().showMessage("Recording started")
        else:
            self.record_button.setText(" Start Recording")
            self.record_button.setIcon(self._create_icon_from_name("media-record"))
            self.record_button.setStyleSheet("""
                background-color: #f38ba8;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
            """)
            self.statusBar().showMessage(f"Recording stopped. {len(self.recorded_data)} data points recorded.")
    
    def export_data(self):
        """Export recorded heart rate data to CSV."""
        if not hasattr(self, 'recorded_data') or len(self.recorded_data) == 0:
            QtWidgets.QMessageBox.warning(
                self, 
                'No Data', 
                'No data available to export. Start recording first.'
            )
            return
            
        # Get file path from user
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Save Heart Rate Data',
            f'heart_rate_data_{current_date}.csv',
            'CSV Files (*.csv)'
        )
        
        if not file_path:
            return  # User canceled
            
        try:
            # Write data to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'DateTime', 'HeartRate'])
                
                for time_val, hr in self.recorded_data:
                    dt_str = datetime.fromtimestamp(time_val).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    writer.writerow([time_val, dt_str, hr])
                    
            self.statusBar().showMessage(f"Data exported to {file_path}")
            
            # Show success message
            QtWidgets.QMessageBox.information(
                self,
                'Export Successful',
                f'Data successfully exported to:\n{file_path}'
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                'Export Error',
                f'An error occurred during export:\n{str(e)}'
            )
    
    def clear_graph_data(self):
        """Clear the graph data."""
        # Create custom dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Clear Data")
        dialog.setFixedSize(400, 180)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 14px;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#YesButton {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton#YesButton:hover {
                background-color: #f5c2e7;
            }
            QPushButton#NoButton {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton#NoButton:hover {
                background-color: #45475a;
            }
        """)
        
        # Create info icon
        icon_label = QtWidgets.QLabel()
        icon_pixmap = self._create_icon_pixmap("info", 32, "#89b4fa")
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Create message
        message = QtWidgets.QLabel("Are you sure you want to clear all graph data?")
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Create buttons
        button_layout = QtWidgets.QHBoxLayout()
        yes_button = QtWidgets.QPushButton("Yes")
        yes_button.setObjectName("YesButton")
        no_button = QtWidgets.QPushButton("No")
        no_button.setObjectName("NoButton")
        
        button_layout.addStretch()
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        button_layout.addStretch()
        
        # Connect buttons
        yes_button.clicked.connect(lambda: self._confirm_clear_data(dialog))
        no_button.clicked.connect(dialog.reject)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(icon_label)
        layout.addWidget(message)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        # Show dialog
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.hr_data = []
            self.hr_timestamps = []
            self.hr_graph.clear_graph()
            self.statusBar().showMessage("Graph data cleared")
            
    def _confirm_clear_data(self, dialog):
        """Confirm clearing the graph data."""
        dialog.accept()

    def show_settings(self):
        """Show settings dialog to adjust parameters."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Get all settings from dialog
            settings = dialog.get_settings()
            
            # Update thread settings
            self.video_thread.set_settings(settings)
            
            # Update graph min/max
            self.hr_graph.set_y_range(settings['min_hr'] - 10, settings['max_hr'] + 10)
            
            # Update graph time range if needed
            if hasattr(self, 'time_range_combo'):
                index = self.time_range_combo.findData(settings['graph_range'])
                if index >= 0:
                    self.time_range_combo.setCurrentIndex(index)
            
            self.statusBar().showMessage("Settings updated")

    def update_face_status(self, face_detected):
        """Update the face detection status display."""
        if face_detected:
            self.face_status.setText("Face detected")
            self.face_status.setStyleSheet("""
                color: #a6e3a1;
                font-weight: bold;
                padding: 4px;
            """)
            self.set_face_status_icon(True)
        else:
            self.face_status.setText("No face detected")
            self.face_status.setStyleSheet("""
                color: #fab387;
                font-weight: bold;
                padding: 4px;
            """)
            self.set_face_status_icon(False)
    
    def set_face_status_icon(self, detected):
        """Set the face status icon based on detection state."""
        if detected:
            pixmap = self._create_icon_pixmap("face", 18, "#a6e3a1")
        else:
            pixmap = self._create_icon_pixmap("face", 18, "#fab387")
        self.face_status_icon.setPixmap(pixmap)
    
    def update_signal_quality(self, quality):
        """Update the signal quality indicator."""
        # Store the value but don't update the widget directly
        self._signal_quality = quality
        # Schedule update for the next event loop cycle to break potential recursion
        QtCore.QTimer.singleShot(0, lambda: self.signal_quality.setValue(int(self._signal_quality * 100)))
    
    def update_time_range(self, index):
        """Update the graph time range."""
        time_range = self.time_range_combo.currentData()
        # Update max data points based on selected time range
        self.max_data_points = time_range
        # Trim data if needed
        while len(self.hr_data) > self.max_data_points:
            self.hr_data.pop(0)
            self.hr_timestamps.pop(0)
        # Update graph
        if len(self.hr_data) > 1:
            self.hr_graph.update_graph(self.hr_data, self.hr_timestamps)
    
    def _create_heart_pixmap(self, size, color="#E91E63"):
        """Create a heart-shaped pixmap for UI."""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Create heart path
        path = QtGui.QPainterPath()
        path.moveTo(int(size/2), int(size/5))
        path.cubicTo(
            int(size/2), int(size/10),
            0, int(size/10),
            0, int(size/2.5)
        )
        path.cubicTo(
            0, size,
            int(size/2), size,
            int(size/2), int(size/1.25)
        )
        path.cubicTo(
            int(size/2), size,
            size, size,
            size, int(size/2.5)
        )
        path.cubicTo(
            size, int(size/10),
            int(size/2), int(size/10),
            int(size/2), int(size/5)
        )
        
        # Fill the heart path
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(color))
        painter.drawPath(path)
        painter.end()
        
        return pixmap
    
    def _create_heart_icon(self):
        """Create a heart icon for the application."""
        return QtGui.QIcon(self._create_heart_pixmap(64))
    
    def _create_icon_pixmap(self, icon_type, size=16, color="#212529"):
        """Create an icon pixmap based on type."""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(color))
        
        if icon_type == "face":
            # Draw simple face icon
            painter.drawEllipse(1, 1, int(size-2), int(size-2))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 1))
            # Draw eyes
            painter.drawEllipse(int(size/3 - 1), int(size/3), 2, 2)
            painter.drawEllipse(int(2*size/3 - 1), int(size/3), 2, 2)
            # Draw smile
            painter.drawArc(int(size/3), int(size/2), int(size/3), int(size/3), 0, 180*16)
        elif icon_type == "info":
            # Draw info icon
            painter.drawEllipse(1, 1, int(size-2), int(size-2))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 1.5))
            painter.drawLine(int(size/2), int(size/3), int(size/2), int(2*size/3))
            painter.drawPoint(int(size/2), int(5*size/6))
        elif icon_type == "chart":
            # Draw chart icon
            path = QtGui.QPainterPath()
            path.moveTo(1, size-1)
            path.lineTo(1, int(size/3))
            path.lineTo(int(size/3), int(size/2))
            path.lineTo(int(2*size/3), int(size/4))
            path.lineTo(size-1, int(size/2))
            path.lineTo(size-1, size-1)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            # Default circle
            painter.drawEllipse(1, 1, int(size-2), int(size-2))
            
        painter.end()
        return pixmap
    
    def _create_icon_from_name(self, icon_name):
        """Create an icon from a standard name."""
        icon = self.style().standardIcon(getattr(QtWidgets.QStyle.StandardPixmap, f"SP_{icon_name}", 
                                                 QtWidgets.QStyle.StandardPixmap.SP_CustomBase))
        
        # If icon not found, use fallback
        if icon.isNull():
            return QtGui.QIcon(self._create_icon_pixmap("default"))
        
        return icon

    def _update_session_time(self):
        """Update the session time display."""
        elapsed_seconds = int(time.time() - self.session_start_time)
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        self.session_time.setText(f"{minutes:02}:{seconds:02}")
        
        # Update data point count
        self.datapoints_count.setText(f"{len(self.hr_data)}")
        
        # Update average heart rate
        if self.hr_data:
            avg = sum(self.hr_data) / len(self.hr_data)
            self.avg_hr.setText(f"{avg:.1f}")
            
            # Update color based on avg HR
            if avg < 60:
                self.avg_hr.setStyleSheet("color: #fab387; font-size: 18px; font-weight: bold;")
            elif avg > 100:
                self.avg_hr.setStyleSheet("color: #f38ba8; font-size: 18px; font-weight: bold;")
            else:
                self.avg_hr.setStyleSheet("color: #a6e3a1; font-size: 18px; font-weight: bold;")
        else:
            self.avg_hr.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")