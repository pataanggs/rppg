from PyQt6 import QtGui


class Colors:
    """Color constants for use throughout the application."""
    # Main colors (Material Design palette)
    PRIMARY = "#E91E63"  # Pink 500
    PRIMARY_DARK = "#C2185B"  # Pink 700
    PRIMARY_LIGHT = "#F8BBD0"  # Pink 100
    ACCENT = "#2196F3"  # Blue 500
    
    # Text colors
    TEXT_PRIMARY = "#212121"  # Grey 900
    TEXT_SECONDARY = "#757575"  # Grey 600
    TEXT_DISABLED = "#9E9E9E"  # Grey 500
    
    # Background colors
    BG_LIGHT = "#FFFFFF"  # White
    BG_MEDIUM = "#F5F5F5"  # Grey 100
    BG_DARK = "#EEEEEE"  # Grey 200
    
    # Status colors
    STATUS_NORMAL = "#4CAF50"  # Green 500
    STATUS_WARNING = "#FFC107"  # Amber 500
    STATUS_DANGER = "#F44336"  # Red 500
    
    # Heart rate specific colors with hex codes for easier use
    HR_LOW = "#F44336"  # Red 500
    HR_LOW_HEX = "#F44336"
    HR_NORMAL = "#4CAF50"  # Green 500 
    HR_NORMAL_HEX = "#4CAF50"
    HR_HIGH = "#F44336"  # Red 500
    HR_HIGH_HEX = "#F44336"
    HR_WARNING = "#FFC107"  # Amber 500
    HR_WARNING_HEX = "#FFC107"


class Fonts:
    """Font constants for use throughout the application."""
    FAMILY = "'Segoe UI', Arial, sans-serif"
    TITLE = "18px"
    SUBTITLE = "14px"
    BODY = "12px"
    SMALL = "10px"


class Layout:
    """Layout constants for use throughout the application."""
    MARGIN = 16
    PADDING = 8
    RADIUS = 4
    VIDEO_MIN_WIDTH = 480
    VIDEO_MIN_HEIGHT = 360


def apply_stylesheet(widget, stylesheet_func):
    """Apply a style sheet to a widget."""
    if callable(stylesheet_func):
        widget.setStyleSheet(stylesheet_func())
    else:
        widget.setStyleSheet(stylesheet_func)


def get_heart_rate_color(hr):
    """Get the appropriate color for a heart rate value."""
    if hr < 50:
        return Colors.HR_LOW
    elif hr < 60:
        return Colors.HR_WARNING
    elif hr <= 90:
        return Colors.HR_NORMAL
    elif hr <= 100:
        return Colors.HR_WARNING
    else:
        return Colors.HR_HIGH


class StyleSheets:
    """Application style sheets for various UI elements."""
    @staticmethod
    def apply_style(widget, stylesheet):
        """Apply a style sheet to a given widget."""
        widget.setStyleSheet(stylesheet)

    @staticmethod
    def get_main_window_style():
        """Get the main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: #f8f9fa;
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.FAMILY};
                font-size: {Fonts.BODY};
            }}
        """

    @staticmethod
    def get_title_label_style():
        """Get the title label style."""
        return f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.TITLE};
                font-weight: bold;
                margin-bottom: {Layout.MARGIN}px;
            }}
        """

    @staticmethod
    def get_subtitle_label_style():
        """Get the subtitle label style."""
        return f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.SUBTITLE};
                font-weight: bold;
                margin-bottom: {Layout.MARGIN / 2}px;
            }}
        """

    @staticmethod
    def get_status_label_style(status="normal"):
        """Get the status label style based on the current status."""
        status_color = {
            "normal": Colors.STATUS_NORMAL,
            "warning": Colors.STATUS_WARNING,
            "danger": Colors.STATUS_DANGER
        }.get(status, Colors.STATUS_NORMAL)
        
        return f"""
            QLabel {{
                background-color: #ffffff;
                color: {status_color};
                font-size: {Fonts.BODY};
                padding: {Layout.PADDING}px;
                border-radius: {Layout.RADIUS}px;
                font-weight: bold;
                border: 1px solid #e0e0e0;
            }}
        """
    
    @staticmethod
    def get_button_style():
        """Get the button style."""
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: {Layout.RADIUS}px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_DISABLED};
            }}
        """

    # Status label style
    STATUS_LABEL = f"""
        QLabel {{
            background-color: #ffffff;
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid #e0e0e0;
            padding: {Layout.PADDING}px;
            border-radius: {Layout.RADIUS}px;
        }}
    """

    @staticmethod
    def get_hr_display_style(hr_color):
        """Generate heart rate display stylesheet with specified color."""
        return f"""
            QLabel {{
                background-color: {Colors.BG_MEDIUM};
                border-radius: 8px;
                padding: {Layout.PADDING}px;
                color: {hr_color};
            }}
        """
