import matplotlib
matplotlib.use('QtAgg')  # Backend for PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
# import matplotlib.pyplot as plt # Tidak terpakai secara eksplisit di kelas ini

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, height=8, dark_mode=False):  # Increased height
        # Set default values first
        self.default_min = 40
        self.default_max = 180
        self.min_range = 60
        self.tick_spacing = 10
        self.dark_mode = dark_mode

        # Create figure with wider aspect ratio for side-by-side plots
        self.fig = Figure(figsize=(12, height), dpi=100, constrained_layout=True)  # Changed width to 12
        super().__init__(self.fig)
        
        self._apply_styling()
        # Change subplot layout to side-by-side
        self.ax1 = self.fig.add_subplot(121)  # Changed from 211 to 121
        self.ax2 = self.fig.add_subplot(122)  # Changed from 212 to 122
        
        self._initialize_plots()
        self._configure_plots()
        
        # Remove tight_layout since we're using constrained_layout
        # self.fig.tight_layout(pad=2.0)

        # Set both axes visible at start
        self.ax2.set_visible(True)
        
    def _apply_styling(self):
        if self.dark_mode:
            self.fig.patch.set_facecolor('#2E3440'); self.text_color = '#E5E9F0'
            self.grid_color = '#4C566A'; self.hr_color = '#5E81AC'; self.resp_color = '#8FBCBB'
        else:
            self.fig.patch.set_facecolor('#FFFFFF'); self.text_color = '#424242'
            self.grid_color = '#E0E0E0'; self.hr_color = '#E91E63'; self.resp_color = '#2196F3'

    def _initialize_plots(self):
        # Heart rate signal plot
        self.line_rppg, = self.ax1.plot([], [], '-', color=self.hr_color, linewidth=1.5, label='Sinyal HR')
        self.fill_rppg = None  # Inisialisasi fill object sebagai None

        # Peak markers untuk HR
        self.line_hr_peaks, = self.ax1.plot([], [], 'o', color='#FF5252', markersize=4, label='Puncak HR', visible=False)
        
        # Respiration signal plot
        self.line_resp, = self.ax2.plot([], [], '-', color=self.resp_color, linewidth=1.5, label='Sinyal Resp.')
        self.fill_resp = None  # Inisialisasi fill object sebagai None
        self.ax2.set_visible(True)  # Always show respiratory plot


    def _configure_plots(self):
        # Konfigurasi ax1 (Heart Rate)
        self.ax1.set_title('Sinyal Detak Jantung', color=self.text_color, fontsize=10)
        self.ax1.set_xlabel('Waktu Relatif (detik)', color=self.text_color, fontsize=9)
        self.ax1.set_ylabel('Amplitudo', color=self.text_color, fontsize=9)
        self.ax1.tick_params(axis='both', which='major', labelsize=8, colors=self.text_color)
        self.ax1.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        self.ax1.spines['top'].set_visible(False); self.ax1.spines['right'].set_visible(False)
        self.ax1.spines['bottom'].set_color(self.grid_color); self.ax1.spines['left'].set_color(self.grid_color)
        self.ax1.legend(loc='upper right', fontsize=8, frameon=False)

        # Konfigurasi ax2 (Respiration)
        self.ax2.set_title('Sinyal Respirasi', color=self.text_color, fontsize=10)
        self.ax2.set_xlabel('Waktu Relatif (detik)', color=self.text_color, fontsize=9)
        self.ax2.set_ylabel('Amplitudo', color=self.text_color, fontsize=9)
        self.ax2.tick_params(axis='both', which='major', labelsize=8, colors=self.text_color)
        self.ax2.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        self.ax2.spines['top'].set_visible(False); self.ax2.spines['right'].set_visible(False)
        self.ax2.spines['bottom'].set_color(self.grid_color); self.ax2.spines['left'].set_color(self.grid_color)
        self.ax2.legend(loc='upper right', fontsize=8, frameon=False)
    
    def update_plot(self, time_data, hr_data, resp_data=None, hr_peaks=None):
        if len(time_data) == 0 or len(hr_data) == 0:
            return
            
        # Convert inputs to numpy arrays
        time_data = np.array(time_data)
        hr_data = np.array(hr_data)
        
        # Make time relative
        time_plot = time_data - time_data[0]
        
        # Calculate visible window (last 10 seconds)
        window_size = 10  # seconds
        current_time = time_plot[-1]
        x_min = max(0, current_time - window_size)
        x_max = current_time + 1
        
        # Update HR plot
        self.line_rppg.set_data(time_plot, hr_data)
        self.ax1.set_xlim(x_min, x_max)
        
        # Set y limits for HR with margins
        visible_hr = hr_data[time_plot >= x_min]
        if len(visible_hr) > 0:
            hr_min = np.min(visible_hr)
            hr_max = np.max(visible_hr)
            hr_margin = max((hr_max - hr_min) * 0.2, 10)
            self.ax1.set_ylim(hr_min - hr_margin, hr_max + hr_margin)
        
        # Update respiratory plot
        if resp_data is not None and len(resp_data) > 0:
            self.ax2.set_visible(True)
            resp_data = np.array(resp_data)
            
            # Create time vector matching respiratory data length
            if len(resp_data) != len(time_plot):
                resp_time = np.linspace(time_plot[0], time_plot[-1], len(resp_data))
            else:
                resp_time = time_plot
            
            self.line_resp.set_data(resp_time, resp_data)
            
            # Set y limits for respiratory plot
            resp_min, resp_max = np.min(resp_data), np.max(resp_data)
            resp_margin = max((resp_max - resp_min) * 0.2, 0.1)
            self.ax2.set_ylim(resp_min - resp_margin, resp_max + resp_margin)
            
            # Set same x limits for respiratory plot
            self.ax2.set_xlim(x_min, x_max)
            
            # Update fill between with matching time vector
            if self.fill_resp is not None:
                self.fill_resp.remove()
            self.fill_resp = self.ax2.fill_between(
                resp_time,
                np.ones_like(resp_data) * (resp_min - resp_margin),
                resp_data,
                alpha=0.2,
                color=self.resp_color
            )
        
        self.draw_idle()
        
    def clear_data(self):
        self.line_rppg.set_data([], [])
        self.line_resp.set_data([], [])
        self.line_hr_peaks.set_data([], [])
        self.line_hr_peaks.set_visible(False)

        if self.fill_rppg is not None:
            self.fill_rppg.remove()
            self.fill_rppg = None
        if self.fill_resp is not None:
            self.fill_resp.remove()
            self.fill_resp = None
        
        self.ax1.relim(); self.ax1.autoscale_view()
        self.ax2.relim(); self.ax2.autoscale_view()
        # Kosongkan juga judul sumbu jika perlu atau set ke default
        # self.ax2.set_visible(False) # Sembunyikan plot respirasi saat clear
        self.fig.tight_layout(pad=2.0)
        self.draw_idle()
            
    def set_dark_mode(self, enabled):
        if self.dark_mode != enabled:
            self.dark_mode = enabled
            self._apply_styling()
            self._configure_plots() # Konfigurasi ulang warna teks, grid, dll.
            # Re-plot data yang ada dengan style baru jika perlu, atau biarkan update_plot berikutnya
            self.fig.tight_layout(pad=2.0)
            self.draw_idle()