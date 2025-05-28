import sys
import cv2
import mediapipe as mp
import threading
import time
import numpy as np
import queue
import csv
import os
from datetime import datetime

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout,
    QFrame, QToolBar, QPushButton, QToolButton, QComboBox, QDialog,
    QFileDialog, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter, QFont, QPainterPath, QPen, QColor
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, Qt, QSize

# =============================================================================
# Placeholder/Import (SESUAIKAN JIKA PERLU)
# =============================================================================
# Asumsi kelas-kelas ini ada dan bisa diimport
# Jika tidak, copy-paste kelasnya ke file ini atau fix path import.

class HeartRateDisplay(QtWidgets.QWidget): # Placeholder
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.hr_label = QtWidgets.QLabel("--")
        self.hr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hr_label.setStyleSheet("font-size: 60px; font-weight: bold;")
        self.layout.addWidget(self.hr_label)
        self.setMinimumHeight(100)

    def set_heart_rate(self, hr):
        self.hr_label.setText(f"{hr:.1f}")

    def set_color(self, color):
        self.hr_label.setStyleSheet(f"font-size: 60px; font-weight: bold; color: {color};")

class HeartRateGraph(QtWidgets.QWidget): # Placeholder
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.graph_label = QtWidgets.QLabel("Graph Placeholder")
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setStyleSheet("background-color: #2a2a3a; border-radius: 8px;")
        self.layout.addWidget(self.graph_label)

    def update_graph(self, data, timestamps): pass
    def clear_graph(self): pass
    def set_y_range(self, min_y, max_y): pass

class ProgressCircleWidget(QtWidgets.QWidget): # Placeholder
    def __init__(self):
        super().__init__()
        self.value = 0
        self.setFixedSize(30, 30)

    def setValue(self, val):
        self.value = val
        self.update() # Minta redraw

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#313244"))
        painter.drawEllipse(rect)

        painter.setPen(QPen(QColor("#a6e3a1"), 3))
        start_angle = 90 * 16
        span_angle = -int((self.value / 100.0) * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)

class SettingsDialog(QDialog): # Placeholder
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings (Placeholder)")
    def get_settings(self):
        return {'min_hr': 40, 'max_hr': 180, 'window_size': 90, 'graph_range': 180}

class AudioManager: # Placeholder
    def __init__(self, parent=None):
        self.is_muted = False
    def play_sound(self, sound, loop=False): print(f"Playing sound: {sound}")
    def stop_sound(self, sound): print(f"Stopping sound: {sound}")
    def toggle_mute(self): self.is_muted = not self.is_muted
    def is_playing(self, sound): return False
    def stop_all_sounds(self): print("Stopping all sounds")

# Asumsi ini ada
class Colors: HR_NORMAL = "#a6e3a1"
class Fonts: pass
class StyleSheets: pass
class Layout: VIDEO_MIN_WIDTH = 480; VIDEO_MIN_HEIGHT = 360
def get_heart_rate_color(hr): return "#a6e3a1" if 60 <= hr <= 100 else "#f38ba8"

# =============================================================================
# 1. Global Signals
# =============================================================================
class GlobalSignals(QObject):
    hr_update = pyqtSignal(float, bool, float) # HR, IsValid, Confidence
    face_detected = pyqtSignal(bool)
    signal_quality_update = pyqtSignal(float) # Tambahkan ini

# =============================================================================
# 2. Signal Processor (GANTI DENGAN KODEMU!)
# =============================================================================
class SignalProcessor:
    def process(self, signal_chunk, timestamps):
        if not signal_chunk or len(signal_chunk) < 10:
            return None, 0.0, 0.0
        dummy_hr = 65.0 + np.random.randn() * 5
        dummy_confidence = 0.6 + np.random.rand() * 0.4
        dummy_quality = 75.0 + np.random.rand() * 20 # Kualitas 0-100
        return dummy_hr, dummy_confidence, dummy_quality

# =============================================================================
# 3. Capture Thread
# =============================================================================
class CaptureThread(threading.Thread):
    def __init__(self, camera_index, frame_queue):
        super().__init__()
        self.daemon = True
        self.camera_index = camera_index
        self.frame_queue = frame_queue
        self.running = False
        self.cap = None

    def _configure_camera(self):
        if not self.cap: return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def run(self):
        print("CaptureThread starting...")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print(f"Error: Unable to open camera {self.camera_index}")
            return

        self._configure_camera()
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            timestamp = time.time()
            if not ret:
                time.sleep(0.1)
                continue
            try:
                self.frame_queue.put((frame, timestamp), block=True, timeout=0.5)
            except queue.Full:
                try: self.frame_queue.get_nowait()
                except queue.Empty: pass

        print("CaptureThread stopping...")
        if self.cap: self.cap.release()
        print("CaptureThread stopped.")

    def stop(self):
        self.running = False
        while not self.frame_queue.empty():
            try: self.frame_queue.get_nowait()
            except queue.Empty: break

