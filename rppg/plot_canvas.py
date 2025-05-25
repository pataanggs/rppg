"""
Matplotlib Canvas for rPPG Signal Visualization

This module provides a specialized Matplotlib canvas for visualizing 
physiological signals from the rPPG monitoring system, including heart rate 
and respiration signals with enhanced visual styling.
"""

import matplotlib
matplotlib.use('QtAgg')  # Backend for PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt


class MplCanvas(FigureCanvas):
    """
    Matplotlib canvas for plotting rPPG and respiration signals with enhanced visualization.
    
    This canvas provides real-time visualization of physiological signals with
    modern styling, gradient fills, and flexible display options.
    """
    
    def __init__(self, parent=None, height=5, dark_mode=False):
        """
        Initialize the plotting canvas with configurable appearance.
        
        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
            height (int, optional): Figure height in inches. Defaults to 5.
            dark_mode (bool, optional): Use dark mode styling. Defaults to False.
        """
        # Create figure with specified size
        self.fig = Figure(figsize=(8, height), dpi=100, constrained_layout=True)
        super().__init__(self.fig)
        
        # Set style based on mode
        self.dark_mode = dark_mode
        self._apply_styling()
        
        # Create the subplot axes
        self.ax1 = self.fig.add_subplot(211)  # Heart rate signal
        self.ax2 = self.fig.add_subplot(212)  # Respiration signal
        
        # Initialize empty plots with enhanced styling
        self._initialize_plots()
        
        # Configure plot appearance
        self._configure_plots()
    
    def _apply_styling(self):
        """Apply visual styling based on selected mode."""
        if self.dark_mode:
            # Dark mode styling
            self.fig.patch.set_facecolor('#2E3440')
            self.text_color = '#E5E9F0'
            self.grid_color = '#4C566A'
            self.hr_color = '#5E81AC'
            self.resp_color = '#8FBCBB'
            
            plt.style.use('dark_background')
        else:
            # Light mode styling (default)
            self.fig.patch.set_facecolor('#FFFFFF')
            self.text_color = '#424242'
            self.grid_color = '#E0E0E0'
            self.hr_color = '#E91E63'
            self.resp_color = '#2196F3'
    
    def _initialize_plots(self):
        """Initialize the plot lines and fill areas."""
        # Heart rate signal plot
        self.line_rppg, = self.ax1.plot([], [], '-', color=self.hr_color, 
                                       linewidth=1.5, label='Heart Rate Signal')
        
        # Create fill area under the heart rate curve
        self.fill_rppg = self.ax1.fill_between([], [], alpha=0.2, color=self.hr_color)
        
        # Respiration signal plot
        self.line_resp, = self.ax2.plot([], [], '-', color=self.resp_color, 
                                      linewidth=1.5, label='Respiration Signal')
        
        # Create fill area under the respiration curve
        self.fill_resp = self.ax2.fill_between([], [], alpha=0.2, color=self.resp_color)
    
    def _configure_plots(self):
        """Configure plot appearance with titles, labels, and styling."""
        # Configure heart rate plot
        self.ax1.set_title('Heart Rate Signal', color=self.text_color, fontsize=12)
        self.ax1.set_xlabel('Time (s)', color=self.text_color, fontsize=10)
        self.ax1.set_ylabel('Amplitude', color=self.text_color, fontsize=10)
        self.ax1.tick_params(colors=self.text_color)
        self.ax1.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        self.ax1.spines['top'].set_visible(False)
        self.ax1.spines['right'].set_visible(False)
        
        # Configure respiration plot
        self.ax2.set_title('Respiration Signal', color=self.text_color, fontsize=12)
        self.ax2.set_xlabel('Time (s)', color=self.text_color, fontsize=10)
        self.ax2.set_ylabel('Amplitude', color=self.text_color, fontsize=10)
        self.ax2.tick_params(colors=self.text_color)
        self.ax2.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        self.ax2.spines['top'].set_visible(False)
        self.ax2.spines['right'].set_visible(False)
        
        # Add legends with improved styling
        self.ax1.legend(loc='upper right', fontsize=9, framealpha=0.7)
        self.ax2.legend(loc='upper right', fontsize=9, framealpha=0.7)
        
    def update_plot(self, time_data, hr_data, resp_data=None, hr_peaks=None):
        """
        Update the plots with new data.
        
        Args:
            time_data (np.ndarray): Time values for x-axis
            hr_data (np.ndarray): Heart rate signal values
            resp_data (np.ndarray, optional): Respiration signal values. If None,
                                              respiration plot is not updated.
            hr_peaks (list, optional): Indices of detected peaks in hr_data.
                                       If provided, they will be highlighted.
        """
        if len(time_data) == 0 or len(hr_data) == 0:
            return
            
        # Update heart rate plot
        self.line_rppg.set_data(time_data, hr_data)
        
        # Update fill area
        self.ax1.collections.clear()  # Clear previous fill
        self.ax1.fill_between(time_data, 0, hr_data, alpha=0.2, color=self.hr_color)
        
        # Add peak indicators if provided
        if hr_peaks is not None and len(hr_peaks) > 0:
            peak_times = [time_data[i] for i in hr_peaks if i < len(time_data)]
            peak_values = [hr_data[i] for i in hr_peaks if i < len(hr_data)]
            self.ax1.plot(peak_times, peak_values, 'o', color='#FF5252', markersize=4)
        
        # Update respiration plot if data is provided
        if resp_data is not None and len(resp_data) == len(time_data):
            self.line_resp.set_data(time_data, resp_data)
            
            # Update fill area
            self.ax2.collections.clear()  # Clear previous fill
            self.ax2.fill_between(time_data, 0, resp_data, alpha=0.2, color=self.resp_color)
        
        # Auto-scale the axes to fit the data
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        
        # Draw the canvas
        self.draw()
        
    def clear_data(self):
        """Clear all plot data."""
        self.line_rppg.set_data([], [])
        self.line_resp.set_data([], [])
        self.ax1.collections.clear()
        self.ax2.collections.clear()
        self.draw()
        
    def set_dark_mode(self, enabled):
        """
        Toggle between dark and light mode.
        
        Args:
            enabled (bool): True for dark mode, False for light mode
        """
        if self.dark_mode != enabled:
            self.dark_mode = enabled
            self._apply_styling()
            self._configure_plots()
            self.draw() 