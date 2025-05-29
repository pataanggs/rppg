# rppg/ui/main_window.py
import sys
import cv2
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
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter, QColor, QFont, QPainterPath, QPen # QStandardPaths dihapus dari sini
from PyQt6.QtCore import QTimer, Qt, QSize, QStandardPaths # QStandardPaths ditambahkan di sini

# Import dari package rppg sendiri
from rppg.threads.rppg_threads import CaptureThread, ProcessThread, AnalysisThread, GlobalSignals
from rppg.core.sound import AudioManager # Diasumsikan ada dan benar
from rppg.ui.components import HeartRateDisplay, HeartRateGraph, ProgressCircleWidget # Diasumsikan ada dan benar
from rppg.ui.settings_dialog import SettingsDialog # Diasumsikan ada dan benar
from rppg.ui.styles import get_heart_rate_color # Diasumsikan ada dan benar (atau gunakan placeholder)

# Placeholder jika styles.py belum lengkap
class ColorsPlaceholder: HR_NORMAL = "#a6e3a1"; HR_LOW = "#fab387"; HR_HIGH = "#f38ba8"
if not callable(get_heart_rate_color): # Cek apakah get_heart_rate_color sudah fungsi
    print("Warning: Using placeholder for get_heart_rate_color")
    def get_heart_rate_color(hr_value):
        if hr_value == 0 : return "#cdd6f4" # Warna default jika 0
        if hr_value < 60: return ColorsPlaceholder.HR_LOW
        elif hr_value > 100: return ColorsPlaceholder.HR_HIGH
        return ColorsPlaceholder.HR_NORMAL


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.hr_data = []
        self.hr_timestamps = []
        self.max_data_points = 180  # Default 3 menit, akan diupdate oleh time_range_combo
        
        self.audio_manager = AudioManager(self) 
        self.is_muted = self.audio_manager.is_muted
        self.is_recording = False
        self.recorded_data = []  # Will store tuples of (timestamp, hr, resp)
        self.resp_data = []  # Add buffer for respiratory data
        
        self._current_hr = 0.0 # Untuk menyimpan HR terakhir dari slot
        self._hr_valid = False # Untuk menyimpan validitas HR terakhir
        self._signal_quality_value = 0 # Untuk menyimpan kualitas sinyal terakhir

        self.initUI() 
        self.init_threads_and_queues()
        self.connect_signals_to_slots()
        self.init_video_timer()

    def initUI(self):
        self.setWindowTitle("rPPG Heart Rate Monitor - Multi Thread")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(850, 650) # Ukuran minimum jendela
        self.setWindowIcon(self._create_heart_icon())
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #cdd6f4; font-family: 'Segoe UI', Arial, sans-serif; }
            QPushButton { background-color: #f38ba8; color: #1e1e2e; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; font-size: 13px; } /* Padding disesuaikan */
            QPushButton:hover { background-color: #f5c2e7; } QPushButton:pressed { background-color: #cba6f7; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
            QToolBar { background-color: #181825; border-bottom: 1px solid #313244; spacing: 10px; padding: 6px; } /* Spacing & padding disesuaikan */
            QToolButton { border: none; border-radius: 6px; padding: 7px; } QToolButton:hover { background-color: #313244; } /* Padding disesuaikan */
            QToolButton:pressed { background-color: #45475a; } QStatusBar { background-color: #181825; color: #a6adc8; border-top: 1px solid #313244; font-size: 12px; padding: 4px; }
            QComboBox { border: 1px solid #313244; border-radius: 6px; padding: 7px 12px; background-color: #313244; color: #cdd6f4; min-height: 22px; } /* Padding & min-height disesuaikan */
            QComboBox::drop-down { border: none; width: 20px; } /* Width dropdown */
            /* QComboBox::down-arrow { image: url(rppg/assets/down-arrow.png); width: 12px; height: 12px; } */ /* Sesuaikan path jika pakai custom arrow */
            QComboBox:hover { border-color: #45475a; background-color: #45475a; }
        """)
        
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15) 
        main_layout.setSpacing(15)

        top_section_widget = QtWidgets.QWidget()
        top_section_layout = QtWidgets.QHBoxLayout(top_section_widget)
        top_section_layout.setContentsMargins(0,0,0,0)
        top_section_layout.setSpacing(15)
        
        left_panel_widget = QtWidgets.QWidget()
        left_panel_layout = QtWidgets.QVBoxLayout(left_panel_widget)
        left_panel_layout.setContentsMargins(0,0,0,0)
        left_panel_layout.setSpacing(10)
        
        self.video_container = QtWidgets.QWidget()
        self.video_container.setObjectName("videoContainer")
        self.video_container.setStyleSheet("#videoContainer { background-color: #181825; border-radius: 12px; border: 1px solid #313244; }")
        video_layout = QtWidgets.QVBoxLayout(self.video_container); video_layout.setContentsMargins(3, 3, 3, 3)
        self.video_label = QtWidgets.QLabel()
        self.video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.video_label.setStyleSheet("border-radius: 10px; background-color: #000;")
        placeholder = QtGui.QPixmap(480, 360); placeholder.fill(QtGui.QColor("#1a1b26"))
        placeholder_painter = QtGui.QPainter(placeholder); placeholder_painter.setPen(QtGui.QColor("#6c7086")); placeholder_painter.setFont(QtGui.QFont("Segoe UI", 14))
        placeholder_painter.drawText(placeholder.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Menghubungkan ke kamera..."); placeholder_painter.end()
        self.video_label.setPixmap(placeholder); video_layout.addWidget(self.video_label)
        
        face_status_container = QtWidgets.QWidget(); face_status_container.setStyleSheet("background-color: #181825; border-radius: 10px; border: 1px solid #313244; padding: 6px;")
        face_status_layout = QtWidgets.QHBoxLayout(face_status_container); face_status_layout.setContentsMargins(10, 6, 10, 6); face_status_layout.setSpacing(8)
        self.face_status_icon = QtWidgets.QLabel(); self.face_status_icon.setFixedSize(18, 18); self.set_face_status_icon(False)
        self.face_status = QtWidgets.QLabel("Wajah: -"); self.face_status.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        status_separator = QtWidgets.QFrame(); status_separator.setFrameShape(QtWidgets.QFrame.Shape.VLine); status_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken); status_separator.setStyleSheet("color: #313244;")
        quality_label = QtWidgets.QLabel("Kualitas:"); quality_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        self.signal_quality_widget = ProgressCircleWidget(); self.signal_quality_widget.setValue(0)
        face_status_layout.addWidget(self.face_status_icon); face_status_layout.addWidget(self.face_status); face_status_layout.addStretch()
        face_status_layout.addWidget(status_separator); face_status_layout.addWidget(quality_label); face_status_layout.addWidget(self.signal_quality_widget)
        
        left_panel_layout.addWidget(self.video_container, 1); left_panel_layout.addWidget(face_status_container)
        left_panel_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        right_panel_container = QtWidgets.QWidget(); right_panel_container.setObjectName("rightPanel"); right_panel_container.setStyleSheet("#rightPanel { background-color: #181825; border-radius: 12px; border: 1px solid #313244; }")
        right_panel_container.setMinimumWidth(320); right_panel_container.setMaximumWidth(400) # Batasi lebar panel kanan
        right_panel_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        right_panel_layout = QtWidgets.QVBoxLayout(right_panel_container); right_panel_layout.setContentsMargins(15, 15, 15, 15); right_panel_layout.setSpacing(12)
        
        header_layout = QtWidgets.QHBoxLayout(); heart_logo_container = QtWidgets.QWidget(); heart_logo_container.setFixedSize(36, 36)
        heart_logo_layout = QtWidgets.QVBoxLayout(heart_logo_container); heart_logo_layout.setContentsMargins(0,0,0,0); self.heart_logo = QtWidgets.QLabel(); heart_pixmap = self._create_heart_pixmap(30, "#f38ba8"); self.heart_logo.setPixmap(heart_pixmap); self.heart_logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter); heart_logo_layout.addWidget(self.heart_logo)
        title_label = QtWidgets.QLabel("rPPG Monitor"); title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f5c2e7;")
        header_layout.addWidget(heart_logo_container); header_layout.addWidget(title_label); header_layout.addStretch()
        
        description = QtWidgets.QLabel("Analisis rPPG untuk mengukur detak jantung melalui kamera.")
        description.setStyleSheet("color: #a6adc8; font-size: 12px;"); description.setWordWrap(True); description.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.hr_display = HeartRateDisplay(); self.hr_display.set_color(ColorsPlaceholder.HR_NORMAL)
        
        status_container_main = QtWidgets.QWidget(); status_container_main.setStyleSheet("background-color: #313244; border-radius: 8px; padding: 6px;")
        status_layout_main = QtWidgets.QHBoxLayout(status_container_main); status_layout_main.setContentsMargins(10, 8, 10, 8)
        status_icon_main = QtWidgets.QLabel(); info_pixmap = self._create_icon_pixmap("info", 18, "#89b4fa"); status_icon_main.setPixmap(info_pixmap)
        self.status_label_main = QtWidgets.QLabel("Menunggu deteksi..."); self.status_label_main.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        status_layout_main.addWidget(status_icon_main); status_layout_main.addWidget(self.status_label_main, 1)
        
        button_container = QtWidgets.QWidget(); button_layout = QtWidgets.QHBoxLayout(button_container); button_layout.setContentsMargins(0,0,0,0); button_layout.setSpacing(10)
        self.record_button = QtWidgets.QPushButton(" Rekam"); self.record_button.setIcon(self._create_icon_from_name("media-record")); self.record_button.clicked.connect(self.toggle_recording)
        self.export_button = QtWidgets.QPushButton(" Ekspor"); self.export_button.setIcon(self._create_icon_from_name("document-save")); self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.record_button, 1); button_layout.addWidget(self.export_button, 1)
        
        stats_container = QtWidgets.QWidget(); stats_container.setStyleSheet("background-color: #313244; border-radius: 8px; padding:8px"); stats_layout = QtWidgets.QHBoxLayout(stats_container); stats_layout.setSpacing(8)
        def create_stat_vbox(label_text):
            vbox = QVBoxLayout(); lbl = QLabel(label_text); lbl.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl = QLabel("--"); val_lbl.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: bold;"); val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(lbl); vbox.addWidget(val_lbl); return vbox, val_lbl
        session_stats, self.session_time_label = create_stat_vbox("Sesi")
        datapoints_stats, self.datapoints_count_label = create_stat_vbox("Data")
        avg_hr_stats, self.avg_hr_label = create_stat_vbox("Rata2 HR")
        stats_layout.addLayout(session_stats,1); stats_layout.addLayout(datapoints_stats,1); stats_layout.addLayout(avg_hr_stats,1)
        
        right_panel_layout.addLayout(header_layout); right_panel_layout.addWidget(description); right_panel_layout.addWidget(self.hr_display)
        right_panel_layout.addWidget(status_container_main); right_panel_layout.addWidget(button_container); right_panel_layout.addWidget(stats_container)
        right_panel_layout.addStretch(1)
        
        top_section_layout.addWidget(left_panel_widget, 7) # Video panel lebih dominan
        top_section_layout.addWidget(right_panel_container, 3)

        graph_container = QtWidgets.QWidget(); graph_container.setObjectName("graphContainer"); graph_container.setStyleSheet("#graphContainer { background-color: #181825; border-radius: 12px; border: 1px solid #313244; }")
        graph_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding); graph_container.setMinimumHeight(220) # Pastikan tinggi minimal grafik
        graph_section_layout = QtWidgets.QVBoxLayout(graph_container); graph_section_layout.setContentsMargins(15, 15, 15, 15); graph_section_layout.setSpacing(10)
        graph_header = QtWidgets.QHBoxLayout(); chart_icon = QtWidgets.QLabel(); chart_pixmap = self._create_icon_pixmap("chart", 20, "#f38ba8"); chart_icon.setPixmap(chart_pixmap)
        graph_title = QtWidgets.QLabel("Riwayat Detak Jantung dan Respirasi"); graph_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f5c2e7;")
        graph_header.addWidget(chart_icon); graph_header.addWidget(graph_title); graph_header.addStretch()
        time_range_label = QtWidgets.QLabel("Rentang:"); time_range_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        self.time_range_combo = QtWidgets.QComboBox(); self.time_range_combo.addItem("1 Menit", 60); self.time_range_combo.addItem("3 Menit", 180); self.time_range_combo.addItem("5 Menit", 300)
        self.time_range_combo.setCurrentIndex(1); self.time_range_combo.setFixedWidth(120); self.time_range_combo.setStyleSheet("background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 5px 7px; font-size: 12px; color: #cdd6f4;")
        self.time_range_combo.currentIndexChanged.connect(self.update_time_range)
        graph_header.addWidget(time_range_label); graph_header.addWidget(self.time_range_combo)
        
        self.hr_graph = HeartRateGraph(dark_mode=True)
        self.hr_graph.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding); self.hr_graph.setMinimumHeight(250)
        
        graph_section_layout.addLayout(graph_header); graph_section_layout.addWidget(self.hr_graph, 1)
        
        main_layout.addWidget(top_section_widget, 5) # Bagian atas 60%
        main_layout.addWidget(graph_container, 5)  # Grafik 40%

        self._setup_toolbar(); self.statusBar().showMessage("Siap - Menunggu inisialisasi kamera")
        self.session_timer = QtCore.QTimer(); self.session_timer.timeout.connect(self._update_session_time); 
        # self.session_start_time = time.time(); # Pindahkan ke saat kamera aktif
        # self.session_timer.start(1000)
        
        # Pindahkan shadow effect ke akhir, setelah semua widget di-add
        # agar tidak ada warning parent
        shadow_widgets = [self.video_container, right_panel_container, graph_container, face_status_container, status_container_main, stats_container]
        for widget in shadow_widgets:
            if widget:
                shadow = QtWidgets.QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(15); shadow.setColor(QtGui.QColor(0,0,0,60)); shadow.setOffset(1,1)
                widget.setGraphicsEffect(shadow)
    
    # ... (SISA KODE MainWindow: init_threads_and_queues, connect_signals_to_slots, init_video_timer, slots, helpers, closeEvent) ...
    # ... SALIN DARI JAWABAN SAYA SEBELUMNYA YANG `main_app.py` atau `coba_multi_thread.py` ...
    # ... ATAU DARI KODE MainWindow YANG SUDAH KAMU PUNYA DAN SUDAH DIEDIT SESUAI INSTRUKSI ...

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
        self.statusBar().showMessage("Threads berjalan...")
        self.session_start_time = time.time() # Mulai timer sesi setelah thread jalan
        self.session_timer.start(1000)


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

    def update_frame_slot(self):
        try:
            frame = self.display_queue.get_nowait()
            qt_img = self.convert_cv_to_qt(frame)
            self.video_label.setPixmap(qt_img)
            # self.display_queue.task_done() # Tidak perlu task_done jika get_nowait
        except queue.Empty:
            pass


    def update_heart_rate_slot(self, hr, is_valid, confidence, resp_signal):
        """Update heart rate value and graph using new data."""
        self._current_hr = hr
        self._hr_valid = is_valid

        if is_valid:
            # Update HR display and other UI elements
            self.hr_display.set_heart_rate(hr)
            hr_color = get_heart_rate_color(hr) 
            self.hr_display.set_color(hr_color)
            
            status_text = ""
            if hr < 60: status_text = f"Rendah: {hr:.1f} BPM (Conf: {confidence:.2f})"; self.status_label_main.setStyleSheet("color: #fab387; font-weight: bold; font-size:12px;")
            elif hr > 100: status_text = f"Tinggi: {hr:.1f} BPM (Conf: {confidence:.2f})"; self.status_label_main.setStyleSheet("color: #f38ba8; font-weight: bold; font-size:12px;")
            else: status_text = f"Normal: {hr:.1f} BPM (Conf: {confidence:.2f})"; self.status_label_main.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size:12px;")
            self.status_label_main.setText(status_text)
            
            if (hr < 60 or hr > 100) and not self.audio_manager.is_muted and not self.audio_manager.is_playing('alarm'):
                self.audio_manager.play_sound('alarm', loop=True)
            elif 60 <= hr <= 100:
                self.audio_manager.stop_sound('alarm')

            if self.is_recording:
                current_time = time.time()
                # Store both HR and respiratory data
                resp_value = resp_signal[-1] if resp_signal is not None and len(resp_signal) > 0 else 0
                self.recorded_data.append((current_time, hr, resp_value))
            
            # Update the graph with both HR and respiratory data
            current_time = time.time()
            self.hr_data.append(hr)
            self.hr_timestamps.append(current_time)
            
            if len(self.hr_data) > self.max_data_points:
                self.hr_data.pop(0)
                self.hr_timestamps.pop(0)
            
            if len(self.hr_data) > 1:
                self.hr_graph.update_plot(
                    np.array(self.hr_timestamps),
                    np.array(self.hr_data),
                    resp_signal if resp_signal is not None else None
                )
        else:
            self.hr_display.set_heart_rate(0) 
            self.status_label_main.setText("Menghitung HR..."); self.status_label_main.setStyleSheet("color: #cdd6f4; font-size:12px;")
            self.audio_manager.stop_sound('alarm')


    def update_face_status_slot(self, detected):
        # Panggil fungsi update_face_status yang sudah ada
        self.update_face_status(detected) # Fungsi ini sudah ada di kodemu
    
    def update_signal_quality_slot(self, quality):
        # Panggil fungsi update_signal_quality yang sudah ada
        self.update_signal_quality(int(quality)) # Fungsi ini sudah ada di kodemu


    def convert_cv_to_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        return pixmap

    def closeEvent(self, event):
        print("Closing application, stopping threads...")
        if hasattr(self, 'video_timer'): self.video_timer.stop() 
        
        threads_to_stop = []
        if hasattr(self, 'capture_thread'): threads_to_stop.append(self.capture_thread)
        if hasattr(self, 'process_thread'): threads_to_stop.append(self.process_thread)
        if hasattr(self, 'analysis_thread'): threads_to_stop.append(self.analysis_thread)

        for thread in threads_to_stop:
            if thread.is_alive():
                thread.stop()
                # thread.join(timeout=1) # Join bisa nge-block UI jika thread lama berhenti

        # Beri waktu sedikit untuk thread stop sebelum join
        # time.sleep(0.5) 
        # for thread in threads_to_stop:
        #     if thread.is_alive():
        #         thread.join(timeout=0.5)


        if hasattr(self, 'audio_manager'): self.audio_manager.stop_all_sounds() 
        
        if self.is_recording and hasattr(self, 'recorded_data') and len(self.recorded_data) > 0:
            reply = QtWidgets.QMessageBox.question(self, 'Simpan Data', 
                'Anda ingin menyimpan data rekaman sebelum keluar?',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes) # Default Yes
            if reply == QtWidgets.QMessageBox.StandardButton.Yes: self.export_data()
        
        print("Closing accepted.")
        event.accept()

    def _setup_toolbar(self):
        toolbar = QtWidgets.QToolBar("Main Toolbar") 
        toolbar.setIconSize(QtCore.QSize(22, 22)) # Ukuran ikon sedikit lebih kecil
        # Stylesheet dipindahkan ke initUI global
        self.addToolBar(toolbar)
        
        title_label = QtWidgets.QLabel("  rPPG Monitor  "); title_label.setStyleSheet("font-weight: bold; color: #f5c2e7; font-size: 14px;")
        toolbar.addWidget(title_label)
        
        spacer = QtWidgets.QWidget(); spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        self.mute_button = QtWidgets.QToolButton(); self._update_mute_button_icon(); self.mute_button.setToolTip("Toggle Suara Alarm"); self.mute_button.clicked.connect(self.toggle_mute_sound)
        toolbar.addWidget(self.mute_button)
        
        settings_button = QtWidgets.QToolButton(); settings_button.setIcon(self._create_icon_from_name("preferences-system")); settings_button.setToolTip("Pengaturan"); settings_button.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_button)
        
        clear_button = QtWidgets.QToolButton(); clear_button.setIcon(self._create_icon_from_name("edit-clear-all")); clear_button.setToolTip("Hapus Data Grafik"); clear_button.clicked.connect(self.clear_graph_data)
        toolbar.addWidget(clear_button)

    def toggle_mute_sound(self):
        self.audio_manager.toggle_mute(); self._update_mute_button_icon()
        self.statusBar().showMessage("Suara alarm " + ("dimatikan." if self.audio_manager.is_muted else "dinyalakan."))

    def _update_mute_button_icon(self):
        icon_name = "audio-volume-muted" if self.audio_manager.is_muted else "audio-volume-high"
        tooltip = "Toggle Suara Alarm (Saat ini: " + ("MATI" if self.audio_manager.is_muted else "NYALA") + ")"
        self.mute_button.setIcon(self._create_icon_from_name(icon_name)); self.mute_button.setToolTip(tooltip)

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.setText(" Stop Rekam"); self.record_button.setIcon(self._create_icon_from_name("media-playback-stop"))
            self.recorded_data = []; self.statusBar().showMessage("Perekaman dimulai...")
        else:
            self.record_button.setText(" Mulai Rekam"); self.record_button.setIcon(self._create_icon_from_name("media-record"))
            self.statusBar().showMessage(f"Perekaman dihentikan. {len(self.recorded_data)} data poin direkam.")
    
    def export_data(self):
        if not self.recorded_data:
            QtWidgets.QMessageBox.warning(self, 'No Data', 'No data available to export. Start recording first.')
            return

        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 
            'Save Heart Rate & Respiratory Data', 
            f'vital_signs_data_{current_date}.csv', 
            'CSV Files (*.csv)'
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'DateTime', 'HeartRate', 'Respiration'])
                
                for time_val, hr, resp in self.recorded_data:
                    dt_str = datetime.fromtimestamp(time_val).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    writer.writerow([time_val, dt_str, hr, resp])
                    
            QtWidgets.QMessageBox.information(
                self, 
                'Export Successful', 
                f'Data successfully exported to:\n{file_path}'
            )
            self.statusBar().showMessage(f"Data exported to {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                'Export Error', 
                f'An error occurred during export:\n{str(e)}'
            )

    def clear_graph_data(self):
        reply = QMessageBox.question(self, "Hapus Data", "Anda yakin ingin menghapus semua data grafik?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.hr_data = []; self.hr_timestamps = []; self.hr_graph.clear_graph()
            self.statusBar().showMessage("Data grafik dihapus")

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            settings = dialog.get_settings()
            # TODO: Implementasikan passing settings ke ProcessThread dan AnalysisThread
            # Ini memerlukan mekanisme seperti Queue atau direct method call (jika aman)
            # Contoh: self.process_thread.show_face_rect = settings.get('show_face_rect', True)
            #         self.analysis_thread.min_hr = settings.get('min_hr', 40)
            #         self.analysis_thread.max_hr = settings.get('max_hr', 180)
            #         self.analysis_thread.window_size = settings.get('window_size', 90)
            
            self.hr_graph.set_y_range(settings.get('min_hr', 40) - 10, settings.get('max_hr', 180) + 10)
            if hasattr(self, 'time_range_combo'):
                index = self.time_range_combo.findData(settings.get('graph_range', 180))
                if index >= 0: self.time_range_combo.setCurrentIndex(index)
            self.statusBar().showMessage("Pengaturan diperbarui (fungsi thread TODO)")

    def update_face_status(self, face_detected): # Fungsi lama yang dipanggil slot baru
        if face_detected:
            self.face_status.setText("Wajah terdeteksi")
            self.face_status.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 12px;")
            self.set_face_status_icon(True)
        else:
            self.face_status.setText("Tidak ada wajah terdeteksi")
            self.face_status.setStyleSheet("color: #fab387; font-weight: bold; font-size: 12px;")
            self.set_face_status_icon(False)

    def set_face_status_icon(self, detected):
        pixmap = self._create_icon_pixmap("face", 18, "#a6e3a1" if detected else "#fab387")
        self.face_status_icon.setPixmap(pixmap)
    
    def update_signal_quality(self, quality): # Fungsi lama yang dipanggil slot baru
        self.signal_quality_widget.setValue(int(quality))
    
    def update_time_range(self, index):
        time_range_seconds = self.time_range_combo.currentData()
        self.max_data_points = time_range_seconds # Asumsi 1 data point per detik
        
        # Trim data yang lebih tua dari rentang waktu yang dipilih
        current_time = time.time()
        cutoff_time = current_time - time_range_seconds
        
        new_hr_data = []
        new_hr_timestamps = []
        for i in range(len(self.hr_timestamps)):
            if self.hr_timestamps[i] >= cutoff_time:
                new_hr_data.append(self.hr_data[i])
                new_hr_timestamps.append(self.hr_timestamps[i])
        
        self.hr_data = new_hr_data
        self.hr_timestamps = new_hr_timestamps
        
        # Update graph hanya jika ada data setelah trimming
        if len(self.hr_data) > 1:
            if hasattr(self.hr_graph, 'update_graph_batch'):
                self.hr_graph.update_graph_batch(self.hr_data, self.hr_timestamps)
            else: # Fallback jika HeartRateGraph diubah
                # Perlu logika untuk re-plot semua data buffer di graph
                # Untuk MplCanvas, mungkin panggil clear lalu update_plot dengan buffer penuh
                self.hr_graph.clear_graph()
                if len(self.hr_data) > 1:
                    self.hr_graph.canvas.update_plot(np.array(self.hr_timestamps), np.array(self.hr_data))
        elif len(self.hr_data) <= 1 : # Jika data sedikit atau kosong, clear graph
            self.hr_graph.clear_graph()


    def _create_heart_pixmap(self, size, color_hex="#E91E63"):
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtGui.QColor(0,0,0,0))
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        path = QtGui.QPainterPath(); path.moveTo(size/2, size/5)
        path.cubicTo(size/2, size/10, 0, size/10, 0, size/2.5)
        path.cubicTo(0, size, size/2, size, size/2, size/1.25)
        path.cubicTo(size/2, size, size, size, size, size/2.5)
        path.cubicTo(size, size/10, size/2, size/10, size/2, size/5)
        painter.setPen(QtCore.Qt.PenStyle.NoPen); painter.setBrush(QtGui.QColor(color_hex)); painter.drawPath(path); painter.end()
        return pixmap
    
    def _create_heart_icon(self): return QtGui.QIcon(self._create_heart_pixmap(64))
    
    def _create_icon_pixmap(self, icon_type, size=16, color_hex="#cdd6f4"):
        pixmap = QtGui.QPixmap(size, size); pixmap.fill(QtGui.QColor(0,0,0,0))
        painter = QtGui.QPainter(pixmap); painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(color_hex), 1.5)
        brush = QtGui.QBrush(QtGui.QColor(color_hex))

        if icon_type == "face":
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(brush)
            painter.drawEllipse(1, 1, size-2, size-2)
            eye_mouth_color = QColor("#1e1e2e") if QColor(color_hex).lightness() > 128 else QColor("#ffffff")
            painter.setPen(QPen(eye_mouth_color, 1)); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(int(size/3 -1), int(size/3), 2, 2); painter.drawEllipse(int(2*size/3 -1), int(size/3), 2, 2)
            painter.drawArc(int(size/3), int(size/2 -1), int(size/3), int(size/3), 0, -180*16)
        elif icon_type == "info": 
            painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(1, 1, size-2, size-2); 
            painter.drawLine(int(size/2), int(size*0.3), int(size/2), int(size*0.65)); 
            painter.setBrush(brush); painter.setPen(Qt.PenStyle.NoPen) # Titik di bawah
            painter.drawEllipse(QtCore.QRectF(size/2 - 1, size*0.75, 2, 2))
        elif icon_type == "chart": 
            painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(2, size-2, 2, int(size/3)); painter.drawLine(2, int(size/3), int(size/3), int(size/2)); 
            painter.drawLine(int(size/3), int(size/2), int(2*size/3), int(size/4)); 
            painter.drawLine(int(2*size/3), int(size/4), size-2, int(size/2)); 
            painter.drawLine(2, size-2, size-2, size-2)
        else: 
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(brush)
            painter.drawRect(1, 1, size-2, size-2) 
        painter.end()
        return pixmap

    def _create_icon_from_name(self, icon_name):
        try:
            icon_map = {
                "media-record": QtWidgets.QStyle.StandardPixmap.SP_MediaPlay, 
                "document-save": QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
                "media-playback-stop": QtWidgets.QStyle.StandardPixmap.SP_MediaStop,
                "audio-volume-muted": QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted,
                "audio-volume-high": QtWidgets.QStyle.StandardPixmap.SP_MediaVolume,
                "preferences-system": QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon, 
                "edit-clear-all": QtWidgets.QStyle.StandardPixmap.SP_TrashIcon, 
            }
            std_icon = icon_map.get(icon_name)
            if std_icon is not None:
                icon = self.style().standardIcon(std_icon)
                if not icon.isNull(): return icon
        except Exception as e: print(f"Error getting std icon {icon_name}: {e}")
        return QtGui.QIcon(self._create_icon_pixmap(icon_name, color_hex="#cdd6f4"))

    def _update_session_time(self):
        elapsed_seconds = int(time.time() - self.session_start_time)
        minutes = elapsed_seconds // 60; seconds = elapsed_seconds % 60
        self.session_time_label.setText(f"{minutes:02}:{seconds:02}")
        self.datapoints_count_label.setText(f"{len(self.hr_data)}")
        if self.hr_data:
            avg = sum(self.hr_data) / len(self.hr_data)
            self.avg_hr_label.setText(f"{avg:.1f}"); self._update_avg_hr_style(avg)
        else: self.avg_hr_label.setText("--"); self.avg_hr_label.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: bold;") # Ukuran font disamakan

    def _update_avg_hr_style(self, avg_hr_value):
        style_sheet = "font-size: 14px; font-weight: bold;" # Ukuran font disamakan
        if avg_hr_value < 60: self.avg_hr_label.setStyleSheet(f"color: {ColorsPlaceholder.HR_LOW}; {style_sheet}")
        elif avg_hr_value > 100: self.avg_hr_label.setStyleSheet(f"color: {ColorsPlaceholder.HR_HIGH}; {style_sheet}")
        else: self.avg_hr_label.setStyleSheet(f"color: {ColorsPlaceholder.HR_NORMAL}; {style_sheet}")