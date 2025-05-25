import sys
from PyQt6 import QtWidgets
<<<<<<< HEAD:main.py
from threads.video_thread import VideoThread
# from ui.main_window import MainWindow
=======
from rppg.camera_selector import CameraSelector
from ui.main_window import MainWindow
>>>>>>> e0e1e3817d1bb11fb28f64bbdc38c2e02476ce2c:rppg/main.py

if __name__ == "__main__":
#    app = QtWidgets.QApplication(sys.argv)
#    selector = CameraSelector()
#    if selector.exec() == QtWidgets.QDialog.DialogCode.Accepted:
#        selected_camera = selector.get_selected_camera()
#        window = MainWindow(camera_index=selected_camera)
#        window.show()
#        sys.exit(app.exec())
    video_thread = VideoThread()
    video_thread.start()
