STYLESHEET = """
    QWidget {
        background-color: #f5f5f7;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QLabel {
        font-size: 20px;
        font-weight: bold;
    }
"""

VIDEO_CONTAINER_STYLE = """
    #videoContainer {
        background-color: #1e1e1e;
        border-radius: 15px;
        min-height: 450px;
    }
"""

STATUS_BAR_STYLE = """
    background-color: white;
    border-radius: 15px;
"""

VITAL_CARD_STYLE = """
    background-color: white;
    border-radius: 15px;
    padding: 15px;
"""

BUTTON_STYLE = {
    "landmark_inactive": """
        QPushButton {
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 14px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.3);
        }
    """,
    "landmark_active": """
        QPushButton {
            background-color: rgba(0, 255, 0, 0.3);
            border-radius: 14px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: rgba(0, 255, 0, 0.5);
        }
    """,
    "bbox_inactive": """
        QPushButton {
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 14px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.3);
        }
    """,
    "bbox_active": """
        QPushButton {
            background-color: rgba(0, 255, 0, 0.3);
            border-radius: 14px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: rgba(0, 255, 0, 0.5);
        }
    """
}