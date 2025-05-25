import matplotlib
matplotlib.use('QtAgg')  # Backend untuk PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class MplCanvas(FigureCanvas):
    """Matplotlib canvas for plotting rPPG and respiration signals."""
    def __init__(self, parent=None, height=5):
        self.fig = Figure(figsize=(8, height), dpi=100)
        super().__init__(self.fig)

        # Create two subplots
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)

        # Plot initial empty lines with labels
        self.line_rppg, = self.ax1.plot([], [], 'r-', label='rPPG Signal')
        self.line_resp, = self.ax2.plot([], [], 'b-', label='Respiration Signal')

        # Set titles and labels
        self.ax1.set_title('rPPG Signal')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Amplitude')
        self.ax1.grid(True)

        self.ax2.set_title('Respiration Signal')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Amplitude')
        self.ax2.grid(True)

        # Add legends
        self.ax1.legend(loc='upper right', fontsize=10)
        self.ax2.legend(loc='upper right', fontsize=10)

        # Adjust layout manually to avoid tight_layout warning
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15, hspace=0.4)