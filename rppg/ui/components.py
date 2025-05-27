from PyQt6 import QtWidgets, QtCore, QtGui
import time
import numpy as np
from rppg.ui.styles import Colors, StyleSheets, apply_stylesheet
import matplotlib
matplotlib.use('qt5agg')  # Use qt5agg which is supported
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime


class HeartRateDisplay(QtWidgets.QWidget):
    """Widget to display the current heart rate and graph of heart rate history."""
    def __init__(self):
        super().__init__()
        self.heart_rate = 0
        self.history = []
        self.history_times = []
        self.display_color = QtGui.QColor(233, 30, 99)  # Material Design pink
        self.setMinimumHeight(220)
        self.setMinimumWidth(250)
        self.last_update_time = time.time()
        self.show_seconds = 30  # Show 30 seconds of history
        
        # No animations - just use static values
        self.displayed_hr = 0.0
        
    def set_heart_rate(self, hr):
        """Update the heart rate and add it to the history."""
        self.heart_rate = hr
        self.displayed_hr = float(hr)  # Directly set value without animation
        
        current_time = time.time()
        
        # Only add a new point every 0.5 seconds to avoid too many points
        if not self.history or (current_time - self.last_update_time) >= 0.5:
            self.history.append(hr)
            self.history_times.append(current_time)
            self.last_update_time = current_time
            
            # Remove old data points (older than show_seconds)
            while self.history_times and (current_time - self.history_times[0]) > self.show_seconds:
                self.history.pop(0)
                self.history_times.pop(0)
                
        self.update()
    
    def set_color(self, color):
        """Set the color of the heart rate display."""
        self.display_color = QtGui.QColor(color)
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        """Handle the painting of the widget (heart rate number and graph)."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Draw card background with subtle gradient
        path = QtGui.QPainterPath()
        rect = QtCore.QRectF(event.rect())
        path.addRoundedRect(rect, 12, 12)
        
        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QtGui.QColor(250, 250, 250))
        gradient.setColorAt(1, QtGui.QColor(245, 245, 245))
        painter.fillPath(path, gradient)
        
        # Add subtle border
        painter.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
        painter.drawPath(path)
        
        # Draw title with improved typography
        font = QtGui.QFont("Segoe UI", 14)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(70, 70, 70))
        
        # Add icon to title (static, no animation)
        heart_icon = self._create_heart_icon(18, self.display_color)
        icon_rect = QtCore.QRect(20, 16, 18, 18)
        painter.drawPixmap(icon_rect, heart_icon)
        
        # Draw title text with offset for icon
        painter.drawText(50, 30, "Heart Rate")
        
        # Draw modern divider line with gradient
        line_gradient = QtGui.QLinearGradient(20, 45, self.width() - 20, 45)
        line_gradient.setColorAt(0, self.display_color)
        line_gradient.setColorAt(0.5, QtGui.QColor(self.display_color.red(), 
                                              self.display_color.green(),
                                              self.display_color.blue(), 
                                              150))
        line_gradient.setColorAt(1, QtGui.QColor(230, 230, 230))
        
        painter.setPen(QtGui.QPen(line_gradient, 2))
        painter.drawLine(20, 45, self.width() - 20, 45)
        
        # Draw heart rate with modern display
        hr_container_rect = QtCore.QRectF(20, 55, self.width() - 40, 80)
        
        # Draw background (static, no glow animation)
        glow_path = QtGui.QPainterPath()
        glow_path.addRoundedRect(hr_container_rect, 8, 8)
        glow_color = QtGui.QColor(self.display_color)
        glow_color.setAlpha(20)  # Static alpha value
        painter.fillPath(glow_path, glow_color)
        
        # Draw heart icon (static, no pulse animation)
        icon_size = 38
        icon_x = 30
        icon_y = 75
        heart_icon = self._create_heart_icon(icon_size, self.display_color)
        
        # Draw heart icon with static size
        heart_rect = QtCore.QRect(
            icon_x, 
            icon_y, 
            icon_size, 
            icon_size
        )
        painter.drawPixmap(heart_rect, heart_icon)
        
        # Draw heart rate value with improved typography
        value_x = icon_x + icon_size + 20
        
        # Display the value
        hr_string = f"{self.displayed_hr:.1f}"
        
        # Draw value and units with modern styling
        font = QtGui.QFont("Segoe UI", 46)
        font.setWeight(QtGui.QFont.Weight.Bold)
        painter.setFont(font)
        
        # Get metrics for proper alignment
        font_metrics = QtGui.QFontMetrics(font)
        value_width = font_metrics.horizontalAdvance(hr_string)
        
        # Draw value with text shadow for depth
        painter.setPen(QtGui.QColor(self.display_color.red(), 
                                  self.display_color.green(), 
                                  self.display_color.blue(), 
                                  30))
        painter.drawText(value_x + 2, 105 + 2, hr_string)
        
        # Draw main text
        painter.setPen(self.display_color)
        painter.drawText(value_x, 105, hr_string)
        
        # Draw "BPM" text with better alignment
        font = QtGui.QFont("Segoe UI", 16)
        font.setWeight(QtGui.QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(value_x + value_width + 10, 105, "BPM")
        
        # Draw HR classification text
        font = QtGui.QFont("Segoe UI", 12)
        painter.setFont(font)
        
        # Determine heart rate category and text
        if self.heart_rate < 60:
            hr_category = "Low"
            category_color = QtGui.QColor("#FF9800")  # Amber
        elif self.heart_rate > 100:
            hr_category = "High"
            category_color = QtGui.QColor("#F44336")  # Red
        else:
            hr_category = "Normal"
            category_color = QtGui.QColor("#4CAF50")  # Green
        
        # Draw category text
        painter.setPen(category_color)
        category_rect = QtCore.QRect(value_x, 110, self.width() - value_x - 20, 30)
        painter.drawText(category_rect, QtCore.Qt.AlignmentFlag.AlignLeft, hr_category)
        
        # Draw the heart rate history graph if available
        if len(self.history) > 1:
            self._draw_heart_rate_graph(painter)
    
    def _draw_heart_rate_graph(self, painter):
        """Draw the heart rate graph based on history."""
        # Area for the graph
        graph_rect = QtCore.QRectF(20, 150, self.width() - 40, 60)
        
        # Draw graph background with slight rounding
        bg_path = QtGui.QPainterPath()
        bg_path.addRoundedRect(graph_rect, 6, 6)
        bg_color = QtGui.QColor(240, 240, 240)
        painter.fillPath(bg_path, bg_color)
        
        # Draw subtle grid
        painter.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1, QtCore.Qt.PenStyle.DotLine))
        
        # Horizontal grid lines
        y_steps = 3
        for i in range(1, y_steps):
            y = int(graph_rect.top() + i * graph_rect.height() / y_steps)
            painter.drawLine(int(graph_rect.left()), y, int(graph_rect.right()), y)
        
        # Vertical grid lines
        x_steps = 6
        for i in range(1, x_steps):
            x = int(graph_rect.left() + i * graph_rect.width() / x_steps)
            painter.drawLine(x, int(graph_rect.top()), x, int(graph_rect.bottom()))
        
        # Calculate x and y scales
        x_scale = graph_rect.width() / self.show_seconds if self.history_times else graph_rect.width() / 100
        
        # Get min/max HR values for scaling
        max_hr = max(max(self.history), 120)
        min_hr = min(min(self.history), 40)
        if max_hr == min_hr:
            hr_range = 50
            min_hr = max_hr - 50
        else:
            hr_range = max_hr - min_hr
        
        # Current time for relative x-positioning
        current_time = time.time() if self.history_times else 0
        
        # Create path for the line
        path = QtGui.QPainterPath()
        fill_path = QtGui.QPainterPath()
        
        # Start point
        if self.history_times:
            x = graph_rect.right() - (current_time - self.history_times[0]) * x_scale
        else:
            x = graph_rect.left()
        
        y = graph_rect.bottom() - ((self.history[0] - min_hr) / hr_range) * graph_rect.height()
        path.moveTo(int(x), int(y))
        fill_path.moveTo(int(x), int(graph_rect.bottom()))
        fill_path.lineTo(int(x), int(y))
        
        # Add points
        for i in range(1, len(self.history)):
            if self.history_times:
                x = graph_rect.right() - (current_time - self.history_times[i]) * x_scale
            else:
                x = graph_rect.left() + i * (graph_rect.width() / len(self.history))
            
            y = graph_rect.bottom() - ((self.history[i] - min_hr) / hr_range) * graph_rect.height()
            path.lineTo(int(x), int(y))
            fill_path.lineTo(int(x), int(y))
        
        # Complete the fill path
        fill_path.lineTo(int(x), int(graph_rect.bottom()))
        fill_path.closeSubpath()
        
        # Draw fill with gradient
        gradient = QtGui.QLinearGradient(0, graph_rect.top(), 0, graph_rect.bottom())
        gradient.setColorAt(0, QtGui.QColor(self.display_color.red(), 
                                         self.display_color.green(),
                                         self.display_color.blue(), 
                                         70))
        gradient.setColorAt(1, QtGui.QColor(self.display_color.red(), 
                                         self.display_color.green(),
                                         self.display_color.blue(), 
                                         10))
        painter.fillPath(fill_path, gradient)
        
        # Draw main line with constant width
        main_pen = QtGui.QPen(self.display_color, 2.0)
        main_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        main_pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(main_pen)
        painter.drawPath(path)
        
        # Draw points at some data locations (not every point, to avoid clutter)
        for i in range(0, len(self.history), 3):  # Draw every 3rd point
            if self.history_times:
                x = graph_rect.right() - (current_time - self.history_times[i]) * x_scale
            else:
                x = graph_rect.left() + i * (graph_rect.width() / len(self.history))
            
            y = graph_rect.bottom() - ((self.history[i] - min_hr) / hr_range) * graph_rect.height()
            
            # Draw simple point without glow
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QColor(255, 255, 255))
            painter.drawEllipse(int(x) - 2, int(y) - 2, 4, 4)
            
            painter.setBrush(self.display_color)
            painter.drawEllipse(int(x) - 1, int(y) - 1, 2, 2)
    
    def _create_heart_icon(self, size, color):
        """Create a heart-shaped icon for the UI."""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Create heart path
        path = QtGui.QPainterPath()
        path.moveTo(int(size/2), int(size/5))
        path.cubicTo(
            int(size/2), int(size/10),
            0, int(size/10),
            0, int(size/2.5)
        )
        path.cubicTo(
            0, size,
            int(size/2), size,
            int(size/2), int(size/1.25)
        )
        path.cubicTo(
            int(size/2), size,
            size, size,
            size, int(size/2.5)
        )
        path.cubicTo(
            size, int(size/10),
            int(size/2), int(size/10),
            int(size/2), int(size/5)
        )
        
        # Draw with subtle gradient
        gradient = QtGui.QLinearGradient(0, 0, 0, size)
        gradient.setColorAt(0, QtGui.QColor(color))
        gradient.setColorAt(1, QtGui.QColor(QtGui.QColor(color).darker(110)))
        
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(path)
        
        painter.end()
        return pixmap


class HeartRateGraph(FigureCanvasQTAgg):
    """A graph widget that displays heart rate history over time."""
    
    def __init__(self, parent=None, width=5, height=2, dpi=100):
        # Create figure first
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # Use a more modern, flat design
        self.fig.set_facecolor('#ffffff')
        
        # Call parent's __init__ method with the figure
        super().__init__(self.fig)
        
        # Set the parent if provided
        self.setParent(parent)
        
        # Create the axes for plotting
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#f9f9f9')  # Light gray background
        
        # Set up the plot with a cleaner, more minimalist style
        self.axes.grid(True, color='#e0e0e0', linestyle='-', linewidth=0.5)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['bottom'].set_color('#d0d0d0')
        self.axes.spines['left'].set_color('#d0d0d0')
        self.axes.tick_params(colors='#505050')
        
        # Y-axis label
        self.axes.set_ylabel('Heart Rate (BPM)', color='#505050')
        
        # Set up the x-axis for time formatting
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Initial y-axis range
        self.set_y_range(40, 120)
        
        # Tight layout
        self.fig.tight_layout(pad=2)
        
        # Store the line object
        self.line = None
        
        # Set background color of the widget
        self.setStyleSheet("background-color: #ffffff; border-radius: 10px;")
        
    def update_graph(self, data, timestamps):
        """Update the graph with new data."""
        if not data or len(data) < 2:
            return
            
        # Convert timestamps to datetime objects
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]
        
        # Clear previous plot
        self.axes.clear()
        
        # Set style again (as clear() removes it)
        self.axes.set_facecolor('#f9f9f9')
        self.axes.grid(True, color='#e0e0e0', linestyle='-', linewidth=0.5)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['bottom'].set_color('#d0d0d0')
        self.axes.spines['left'].set_color('#d0d0d0')
        self.axes.tick_params(colors='#505050')
        self.axes.set_ylabel('Heart Rate (BPM)', color='#505050')
        
        # Set time formatting
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Plot the data with a more modern visualization style
        # Use a gradient line
        main_color = '#E91E63'  # Material Design pink
        
        # Create gradient line
        self.line = self.axes.plot(dates, data, 
                                  color=main_color, 
                                  linewidth=2.5,
                                  marker='o',
                                  markersize=5,
                                  markerfacecolor='white',
                                  markeredgecolor=main_color,
                                  markeredgewidth=1.5)[0]
        
        # Add shaded area below line for better visualization
        self.axes.fill_between(dates, data, alpha=0.2, color=main_color)
        
        # Color regions based on heart rate zones
        self._add_hr_zone_highlights()
        
        # Set y-axis limits
        self._update_y_limits(data)
        
        # Format x-axis to show only the necessary range
        time_range = (dates[-1] - dates[0]).total_seconds()
        if time_range < 60:  # less than a minute
            self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        else:
            self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
        # Rotate x labels for better readability
        plt = self.figure.axes[0]
        plt.tick_params(axis='x', rotation=30)
        
        # Update the plot
        self.fig.tight_layout(pad=2)
        self.draw()
        
    def set_y_range(self, min_hr, max_hr):
        """Set the y-axis range."""
        self.axes.set_ylim(min_hr, max_hr)
        self.draw()
        
    def clear_graph(self):
        """Clear all data from the graph."""
        if self.line:
            self.line.set_xdata([])
            self.line.set_ydata([])
            self.draw()
            
    def _add_hr_zone_highlights(self):
        """Add colored background for different heart rate zones."""
        y_min, y_max = self.axes.get_ylim()
        
        # Define zones with more modern, subtle colors
        alpha = 0.1  # Subtle background
        
        # Below 50 (Danger low)
        self.axes.axhspan(y_min, 50, alpha=alpha, color='#F44336', zorder=0)  # Material Red
        
        # 50-60 (Warning low)
        self.axes.axhspan(50, 60, alpha=alpha, color='#FFC107', zorder=0)  # Material Amber
        
        # 60-90 (Normal)
        self.axes.axhspan(60, 90, alpha=alpha, color='#4CAF50', zorder=0)  # Material Green
        
        # 90-100 (Warning high)
        self.axes.axhspan(90, 100, alpha=alpha, color='#FFC107', zorder=0)  # Material Amber
        
        # Above 100 (Danger high)
        self.axes.axhspan(100, y_max, alpha=alpha, color='#F44336', zorder=0)  # Material Red
        
        # Add labels for the zones at the right edge
        self.axes.text(0.98, (50 + y_min) / 2 / y_max, "Low", transform=self.axes.get_yaxis_transform(),
                      ha='right', va='center', color='#D32F2F', fontsize=8, alpha=0.7)
        
        self.axes.text(0.98, 75 / y_max, "Normal", transform=self.axes.get_yaxis_transform(),
                      ha='right', va='center', color='#388E3C', fontsize=8, alpha=0.7)
        
        self.axes.text(0.98, (100 + y_max) / 2 / y_max, "High", transform=self.axes.get_yaxis_transform(),
                      ha='right', va='center', color='#D32F2F', fontsize=8, alpha=0.7)
        
    def _update_y_limits(self, data):
        """Update y-axis limits based on the data."""
        if data:
            data_min = min(data)
            data_max = max(data)
            
            # Add some padding
            y_min = max(30, data_min - 10) 
            y_max = min(200, data_max + 10)
            
            # Ensure reasonable range
            if y_max - y_min < 30:
                mean = (y_max + y_min) / 2
                y_min = mean - 15
                y_max = mean + 15
                
            self.axes.set_ylim(y_min, y_max)


class ProgressCircleWidget(QtWidgets.QWidget):
    """Circular progress indicator for signal quality."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0  # 0-100
        self.setMinimumSize(80, 80)
        # No animation properties or timers
        
    def setValue(self, value):
        """Set the progress value (0-100)."""
        self.value = max(0, min(100, value))
        self.update()
        
    def paintEvent(self, event):
        """Paint the progress circle with modern design."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = min(self.width(), self.height())
        outer_radius = width * 0.45
        inner_radius = outer_radius * 0.75
        center = QtCore.QPoint(int(self.width() / 2), int(self.height() / 2))
        
        # Draw drop shadow
        shadow_radius = outer_radius + 2
        shadow = QtGui.QRadialGradient(QtCore.QPointF(center), shadow_radius)
        shadow.setColorAt(0.8, QtGui.QColor(0, 0, 0, 30))
        shadow.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawEllipse(center, int(shadow_radius), int(shadow_radius))
        
        # Create base circle with subtle gradient
        base_gradient = QtGui.QRadialGradient(QtCore.QPointF(center), outer_radius)
        base_gradient.setColorAt(0, QtGui.QColor(240, 240, 240))
        base_gradient.setColorAt(1, QtGui.QColor(220, 220, 220))
        painter.setBrush(base_gradient)
        painter.drawEllipse(center, int(outer_radius), int(outer_radius))
        
        # Draw progress arc with nice gradient
        if self.value > 0:
            # Create colored pen based on value with material design colors
            if self.value < 50:
                # Red to amber gradient
                start_color = QtGui.QColor("#F44336")  # Material Red
                end_color = QtGui.QColor("#FFC107")    # Material Amber
                ratio = self.value / 50.0
                color = QtGui.QColor(
                    int(start_color.red() + (end_color.red() - start_color.red()) * ratio),
                    int(start_color.green() + (end_color.green() - start_color.green()) * ratio),
                    int(start_color.blue() + (end_color.blue() - start_color.blue()) * ratio)
                )
            else:
                # Amber to green gradient
                start_color = QtGui.QColor("#FFC107")  # Material Amber
                end_color = QtGui.QColor("#4CAF50")    # Material Green
                ratio = (self.value - 50) / 50.0
                color = QtGui.QColor(
                    int(start_color.red() + (end_color.red() - start_color.red()) * ratio),
                    int(start_color.green() + (end_color.green() - start_color.green()) * ratio),
                    int(start_color.blue() + (end_color.blue() - start_color.blue()) * ratio)
                )
            
            # Create arc path with rounded caps
            arc_width = outer_radius * 0.15
            pen = QtGui.QPen(color)
            pen.setWidth(int(arc_width))
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # No glow animation, just draw the main arc
            span_angle = int(self.value / 100 * 360 * 16)  # 16 is the QPainter angle unit
            painter.drawArc(
                int(center.x() - outer_radius * 0.85),
                int(center.y() - outer_radius * 0.85),
                int(outer_radius * 1.7),
                int(outer_radius * 1.7),
                90 * 16,  # Start at bottom
                -span_angle
            )
        
        # Draw inner circle with gradient
        inner_gradient = QtGui.QRadialGradient(QtCore.QPointF(center), inner_radius)
        inner_gradient.setColorAt(0, QtGui.QColor(255, 255, 255))
        inner_gradient.setColorAt(1, QtGui.QColor(245, 245, 245))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(inner_gradient)
        painter.drawEllipse(center, int(inner_radius), int(inner_radius))
        
        # Draw text with better typography
        label_font = QtGui.QFont("Segoe UI", int(inner_radius / 3))
        label_font.setWeight(QtGui.QFont.Weight.Medium)
        painter.setFont(label_font)
        
        # Draw "Signal Quality" label
        painter.setPen(QtGui.QColor(100, 100, 100))
        text_rect = QtCore.QRect(
            int(center.x() - inner_radius),
            int(center.y() - inner_radius * 0.6),
            int(inner_radius * 2),
            int(inner_radius * 0.5)
        )
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "Signal")
        
        # Draw percentage with value-based color
        value_font = QtGui.QFont("Segoe UI", int(inner_radius / 2))
        value_font.setWeight(QtGui.QFont.Weight.Bold)
        painter.setFont(value_font)
        
        # Use different colors based on quality
        if self.value < 30:
            painter.setPen(QtGui.QColor("#F44336"))  # Red
        elif self.value < 70:
            painter.setPen(QtGui.QColor("#FFC107"))  # Amber
        else:
            painter.setPen(QtGui.QColor("#4CAF50"))  # Green
            
        percentage_rect = QtCore.QRect(
            int(center.x() - inner_radius),
            int(center.y() - inner_radius * 0.1),
            int(inner_radius * 2),
            int(inner_radius * 0.7)
        )
        painter.drawText(percentage_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"{self.value}%")

