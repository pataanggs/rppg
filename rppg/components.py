from PyQt6 import QtWidgets, QtCore, QtGui
from plot_canvas import MplCanvas
from ui.styles import VIDEO_CONTAINER_STYLE, STATUS_BAR_STYLE, BUTTON_STYLE, VITAL_CARD_STYLE

def create_video_container():
    """Create video container with header, status, and toggle buttons."""
    video_container = QtWidgets.QWidget()
    video_container.setObjectName("videoContainer")
    video_container.setStyleSheet(VIDEO_CONTAINER_STYLE)
    video_layout = QtWidgets.QVBoxLayout(video_container)
    video_layout.setContentsMargins(0, 0, 0, 0)
    video_layout.setSpacing(0)

    # Header
    camera_header = QtWidgets.QWidget()
    camera_header.setFixedHeight(40)
    camera_header.setStyleSheet("""
        background-color: rgba(0, 0, 0, 0.6);
        border-top-left-radius: 15px;
        border-top-right-radius: 15px;
    """)
    header_layout = QtWidgets.QHBoxLayout(camera_header)
    header_layout.setContentsMargins(15, 0, 15, 0)

    rec_indicator = QtWidgets.QLabel()
    rec_indicator.setFixedSize(10, 10)
    rec_indicator.setStyleSheet("background-color: #9e9e9e; border-radius: 5px;")

    header_title = QtWidgets.QLabel("Camera Feed")
    header_title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")

    header_layout.addWidget(rec_indicator)
    header_layout.addWidget(header_title)
    header_layout.addStretch()

    landmark_btn = QtWidgets.QPushButton()
    landmark_btn.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton))
    landmark_btn.setToolTip("Toggle Facial Landmarks")
    landmark_btn.setFixedSize(28, 28)
    landmark_btn.setStyleSheet(BUTTON_STYLE["landmark_inactive"])
    landmark_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    bbox_btn = QtWidgets.QPushButton()
    bbox_btn.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
    bbox_btn.setToolTip("Toggle Bounding Box")
    bbox_btn.setFixedSize(28, 28)
    bbox_btn.setStyleSheet(BUTTON_STYLE["bbox_inactive"])
    bbox_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    header_layout.addWidget(landmark_btn)
    header_layout.addSpacing(5)
    header_layout.addWidget(bbox_btn)

    # Video label
    video_label = QtWidgets.QLabel()
    video_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    video_label.setMinimumHeight(400)
    video_label.setStyleSheet("background-color: transparent;")

    # Status bar
    camera_status = QtWidgets.QWidget()
    camera_status.setFixedHeight(40)
    camera_status.setStyleSheet("""
        background-color: rgba(0, 0, 0, 0.6);
        border-bottom-left-radius: 15px;
        border-bottom-right-radius: 15px;
    """)
    status_layout = QtWidgets.QHBoxLayout(camera_status)
    status_layout.setContentsMargins(15, 0, 15, 0)

    status_icon = QtWidgets.QLabel()
    status_icon.setFixedSize(10, 10)
    status_icon.setStyleSheet("background-color: #9e9e9e; border-radius: 5px;")

    status_text = QtWidgets.QLabel("Camera not active")
    status_text.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")

    fps_label = QtWidgets.QLabel("0 FPS")
    fps_label.setStyleSheet("color: #ccc; font-size: 12px;")

    face_status = QtWidgets.QLabel("No Face")
    face_status.setStyleSheet("color: #ff6b6b; font-size: 12px; font-weight: bold;")

    status_layout.addWidget(status_icon)
    status_layout.addWidget(status_text)
    status_layout.addStretch()
    status_layout.addWidget(fps_label)
    status_layout.addSpacing(10)
    status_layout.addWidget(face_status)

    video_layout.addWidget(camera_header)
    video_layout.addWidget(video_label, 1)
    video_layout.addWidget(camera_status)

    return video_container, video_label, rec_indicator, status_icon, status_text, fps_label, face_status, landmark_btn, bbox_btn

