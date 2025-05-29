# rppg/ui/components.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt
import numpy as np
import time 

from .plot_canvas import MplCanvas 

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
    def __init__(self, parent=None, dark_mode=True): 
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.canvas = MplCanvas(self, height=2.2, dark_mode=dark_mode) 
        self.layout.addWidget(self.canvas)
        self.setMinimumHeight(150) 
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        self.hr_buffer = [] 
        self.time_buffer = [] 
        self.max_buffer_duration_seconds = 180 # Default 3 menit, akan diupdate oleh MainWindow
        # self.effective_fps_for_graph = 1 # Tidak terlalu krusial jika trimming berdasarkan durasi

    def update_graph_settings(self, max_time_seconds=None):
        """Dipanggil dari MainWindow saat time_range_combo berubah."""
        if max_time_seconds is not None:
            self.max_buffer_duration_seconds = max_time_seconds
            print(f"[HeartRateGraph] Durasi buffer grafik diatur ke: {self.max_buffer_duration_seconds} detik")
        # Penting: Kosongkan buffer saat rentang waktu diubah agar grafik mulai dari awal
        # dengan data yang sesuai rentang baru.
        self.clear_graph() 

    def _trim_buffers(self):
        """Fungsi helper internal untuk memotong buffer sesuai durasi dan batas poin."""
        if not self.time_buffer: # Jika buffer kosong, tidak ada yang perlu di-trim
            return

        # 1. Trim berdasarkan durasi waktu
        #    Titik waktu tertua yang diizinkan adalah (timestamp terakhir - durasi buffer maksimal)
        oldest_allowed_timestamp = self.time_buffer[-1] - self.max_buffer_duration_seconds
        
        new_time_buffer = []
        new_hr_buffer = []
        for i in range(len(self.time_buffer)):
            if self.time_buffer[i] >= oldest_allowed_timestamp:
                new_time_buffer.append(self.time_buffer[i])
                new_hr_buffer.append(self.hr_buffer[i])
        
        self.time_buffer = new_time_buffer
        self.hr_buffer = new_hr_buffer

        # 2. Trim berdasarkan jumlah poin absolut (sebagai pengaman tambahan)
        #    Misalnya, kita batasi maksimal 600 poin (10 menit jika 1 data/detik)
        #    agar tidak terlalu berat jika data sangat rapat.
        #    Nilai ini sebaiknya lebih besar dari (max_buffer_duration_seconds * data_rate)
        max_absolute_points = self.max_buffer_duration_seconds * 2 # Izinkan 2x data per detik sebagai buffer
        if len(self.hr_buffer) > max_absolute_points:
            excess_points = len(self.hr_buffer) - max_absolute_points
            self.hr_buffer = self.hr_buffer[excess_points:]
            self.time_buffer = self.time_buffer[excess_points:]

    def update_graph(self, hr_value, timestamp):
        """Menerima satu data point HR dan timestamp, lalu update MplCanvas."""
        if hr_value is None: return # Jangan proses jika HR tidak valid

        self.hr_buffer.append(hr_value)
        self.time_buffer.append(timestamp) # timestamp dari time.time()
        
        self._trim_buffers() # Panggil fungsi untuk memotong buffer

        if len(self.hr_buffer) > 1:
            self.canvas.update_plot(np.array(self.time_buffer), np.array(self.hr_buffer))
        elif len(self.hr_buffer) == 1: 
            # Jika hanya satu titik, gambar sebagai garis horizontal pendek agar terlihat
            current_ts = self.time_buffer[0]
            # MplCanvas bisa dimodifikasi untuk handle single point atau kita buat data dummy pendek
            self.canvas.update_plot(np.array([current_ts - 0.1, current_ts + 0.1]), 
                                     np.array([self.hr_buffer[0], self.hr_buffer[0]]))
        else: # Jika buffer kosong setelah trimming (seharusnya jarang terjadi jika ada data baru)
             self.canvas.clear_data()

    def update_graph_batch(self, hr_data_list, timestamp_list):
        """Update grafik dengan sekumpulan data (batch)."""
        if hr_data_list and timestamp_list:
            # Langsung ganti buffer dengan data baru batch ini
            self.hr_buffer = list(hr_data_list) 
            self.time_buffer = list(timestamp_list)
            
            self._trim_buffers() # Terapkan trimming yang sama

            if len(self.hr_buffer) > 1:
                self.canvas.update_plot(np.array(self.time_buffer), np.array(self.hr_buffer))
            elif len(self.hr_buffer) == 1:
                current_ts = self.time_buffer[0]
                self.canvas.update_plot(np.array([current_ts - 0.1, current_ts + 0.1]), 
                                         np.array([self.hr_buffer[0], self.hr_buffer[0]]))
            else:
                self.canvas.clear_data()
        else: # Jika data batch kosong, bersihkan grafik
            self.clear_graph()

    def clear_graph(self):
        self.hr_buffer = []; self.time_buffer = []
        if hasattr(self, 'canvas'): # Pastikan canvas sudah ada
            self.canvas.clear_data()

    def set_y_range(self, min_y, max_y):
        if hasattr(self, 'canvas'):
            self.canvas.ax1.set_ylim(min_y, max_y)
            self.canvas.draw_idle()

    def set_dark_mode(self, enabled):
        if hasattr(self, 'canvas'):
            self.canvas.set_dark_mode(enabled)

# --- Kelas ProgressCircleWidget ---
class ProgressCircleWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setFixedSize(30, 30)

    def setValue(self, val):
        self._value = max(0, min(100, int(val)))
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#313244"))
        painter.drawEllipse(rect)
        pen = QPen(QColor("#a6e3a1"), 3)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        start_angle = 90 * 16
        span_angle = -int((self._value / 100.0) * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)