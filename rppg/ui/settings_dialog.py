# rppg/ui/settings_dialog.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFormLayout, QSpinBox, QCheckBox, QComboBox

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pengaturan Aplikasi (Placeholder)")
        self.layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()

        self.min_hr_spin = QSpinBox()
        self.min_hr_spin.setRange(30, 100)
        self.min_hr_spin.setValue(40)
        self.form_layout.addRow("Min HR (BPM):", self.min_hr_spin)

        self.max_hr_spin = QSpinBox()
        self.max_hr_spin.setRange(100, 220)
        self.max_hr_spin.setValue(180)
        self.form_layout.addRow("Max HR (BPM):", self.max_hr_spin)
        
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setRange(30, 300) # Misal 1-10 detik jika FPS ~30
        self.window_size_spin.setValue(90) 
        self.window_size_spin.setToolTip("Jumlah frame untuk analisis sinyal (sekitar 3 detik @30fps)")
        self.form_layout.addRow("Ukuran Jendela Analisis (frames):", self.window_size_spin)

        self.graph_range_combo = QComboBox()
        self.graph_range_combo.addItem("1 Menit", 60)
        self.graph_range_combo.addItem("3 Menit", 180)
        self.graph_range_combo.addItem("5 Menit", 300)
        self.graph_range_combo.setCurrentIndex(1) # Default 3 menit
        self.form_layout.addRow("Rentang Waktu Grafik:", self.graph_range_combo)

        self.show_face_rect_check = QCheckBox("Tampilkan Kotak Wajah & ROI")
        self.show_face_rect_check.setChecked(True)
        self.form_layout.addRow(self.show_face_rect_check)

        self.layout.addLayout(self.form_layout)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_settings(self):
        return {
            'min_hr': self.min_hr_spin.value(),
            'max_hr': self.max_hr_spin.value(),
            'window_size': self.window_size_spin.value(),
            'graph_range': self.graph_range_combo.currentData(),
            'show_face_rect': self.show_face_rect_check.isChecked(),
            # Tambahkan settings lain jika ada
        }