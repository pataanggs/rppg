from PyQt6 import QtWidgets, QtCore, QtGui
import time


class HeartRateDisplay(QtWidgets.QWidget):
    """Widget to display the current heart rate and graph of heart rate history."""
    def __init__(self):
        super().__init__()
        self.heart_rate = 0
        self.history = []
        self.history_times = []
        self.display_color = QtGui.QColor(220, 0, 0)
        self.setMinimumHeight(200)  # Increased height for better visualization
        self.setMinimumWidth(250)
        self.last_update_time = time.time()
        self.show_seconds = 30  # Show 30 seconds of history
        
    def set_heart_rate(self, hr):
        """Update the heart rate and add it to the history."""
        self.heart_rate = hr
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
        
        # Draw background
        painter.fillRect(event.rect(), QtGui.QColor(240, 240, 240))
        
        # Draw title
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(60, 60, 60))
        painter.drawText(10, 25, "Heart Rate Monitor")
        
        # Draw heart rate with larger font
        font.setPointSize(36)
        painter.setFont(font)
        painter.setPen(self.display_color)
        painter.drawText(10, 70, f"{self.heart_rate:.1f}")
        
        # Draw "BPM" text
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(120, 70, "BPM")
        
        # Draw horizontal separator line
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200), 1))
        painter.drawLine(10, 85, self.width() - 10, 85)
        
        # Draw the heart rate history graph if available
        if len(self.history) > 1:
            self._draw_heart_rate_graph(painter)
            
        # Draw graph border
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200), 1))
        graph_rect = QtCore.QRect(10, 95, self.width() - 20, self.height() - 105)
        painter.drawRect(graph_rect)
    
    def _draw_heart_rate_graph(self, painter):
        """Draw the heart rate graph based on history."""
        # Area for the graph
        graph_width = self.width() - 20
        graph_height = self.height() - 105
        y_base = 95 + graph_height
        
        # If we have time values, use them for x-axis scaling
        x_scale = graph_width / self.show_seconds if self.history_times else graph_width / 100
        
        # Normalize heart rate values for y-axis scaling
        if not self.history:
            return
            
        max_hr = max(max(self.history), 120)
        min_hr = min(min(self.history), 40)
        if max_hr == min_hr:  # Avoid division by zero
            hr_range = 50
            min_hr = max_hr - 50
        else:
            hr_range = max_hr - min_hr
            
        # Create gradient for fill
        gradient = QtGui.QLinearGradient(0, y_base, 0, y_base - graph_height)
        gradient.setColorAt(0, QtGui.QColor(self.display_color.red(), self.display_color.green(),
                                          self.display_color.blue(), 30))
        gradient.setColorAt(1, QtGui.QColor(self.display_color.red(), self.display_color.green(),
                                          self.display_color.blue(), 5))
        
        # Create path for the line
        path = QtGui.QPainterPath()
        fill_path = QtGui.QPainterPath()
        
        # Get the current time for relative x-position
        current_time = time.time() if self.history_times else 0
        
        # Start points
        if self.history_times:
            x = graph_width - (current_time - self.history_times[0]) * x_scale
        else:
            x = 10
            
        y = y_base - ((self.history[0] - min_hr) / hr_range) * graph_height
        path.moveTo(x, y)
        fill_path.moveTo(x, y_base)
        fill_path.lineTo(x, y)
        
        # Add points to the path
        for i in range(1, len(self.history)):
            if self.history_times:
                x = graph_width - (current_time - self.history_times[i]) * x_scale + 10
            else:
                x = 10 + i * (graph_width / len(self.history))
                
            y = y_base - ((self.history[i] - min_hr) / hr_range) * graph_height
            path.lineTo(x, y)
            fill_path.lineTo(x, y)
            
        # Complete the fill path
        fill_path.lineTo(x, y_base)
        fill_path.closeSubpath()
        
        # Draw the fill
        painter.fillPath(fill_path, gradient)
        
        # Draw the line
        painter.setPen(QtGui.QPen(self.display_color, 2))
        painter.drawPath(path)
        
        # Draw horizontal guide lines
        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 1, QtCore.Qt.PenStyle.DashLine))
        steps = 4
        for i in range(steps + 1):
            # Convert y_pos to integer to fix TypeError
            y_pos = int(y_base - (i * graph_height / steps))
            hr_val = min_hr + (i * hr_range / steps)
            painter.drawLine(10, y_pos, self.width() - 10, y_pos)
            
            # Label the guide lines with HR values (also fix y-coordinate)
            if i > 0 and i < steps:  # Skip the top and bottom lines
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                painter.setPen(QtGui.QColor(100, 100, 100))
                painter.drawText(self.width() - 35, y_pos - 5, f"{int(hr_val)}")
