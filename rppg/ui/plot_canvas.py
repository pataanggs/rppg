import matplotlib
matplotlib.use('QtAgg')  # Backend for PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
# import matplotlib.pyplot as plt # Tidak terpakai secara eksplisit di kelas ini

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, height=5, dark_mode=False):
        self.fig = Figure(figsize=(8, height), dpi=100, constrained_layout=False) # constrained_layout=False dulu, lalu tight_layout
        super().__init__(self.fig)
        self.dark_mode = dark_mode
        self._apply_styling()
        self.ax1 = self.fig.add_subplot(211)  # Heart rate signal
        self.ax2 = self.fig.add_subplot(212)  # Respiration signal
        self._initialize_plots()
        self._configure_plots()
        self.fig.tight_layout(pad=2.0) # Panggil setelah subplot dibuat


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
        self.ax2.set_visible(False) # Sembunyikan plot respirasi di awal jika tidak ada data


    def _configure_plots(self):
        # Konfigurasi ax1 (Heart Rate)
        self.ax1.set_title('Riwayat Detak Jantung', color=self.text_color, fontsize=10) # Judul bisa ini atau "Sinyal Detak Jantung"
        self.ax1.set_xlabel('Waktu Relatif (detik)', color=self.text_color, fontsize=9)
        
        self.ax1.set_ylabel('Detak Jantung (BPM)', color=self.text_color, fontsize=9) 
        self.ax1.set_ylim(40, 160)  
        
        self.ax1.tick_params(axis='both', which='major', labelsize=8, colors=self.text_color)
        self.ax1.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        self.ax1.spines['top'].set_visible(False); self.ax1.spines['right'].set_visible(False)
        self.ax1.spines['bottom'].set_color(self.grid_color); self.ax1.spines['left'].set_color(self.grid_color)
        self.ax1.legend(loc='upper right', fontsize=8, frameon=False)

        # Konfigurasi ax2 (Respiration) - Biarkan seperti sebelumnya jika belum dipakai aktif
        self.ax2.set_title('Sinyal Respirasi (Contoh)', color=self.text_color, fontsize=10)
        self.ax2.set_xlabel('Waktu Relatif (detik)', color=self.text_color, fontsize=9)
        self.ax2.set_ylabel('Amplitudo', color=self.text_color, fontsize=9) # Sumbu Y ax2 bisa tetap Amplitudo
        # self.ax2.set_ylim(Y_MIN_RESP, Y_MAX_RESP) # Jika perlu, atur juga Y-lim untuk respirasi
        self.ax2.tick_params(axis='both', which='major', labelsize=8, colors=self.text_color)
        self.ax2.grid(True, linestyle='--', alpha=0.7, color=self.grid_color)
        self.ax2.spines['top'].set_visible(False); self.ax2.spines['right'].set_visible(False)
        self.ax2.spines['bottom'].set_color(self.grid_color); self.ax2.spines['left'].set_color(self.grid_color)
        self.ax2.legend(loc='upper right', fontsize=8, frameon=False)
        # self.ax2.set_visible(False) # Kamu bisa set ax2 tidak terlihat di awal jika belum ada data

        try:
            self.fig.tight_layout(pad=2.0) # Panggil setelah semua konfigurasi subplot
        except Exception:
            pass # Kadang tight_layout bisa error jika figure belum siap sepenuhnya
    
    
    def update_plot(self, time_data, hr_data, resp_data=None, hr_peaks=None):
        if not isinstance(time_data, np.ndarray): time_data = np.array(time_data)
        if not isinstance(hr_data, np.ndarray): hr_data = np.array(hr_data)
        if resp_data is not None and not isinstance(resp_data, np.ndarray): resp_data = np.array(resp_data)

        if len(time_data) == 0 or len(hr_data) == 0:
            self.clear_data() # Atau return saja jika tidak ingin clear saat data kosong sementara
            return
            
        time_plot = time_data
        # Jika time_data adalah unix timestamp, buat relatif dari titik pertama data saat ini
        if len(time_data) > 0 and time_data[0] > 1e9 : 
            time_plot = time_data - time_data[0]

        # --- Update Heart Rate Plot (ax1) ---
        self.line_rppg.set_data(time_plot, hr_data)
        
        # Hapus fill sebelumnya jika ada
        if self.fill_rppg is not None:
            self.fill_rppg.remove()
            self.fill_rppg = None 
        # Buat fill baru
        if hr_data.size > 0:
             # Gunakan baseline 0 atau nilai min dari data untuk fill
            baseline_hr = 0 # atau np.min(hr_data) jika ingin fill dari min data
            self.fill_rppg = self.ax1.fill_between(time_plot, baseline_hr, hr_data, alpha=0.2, color=self.hr_color, interpolate=True)
        
        # Update peak markers
        if hr_peaks is not None and len(hr_peaks) > 0:
            peak_times_plot = [time_plot[i] for i in hr_peaks if 0 <= i < len(time_plot)]
            peak_values_plot = [hr_data[i] for i in hr_peaks if 0 <= i < len(hr_data)]
            if peak_times_plot and peak_values_plot: # Pastikan tidak kosong
                self.line_hr_peaks.set_data(peak_times_plot, peak_values_plot)
                self.line_hr_peaks.set_visible(True)
            else:
                self.line_hr_peaks.set_data([], [])
                self.line_hr_peaks.set_visible(False)
        else:
            self.line_hr_peaks.set_data([], [])
            self.line_hr_peaks.set_visible(False)
        
        self.ax1.relim()
        self.ax1.autoscale_view(scalex=True, scaley=False)

        # --- Update Respiration Plot (ax2) ---
        if resp_data is not None and len(resp_data) == len(time_plot):
            self.ax2.set_visible(True)
            self.line_resp.set_data(time_plot, resp_data)
            if self.fill_resp is not None:
                self.fill_resp.remove()
                self.fill_resp = None
            if resp_data.size > 0:
                baseline_resp = 0 # atau np.min(resp_data)
                self.fill_resp = self.ax2.fill_between(time_plot, baseline_resp, resp_data, alpha=0.2, color=self.resp_color, interpolate=True)
            self.ax2.relim()
            self.ax2.autoscale_view()
        else:
            self.line_resp.set_data([], [])
            if self.fill_resp is not None:
                self.fill_resp.remove()
                self.fill_resp = None
            self.ax2.set_visible(False) # Sembunyikan jika tidak ada data respirasi

        # Pastikan legenda selalu ada setelah autoscale
        self.ax1.legend(loc='upper right', fontsize=8, frameon=False)
        if self.ax2.get_visible():
            self.ax2.legend(loc='upper right', fontsize=8, frameon=False)

        self.fig.tight_layout(pad=2.0) # Panggil lagi setelah data berubah untuk adjust layout
        self.draw_idle() # Gunakan draw_idle untuk efisiensi
        
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