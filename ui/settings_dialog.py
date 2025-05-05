# ui/settings_dialog.py - create this new file
from PyQt6 import QtWidgets, QtCore
from ui.styles import apply_stylesheet, StyleSheets, Colors

class SettingsDialog(QtWidgets.QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("rPPG Settings")
        self.setMinimumWidth(400)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the dialog UI components."""
        layout = QtWidgets.QVBoxLayout()
        
        # Heart rate thresholds group
        hr_group = QtWidgets.QGroupBox("Heart Rate Thresholds")
        hr_layout = QtWidgets.QFormLayout()
        
        self.min_normal = QtWidgets.QSpinBox()
        self.min_normal.setRange(30, 70)
        self.min_normal.setValue(50)
        
        self.max_normal = QtWidgets.QSpinBox()
        self.max_normal.setRange(80, 150)
        self.max_normal.setValue(100)
        
        hr_layout.addRow("Minimum Normal HR:", self.min_normal)
        hr_layout.addRow("Maximum Normal HR:", self.max_normal)
        hr_group.setLayout(hr_layout)
        
        # Algorithm settings group
        algo_group = QtWidgets.QGroupBox("Algorithm Settings")
        algo_layout = QtWidgets.QFormLayout()
        
        self.window_size = QtWidgets.QSpinBox()
        self.window_size.setRange(60, 180)
        self.window_size.setValue(90)
        self.window_size.setSingleStep(30)
        
        self.min_fps = QtWidgets.QSpinBox()
        self.min_fps.setRange(15, 60)
        self.min_fps.setValue(30)
        
        algo_layout.addRow("Analysis Window Size (frames):", self.window_size)
        algo_layout.addRow("Target FPS:", self.min_fps)
        algo_group.setLayout(algo_layout)
        
        # Display settings group
        disp_group = QtWidgets.QGroupBox("Display Settings")
        disp_layout = QtWidgets.QFormLayout()
        
        self.show_bpm = QtWidgets.QCheckBox()
        self.show_bpm.setChecked(True)
        
        self.show_face_rect = QtWidgets.QCheckBox()
        self.show_face_rect.setChecked(True)
        
        disp_layout.addRow("Show BPM on Video:", self.show_bpm)
        disp_layout.addRow("Show Face Rectangle:", self.show_face_rect)
        disp_group.setLayout(disp_layout)
        
        # Add groups to main layout
        layout.addWidget(hr_group)
        layout.addWidget(algo_group)
        layout.addWidget(disp_group)
        
        # Add buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)