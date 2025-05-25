# ui/settings_dialog.py - create this new file
from PyQt6 import QtWidgets, QtCore, QtGui
from ui.styles import apply_stylesheet, StyleSheets, Colors

class SettingsDialog(QtWidgets.QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("rPPG Settings")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        
        # Apply modern window style
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 8px 12px;
                margin-right: 2px;
                color: #505050;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
                color: #E91E63;
            }
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px 12px;
                color: #404040;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #e0e0e0;
                background: white;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #E91E63;
                border: 1px solid #E91E63;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::add-page:horizontal {
                background: white;
            }
            QSlider::sub-page:horizontal {
                background: #F8BBD0;
                border-radius: 4px;
            }
        """)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the dialog UI components."""
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Create tab widget for better organization
        tab_widget = QtWidgets.QTabWidget()
        
        # Create heart rate tab
        hr_tab = QtWidgets.QWidget()
        hr_layout = QtWidgets.QVBoxLayout()
        hr_layout.setContentsMargins(16, 16, 16, 16)
        hr_layout.setSpacing(16)
        hr_tab.setLayout(hr_layout)
        
        # Heart rate thresholds group
        hr_group = QtWidgets.QGroupBox("Heart Rate Thresholds")
        hr_form_layout = QtWidgets.QFormLayout()
        hr_form_layout.setSpacing(12)
        hr_form_layout.setContentsMargins(16, 24, 16, 16)
        
        self.min_normal = QtWidgets.QSpinBox()
        self.min_normal.setRange(30, 70)
        self.min_normal.setValue(50)
        self.min_normal.setFixedWidth(100)
        
        self.max_normal = QtWidgets.QSpinBox()
        self.max_normal.setRange(80, 150)
        self.max_normal.setValue(100)
        self.max_normal.setFixedWidth(100)
        
        # Create styled labels
        min_label = QtWidgets.QLabel("Minimum Normal HR:")
        min_label.setStyleSheet("font-weight: bold; color: #404040;")
        max_label = QtWidgets.QLabel("Maximum Normal HR:")
        max_label.setStyleSheet("font-weight: bold; color: #404040;")
        
        hr_form_layout.addRow(min_label, self.min_normal)
        hr_form_layout.addRow(max_label, self.max_normal)
        hr_group.setLayout(hr_form_layout)
        
        # Algorithm settings group
        algo_group = QtWidgets.QGroupBox("Algorithm Settings")
        algo_layout = QtWidgets.QFormLayout()
        algo_layout.setSpacing(12)
        algo_layout.setContentsMargins(16, 24, 16, 16)
        
        self.window_size = QtWidgets.QSpinBox()
        self.window_size.setRange(60, 300)
        self.window_size.setValue(90)
        self.window_size.setSingleStep(30)
        self.window_size.setFixedWidth(100)
        
        self.min_fps = QtWidgets.QSpinBox()
        self.min_fps.setRange(15, 60)
        self.min_fps.setValue(30)
        self.min_fps.setFixedWidth(100)
        
        self.signal_threshold = QtWidgets.QDoubleSpinBox()
        self.signal_threshold.setRange(0.1, 1.0)
        self.signal_threshold.setValue(0.4)
        self.signal_threshold.setSingleStep(0.1)
        self.signal_threshold.setFixedWidth(100)
        
        # Create styled labels
        window_label = QtWidgets.QLabel("Analysis Window Size (frames):")
        window_label.setStyleSheet("font-weight: bold; color: #404040;")
        fps_label = QtWidgets.QLabel("Target FPS:")
        fps_label.setStyleSheet("font-weight: bold; color: #404040;")
        threshold_label = QtWidgets.QLabel("Signal Quality Threshold:")
        threshold_label.setStyleSheet("font-weight: bold; color: #404040;")
        
        algo_layout.addRow(window_label, self.window_size)
        algo_layout.addRow(fps_label, self.min_fps)
        algo_layout.addRow(threshold_label, self.signal_threshold)
        algo_group.setLayout(algo_layout)
        
        # Add groups to heart rate tab
        hr_layout.addWidget(hr_group)
        hr_layout.addWidget(algo_group)
        hr_layout.addStretch()
        
        # Create display tab
        display_tab = QtWidgets.QWidget()
        display_layout = QtWidgets.QVBoxLayout()
        display_layout.setContentsMargins(16, 16, 16, 16)
        display_layout.setSpacing(16)
        display_tab.setLayout(display_layout)
        
        # Display settings group
        disp_group = QtWidgets.QGroupBox("Display Settings")
        disp_layout = QtWidgets.QFormLayout()
        disp_layout.setSpacing(12)
        disp_layout.setContentsMargins(16, 24, 16, 16)
        
        self.show_bpm = QtWidgets.QCheckBox()
        self.show_bpm.setChecked(True)
        self.show_bpm.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        
        self.show_face_rect = QtWidgets.QCheckBox()
        self.show_face_rect.setChecked(True)
        self.show_face_rect.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        
        self.show_landmarks = QtWidgets.QCheckBox()
        self.show_landmarks.setChecked(False)
        self.show_landmarks.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        
        self.mirror_preview = QtWidgets.QCheckBox()
        self.mirror_preview.setChecked(True)
        self.mirror_preview.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        
        self.graph_range = QtWidgets.QComboBox()
        self.graph_range.addItem("1 minute", 60)
        self.graph_range.addItem("3 minutes", 180)
        self.graph_range.addItem("5 minutes", 300)
        self.graph_range.setFixedWidth(150)
        
        # Create styled labels
        bpm_label = QtWidgets.QLabel("Show BPM on Video:")
        bpm_label.setStyleSheet("font-weight: bold; color: #404040;")
        rect_label = QtWidgets.QLabel("Show Face Rectangle:")
        rect_label.setStyleSheet("font-weight: bold; color: #404040;")
        landmarks_label = QtWidgets.QLabel("Show Face Landmarks:")
        landmarks_label.setStyleSheet("font-weight: bold; color: #404040;")
        mirror_label = QtWidgets.QLabel("Mirror Preview:")
        mirror_label.setStyleSheet("font-weight: bold; color: #404040;")
        graph_label = QtWidgets.QLabel("Graph Time Range:")
        graph_label.setStyleSheet("font-weight: bold; color: #404040;")
        
        disp_layout.addRow(bpm_label, self.show_bpm)
        disp_layout.addRow(rect_label, self.show_face_rect)
        disp_layout.addRow(landmarks_label, self.show_landmarks)
        disp_layout.addRow(mirror_label, self.mirror_preview)
        disp_layout.addRow(graph_label, self.graph_range)
        disp_group.setLayout(disp_layout)
        
        # Add groups to display tab
        display_layout.addWidget(disp_group)
        display_layout.addStretch()
        
        # Create camera tab
        camera_tab = QtWidgets.QWidget()
        camera_layout = QtWidgets.QVBoxLayout()
        camera_layout.setContentsMargins(16, 16, 16, 16)
        camera_layout.setSpacing(16)
        camera_tab.setLayout(camera_layout)
        
        # Camera settings group
        camera_group = QtWidgets.QGroupBox("Camera Settings")
        camera_form_layout = QtWidgets.QFormLayout()
        camera_form_layout.setSpacing(12)
        camera_form_layout.setContentsMargins(16, 24, 16, 16)
        
        self.auto_settings = QtWidgets.QCheckBox()
        self.auto_settings.setChecked(True)
        self.auto_settings.stateChanged.connect(self._toggle_camera_settings)
        self.auto_settings.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        
        self.exposure_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.exposure_slider.setRange(-10, 10)
        self.exposure_slider.setValue(0)
        self.exposure_slider.setEnabled(False)
        self.exposure_slider.setFixedWidth(200)
        
        exposure_layout = QtWidgets.QHBoxLayout()
        exposure_layout.addWidget(self.exposure_slider)
        self.exposure_value = QtWidgets.QLabel("0")
        self.exposure_value.setFixedWidth(30)
        self.exposure_value.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.exposure_value.setStyleSheet("color: #E91E63; font-weight: bold;")
        exposure_layout.addWidget(self.exposure_value)
        
        self.exposure_slider.valueChanged.connect(
            lambda val: self.exposure_value.setText(str(val)))
        
        self.detector_combo = QtWidgets.QComboBox()
        self.detector_combo.addItem("Face Mesh (Best Quality)", "mesh")
        self.detector_combo.addItem("MediaPipe (Fast)", "mediapipe")
        self.detector_combo.addItem("Haar Cascade (Fallback)", "haar")
        self.detector_combo.addItem("Auto (Default)", "auto")
        self.detector_combo.setFixedWidth(200)
        
        # Create styled labels
        auto_label = QtWidgets.QLabel("Auto Camera Settings:")
        auto_label.setStyleSheet("font-weight: bold; color: #404040;")
        exposure_label = QtWidgets.QLabel("Manual Exposure:")
        exposure_label.setStyleSheet("font-weight: bold; color: #404040;")
        detector_label = QtWidgets.QLabel("Face Detector:")
        detector_label.setStyleSheet("font-weight: bold; color: #404040;")
        
        camera_form_layout.addRow(auto_label, self.auto_settings)
        camera_form_layout.addRow(exposure_label, exposure_layout)
        camera_form_layout.addRow(detector_label, self.detector_combo)
        camera_group.setLayout(camera_form_layout)
        
        # Add groups to camera tab
        camera_layout.addWidget(camera_group)
        camera_layout.addStretch()
        
        # Create performance tab
        performance_tab = QtWidgets.QWidget()
        performance_layout = QtWidgets.QVBoxLayout()
        performance_layout.setContentsMargins(16, 16, 16, 16)
        performance_layout.setSpacing(16)
        performance_tab.setLayout(performance_layout)
        
        # Performance settings group
        perf_group = QtWidgets.QGroupBox("Performance Settings")
        perf_layout = QtWidgets.QFormLayout()
        perf_layout.setSpacing(12)
        perf_layout.setContentsMargins(16, 24, 16, 16)
        
        # Target FPS setting to control frame skipping
        self.target_fps = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.target_fps.setRange(5, 30)
        self.target_fps.setValue(20)
        self.target_fps.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.target_fps.setTickInterval(5)
        self.target_fps.setFixedWidth(200)
        
        # Add a label to show current value
        fps_layout = QtWidgets.QHBoxLayout()
        fps_layout.addWidget(self.target_fps)
        self.fps_value = QtWidgets.QLabel("20")
        self.fps_value.setFixedWidth(30)
        self.fps_value.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.fps_value.setStyleSheet("color: #E91E63; font-weight: bold;")
        fps_layout.addWidget(self.fps_value)
        self.target_fps.valueChanged.connect(
            lambda val: self.fps_value.setText(str(val)))
        
        # Processing resolution dropdown
        self.process_resolution = QtWidgets.QComboBox()
        self.process_resolution.addItem("Low (320x240) - Fastest", "low")
        self.process_resolution.addItem("Medium (480x360) - Balanced", "medium")
        self.process_resolution.addItem("High (640x480) - Best Quality", "high")
        self.process_resolution.setCurrentIndex(0)  # Default to low for better performance
        self.process_resolution.setFixedWidth(200)
        
        # Create styled labels
        fps_label = QtWidgets.QLabel("Target Frame Rate:")
        fps_label.setStyleSheet("font-weight: bold; color: #404040;")
        resolution_label = QtWidgets.QLabel("Processing Resolution:")
        resolution_label.setStyleSheet("font-weight: bold; color: #404040;")
        
        perf_layout.addRow(fps_label, fps_layout)
        perf_layout.addRow(resolution_label, self.process_resolution)
        perf_group.setLayout(perf_layout)
        
        # Performance Tips
        tips_group = QtWidgets.QGroupBox("Performance Tips")
        tips_layout = QtWidgets.QVBoxLayout()
        tips_layout.setContentsMargins(16, 24, 16, 16)
        
        # Create styled tips
        tips_text = QtWidgets.QLabel(
            "• Use lower resolution for smoother video performance\n"
            "• Reduce target frame rate if CPU usage is high\n"
            "• Ensure good, consistent lighting for better results\n"
            "• Keep face centered and minimize movement\n"
            "• Choose 'MediaPipe' detector for better performance"
        )
        tips_text.setStyleSheet("color: #606060;")
        tips_text.setWordWrap(True)
        tips_layout.addWidget(tips_text)
        tips_group.setLayout(tips_layout)
        
        # Add groups to performance tab
        performance_layout.addWidget(perf_group)
        performance_layout.addWidget(tips_group)
        performance_layout.addStretch()
        
        # Add tabs to tab widget with icons
        tab_widget.addTab(hr_tab, self._create_icon('#F44336'), "Heart Rate")
        tab_widget.addTab(display_tab, self._create_icon('#2196F3'), "Display")
        tab_widget.addTab(camera_tab, self._create_icon('#4CAF50'), "Camera")
        tab_widget.addTab(performance_tab, self._create_icon('#FF9800'), "Performance")
        
        # Add tab widget to main layout
        layout.addWidget(tab_widget)
        
        # Add reset to defaults button with icon
        reset_button = QtWidgets.QPushButton("Reset to Defaults")
        reset_icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton)
        reset_button.setIcon(reset_icon)
        reset_button.clicked.connect(self._reset_to_defaults)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #404040;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        
        # Add buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        
        # Style the OK button to be more prominent
        ok_button = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #D81B60;
            }
            QPushButton:pressed {
                background-color: #C2185B;
            }
        """)
        
        cancel_button = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add reset button to left of button box
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _create_icon(self, color):
        """Create a colored icon for tabs."""
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(color))
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        return QtGui.QIcon(pixmap)
        
    def _toggle_camera_settings(self, state):
        """Enable or disable manual camera settings based on checkbox state."""
        self.exposure_slider.setEnabled(not state)
        
    def _reset_to_defaults(self):
        """Reset all settings to their default values."""
        # Heart rate defaults
        self.min_normal.setValue(50)
        self.max_normal.setValue(100)
        
        # Algorithm defaults
        self.window_size.setValue(90)
        self.min_fps.setValue(30)
        self.signal_threshold.setValue(0.4)
        
        # Display defaults
        self.show_bpm.setChecked(True)
        self.show_face_rect.setChecked(True)
        self.show_landmarks.setChecked(False)
        self.mirror_preview.setChecked(True)
        self.graph_range.setCurrentIndex(1)  # 3 minutes
        
        # Camera defaults
        self.auto_settings.setChecked(True)
        self.exposure_slider.setValue(0)
        self.detector_combo.setCurrentIndex(3)  # Auto
        
        # Performance defaults - set to lower quality for better performance
        self.target_fps.setValue(20)
        self.process_resolution.setCurrentIndex(0)  # Low resolution
        
    def get_settings(self):
        """Get all settings as a dictionary."""
        return {
            # Heart rate settings
            'min_hr': self.min_normal.value(),
            'max_hr': self.max_normal.value(),
            
            # Algorithm settings
            'window_size': self.window_size.value(),
            'min_fps': self.min_fps.value(),
            'signal_threshold': self.signal_threshold.value(),
            
            # Display settings
            'show_bpm_on_frame': self.show_bpm.isChecked(),
            'show_face_rect': self.show_face_rect.isChecked(),
            'show_landmarks': self.show_landmarks.isChecked(),
            'mirror_preview': self.mirror_preview.isChecked(),
            'graph_range': self.graph_range.currentData(),
            
            # Camera settings
            'auto_settings': self.auto_settings.isChecked(),
            'exposure': self.exposure_slider.value(),
            'detector': self.detector_combo.currentData(),
            
            # Performance settings
            'target_fps': self.target_fps.value(),
            'process_resolution': self.process_resolution.currentData()
        }