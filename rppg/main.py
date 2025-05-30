# rppg/main.py
import sys
import cv2 # Hanya untuk list_available_cameras awal
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog # Tambahkan QDialog
from rppg.ui.main_window import MainWindow
from rppg.ui.camera_selector import CameraSelector # Import kelasnya

def preliminary_camera_check():
    print("Melakukan pemeriksaan kamera awal (cepat)...")
    for i in range(3): # Hanya cek 3 indeks pertama
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            cap.release()
            print(f"Pemeriksaan awal: Kamera terdeteksi di indeks {i}.")
            return True
        cap.release()
    print("Pemeriksaan awal: Tidak ada kamera terdeteksi di 3 indeks pertama.")
    return False

def main():
    app = QApplication(sys.argv)

    # Initialize multimedia system
    try:
        dummy_player = QMediaPlayer()  # This will initialize the multimedia system
    except Exception as e:
        print(f"Multimedia initialization warning: {e}")

    if not preliminary_camera_check():
        QMessageBox.critical(None, "Error Kamera", "Tidak ada kamera yang terdeteksi. Aplikasi akan ditutup.")
        return -1

    # Buat instance dan tampilkan CameraSelector dialog
    selector_dialog = CameraSelector()
    result = selector_dialog.exec() # Tampilkan dialog secara modal

    selected_camera_idx = None
    if result == QDialog.DialogCode.Accepted:
        selected_camera_idx = selector_dialog.get_selected_camera_index()
        print(f"Kamera dipilih dari dialog: Indeks {selected_camera_idx}")
    else:
        print("Pemilihan kamera dibatalkan atau ditutup. Aplikasi keluar.")
        return 0 # Keluar jika dialog dibatalkan atau ditutup

    if selected_camera_idx is None: # Jika tidak ada kamera yang dipilih (misal, tidak ada kamera di daftar dialog)
        QMessageBox.critical(None, "Error Kamera", "Tidak ada kamera yang dipilih atau kamera tidak valid. Aplikasi akan ditutup.")
        return -1
        
    window = MainWindow(camera_index=selected_camera_idx)
    window.show()
    return app.exec()