def create_vital_cards():
    """Create vital sign cards for heart rate and respiration rate."""
    canvas = MplCanvas(None, height=8)
    canvas.setMinimumHeight(300)
    graph_shadow = QtWidgets.QGraphicsDropShadowEffect()
    graph_shadow.setBlurRadius(20)
    graph_shadow.setColor(QtGui.QColor(0, 0, 0, 50))
    graph_shadow.setOffset(0, 5)
    canvas.setGraphicsEffect(graph_shadow)

    hr_card = QtWidgets.QWidget()
    hr_card.setStyleSheet(VITAL_CARD_STYLE)
    hr_card_shadow = QtWidgets.QGraphicsDropShadowEffect()
    hr_card_shadow.setBlurRadius(20)
    hr_card_shadow.setColor(QtGui.QColor(0, 0, 0, 40))
    hr_card_shadow.setOffset(0, 5)
    hr_card.setGraphicsEffect(hr_card_shadow)

    hr_layout = QtWidgets.QVBoxLayout(hr_card)
    hr_title = QtWidgets.QLabel("Heart Rate")
    hr_title.setStyleSheet("font-size: 14px; color: #555; font-weight: bold;")
    heart_rate_label = QtWidgets.QLabel("-- BPM")
    heart_rate_label.setStyleSheet("color: #4CAF50; font-size: 28px; font-weight: bold;")
    heart_rate_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    hr_indicator = QtWidgets.QLabel()
    hr_indicator.setFixedSize(100, 6)
    hr_indicator.setStyleSheet("background-color: #4CAF50; border-radius: 3px;")
    hr_range = QtWidgets.QLabel("Normal: 50-120 BPM")
    hr_range.setStyleSheet("font-size: 12px; color: #777;")
    hr_range.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    hr_layout.addWidget(hr_title)
    hr_layout.addWidget(heart_rate_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
    hr_layout.addWidget(hr_indicator, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
    hr_layout.addWidget(hr_range)

    rr_card = QtWidgets.QWidget()
    rr_card.setStyleSheet(VITAL_CARD_STYLE)
    rr_card_shadow = QtWidgets.QGraphicsDropShadowEffect()
    rr_card_shadow.setBlurRadius(20)
    rr_card_shadow.setColor(QtGui.QColor(0, 0, 0, 40))
    rr_card_shadow.setOffset(0, 5)
    rr_card.setGraphicsEffect(rr_card_shadow)

    rr_layout = QtWidgets.QVBoxLayout(rr_card)
    rr_title = QtWidgets.QLabel("Respiration Rate")
    rr_title.setStyleSheet("font-size: 14px; color: #555; font-weight: bold;")
    respiration_rate_label = QtWidgets.QLabel("-- BPM")
    respiration_rate_label.setStyleSheet("color: #2196F3; font-size: 28px; font-weight: bold;")
    respiration_rate_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    rr_indicator = QtWidgets.QLabel()
    rr_indicator.setFixedSize(100, 6)
    rr_indicator.setStyleSheet("background-color: #2196F3; border-radius: 3px;")
    rr_range = QtWidgets.QLabel("Normal: 12-20 BPM")
    rr_range.setStyleSheet("font-size: 12px; color: #777;")
    rr_range.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    rr_layout.addWidget(rr_title)
    rr_layout.addWidget(respiration_rate_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
    rr_layout.addWidget(rr_indicator, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
    rr_layout.addWidget(rr_range)

    return canvas, hr_card, rr_card, heart_rate_label, respiration_rate_label

def create_status_bar():
    """Create status bar with start/stop buttons and mute toggle."""
    status_bar = QtWidgets.QWidget()
    status_bar.setFixedHeight(50)
    status_bar.setStyleSheet(STATUS_BAR_STYLE)
    status_shadow = QtWidgets.QGraphicsDropShadowEffect()
    status_shadow.setBlurRadius(10)
    status_shadow.setColor(QtGui.QColor(0, 0, 0, 30))
    status_shadow.setOffset(0, 2)
    status_bar.setGraphicsEffect(status_shadow)

    status_layout = QtWidgets.QHBoxLayout(status_bar)
    status_layout.setContentsMargins(10, 10, 10, 10)
    status_layout.setSpacing(10)

    status_indicator = QtWidgets.QLabel()
    status_indicator.setFixedSize(10, 10)
    status_indicator.setStyleSheet("background-color: #9e9e9e; border-radius: 5px;")

    status_label = QtWidgets.QLabel("Status: Ready")
    status_label.setStyleSheet("color: #555; font-size: 14px; font-weight: normal;")

    start_button = QtWidgets.QPushButton("Start Monitoring")
    start_button.setFixedSize(120, 30)
    start_button.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
    start_button.setIconSize(QtCore.QSize(16, 16))  # Perbaikan: Hapus QtCore.QtCore
    start_button.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 5px;
            border-radius: 5px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
    """)
    start_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    exit_button = QtWidgets.QPushButton("Close")
    exit_button.setFixedSize(80, 30)
    exit_button.setStyleSheet("""
        background-color: #f44336;
        color: white;
        font-size: 12px;
        font-weight: bold;
        border-radius: 5px;
    """)
    exit_button.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogCloseButton))
    exit_button.setIconSize(QtCore.QSize(12, 12))  # Perbaikan: Hapus QtCore.QtCore
    exit_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    mute_button = QtWidgets.QPushButton()
    mute_button.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolume))
    mute_button.setIconSize(QtCore.QSize(16, 16))  # Perbaikan: Hapus QtCore.QtCore
    mute_button.setFixedSize(30, 30)
    mute_button.setStyleSheet("""
        QPushButton {
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: rgba(240, 240, 240, 0.9);
        }
    """)
    mute_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
    mute_button.setToolTip("Toggle alarm sound (currently ON)")

    version_label = QtWidgets.QLabel("v1.0")
    version_label.setStyleSheet("color: #999; font-size: 12px;")

    status_layout.addWidget(status_indicator)
    status_layout.addWidget(status_label)
    status_layout.addStretch()
    status_layout.addWidget(start_button)
    status_layout.addSpacing(10)
    status_layout.addWidget(exit_button)
    status_layout.addSpacing(10)
    status_layout.addWidget(mute_button)
    status_layout.addSpacing(10)
    status_layout.addWidget(version_label)

    return status_bar, status_indicator, status_label, mute_button, start_button, exit_button

def create_exit_dialog(parent):
    """Create custom exit confirmation dialog."""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Exit Confirmation")
    dialog.setFixedWidth(400)
    dialog.setStyleSheet("""
        QDialog {
            background-color: white;
            border-radius: 15px;
        }
        QLabel {
            color: #333333;
            font-size: 16px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QPushButton {
            font-size: 16px;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: bold;
        }
        QPushButton#yes_button {
            background-color: #f44336;
            color: white;
        }
        QPushButton#yes_button:hover {
            background-color: #d32f2f;
        }
        QPushButton#no_button {
            background-color: #4CAF50;
            color: white;
        }
        QPushButton#no_button:hover {
            background-color: #43A047;
        }
    """)

    shadow = QtWidgets.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(30)
    shadow.setColor(QtGui.QColor(0, 0, 0, 80))
    shadow.setOffset(0, 0)
    dialog.setGraphicsEffect(shadow)

    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setSpacing(20)
    layout.setContentsMargins(25, 25, 25, 25)

    header_layout = QtWidgets.QHBoxLayout()
    icon_label = QtWidgets.QLabel()
    icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
    icon_label.setPixmap(icon.pixmap(48, 48))
    header_text = QtWidgets.QLabel("Confirm Exit")
    header_text.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
    header_layout.addWidget(icon_label)
    header_layout.addWidget(header_text)
    header_layout.addStretch()

    message = QtWidgets.QLabel("Are you sure you want to exit the application?\nAll monitoring will stop.")
    message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    message.setStyleSheet("margin: 10px 0; font-size: 16px; color: #555;")

    button_layout = QtWidgets.QHBoxLayout()
    yes_button = QtWidgets.QPushButton("Yes, Exit")
    yes_button.setObjectName("yes_button")
    yes_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
    no_button = QtWidgets.QPushButton("No, Continue")
    no_button.setObjectName("no_button")
    no_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    button_layout.addStretch()
    button_layout.addWidget(no_button)
    button_layout.addWidget(yes_button)
    button_layout.addStretch()

    layout.addLayout(header_layout)
    layout.addWidget(message)
    layout.addSpacing(10)
    layout.addLayout(button_layout)

    yes_button.clicked.connect(dialog.accept)
    no_button.clicked.connect(dialog.reject)

    return dialog