# =============================================================================
# 4. Process Thread
# =============================================================================
class ProcessThread(threading.Thread):
    def __init__(self, frame_queue, signal_queue, display_queue, signals_obj):
        super().__init__()
        self.daemon = True
        self.frame_queue = frame_queue
        self.signal_queue = signal_queue
        self.display_queue = display_queue
        self.signals = signals_obj
        self.running = False

        self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5)
        
        self.smoothed_bbox = None
        self.smoothing_alpha = 0.7
        self.has_face = False
        self.last_face_time = 0
        self.face_lost_threshold = 1.0
        self.process_width = 320
        self.process_height = 240
        self.show_face_rect = True
        self.current_hr_for_display = 0.0

        self.signals.hr_update.connect(self._update_hr_for_display)

    def _update_hr_for_display(self, hr, is_valid, confidence):
        self.current_hr_for_display = hr if is_valid else 0.0

    def _process_mp_face(self, display_frame, process_frame):
        frame_rgb = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.mp_face_detection.process(frame_rgb)
        frame_rgb.flags.writeable = True
        green_avg = None
        face_found = False

        if results and results.detections:
            detection = results.detections[0]
            bbox_rel = detection.location_data.relative_bounding_box
            ih, iw, _ = process_frame.shape
            x, y, w, h = int(bbox_rel.xmin * iw), int(bbox_rel.ymin * ih), int(bbox_rel.width * iw), int(bbox_rel.height * ih)
            current_bbox = np.array([x, y, w, h], dtype=np.float32)
            if self.smoothed_bbox is None: self.smoothed_bbox = current_bbox
            else: self.smoothed_bbox = self.smoothing_alpha * current_bbox + (1 - self.smoothing_alpha) * self.smoothed_bbox
            sx, sy, sw, sh = map(int, self.smoothed_bbox)
            fx = sx + int(sw * 0.2); fy = sy + int(sh * 0.1)
            fw = int(sw * 0.6); fh = int(sh * 0.15)
            if 0 <= fx < iw and 0 <= fy < ih and fw > 0 and fh > 0 and (fx + fw) <= iw and (fy + fh) <= ih:
                forehead_roi = process_frame[fy:fy + fh, fx:fx + fw]
                if forehead_roi.size > 0:
                    green_avg = np.mean(forehead_roi[:, :, 1])
                    face_found = True
                    if self.show_face_rect:
                        self._draw_boxes(display_frame, (sx, sy, sw, sh), (fx, fy, fw, fh), (0, 255, 0))
        return green_avg, face_found

    def _draw_boxes(self, frame, face_box, roi_box, color):
        ih, iw = self.process_height, self.process_width
        dh, dw = frame.shape[:2]
        scale_x = dw / iw; scale_y = dh / ih
        sx, sy, sw, sh = face_box
        fx, fy, fw, fh = roi_box
        cv2.rectangle(frame, (int(sx*scale_x), int(sy*scale_y)), (int((sx+sw)*scale_x), int((sy+sh)*scale_y)), color, 2)
        cv2.rectangle(frame, (int(fx*scale_x), int(fy*scale_y)), (int((fx+fw)*scale_x), int((fy+fh)*scale_y)), (0, 255, 255), 1)

    def _add_info_to_frame(self, frame):
        if self.current_hr_for_display > 0:
             cv2.putText(frame, f"HR: {self.current_hr_for_display:.1f} BPM", (10, 30), 
                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def run(self):
        print("ProcessThread starting...")
        self.running = True
        while self.running:
            try:
                frame, timestamp = self.frame_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                if not self.running: break
                continue
            display_frame = cv2.flip(frame.copy(), 1)
            scale = self.process_width / frame.shape[1]
            process_frame = cv2.resize(frame, (self.process_width, int(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)
            process_frame = cv2.flip(process_frame, 1)
            green_avg, face_detected_in_frame = self._process_mp_face(display_frame, process_frame)
            current_time = time.time()
            if face_detected_in_frame:
                if not self.has_face: self.signals.face_detected.emit(True)
                self.has_face = True
                self.last_face_time = current_time
            elif self.has_face and (current_time - self.last_face_time) > self.face_lost_threshold:
                if self.has_face: self.signals.face_detected.emit(False)
                self.has_face = False
                self.smoothed_bbox = None
            if green_avg is not None:
                try: self.signal_queue.put_nowait((green_avg, timestamp))
                except queue.Full: pass
            self._add_info_to_frame(display_frame)
            try: self.display_queue.put_nowait(display_frame)
            except queue.Full:
                try: self.display_queue.get_nowait()
                except queue.Empty: pass
                try: self.display_queue.put_nowait(display_frame)
                except queue.Full: pass
            self.frame_queue.task_done()
        print("ProcessThread stopped.")
        self.mp_face_detection.close()

    def stop(self):
        self.running = False
        while not self.signal_queue.empty():
            try: self.signal_queue.get_nowait()
            except queue.Empty: break
        while not self.display_queue.empty():
            try: self.display_queue.get_nowait()
            except queue.Empty: break

# =============================================================================
# 5. Analysis Thread
# =============================================================================
class AnalysisThread(threading.Thread):
    def __init__(self, signal_queue, signals_obj):
        super().__init__()
        self.daemon = True
        self.signal_queue = signal_queue
        self.signals = signals_obj
        self.running = False
        self.signal_processor = SignalProcessor()
        self.window_size = 90
        self.min_hr = 40
        self.max_hr = 180
        self.buffer = []
        self.timestamps = []
        self.hr_update_interval = 1.0
        self.last_hr_update_time = 0

    def run(self):
        print("AnalysisThread starting...")
        self.running = True
        while self.running:
            try:
                signal_val, timestamp = self.signal_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                if not self.running: break
                continue
            self.buffer.append(signal_val)
            self.timestamps.append(timestamp)
            while len(self.buffer) > self.window_size * 2:
                self.buffer.pop(0)
                self.timestamps.pop(0)
            current_time = time.time()
            if len(self.buffer) >= self.window_size and \
               (current_time - self.last_hr_update_time) >= self.hr_update_interval:
                hr, confidence, quality = self.signal_processor.process(
                    self.buffer[-self.window_size:], self.timestamps[-self.window_size:])
                is_valid = False
                current_hr = 0.0
                if hr is not None and self.min_hr <= hr <= self.max_hr:
                    current_hr = hr
                    is_valid = True
                self.signals.hr_update.emit(current_hr, is_valid, confidence)
                self.signals.signal_quality_update.emit(quality) # Emit kualitas
                self.last_hr_update_time = current_time
            self.signal_queue.task_done()
        print("AnalysisThread stopped.")

    def stop(self):
        self.running = False

# =============================================================================
# 6. Main Window (PyQt6 UI) - MENGGABUNGKAN KODEMU DENGAN MULTI-THREAD
# =============================================================================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.hr_data = []
        self.hr_timestamps = []
        self.max_data_points = 180 # Default 3 menit
        self.audio_manager = AudioManager(self) 
        self.is_muted = self.audio_manager.is_muted
        self.is_recording = False
        self.recorded_data = []
        
        self.initUI() 
        
        # --- INISIALISASI BARU ---
        self.init_threads_and_queues()
        self.connect_signals_to_slots()
        self.init_video_timer()
        # -------------------------

    def initUI(self):
        self.setWindowTitle("rPPG Heart Rate Monitor - Multi Thread")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(self._create_heart_icon())
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #cdd6f4; font-family: 'Segoe UI', Arial, sans-serif; }
            QPushButton { background-color: #f38ba8; color: #1e1e2e; border: none; border-radius: 6px; padding: 12px 20px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #f5c2e7; } QPushButton:pressed { background-color: #cba6f7; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
            QToolBar { background-color: #181825; border-bottom: 1px solid #313244; spacing: 12px; padding: 8px 6px; }
            QToolButton { border: none; border-radius: 6px; padding: 8px; } QToolButton:hover { background-color: #313244; }
            QToolButton:pressed { background-color: #45475a; } QStatusBar { background-color: #181825; color: #a6adc8; border-top: 1px solid #313244; font-size: 12px; padding: 4px; }
            QComboBox { border: 1px solid #313244; border-radius: 6px; padding: 8px 14px; background-color: #313244; color: #cdd6f4; min-height: 24px; }
            QComboBox::drop-down { border: none; width: 24px; }
            /* QComboBox::down-arrow { image: url(ui/assets/down-arrow.png); width: 12px; height: 12px; } */ /* Commented out if no asset */
            QComboBox:hover { border-color: #45475a; background-color: #45475a; }
        """)
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(30)
        top_section = QtWidgets.QHBoxLayout(); top_section.setSpacing(30)
        left_panel = QtWidgets.QVBoxLayout(); left_panel.setSpacing(20)
        self.video_container = QtWidgets.QWidget(); self.video_container.setObjectName("videoContainer")
        self.video_container.setStyleSheet("#videoContainer { background-color: #181825; border-radius: 16px; border: 1px solid #313244; }")
        video_layout = QtWidgets.QVBoxLayout(self.video_container); video_layout.setContentsMargins(3, 3, 3, 3)
        self.video_label = QtWidgets.QLabel(); self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(480, 360) # Adjusted size
        self.video_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.video_label.setStyleSheet("border-radius: 14px;")
        placeholder = QtGui.QPixmap(480, 360); placeholder.fill(QtGui.QColor("#1a1b26"))
        placeholder_painter = QtGui.QPainter(placeholder); placeholder_painter.setPen(QtGui.QColor("#6c7086")); placeholder_painter.setFont(QtGui.QFont("Segoe UI", 14))
        placeholder_painter.drawText(placeholder.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Connecting to camera..."); placeholder_painter.end()
        self.video_label.setPixmap(placeholder); video_layout.addWidget(self.video_label)
        face_status_container = QtWidgets.QWidget(); face_status_container.setStyleSheet("background-color: #181825; border-radius: 10px; border: 1px solid #313244;")
        face_status_layout = QtWidgets.QHBoxLayout(face_status_container); face_status_layout.setContentsMargins(16, 12, 16, 12); face_status_layout.setSpacing(14)
        self.face_status_icon = QtWidgets.QLabel(); self.face_status_icon.setFixedSize(22, 22); self.set_face_status_icon(False)
        self.face_status = QtWidgets.QLabel("No face detected"); self.face_status.setStyleSheet("color: #fab387; font-weight: bold; font-size: 14px;")
        status_separator = QtWidgets.QFrame(); status_separator.setFrameShape(QtWidgets.QFrame.Shape.VLine); status_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken); status_separator.setStyleSheet("color: #313244;")
        quality_label = QtWidgets.QLabel("Signal Quality:"); quality_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        self.signal_quality = ProgressCircleWidget(); self.signal_quality.setValue(0)
        face_status_layout.addWidget(self.face_status_icon); face_status_layout.addWidget(self.face_status); face_status_layout.addStretch()
        face_status_layout.addWidget(status_separator); face_status_layout.addWidget(quality_label); face_status_layout.addWidget(self.signal_quality)
        left_panel.addWidget(self.video_container, 1); left_panel.addWidget(face_status_container)
        right_panel_container = QtWidgets.QWidget(); right_panel_container.setObjectName("rightPanel"); right_panel_container.setStyleSheet("#rightPanel { background-color: #181825; border-radius: 16px; border: 1px solid #313244; }")
        right_panel = QtWidgets.QVBoxLayout(right_panel_container); right_panel.setContentsMargins(30, 30, 30, 30); right_panel.setSpacing(25)
        header_layout = QtWidgets.QHBoxLayout(); heart_logo_container = QtWidgets.QWidget(); heart_logo_container.setFixedSize(44, 44)
        heart_logo_layout = QtWidgets.QVBoxLayout(heart_logo_container); heart_logo_layout.setContentsMargins(0, 0, 0, 0)
        self.heart_logo = QtWidgets.QLabel(); heart_pixmap = self._create_heart_pixmap(36, "#f38ba8"); self.heart_logo.setPixmap(heart_pixmap); self.heart_logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        heart_logo_layout.addWidget(self.heart_logo); title_label = QtWidgets.QLabel("rPPG Heart Rate Monitor"); title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #f5c2e7;")
        header_layout.addWidget(heart_logo_container); header_layout.addWidget(title_label); header_layout.addStretch()
        description = QtWidgets.QLabel("Remote photoplethysmography (rPPG) analyzes subtle color changes in facial skin to measure heart rate non-invasively using only a standard camera.")
        description.setStyleSheet("color: #a6adc8; font-size: 14px; line-height: 1.5;"); description.setWordWrap(True)
        self.hr_display = HeartRateDisplay(); self.hr_display.set_color("#a6e3a1") # Use a defined color
        status_container = QtWidgets.QWidget(); status_container.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 4px;")
        status_layout = QtWidgets.QHBoxLayout(status_container); status_layout.setContentsMargins(16, 14, 16, 14)
        status_icon = QtWidgets.QLabel(); info_pixmap = self._create_icon_pixmap("info", 22, "#89b4fa"); status_icon.setPixmap(info_pixmap)
        self.status_label_main = QtWidgets.QLabel("Waiting for face detection..."); self.status_label_main.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: 500;")
        status_layout.addWidget(status_icon); status_layout.addWidget(self.status_label_main, 1)
        button_container = QtWidgets.QWidget(); button_layout = QtWidgets.QHBoxLayout(button_container); button_layout.setContentsMargins(0, 0, 0, 0); button_layout.setSpacing(20)
        self.record_button = QtWidgets.QPushButton(" Start Recording"); self.record_button.setIcon(self._create_icon_from_name("media-record")); self.record_button.clicked.connect(self.toggle_recording)
        self.export_button = QtWidgets.QPushButton(" Export Data"); self.export_button.setIcon(self._create_icon_from_name("document-save")); self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.record_button); button_layout.addWidget(self.export_button)
        stats_container = QtWidgets.QWidget(); stats_container.setStyleSheet("background-color: #313244; border-radius: 10px;"); stats_layout = QtWidgets.QHBoxLayout(stats_container)
        session_stats = QtWidgets.QVBoxLayout(); session_label = QtWidgets.QLabel("Session"); session_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.session_time = QtWidgets.QLabel("00:00"); self.session_time.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        session_stats.addWidget(session_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); session_stats.addWidget(self.session_time, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        datapoints_stats = QtWidgets.QVBoxLayout(); datapoints_label = QtWidgets.QLabel("Data Points"); datapoints_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.datapoints_count = QtWidgets.QLabel("0"); self.datapoints_count.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        datapoints_stats.addWidget(datapoints_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); datapoints_stats.addWidget(self.datapoints_count, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        avg_hr_stats = QtWidgets.QVBoxLayout(); avg_hr_label = QtWidgets.QLabel("Avg HR"); avg_hr_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.avg_hr = QtWidgets.QLabel("--"); self.avg_hr.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        avg_hr_stats.addWidget(avg_hr_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); avg_hr_stats.addWidget(self.avg_hr, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        stats_layout.addLayout(session_stats); stats_layout.addLayout(datapoints_stats); stats_layout.addLayout(avg_hr_stats)
        right_panel.addLayout(header_layout); right_panel.addWidget(description); right_panel.addWidget(self.hr_display); right_panel.addWidget(status_container); right_panel.addWidget(button_container); right_panel.addWidget(stats_container); right_panel.addStretch()
        top_section.addLayout(left_panel, 3); top_section.addWidget(right_panel_container, 2)
        graph_container = QtWidgets.QWidget(); graph_container.setObjectName("graphContainer"); graph_container.setStyleSheet("#graphContainer { background-color: #181825; border-radius: 16px; border: 1px solid #313244; }")
        graph_section = QtWidgets.QVBoxLayout(graph_container); graph_section.setContentsMargins(24, 24, 24, 24); graph_section.setSpacing(20)
        graph_header = QtWidgets.QHBoxLayout(); chart_icon = QtWidgets.QLabel(); chart_pixmap = self._create_icon_pixmap("chart", 22, "#f38ba8"); chart_icon.setPixmap(chart_pixmap)
        graph_title = QtWidgets.QLabel("Heart Rate History"); graph_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f5c2e7;")
        graph_header.addWidget(chart_icon); graph_header.addWidget(graph_title); graph_header.addStretch()
        time_range_label = QtWidgets.QLabel("Time Range:"); time_range_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        self.time_range_combo = QtWidgets.QComboBox(); self.time_range_combo.addItem("Last 1 minute", 60); self.time_range_combo.addItem("Last 3 minutes", 180); self.time_range_combo.addItem("Last 5 minutes", 300)
        self.time_range_combo.setCurrentIndex(1); self.time_range_combo.setFixedWidth(150); self.time_range_combo.setStyleSheet("background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 6px 8px; font-size: 13px; color: #cdd6f4;")
        self.time_range_combo.currentIndexChanged.connect(self.update_time_range)
        graph_header.addWidget(time_range_label); graph_header.addWidget(self.time_range_combo)
        self.hr_graph = HeartRateGraph(); self.hr_graph.setMinimumHeight(220)
        graph_section.addLayout(graph_header); graph_section.addWidget(self.hr_graph)
        main_layout.addLayout(top_section, 3); main_layout.addWidget(graph_container, 1)
        main_widget.setLayout(main_layout); self.setCentralWidget(main_widget)
        self._setup_toolbar(); self.statusBar().showMessage("Ready - Waiting for camera initialization")
        self.session_timer = QtCore.QTimer(); self.session_timer.timeout.connect(self._update_session_time); self.session_start_time = time.time(); self.session_timer.start(1000)
        for widget in [self.video_container, right_panel_container, graph_container, face_status_container]:
            shadow = QtWidgets.QGraphicsDropShadowEffect(); shadow.setBlurRadius(20); shadow.setColor(QtGui.QColor(0, 0, 0, 45)); shadow.setOffset(0, 4); widget.setGraphicsEffect(shadow)

    # --- FUNGSI BARU UNTUK SETUP THREAD ---
    def init_threads_and_queues(self):
        print("Initializing Queues and Signals...")
        self.frame_queue = queue.Queue(maxsize=5)
        self.signal_queue = queue.Queue(maxsize=100)
        self.display_queue = queue.Queue(maxsize=5)
        self.signals = GlobalSignals()

        print("Initializing Threads...")
        self.capture_thread = CaptureThread(self.camera_index, self.frame_queue)
        self.process_thread = ProcessThread(self.frame_queue, self.signal_queue, self.display_queue, self.signals)
        self.analysis_thread = AnalysisThread(self.signal_queue, self.signals)

        print("Starting Threads...")
        self.capture_thread.start()
        self.process_thread.start()
        self.analysis_thread.start()
        self.statusBar().showMessage("Threads running...")

    def connect_signals_to_slots(self):
        print("Connecting signals...")
        self.signals.hr_update.connect(self.update_heart_rate_slot) 
        self.signals.face_detected.connect(self.update_face_status_slot)
        self.signals.signal_quality_update.connect(self.update_signal_quality_slot)

    def init_video_timer(self):
        print("Initializing video timer...")
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_frame_slot)
        self.video_timer.start(33) # ~30 FPS

    # --- HAPUS FUNGSI setup_video LAMA ---
    # def setup_video(self):
    #     ... (HAPUS INI) ...

    # --- FUNGSI SLOT BARU ---
    def update_frame_slot(self):
        try:
            frame = self.display_queue.get_nowait()
            qt_img = self.convert_cv_to_qt(frame)
            self.video_label.setPixmap(qt_img)
            self.display_queue.task_done()
        except queue.Empty:
            pass

    def update_heart_rate_slot(self, hr, is_valid, confidence):
        """Update heart rate value and graph using new data."""
        self._current_hr = hr
        self._hr_valid = is_valid
        self._confidence = confidence # Simpan confidence jika perlu
        
        # Panggil fungsi lama untuk update UI (tapi dengan data baru)
        self._do_heart_rate_update() 

    def update_face_status_slot(self, detected):
        """Update face status using new signal."""
        # Panggil fungsi lama untuk update UI
        self.update_face_status(detected)

    def update_signal_quality_slot(self, quality):
        """Update signal quality using new signal."""
        # Panggil fungsi lama untuk update UI
        self.update_signal_quality(quality)

    # --- FUNGSI UPDATE UI LAMA (Beberapa mungkin perlu sedikit adaptasi) ---
    def update_frame(self, frame): # JANGAN Panggil ini langsung dari thread
        qt_img = self.convert_cv_to_qt(frame)
        self.video_label.setPixmap(qt_img)
        
    def update_heart_rate(self, hr, is_valid): # JANGAN Panggil ini langsung dari thread
        self._current_hr = hr; self._hr_valid = is_valid
        QtCore.QTimer.singleShot(0, self._do_heart_rate_update)

    def _do_heart_rate_update(self):
        if not hasattr(self, '_current_hr'): return
        hr = self._current_hr; is_valid = self._hr_valid
        if is_valid:
            self.hr_display.set_heart_rate(hr)
            hr_color = get_heart_rate_color(hr)
            self.hr_display.set_color(hr_color)
            if hr < 60: status_text = f"Low: {hr:.1f} BPM"; self.status_label_main.setStyleSheet("color: #fab387; font-weight: bold;")
            elif hr > 100: status_text = f"High: {hr:.1f} BPM"; self.status_label_main.setStyleSheet("color: #f38ba8; font-weight: bold;")
            else: status_text = f"Normal: {hr:.1f} BPM"; self.status_label_main.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.status_label_main.setText(status_text)
            if self.is_recording:
                current_time = time.time()
                self.recorded_data.append((current_time, hr))
            current_time = time.time()
            self.hr_data.append(hr); self.hr_timestamps.append(current_time)
            if len(self.hr_data) > self.max_data_points: self.hr_data.pop(0); self.hr_timestamps.pop(0)
            if len(self.hr_data) > 1: self.hr_graph.update_graph(self.hr_data, self.hr_timestamps)
        else:
            self.status_label_main.setText("Calculating..."); self.status_label_main.setStyleSheet("color: #cdd6f4;")
    
    def convert_cv_to_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        return pixmap
    
    # --- UBAH closeEvent ---
    def closeEvent(self, event):
        print("Closing application, stopping threads...")
        self.video_timer.stop() 

        self.capture_thread.stop()
        self.process_thread.stop()
        self.analysis_thread.stop()

        self.capture_thread.join(timeout=2)
        self.process_thread.join(timeout=2)
        self.analysis_thread.join(timeout=2)

        self.audio_manager.stop_all_sounds() 
        if self.is_recording and hasattr(self, 'recorded_data') and len(self.recorded_data) > 0:
            reply = QtWidgets.QMessageBox.question(self, 'Save Data', 
                'Would you like to save the recorded heart rate data before exiting?',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes: self.export_data()
        
        print("Closing accepted.")
        event.accept()

    def _setup_toolbar(self):
        toolbar = QtWidgets.QToolBar(); toolbar.setIconSize(QtCore.QSize(24, 24))
        toolbar.setStyleSheet("QToolBar { spacing: 12px; padding: 6px; background-color: #181825; border-bottom: 1px solid #313244; } QToolButton { border-radius: 6px; padding: 6px; } QToolButton:hover { background-color: #313244; } QToolButton:pressed { background-color: #45475a; }")
        self.addToolBar(toolbar)
        title_label = QtWidgets.QLabel("   rPPG Monitor"); title_label.setStyleSheet("font-weight: bold; color: #f5c2e7; font-size: 15px;"); toolbar.addWidget(title_label)
        spacer = QtWidgets.QWidget(); spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred); toolbar.addWidget(spacer)
        self.mute_button = QtWidgets.QToolButton(); self._update_mute_button_icon(); self.mute_button.setToolTip("Toggle alarm sound (currently ON)"); self.mute_button.clicked.connect(self.toggle_mute_sound); toolbar.addWidget(self.mute_button)
        settings_button = QtWidgets.QToolButton(); settings_button.setIcon(self._create_icon_from_name("preferences-system")); settings_button.setToolTip("Settings"); settings_button.clicked.connect(self.show_settings); toolbar.addWidget(settings_button)
        clear_button = QtWidgets.QToolButton(); clear_button.setIcon(self._create_icon_from_name("edit-clear-all")); clear_button.setToolTip("Clear Graph Data"); clear_button.clicked.connect(self.clear_graph_data); toolbar.addWidget(clear_button)

    def toggle_mute_sound(self):
        self.audio_manager.toggle_mute(); self._update_mute_button_icon()
        self.statusBar().showMessage("Alarm sound " + ("muted." if self.audio_manager.is_muted else "unmuted."))

    def _update_mute_button_icon(self):
        icon_name = "audio-volume-muted" if self.audio_manager.is_muted else "audio-volume-high"
        tooltip = "Toggle alarm sound (currently " + ("OFF" if self.audio_manager.is_muted else "ON") + ")"
        self.mute_button.setIcon(self._create_icon_from_name(icon_name)); self.mute_button.setToolTip(tooltip)

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.setText(" Stop Recording"); self.record_button.setIcon(self._create_icon_from_name("media-playback-stop"))
            self.recorded_data = []; self.statusBar().showMessage("Recording started")
        else:
            self.record_button.setText(" Start Recording"); self.record_button.setIcon(self._create_icon_from_name("media-record"))
            self.statusBar().showMessage(f"Recording stopped. {len(self.recorded_data)} data points recorded.")
    
    def export_data(self):
        if not self.recorded_data:
            QtWidgets.QMessageBox.warning(self, 'No Data', 'No data available to export. Start recording first.')
            return
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Heart Rate Data', f'heart_rate_data_{current_date}.csv', 'CSV Files (*.csv)')
        if not file_path: return
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile); writer.writerow(['Timestamp', 'DateTime', 'HeartRate'])
                for time_val, hr in self.recorded_data:
                    dt_str = datetime.fromtimestamp(time_val).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    writer.writerow([time_val, dt_str, hr])
            QtWidgets.QMessageBox.information(self, 'Export Successful', f'Data successfully exported to:\n{file_path}')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Export Error', f'An error occurred during export:\n{str(e)}')

    def clear_graph_data(self):
        reply = QMessageBox.question(self, "Clear Data", "Are you sure you want to clear all graph data?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.hr_data = []; self.hr_timestamps = []; self.hr_graph.clear_graph()
            self.statusBar().showMessage("Graph data cleared")

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            settings = dialog.get_settings()
            # TODO: Implement passing settings to the new threads (needs Queues/Signals)
            # self.process_thread.set_settings(settings) # Contoh, perlu implementasi
            # self.analysis_thread.set_settings(settings) # Contoh, perlu implementasi
            self.hr_graph.set_y_range(settings['min_hr'] - 10, settings['max_hr'] + 10)
            index = self.time_range_combo.findData(settings['graph_range'])
            if index >= 0: self.time_range_combo.setCurrentIndex(index)
            self.statusBar().showMessage("Settings updated (Thread settings TODO)")

    def update_face_status(self, face_detected):
        if face_detected:
            self.face_status.setText("Face detected"); self.face_status.setStyleSheet("color: #a6e3a1; font-weight: bold; padding: 4px;")
            self.set_face_status_icon(True)
        else:
            self.face_status.setText("No face detected"); self.face_status.setStyleSheet("color: #fab387; font-weight: bold; padding: 4px;")
            self.set_face_status_icon(False)

    def set_face_status_icon(self, detected):
        pixmap = self._create_icon_pixmap("face", 18, "#a6e3a1" if detected else "#fab387")
        self.face_status_icon.setPixmap(pixmap)
    
    def update_signal_quality(self, quality):
        # Langsung update, karena ProgressCircleWidget sederhana
        self.signal_quality.setValue(int(quality))
    
    def update_time_range(self, index):
        time_range = self.time_range_combo.currentData(); self.max_data_points = time_range
        while len(self.hr_data) > self.max_data_points:
            self.hr_data.pop(0); self.hr_timestamps.pop(0)
        if len(self.hr_data) > 1: self.hr_graph.update_graph(self.hr_data, self.hr_timestamps)
    
    def _create_heart_pixmap(self, size, color="#E91E63"):
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        path = QtGui.QPainterPath(); path.moveTo(size/2, size/5)
        path.cubicTo(size/2, size/10, 0, size/10, 0, size/2.5)
        path.cubicTo(0, size, size/2, size, size/2, size/1.25)
        path.cubicTo(size/2, size, size, size, size, size/2.5)
        path.cubicTo(size, size/10, size/2, size/10, size/2, size/5)
        painter.setPen(QtCore.Qt.PenStyle.NoPen); painter.setBrush(QtGui.QColor(color)); painter.drawPath(path); painter.end()
        return pixmap
    
    def _create_heart_icon(self): return QtGui.QIcon(self._create_heart_pixmap(64))
    
    def _create_icon_pixmap(self, icon_type, size=16, color="#cdd6f4"): # Changed color to whiteish
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(color), 1.5)) # Use pen for outlines
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        if icon_type == "face": painter.drawEllipse(1, 1, size-2, size-2); painter.drawEllipse(int(size/3 - 1), int(size/3), 2, 2); painter.drawEllipse(int(2*size/3 - 1), int(size/3), 2, 2); painter.drawArc(int(size/3), int(size/2), int(size/3), int(size/3), 0, -180*16)
        elif icon_type == "info": painter.drawEllipse(1, 1, size-2, size-2); painter.drawLine(int(size/2), int(size/4), int(size/2), int(2*size/3)); painter.drawPoint(int(size/2), int(5*size/6))
        elif icon_type == "chart": painter.drawLine(1, size-1, 1, int(size/3)); painter.drawLine(1, int(size/3), int(size/3), int(size/2)); painter.drawLine(int(size/3), int(size/2), int(2*size/3), int(size/4)); painter.drawLine(int(2*size/3), int(size/4), size-1, int(size/2)); painter.drawLine(1, size-1, size-1, size-1)
        else: painter.drawRect(1, 1, size-2, size-2) # Fallback square
        painter.end()
        return pixmap

    def _create_icon_from_name(self, icon_name):
        # Coba pakai ikon standar Qt
        try:
            icon_map = {
                "media-record": QtWidgets.QStyle.StandardPixmap.SP_DialogYesButton, # Kurang pas, tapi ada
                "document-save": QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
                "media-playback-stop": QtWidgets.QStyle.StandardPixmap.SP_MediaStop,
                "audio-volume-muted": QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted,
                "audio-volume-high": QtWidgets.QStyle.StandardPixmap.SP_MediaVolume,
                "preferences-system": QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon, # Kurang pas
                "edit-clear-all": QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton, # Kurang pas
                "zoom-out": QtWidgets.QStyle.StandardPixmap.SP_ArrowLeft, # Kurang pas
                "zoom-in": QtWidgets.QStyle.StandardPixmap.SP_ArrowRight, # Kurang pas
            }
            std_icon = icon_map.get(icon_name, QtWidgets.QStyle.StandardPixmap.SP_CustomBase)
            icon = self.style().standardIcon(std_icon)
            if not icon.isNull(): return icon
        except Exception:
             pass # Abaikan jika ikon standar tidak ada / error
        
        # Fallback ke _create_icon_pixmap jika ikon standar tidak ada
        return QtGui.QIcon(self._create_icon_pixmap(icon_name))

    def _update_session_time(self):
        elapsed_seconds = int(time.time() - self.session_start_time)
        minutes = elapsed_seconds // 60; seconds = elapsed_seconds % 60
        self.session_time.setText(f"{minutes:02}:{seconds:02}")
        self.datapoints_count.setText(f"{len(self.hr_data)}")
        if self.hr_data:
            avg = sum(self.hr_data) / len(self.hr_data)
            self.avg_hr.setText(f"{avg:.1f}"); self._update_avg_hr_style(avg)
        else: self.avg_hr.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")

    def _update_avg_hr_style(self, avg_hr_value):
        if avg_hr_value < 60: self.avg_hr.setStyleSheet("color: #fab387; font-size: 18px; font-weight: bold;")
        elif avg_hr_value > 100: self.avg_hr.setStyleSheet("color: #f38ba8; font-size: 18px; font-weight: bold;")
        else: self.avg_hr.setStyleSheet("color: #a6e3a1; font-size: 18px; font-weight: bold;")

# =============================================================================
# 7. Main Execution Block
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # --- PENTING: Pindahkan thread classes KE ATAS sebelum MainWindow ---
    # ... (Pastikan semua kelas thread sudah didefinisikan di atas) ...
    window = MainWindow(camera_index=0) 
    window.show()
    sys.exit(app.exec())