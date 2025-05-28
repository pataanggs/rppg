# rppg/ui/components.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QPainter, QColor, QPen # Tambahkan QPen
from PyQt6.QtCore import Qt

class HeartRateDisplay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.hr_label = QtWidgets.QLabel("--")
        self.hr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hr_label.setStyleSheet("font-size: 60px; font-weight: bold; color: #a6e3a1;")
        self.layout.addWidget(self.hr_label)
        self.setMinimumHeight(100)

    def set_heart_rate(self, hr):
        self.hr_label.setText(f"{hr:.1f}" if hr > 0 else "--")

    def set_color(self, color_hex):
        self.hr_label.setStyleSheet(f"font-size: 60px; font-weight: bold; color: {color_hex};")

class HeartRateGraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.graph_label = QtWidgets.QLabel("Grafik Detak Jantung (Placeholder)")
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setStyleSheet("background-color: #2a2a3a; border-radius: 8px; color: #cdd6f4; padding: 10px;")
        self.layout.addWidget(self.graph_label)
        self.setMinimumHeight(150) # Beri tinggi minimum

    def update_graph(self, data, timestamps):
        if data:
            self.graph_label.setText(f"Data terakhir: {data[-1]:.1f} BPM ({len(data)} poin)")
        else:
            self.graph_label.setText("Grafik Detak Jantung (Placeholder)")
    
    def clear_graph(self):
        self.graph_label.setText("Grafik Detak Jantung (Data Dihapus)")

    def set_y_range(self, min_y, max_y):
        print(f"[Graph] Y-Range set to: {min_y} - {max_y}")


class ProgressCircleWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setFixedSize(30, 30) # Ukuran lingkaran

    def setValue(self, val):
        self._value = max(0, min(100, int(val))) # Pastikan antara 0-100
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2) # Beri sedikit padding
        
        # Gambar background lingkaran
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#313244")) # Warna background
        painter.drawEllipse(rect)

        # Gambar progress arc
        pen = QPen(QColor("#a6e3a1"), 3) # Warna progress, ketebalan 3
        pen.setCapStyle(Qt.PenCapStyle.FlatCap) # Atau RoundCap
        painter.setPen(pen)
        
        start_angle = 90 * 16 # Mulai dari atas
        span_angle = -int((self._value / 100.0) * 360 * 16) # Negatif = searah jarum jam dari atas
        painter.drawArc(rect, start_angle, span_angle)