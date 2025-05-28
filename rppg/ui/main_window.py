# rppg/ui/main_window.py
import sys
import cv2
# import mediapipe as mp # Tidak perlu di sini lagi, sudah di ProcessThread
import threading # Tidak perlu di sini lagi
import time
import numpy as np
import queue # Perlu untuk Exception Empty
import csv
import os
from datetime import datetime

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout,
    QFrame, QToolBar, QPushButton, QToolButton, QComboBox, QDialog,
    QFileDialog, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter, QColor, QFont, QPainterPath
from PyQt6.QtCore import QTimer, Qt, QSize # QObject, pyqtSignal tidak perlu di sini

# Import dari package rppg sendiri
from rppg.threads.rppg_threads import CaptureThread, ProcessThread, AnalysisThread, GlobalSignals
from rppg.core.sound import AudioManager # Pastikan rppg.core.sound ada
from rppg.ui.components import HeartRateDisplay, HeartRateGraph, ProgressCircleWidget # Placeholder
from rppg.ui.settings_dialog import SettingsDialog # Placeholder
from rppg.ui.styles import get_heart_rate_color # Placeholder, sesuaikan

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.hr_data = []
        self.hr_timestamps = []
        self.max_data_points = 180 
        self.audio_manager = AudioManager(self) 
        self.is_muted = self.audio_manager.is_muted
        self.is_recording = False
        self.recorded_data = []
        
        self.initUI() 
        self.init_threads_and_queues()
        self.connect_signals_to_slots()
        self.init_video_timer()

    def initUI(self):
        # ... (Salin SELURUH isi fungsi initUI dari kode coba_multi_thread.py ke sini) ...
        # ... Pastikan Placeholder UI components seperti HeartRateDisplay di-import dengan benar ...
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
            QComboBox:hover { border-color: #45475a; background-color: #45475a; }
        """)
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget) # Set central widget dulu
        main_layout = QtWidgets.QVBoxLayout(main_widget) # Baru buat layout untuk central widget
        main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(30)
        top_section = QtWidgets.QHBoxLayout(); top_section.setSpacing(30)
        left_panel = QtWidgets.QVBoxLayout(); left_panel.setSpacing(20)
        self.video_container = QtWidgets.QWidget(); self.video_container.setObjectName("videoContainer")
        self.video_container.setStyleSheet("#videoContainer { background-color: #181825; border-radius: 16px; border: 1px solid #313244; }")
        video_layout = QtWidgets.QVBoxLayout(self.video_container); video_layout.setContentsMargins(3, 3, 3, 3)
        self.video_label = QtWidgets.QLabel(); self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(480, 360) 
        self.video_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.video_label.setStyleSheet("border-radius: 14px;")
        placeholder = QtGui.QPixmap(480, 360); placeholder.fill(QtGui.QColor("#1a1b26"))
        placeholder_painter = QtGui.QPainter(placeholder); placeholder_painter.setPen(QtGui.QColor("#6c7086")); placeholder_painter.setFont(QtGui.QFont("Segoe UI", 14))
        placeholder_painter.drawText(placeholder.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Menghubungkan ke kamera..."); placeholder_painter.end()
        self.video_label.setPixmap(placeholder); video_layout.addWidget(self.video_label)
        face_status_container = QtWidgets.QWidget(); face_status_container.setStyleSheet("background-color: #181825; border-radius: 10px; border: 1px solid #313244;")
        face_status_layout = QtWidgets.QHBoxLayout(face_status_container); face_status_layout.setContentsMargins(16, 12, 16, 12); face_status_layout.setSpacing(14)
        self.face_status_icon = QtWidgets.QLabel(); self.face_status_icon.setFixedSize(22, 22); self.set_face_status_icon(False)
        self.face_status = QtWidgets.QLabel("Tidak ada wajah terdeteksi"); self.face_status.setStyleSheet("color: #fab387; font-weight: bold; font-size: 14px;") # Ganti nama variabel status
        status_separator = QtWidgets.QFrame(); status_separator.setFrameShape(QtWidgets.QFrame.Shape.VLine); status_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken); status_separator.setStyleSheet("color: #313244;")
        quality_label = QtWidgets.QLabel("Kualitas Sinyal:"); quality_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        self.signal_quality_widget = ProgressCircleWidget(); self.signal_quality_widget.setValue(0) # Ganti nama variabel
        face_status_layout.addWidget(self.face_status_icon); face_status_layout.addWidget(self.face_status); face_status_layout.addStretch()
        face_status_layout.addWidget(status_separator); face_status_layout.addWidget(quality_label); face_status_layout.addWidget(self.signal_quality_widget)
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
        self.hr_display = HeartRateDisplay(); self.hr_display.set_color("#a6e3a1")
        status_container_main = QtWidgets.QWidget(); status_container_main.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 4px;") # Ganti nama
        status_layout_main = QtWidgets.QHBoxLayout(status_container_main); status_layout_main.setContentsMargins(16, 14, 16, 14) # Ganti nama
        status_icon_main = QtWidgets.QLabel(); info_pixmap = self._create_icon_pixmap("info", 22, "#89b4fa"); status_icon_main.setPixmap(info_pixmap) # Ganti nama
        self.status_label_main = QtWidgets.QLabel("Menunggu deteksi wajah..."); self.status_label_main.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: 500;")
        status_layout_main.addWidget(status_icon_main); status_layout_main.addWidget(self.status_label_main, 1) # Ganti nama
        button_container = QtWidgets.QWidget(); button_layout = QtWidgets.QHBoxLayout(button_container); button_layout.setContentsMargins(0, 0, 0, 0); button_layout.setSpacing(20)
        self.record_button = QtWidgets.QPushButton(" Mulai Rekam"); self.record_button.setIcon(self._create_icon_from_name("media-record")); self.record_button.clicked.connect(self.toggle_recording)
        self.export_button = QtWidgets.QPushButton(" Ekspor Data"); self.export_button.setIcon(self._create_icon_from_name("document-save")); self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.record_button); button_layout.addWidget(self.export_button)
        stats_container = QtWidgets.QWidget(); stats_container.setStyleSheet("background-color: #313244; border-radius: 10px;"); stats_layout = QtWidgets.QHBoxLayout(stats_container)
        session_stats = QtWidgets.QVBoxLayout(); session_label = QtWidgets.QLabel("Sesi"); session_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.session_time_label = QtWidgets.QLabel("00:00"); self.session_time_label.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;") # Ganti nama
        session_stats.addWidget(session_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); session_stats.addWidget(self.session_time_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        datapoints_stats = QtWidgets.QVBoxLayout(); datapoints_label = QtWidgets.QLabel("Data Poin"); datapoints_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.datapoints_count_label = QtWidgets.QLabel("0"); self.datapoints_count_label.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;") # Ganti nama
        datapoints_stats.addWidget(datapoints_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); datapoints_stats.addWidget(self.datapoints_count_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        avg_hr_stats = QtWidgets.QVBoxLayout(); avg_hr_label = QtWidgets.QLabel("Rata2 HR"); avg_hr_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 13px;")
        self.avg_hr_label = QtWidgets.QLabel("--"); self.avg_hr_label.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;") # Ganti nama
        avg_hr_stats.addWidget(avg_hr_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); avg_hr_stats.addWidget(self.avg_hr_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        stats_layout.addLayout(session_stats); stats_layout.addLayout(datapoints_stats); stats_layout.addLayout(avg_hr_stats)
        right_panel.addLayout(header_layout); right_panel.addWidget(description); right_panel.addWidget(self.hr_display); right_panel.addWidget(status_container_main); right_panel.addWidget(button_container); right_panel.addWidget(stats_container); right_panel.addStretch()
        top_section.addLayout(left_panel, 3); top_section.addWidget(right_panel_container, 2)
        graph_container = QtWidgets.QWidget(); graph_container.setObjectName("graphContainer"); graph_container.setStyleSheet("#graphContainer { background-color: #181825; border-radius: 16px; border: 1px solid #313244; }")
        graph_section = QtWidgets.QVBoxLayout(graph_container); graph_section.setContentsMargins(24, 24, 24, 24); graph_section.setSpacing(20)
        graph_header = QtWidgets.QHBoxLayout(); chart_icon = QtWidgets.QLabel(); chart_pixmap = self._create_icon_pixmap("chart", 22, "#f38ba8"); chart_icon.setPixmap(chart_pixmap)
        graph_title = QtWidgets.QLabel("Riwayat Detak Jantung"); graph_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f5c2e7;")
        graph_header.addWidget(chart_icon); graph_header.addWidget(graph_title); graph_header.addStretch()
        time_range_label = QtWidgets.QLabel("Rentang Waktu:"); time_range_label.setStyleSheet("color: #a6adc8; font-size: 14px;")
        self.time_range_combo = QtWidgets.QComboBox(); self.time_range_combo.addItem("1 Menit Terakhir", 60); self.time_range_combo.addItem("3 Menit Terakhir", 180); self.time_range_combo.addItem("5 Menit Terakhir", 300)
        self.time_range_combo.setCurrentIndex(1); self.time_range_combo.setFixedWidth(150); self.time_range_combo.setStyleSheet("background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 6px 8px; font-size: 13px; color: #cdd6f4;")
        self.time_range_combo.currentIndexChanged.connect(self.update_time_range)
        graph_header.addWidget(time_range_label); graph_header.addWidget(self.time_range_combo)
        self.hr_graph = HeartRateGraph(); self.hr_graph.setMinimumHeight(220)
        graph_section.addLayout(graph_header); graph_section.addWidget(self.hr_graph)
        main_layout.addLayout(top_section, 3); main_layout.addWidget(graph_container, 1)
        self._setup_toolbar(); self.statusBar().showMessage("Siap - Menunggu inisialisasi kamera")
        self.session_timer = QtCore.QTimer(); self.session_timer.timeout.connect(self._update_session_time); self.session_start_time = time.time(); self.session_timer.start(1000)
        for widget in [self.video_container, right_panel_container, graph_container, face_status_container]:
            shadow = QtWidgets.QGraphicsDropShadowEffect(); shadow.setBlurRadius(20); shadow.setColor(QtGui.QColor(0, 0, 0, 45)); shadow.setOffset(0, 4); widget.setGraphicsEffect(shadow)


    def init_threads_and_queues(self):
        # ... (Salin dari coba_multi_thread.py) ...
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
        self.statusBar().showMessage("Threads berjalan...")


    def connect_signals_to_slots(self):
        # ... (Salin dari coba_multi_thread.py) ...
        print("Connecting signals...")
        self.signals.hr_update.connect(self.update_heart_rate_slot) 
        self.signals.face_detected.connect(self.update_face_status_slot)
        self.signals.signal_quality_update.connect(self.update_signal_quality_slot)


    def init_video_timer(self):
        # ... (Salin dari coba_multi_thread.py) ...
        print("Initializing video timer...")
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_frame_slot)
        self.video_timer.start(33) 

    def update_frame_slot(self):
        # ... (Salin dari coba_multi_thread.py, sesuaikan self.video_label) ...
        try:
            frame = self.display_queue.get_nowait()
            qt_img = self.convert_cv_to_qt(frame)
            self.video_label.setPixmap(qt_img)
            self.display_queue.task_done()
        except queue.Empty:
            pass


    def update_heart_rate_slot(self, hr, is_valid, confidence):
        # ... (Logika dari _do_heart_rate_update lama, tapi pakai argumen baru) ...
        self._current_hr = hr
        self._hr_valid = is_valid
        # self._confidence = confidence # Simpan jika perlu
        
        # Panggil fungsi lama untuk update UI (tapi dengan data baru)
        # atau pindahkan logika _do_heart_rate_update ke sini langsung
        if not hasattr(self, '_current_hr'): return
        hr_val = self._current_hr; is_valid_val = self._hr_valid
        if is_valid_val:
            self.hr_display.set_heart_rate(hr_val)
            hr_color = get_heart_rate_color(hr_val) # Pastikan fungsi ini ada
            self.hr_display.set_color(hr_color)
            if hr_val < 60: status_text = f"Rendah: {hr_val:.1f} BPM"; self.status_label_main.setStyleSheet("color: #fab387; font-weight: bold;")
            elif hr_val > 100: status_text = f"Tinggi: {hr_val:.1f} BPM"; self.status_label_main.setStyleSheet("color: #f38ba8; font-weight: bold;")
            else: status_text = f"Normal: {hr_val:.1f} BPM"; self.status_label_main.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.status_label_main.setText(status_text) # Ganti self.status_label
            
            # Logika Alarm (dari _do_heart_rate_update lama)
            if (hr_val < 60 or hr_val > 100) and not self.audio_manager.is_muted and not self.audio_manager.is_playing('alarm'):
                self.audio_manager.play_sound('alarm', loop=True)
            elif 60 <= hr_val <= 100:
                self.audio_manager.stop_sound('alarm')

            if self.is_recording:
                current_time_ts = time.time()
                self.recorded_data.append((current_time_ts, hr_val))
            current_time_ts = time.time() # Timestamp untuk grafik
            self.hr_data.append(hr_val); self.hr_timestamps.append(current_time_ts)
            if len(self.hr_data) > self.max_data_points: self.hr_data.pop(0); self.hr_timestamps.pop(0)
            if len(self.hr_data) > 1: self.hr_graph.update_graph(self.hr_data, self.hr_timestamps)
        else:
            self.hr_display.set_heart_rate(0) # Atau "--"
            self.status_label_main.setText("Menghitung..."); self.status_label_main.setStyleSheet("color: #cdd6f4;")
            self.audio_manager.stop_sound('alarm')


    def update_face_status_slot(self, detected):
        # ... (Logika dari update_face_status lama) ...
        if detected:
            self.face_status.setText("Wajah terdeteksi")
            self.face_status.setStyleSheet("color: #a6e3a1; font-weight: bold; padding: 4px;")
            self.set_face_status_icon(True)
        else:
            self.face_status.setText("Tidak ada wajah terdeteksi")
            self.face_status.setStyleSheet("color: #fab387; font-weight: bold; padding: 4px;")
            self.set_face_status_icon(False)
    
    def update_signal_quality_slot(self, quality):
        # ... (Logika dari update_signal_quality lama) ...
        # self._signal_quality = quality # Tidak perlu simpan _signal_quality jika langsung update
        self.signal_quality_widget.setValue(int(quality)) # Ganti nama variabel

    def convert_cv_to_qt(self, cv_img):
        # ... (Salin dari coba_multi_thread.py) ...
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        return pixmap

    def closeEvent(self, event):
        # ... (Salin dari coba_multi_thread.py, pastikan semua 3 thread di stop) ...
        print("Closing application, stopping threads...")
        self.video_timer.stop() 

        if hasattr(self, 'capture_thread') and self.capture_thread.is_alive():
            self.capture_thread.stop()
            self.capture_thread.join(timeout=1)
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            self.process_thread.stop()
            self.process_thread.join(timeout=1)
        if hasattr(self, 'analysis_thread') and self.analysis_thread.is_alive():
            self.analysis_thread.stop()
            self.analysis_thread.join(timeout=1)

        self.audio_manager.stop_all_sounds() 
        if self.is_recording and hasattr(self, 'recorded_data') and len(self.recorded_data) > 0:
            reply = QtWidgets.QMessageBox.question(self, 'Save Data', 
                'Would you like to save the recorded heart rate data before exiting?',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes: self.export_data()
        
        print("Closing accepted.")
        event.accept()

    # --- Sisa fungsi (toggle_recording, export_data, dll.) bisa disalin dari kode MainWindow lamamu ---
    # --- Pastikan semua _create_icon_pixmap dan _create_icon_from_name juga ada ---
    def _setup_toolbar(self):
        # ... (Salin dari kode MainWindow lamamu) ...
        toolbar = QtWidgets.QToolBar(); toolbar.setIconSize(QtCore.QSize(24, 24))
        toolbar.setStyleSheet("QToolBar { spacing: 12px; padding: 6px; background-color: #181825; border-bottom: 1px solid #313244; } QToolButton { border-radius: 6px; padding: 6px; } QToolButton:hover { background-color: #313244; } QToolButton:pressed { background-color: #45475a; }")
        self.addToolBar(toolbar)
        title_label = QtWidgets.QLabel("   rPPG Monitor"); title_label.setStyleSheet("font-weight: bold; color: #f5c2e7; font-size: 15px;"); toolbar.addWidget(title_label)
        spacer = QtWidgets.QWidget(); spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred); toolbar.addWidget(spacer)
        self.mute_button = QtWidgets.QToolButton(); self._update_mute_button_icon(); self.mute_button.setToolTip("Toggle alarm sound"); self.mute_button.clicked.connect(self.toggle_mute_sound); toolbar.addWidget(self.mute_button)
        settings_button = QtWidgets.QToolButton(); settings_button.setIcon(self._create_icon_from_name("preferences-system")); settings_button.setToolTip("Settings"); settings_button.clicked.connect(self.show_settings); toolbar.addWidget(settings_button)
        clear_button = QtWidgets.QToolButton(); clear_button.setIcon(self._create_icon_from_name("edit-clear-all")); clear_button.setToolTip("Clear Graph Data"); clear_button.clicked.connect(self.clear_graph_data); toolbar.addWidget(clear_button)


    def toggle_mute_sound(self):
        # ... (Salin dari kode MainWindow lamamu) ...
        self.audio_manager.toggle_mute(); self._update_mute_button_icon()
        self.statusBar().showMessage("Alarm sound " + ("muted." if self.audio_manager.is_muted else "unmuted."))

    def _update_mute_button_icon(self):
        # ... (Salin dari kode MainWindow lamamu) ...
        icon_name = "audio-volume-muted" if self.audio_manager.is_muted else "audio-volume-high"
        tooltip = "Toggle alarm sound (currently " + ("OFF" if self.audio_manager.is_muted else "ON") + ")"
        self.mute_button.setIcon(self._create_icon_from_name(icon_name)); self.mute_button.setToolTip(tooltip)


    def toggle_recording(self):
        # ... (Salin dari kode MainWindow lamamu) ...
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.setText(" Stop Rekam"); self.record_button.setIcon(self._create_icon_from_name("media-playback-stop"))
            self.recorded_data = []; self.statusBar().showMessage("Perekaman dimulai")
        else:
            self.record_button.setText(" Mulai Rekam"); self.record_button.setIcon(self._create_icon_from_name("media-record"))
            self.statusBar().showMessage(f"Perekaman dihentikan. {len(self.recorded_data)} data poin direkam.")


    def export_data(self):
        # ... (Salin dari kode MainWindow lamamu) ...
        if not hasattr(self, 'recorded_data') or not self.recorded_data :
            QtWidgets.QMessageBox.warning(self, 'Tidak Ada Data', 'Tidak ada data untuk diekspor. Mulai rekam dulu.')
            return
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f'heart_rate_data_{current_date}.csv'
        # Coba dapatkan path Documents
        documents_path = QtGui.QStandardPaths.writableLocation(QtGui.QStandardPaths.StandardLocation.DocumentsLocation)
        default_path = os.path.join(documents_path, default_filename) if documents_path else default_filename

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Simpan Data Detak Jantung', default_path, 'CSV Files (*.csv)')
        if not file_path: return
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile); writer.writerow(['Timestamp', 'DateTime', 'HeartRate'])
                for time_val, hr in self.recorded_data:
                    dt_str = datetime.fromtimestamp(time_val).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    writer.writerow([time_val, dt_str, hr])
            QtWidgets.QMessageBox.information(self, 'Ekspor Berhasil', f'Data berhasil diekspor ke:\n{file_path}')
            self.statusBar().showMessage(f"Data diekspor ke {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error Ekspor', f'Terjadi error saat ekspor:\n{str(e)}')


    def clear_graph_data(self):
        # ... (Salin dari kode MainWindow lamamu, sesuaikan dengan nama QMessageBox jika perlu) ...
        reply = QMessageBox.question(self, "Hapus Data", "Apakah Anda yakin ingin menghapus semua data grafik?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No) # Default ke No
        if reply == QMessageBox.StandardButton.Yes:
            self.hr_data = []; self.hr_timestamps = []; self.hr_graph.clear_graph()
            self.statusBar().showMessage("Data grafik dihapus")


    def show_settings(self):
        # ... (Salin dari kode MainWindow lamamu) ...
        dialog = SettingsDialog(self) # Pastikan SettingsDialog diimport
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            settings = dialog.get_settings()
            # TODO: Implement passing settings to the new threads (needs Queues/Signals or direct method calls if safe)
            # Contoh:
            # if hasattr(self, 'process_thread'): self.process_thread.show_face_rect = settings.get('show_face_rect', True)
            # if hasattr(self, 'analysis_thread'): 
            #     self.analysis_thread.min_hr = settings.get('min_hr', 40)
            #     self.analysis_thread.max_hr = settings.get('max_hr', 180)
            #     self.analysis_thread.window_size = settings.get('window_size', 90)

            self.hr_graph.set_y_range(settings.get('min_hr', 40) - 10, settings.get('max_hr', 180) + 10)
            if hasattr(self, 'time_range_combo'): # Pastikan combo box ada
                index = self.time_range_combo.findData(settings.get('graph_range', 180))
                if index >= 0: self.time_range_combo.setCurrentIndex(index)
            self.statusBar().showMessage("Pengaturan diperbarui (Pengaturan thread TODO)")


    def update_face_status(self, face_detected): # Ini adalah fungsi lama, akan dipanggil oleh slot
        # ... (Salin dari kode MainWindow lamamu) ...
        if face_detected:
            self.face_status.setText("Wajah terdeteksi")
            self.face_status.setStyleSheet("color: #a6e3a1; font-weight: bold; padding: 4px;")
            self.set_face_status_icon(True)
        else:
            self.face_status.setText("Tidak ada wajah terdeteksi")
            self.face_status.setStyleSheet("color: #fab387; font-weight: bold; padding: 4px;")
            self.set_face_status_icon(False)


    def set_face_status_icon(self, detected):
        # ... (Salin dari kode MainWindow lamamu) ...
        pixmap = self._create_icon_pixmap("face", 18, "#a6e3a1" if detected else "#fab387")
        self.face_status_icon.setPixmap(pixmap)
    
    def update_signal_quality(self, quality): # Ini adalah fungsi lama, akan dipanggil oleh slot
        # ... (Salin dari kode MainWindow lamamu, sesuaikan nama variabel progress bar) ...
        self.signal_quality_widget.setValue(int(quality)) # Ganti nama progress bar jika beda


    def update_time_range(self, index):
        # ... (Salin dari kode MainWindow lamamu) ...
        time_range = self.time_range_combo.currentData(); self.max_data_points = time_range
        while len(self.hr_data) > self.max_data_points:
            self.hr_data.pop(0); self.hr_timestamps.pop(0)
        if len(self.hr_data) > 1: self.hr_graph.update_graph(self.hr_data, self.hr_timestamps)
    
    def _create_heart_pixmap(self, size, color="#E91E63"):
        # ... (Salin dari kode MainWindow lamamu) ...
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        path = QtGui.QPainterPath(); path.moveTo(size/2, size/5)
        path.cubicTo(size/2, size/10, 0, size/10, 0, size/2.5)
        path.cubicTo(0, size, size/2, size, size/2, size/1.25)
        path.cubicTo(size/2, size, size, size, size, size/2.5)
        path.cubicTo(size, size/10, size/2, size/10, size/2, size/5)
        painter.setPen(QtCore.Qt.PenStyle.NoPen); painter.setBrush(QtGui.QColor(color)); painter.drawPath(path); painter.end()
        return pixmap

    def _create_heart_icon(self): 
        # ... (Salin dari kode MainWindow lamamu) ...
        return QtGui.QIcon(self._create_heart_pixmap(64))
    
    def _create_icon_pixmap(self, icon_type, size=16, color="#cdd6f4"):
        # ... (Salin dari kode MainWindow lamamu) ...
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        # Pakai pen untuk outline, atau brush untuk fill
        painter.setPen(QtGui.QPen(QtGui.QColor(color), 1.5 if icon_type != "face" else 1)) 
        if icon_type == "face":
             painter.setBrush(QtGui.QColor(color)) # Fill face
             painter.drawEllipse(1, 1, size-2, size-2)
             painter.setPen(QtGui.QPen(QtGui.QColor(0,0,0,100), 1)) # Eyes/mouth color
             painter.drawEllipse(int(size/3 -1), int(size/3), 2, 2)
             painter.drawEllipse(int(2*size/3 -1), int(size/3), 2, 2)
             painter.drawArc(int(size/3), int(size/2), int(size/3), int(size/3), 0, -180*16)
        elif icon_type == "info": 
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(1, 1, size-2, size-2); 
            painter.drawLine(int(size/2), int(size/4), int(size/2), int(2*size/3)); 
            painter.drawPoint(int(size/2), int(5*size/6))
        elif icon_type == "chart": 
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawLine(1, size-1, 1, int(size/3)); painter.drawLine(1, int(size/3), int(size/3), int(size/2)); 
            painter.drawLine(int(size/3), int(size/2), int(2*size/3), int(size/4)); 
            painter.drawLine(int(2*size/3), int(size/4), size-1, int(size/2)); 
            painter.drawLine(1, size-1, size-1, size-1)
        else: 
            painter.setBrush(QtGui.QColor(color))
            painter.drawRect(1, 1, size-2, size-2) 
        painter.end()
        return pixmap


    def _create_icon_from_name(self, icon_name):
        # ... (Salin dari kode MainWindow lamamu) ...
        try:
            icon_map = {
                "media-record": QtWidgets.QStyle.StandardPixmap.SP_DialogYesButton, 
                "document-save": QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
                "media-playback-stop": QtWidgets.QStyle.StandardPixmap.SP_MediaStop,
                "audio-volume-muted": QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted,
                "audio-volume-high": QtWidgets.QStyle.StandardPixmap.SP_MediaVolume,
                "preferences-system": QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon, 
                "edit-clear-all": QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton, 
            }
            std_icon = icon_map.get(icon_name)
            if std_icon is not None:
                icon = self.style().standardIcon(std_icon)
                if not icon.isNull(): return icon
        except Exception as e:
            print(f"Error getting standard icon {icon_name}: {e}")
        
        return QtGui.QIcon(self._create_icon_pixmap(icon_name, color="#cdd6f4"))


    def _update_session_time(self):
        elapsed_seconds = int(time.time() - self.session_start_time)
        minutes = elapsed_seconds // 60; seconds = elapsed_seconds % 60
        self.session_time_label.setText(f"{minutes:02}:{seconds:02}") # Ganti nama
        self.datapoints_count_label.setText(f"{len(self.hr_data)}") # Ganti nama
        if self.hr_data:
            avg = sum(self.hr_data) / len(self.hr_data)
            self.avg_hr_label.setText(f"{avg:.1f}"); self._update_avg_hr_style(avg) # Ganti nama
        else: self.avg_hr_label.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")


    def _update_avg_hr_style(self, avg_hr_value):
        # ... (Salin dari kode MainWindow lamamu) ...
        if avg_hr_value < 60: self.avg_hr_label.setStyleSheet("color: #fab387; font-size: 18px; font-weight: bold;")
        elif avg_hr_value > 100: self.avg_hr_label.setStyleSheet("color: #f38ba8; font-size: 18px; font-weight: bold;")
        else: self.avg_hr_label.setStyleSheet("color: #a6e3a1; font-size: 18px; font-weight: bold;")