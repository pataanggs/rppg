# rppg/ui/camera_selector.py
import cv2
from PyQt6 import QtWidgets, QtCore, QtGui

class CameraSelector(QtWidgets.QDialog):
    """Dialog for selecting a camera device with real-time preview."""
    def __init__(self, parent=None): # Kita tidak perlu available_cameras di sini, dialog akan cari sendiri
        super().__init__(parent)
        self.setWindowTitle("Pilih Perangkat Kamera") # Ubah ke Bahasa Indonesia jika mau
        self.setFixedSize(600, 550)

        self.current_camera_index = None
        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_preview)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15) # Kurangi sedikit spacing global

        title = QtWidgets.QLabel("Pilih Kameramu")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;") # Warna bisa disesuaikan tema
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        instruction = QtWidgets.QLabel("Pilih perangkat kamera dari daftar di bawah")
        instruction.setStyleSheet("font-size: 14px; color: #666;")
        instruction.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)

        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("border: 1px solid #ccc; border-radius: 8px; background-color: #000;") # Border lebih tipis
        self.camera_label.setFixedSize(480, 270) # Sesuaikan ukuran preview jika perlu (16:9)
        layout.addWidget(self.camera_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Camera selection dropdown
        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.setStyleSheet("""
            QComboBox { padding: 8px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
            QComboBox::drop-down { border-left: 1px solid #ccc; padding: 5px; }
        """)
        self.camera_combo.setFixedWidth(400) # Lebar dropdown
        self.camera_combo.currentIndexChanged.connect(self.switch_camera)
        layout.addWidget(self.camera_combo, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Status jumlah kamera
        self.status_label = QtWidgets.QLabel("Mendeteksi kamera...")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10) # Spacer

        # Tombol
        button_layout = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh Daftar")
        self.refresh_button.setStyleSheet("""
            QPushButton { background-color: #5bc0de; color: white; padding: 10px; border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #31b0d5; }
        """)
        self.refresh_button.clicked.connect(self.populate_cameras)
        
        self.select_button = QtWidgets.QPushButton("Pilih Kamera Ini")
        self.select_button.setStyleSheet("""
            QPushButton { background-color: #007bff; color: white; padding: 10px; border-radius: 5px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.select_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.select_button.clicked.connect(self.accept_selection) # Ganti ke accept_selection
        
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.select_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.populate_cameras() # Panggil untuk mengisi kamera saat dialog dibuat

    def populate_cameras(self):
        """Isi dropdown kamera dengan perangkat yang tersedia."""
        self.timer.stop() # Hentikan preview sementara
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.camera_label.clear()
        self.camera_label.setText("Menyegarkan daftar kamera...")
        self.camera_label.setStyleSheet("color: #666; font-size: 14px;")
        
        QtWidgets.QApplication.processEvents() # Paksa update UI

        self.camera_combo.clear()
        index = 0
        count = 0
        found_cameras_data = []
        while True:
            # Coba buka kamera dengan backend default dan CAP_DSHOW untuk Windows
            cap_test = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap_test.isOpened():
                cap_test.release()
                # Jika CAP_DSHOW gagal, coba backend default
                cap_test = cv2.VideoCapture(index) 
                if not cap_test.isOpened():
                    cap_test.release()
                    break # Berhenti jika tidak ada kamera lagi
            
            # Untuk mendapatkan nama perangkat mungkin perlu library tambahan atau OS specific
            # Untuk sekarang kita beri nama "Kamera X"
            device_name = f"Kamera {index}"
            found_cameras_data.append({"name": device_name, "id": index})
            cap_test.release()
            index += 1
            count +=1
            if index > 5: # Batasi pencarian
                break
        
        if count > 0:
            for cam_data in found_cameras_data:
                self.camera_combo.addItem(cam_data["name"], cam_data["id"])
            self.status_label.setText(f"Ditemukan {count} kamera")
            self.camera_combo.setCurrentIndex(0) # Pilih kamera pertama secara default
            self.switch_camera() # Mulai preview untuk kamera pertama
            self.select_button.setEnabled(True)
        else:
            self.status_label.setText("Tidak ada kamera ditemukan")
            self.camera_label.setText("Tidak ada kamera ditemukan")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.select_button.setEnabled(False)


    def switch_camera(self):
        """Beralih ke kamera yang dipilih dan mulai preview."""
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        index = self.camera_combo.currentData()
        if index is None and self.camera_combo.count() > 0: # Jika currentData None tapi ada item
            index = self.camera_combo.itemData(0) # Ambil data item pertama
        
        if index is None : # Jika tetap None (tidak ada kamera di combo)
            self.camera_label.setText("Tidak ada kamera dipilih")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.select_button.setEnabled(False)
            return

        self.current_camera_index = index
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.cap.isOpened(): # Coba fallback jika DSHOW gagal
            self.cap.release()
            self.cap = cv2.VideoCapture(index)

        if self.cap.isOpened():
            # Coba set resolusi preview yang umum
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.timer.start(33)  # Sekitar 30 FPS
            self.camera_label.clear() # Hapus teks "Camera not available"
            self.select_button.setEnabled(True)
        else:
            self.camera_label.setText(f"Kamera {index} tidak tersedia")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.cap = None
            self.select_button.setEnabled(False)


    def update_preview(self):
        """Update preview kamera."""
        if self.cap is None or not self.cap.isOpened():
            # Coba switch camera jika cap tiba-tiba None tapi ada item terpilih
            if self.camera_combo.count() > 0 and self.current_camera_index is not None:
                print(f"Preview error, mencoba switch ke kamera {self.current_camera_index}")
                # self.switch_camera() # Hindari rekursi jika switch juga gagal
                self.timer.stop()
                self.camera_label.setText("Koneksi kamera terputus")
                self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1) # Cermin agar intuitif
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            image = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(image)
            # Sesuaikan ukuran preview dengan label, jaga aspek rasio
            scaled_pixmap = pixmap.scaled(self.camera_label.size(), 
                                          QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding, # atau KeepAspectRatio
                                          QtCore.Qt.TransformationMode.SmoothTransformation)
            # Crop jika perlu setelah KeepAspectRatioByExpanding
            if scaled_pixmap.width() > self.camera_label.width() or scaled_pixmap.height() > self.camera_label.height():
                 scaled_pixmap = scaled_pixmap.copy(
                    (scaled_pixmap.width() - self.camera_label.width()) // 2,
                    (scaled_pixmap.height() - self.camera_label.height()) // 2,
                    self.camera_label.width(),
                    self.camera_label.height()
                )
            self.camera_label.setPixmap(scaled_pixmap)
        else:
            self.camera_label.setText("Tidak bisa memuat preview")
            self.camera_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.timer.stop()

    def get_selected_camera_index(self): # Ganti nama fungsi agar lebih jelas
        """Mengembalikan indeks kamera yang dipilih."""
        return self.camera_combo.currentData()

    def accept_selection(self): # Fungsi baru untuk tombol "Select"
        if self.get_selected_camera_index() is not None and self.cap and self.cap.isOpened():
            self.accept() # Tutup dialog dan kembalikan QDialog.DialogCode.Accepted
        else:
            QtWidgets.QMessageBox.warning(self, "Kamera Tidak Valid", "Silakan pilih kamera yang valid dan tersedia.")


    def closeEvent(self, event):
        """Pastikan kamera dilepas saat dialog ditutup."""
        print("CameraSelector dialog closing...")
        self.timer.stop()
        if self.cap is not None:
            print("Releasing camera from CameraSelector...")
            self.cap.release()
            self.cap = None
        event.accept()