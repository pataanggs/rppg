# rppg/ui/components.py
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QPainter, QColor, QPen # Pastikan QPen dan QColor ada
from PyQt6.QtCore import Qt
import numpy as np # Diperlukan untuk MplCanvas jika data dikirim sebagai array numpy
import time

# Import MplCanvas dari plot_canvas.py kamu
# Pastikan file plot_canvas.py ada di rppg/ui/plot_canvas.py
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

# --- GANTI KELAS HeartRateGraph DI BAWAH INI ---
class HeartRateGraph(QtWidgets.QWidget):
    def __init__(self, parent=None, dark_mode=True): # Tambahkan dark_mode
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)

        # Buat instance MplCanvas dan teruskan argumen dark_mode
        self.canvas = MplCanvas(self, height=2.2, dark_mode=dark_mode) 
        
        self.layout.addWidget(self.canvas)
        
        self.setMinimumHeight(150) 
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        # Buffer data untuk plotting
        self.hr_buffer = [] 
        self.resp_buffer = [] # Tambahkan buffer untuk data respirasi
        self.time_buffer = [] 
        # max_buffer_points bisa diambil dari pengaturan atau combo box di MainWindow
        # Untuk sementara, kita set di sini, tapi idealnya bisa diubah
        self.max_buffer_points_seconds = 180 # Default 3 menit
        self.effective_fps_for_graph = 1 # Asumsi 1 data HR per detik masuk ke grafik


    def update_graph_settings(self, max_time_seconds=None):
        """Update pengaturan buffer grafik, misal dari time_range_combo."""
        if max_time_seconds:
            self.max_buffer_points_seconds = max_time_seconds
        # Hitung ulang max_buffer_points berdasarkan asumsi 1 data per detik (atau fps sebenarnya dari data HR)
        self.max_buffer_points = self.max_buffer_points_seconds * self.effective_fps_for_graph


    def update_graph(self, hr_value, timestamp, resp_value=None):
        """Menerima satu data point HR dan timestamp, lalu update MplCanvas."""
        if hr_value is None: return

        self.hr_buffer.append(hr_value)
        self.time_buffer.append(timestamp)
        if resp_value is not None:
            self.resp_buffer.append(resp_value) # Simpan data respirasi jika ada

        # Jaga ukuran buffer berdasarkan durasi waktu
        # Hapus data yang lebih tua dari max_buffer_points_seconds
        current_time = time.time() # Jika timestamp adalah unix time, bisa pakai ini
        if self.time_buffer:
             cutoff_time = self.time_buffer[-1] - self.max_buffer_points_seconds
        else:
             cutoff_time = current_time - self.max_buffer_points_seconds

        while self.time_buffer and self.time_buffer[0] < cutoff_time:
            self.time_buffer.pop(0)
            self.hr_buffer.pop(0)
            if self.resp_buffer: # Hapus juga data respirasi yang sudah tidak relevan
                self.resp_buffer.pop(0)
        
        # Jaga juga agar jumlah poin tidak melebihi batas absolut (misal 300-500 poin agar tidak berat)
        # Ini bisa jadi redundant jika pemotongan berdasarkan waktu sudah efektif
        max_absolute_points = 500 
        while len(self.hr_buffer) > max_absolute_points:
            self.hr_buffer.pop(0)
            self.time_buffer.pop(0)
            if self.resp_buffer: # Hapus juga dari buffer respirasi
                self.resp_buffer.pop(0)


        if len(self.hr_buffer) > 1:
            # MplCanvas akan membuat waktu relatif dari timestamp pertama
            self.canvas.update_plot(np.array(self.time_buffer), np.array(self.hr_buffer), np.array(self.resp_buffer) if self.resp_buffer else None)

    def update_plot(self, time_data, hr_data, resp_data=None):
        """Update both heart rate and respiratory plots"""
        self.canvas.update_plot(time_data, hr_data, resp_data)

    def update_graph_batch(self, hr_data_list, timestamp_list):
        """
        Metode untuk update graph dengan data batch (jika masih dipakai).
        Lebih disarankan update per data point untuk real-time feel.
        """
        if hr_data_list and timestamp_list:
            self.hr_buffer = list(hr_data_list) 
            self.time_buffer = list(timestamp_list)
            
            # Jaga ukuran buffer seperti di update_graph
            current_time = time.time()
            if self.time_buffer:
                 cutoff_time = self.time_buffer[-1] - self.max_buffer_points_seconds
            else:
                 cutoff_time = current_time - self.max_buffer_points_seconds

            while self.time_buffer and self.time_buffer[0] < cutoff_time:
                self.time_buffer.pop(0)
                self.hr_buffer.pop(0)
            
            max_absolute_points = 500
            while len(self.hr_buffer) > max_absolute_points:
                self.hr_buffer.pop(0)
                self.time_buffer.pop(0)

            if len(self.hr_buffer) > 1:
                self.canvas.update_plot(np.array(self.time_buffer), np.array(self.hr_buffer))


    def clear_graph(self):
        self.hr_buffer = []; self.resp_buffer = []; self.time_buffer = []
        self.canvas.clear_data()

    def set_y_range(self, min_y, max_y):
        self.canvas.ax1.set_ylim(min_y, max_y) # Akses ax1 dari MplCanvas
        self.canvas.draw_idle()

    def set_dark_mode(self, enabled):
        self.canvas.set_dark_mode(enabled)

# --- Kelas ProgressCircleWidget kamu ---
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