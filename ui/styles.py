from PyQt6 import QtGui


class Colors:
    """Color scheme for the application."""
    PRIMARY = "#2C3E50"
    SECONDARY = "#34495E"
    ACCENT = "#E74C3C"
    ACCENT_LIGHT = "#F39C12"
    BACKGROUND_LIGHT = "#ECF0F1"
    BACKGROUND_DARK = "#2C3E50"
    TEXT_LIGHT = "#FFFFFF"
    TEXT_DARK = "#2C3E50"
    SUCCESS = "#2ECC71"
    WARNING = "#F39C12"
    DANGER = "#E74C3C"
    INFO = "#3498DB"
    HR_NORMAL = "#2ECC71"  # Green
    HR_WARNING = "#F39C12"  # Orange
    HR_DANGER = "#E74C3C"  # Red
    HR_GRAPH = "#E74C3C"   # Red
    HR_GRAPH_FILL = "#FADBD8"  # Light red


class Fonts:
    """Font definitions for the application."""
    FAMILY = "Segoe UI"
    SMALL = QtGui.QFont(FAMILY, 9)
    NORMAL = QtGui.QFont(FAMILY, 10)
    MEDIUM = QtGui.QFont(FAMILY, 12)
    LARGE = QtGui.QFont(FAMILY, 16)
    EXTRA_LARGE = QtGui.QFont(FAMILY, 24)

    # Bold variants
    SMALL_BOLD = QtGui.QFont(FAMILY, 9, QtGui.QFont.Weight.Bold)
    NORMAL_BOLD = QtGui.QFont(FAMILY, 10, QtGui.QFont.Weight.Bold)
    MEDIUM_BOLD = QtGui.QFont(FAMILY, 12, QtGui.QFont.Weight.Bold)
    LARGE_BOLD = QtGui.QFont(FAMILY, 16, QtGui.QFont.Weight.Bold)
    EXTRA_LARGE_BOLD = QtGui.QFont(FAMILY, 24, QtGui.QFont.Weight.Bold)


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
                background-color: {Colors.BACKGROUND_LIGHT};
            }}
        """

    @staticmethod
    def get_title_label_style():
        """Get the title label style."""
        return f"""
            QLabel {{
                color: {Colors.PRIMARY};
                font-family: {Fonts.FAMILY};
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
            }}
        """

    @staticmethod
    def get_status_label_style(status="normal"):
        """Get the status label style based on the current status."""
        if status == "normal":
            bg_color = Colors.SUCCESS
        elif status == "warning":
            bg_color = Colors.WARNING
        elif status == "danger":
            bg_color = Colors.DANGER
        else:
            bg_color = Colors.INFO
            
        return f"""
            QLabel {{
                color: {Colors.TEXT_LIGHT};
                background-color: {bg_color};
                font-family: {Fonts.FAMILY};
                font-size: 14px;
                padding: 8px;
                border-radius: 4px;
            }}
        """

    @staticmethod
    def get_button_style():
        """Get the button style."""
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                font-family: {Fonts.FAMILY};
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            
            QPushButton:hover {{
                background-color: {Colors.SECONDARY};
            }}
            
            QPushButton:pressed {{
                background-color: {Colors.ACCENT};
            }}
            
            QPushButton:disabled {{
                background-color: #95A5A6;
                color: #7F8C8D;
            }}
        """

    STATUS_LABEL = lambda: StyleSheets.get_status_label_style("normal")


class Layout:
    """Layout constants and styling helper methods."""
    MARGIN = 10
    SPACING = 10
    PADDING = 20
    BUTTON_HEIGHT = 30
    BUTTON_WIDTH = 100
    VIDEO_MIN_HEIGHT = 360
    VIDEO_MIN_WIDTH = 480
    HEART_RATE_DISPLAY_HEIGHT = 120


def get_heart_rate_color(heart_rate):
    """Get color based on the heart rate value."""
    if heart_rate < 50 or heart_rate > 100:
        return Colors.HR_DANGER
    elif heart_rate < 60 or heart_rate > 90:
        return Colors.HR_WARNING
    else:
        return Colors.HR_NORMAL


def apply_stylesheet(widget, stylesheet_function):
    """Helper function to apply a stylesheet to a widget.
    
    Args:
        widget: The widget to apply the stylesheet to.
        stylesheet_function: A function that returns a stylesheet.
    """
    if callable(stylesheet_function):
        # If it's a function, call it to get the stylesheet
        stylesheet = stylesheet_function()
    else:
        # Otherwise, assume it's the stylesheet itself
        stylesheet = stylesheet_function
    
    StyleSheets.apply_style(widget, stylesheet)
