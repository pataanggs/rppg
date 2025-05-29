# rppg/signal/signal_processor.py
import numpy as np
from scipy import signal as sg
from scipy.interpolate import interp1d
import sys # Untuk error printing

class SignalProcessor:
    """Processes raw rPPG signals to extract heart rate information."""
    
    def __init__(self):
        """Initialize the signal processor."""
        self.last_hr = None
        self.hr_history = []
        self.max_history = 10  # Jumlah HR terakhir untuk smoothing
        self.signal_quality = 0.0 # Kualitas sinyal dalam persentase (0-100)
        self.resp_buffer = []  # Add respiratory signal buffer
        print("SignalProcessor (User's Version) Initialized")
    
    def process(self, signal, timestamps):
        """Process a raw PPG signal to estimate heart rate.
        
        Args:
            signal: List of raw signal values (green channel averages)
            timestamps: List of timestamps corresponding to signal samples
            
        Returns:
            Tuple of (heart_rate, confidence, signal_quality)
            heart_rate (float or None): Estimated heart rate in BPM.
            confidence (float): Confidence of the HR estimation (0.0 to 1.0).
            signal_quality (float): Quality of the signal (0.0 to 100.0).
        """
        try:
            print(f"Processing signal length: {len(signal)}")  # Debug print
            
            if not isinstance(signal, list) or not isinstance(timestamps, list):
                print("SignalProcessor: Input 'signal' and 'timestamps' harus berupa list.")
                return None, 0.0, 0.0
                
            if len(signal) < 60:  # Butuh minimal sekitar 2 detik data @30fps
                # print("SignalProcessor: Data sinyal tidak cukup.")
                self.signal_quality = 0.0 # Set kualitas rendah jika data tidak cukup
                return None, 0.0, self.signal_quality
                
            # Hitung frekuensi sampling (fs)
            if timestamps[-1] - timestamps[0] <= 0:
                print("SignalProcessor: Durasi timestamps tidak valid.")
                self.signal_quality = 0.0
                return None, 0.0, self.signal_quality
            fs = len(signal) / (timestamps[-1] - timestamps[0])
            if fs <= 0: # Perlu fs positif
                print(f"SignalProcessor: Frekuensi sampling tidak valid: {fs}")
                self.signal_quality = 0.0
                return None, 0.0, self.signal_quality
                
            signal_array = np.array(signal, dtype=float) # Pastikan float
            
            # 1. Hapus Outlier
            signal_array = self._remove_outliers(signal_array)
            
            # 2. Normalisasi sinyal (0-1)
            min_val, max_val = np.min(signal_array), np.max(signal_array)
            if max_val - min_val < 1e-10: # Hindari pembagian dengan nol jika sinyal datar
                # print("SignalProcessor: Sinyal datar setelah outlier removal.")
                self.signal_quality = 0.0
                return None, 0.0, self.signal_quality
            signal_normalized = (signal_array - min_val) / (max_val - min_val)
            
            # 3. Detrending
            detrended_signal = sg.detrend(signal_normalized)
            
            # 4. Interpolasi untuk sampling rate yang uniform (jika perlu)
            # Untuk rPPG, timestamps dari frame video biasanya sudah cukup uniform
            # Namun, jika ada frame drop, interpolasi bisa membantu.
            # Disarankan untuk memastikan timestamps dari ProcessThread sudah se-uniform mungkin.
            # Untuk sekarang, kita asumsikan timestamps yang masuk sudah cukup baik.
            # Jika outlier removal mengubah panjang, perlu penyesuaian
            uniform_time_vector = np.linspace(timestamps[0], timestamps[-1], len(detrended_signal))
            # (Jika panjang signal_array dan detrended_signal berbeda karena outlier removal,
            #  logika interpolasi f = interp1d(timestamps, detrended_signal,...) perlu disesuaikan
            #  agar timestamps dan detrended_signal punya panjang yang sama sebelum interp1d)
            # Untuk sementara, kita anggap panjangnya sama setelah outlier removal
            # atau outlier removal tidak signifikan mengubah panjang.
            # Jika berbeda, ini bisa jadi sumber error:
            if len(uniform_time_vector) != len(detrended_signal):
                # Jika panjang berbeda, kita harus melakukan interpolasi pada timestamps asli ke panjang detrended_signal
                # atau sebaliknya. Ini bisa rumit jika outlier removal signifikan.
                # Untuk sekarang, kita resize detrended_signal agar cocok dengan uniform_time_vector jika panjangnya beda sedikit
                if abs(len(uniform_time_vector) - len(detrended_signal)) < 5 and len(uniform_time_vector)>0: # Toleransi perbedaan kecil
                    # print(f"Warning: Resampling detrended signal from {len(detrended_signal)} to {len(uniform_time_vector)}")
                    resampled_detrended = np.interp(uniform_time_vector, 
                                                    np.linspace(timestamps[0], timestamps[-1], len(detrended_signal)), 
                                                    detrended_signal)
                    detrended_signal = resampled_detrended
                else:
                    # print(f"SignalProcessor: Perbedaan panjang signifikan setelah detrend/outlier removal. {len(uniform_time_vector)} vs {len(detrended_signal)}")
                    self.signal_quality = 10.0 # Kualitas rendah
                    # return None, 0.0, self.signal_quality # Atau coba lanjutkan dengan risiko

            # 5. Bandpass Filter (misal 0.7 Hz - 4 Hz, atau 42-240 BPM)
            lowcut_hz = 0.7
            highcut_hz = 4.0
            nyquist_freq = 0.5 * fs
            
            # Pastikan frekuensi cutoff valid
            if lowcut_hz >= nyquist_freq or highcut_hz >= nyquist_freq or lowcut_hz <= 0 or highcut_hz <=0:
                # print(f"SignalProcessor: Frekuensi cutoff tidak valid untuk fs={fs:.2f}. Melewati filter.")
                filtered_signal = detrended_signal # Atau uniform_signal jika interpolasi dipakai
                self.signal_quality = 15.0 # Kualitas rendah karena filter gagal
            else:
                low = lowcut_hz / nyquist_freq
                high = highcut_hz / nyquist_freq
                # Pastikan low < high dan keduanya antara 0 dan 1
                if low >= high or not (0 < low < 1 and 0 < high < 1):
                    # print(f"SignalProcessor: Frekuensi normalisasi tidak valid: low={low:.2f}, high={high:.2f}. Melewati filter.")
                    filtered_signal = detrended_signal
                    self.signal_quality = 15.0
                else:
                    try:
                        b, a = sg.butter(3, [low, high], btype='bandpass')
                        filtered_signal = sg.filtfilt(b, a, detrended_signal) # Atau uniform_signal
                    except ValueError as ve:
                        print(f"SignalProcessor: Error saat filtering butterworth: {ve}. Melewati filter.")
                        filtered_signal = detrended_signal
                        self.signal_quality = 15.0


            # 6. Moving Average Smoothing (opsional, bisa membantu sebelum peak detection)
            # window_ma = max(3, int(fs / 10)) # Jendela adaptif
            # smoothed_signal = np.convolve(filtered_signal, np.ones(window_ma)/window_ma, mode='same')
            smoothed_signal = filtered_signal # Untuk sekarang, pakai yang sudah difilter

            # 7. Estimasi Heart Rate
            # Time domain (peak detection)
            # Jarak minimal antar peak (misal tidak lebih cepat dari 240 BPM = 0.25s atau fs/4)
            # Tinggi peak dan prominence bisa diadaptasi dari standar deviasi sinyal
            min_peak_dist = fs / (240.0 / 60.0) # Max HR 240 BPM
            peaks, properties = sg.find_peaks(smoothed_signal, 
                                              distance=min_peak_dist, 
                                              height=0.1 * np.std(smoothed_signal) if np.std(smoothed_signal) > 1e-5 else 0.01,
                                              prominence=0.1 * np.std(smoothed_signal) if np.std(smoothed_signal) > 1e-5 else 0.01)
            
            time_domain_hr = None
            if len(peaks) > 1:
                peak_ts = np.array(uniform_time_vector)[peaks] # Gunakan uniform_time_vector jika interpolasi dilakukan
                intervals = np.diff(peak_ts)
                # Filter interval yang tidak wajar (misal <0.25s atau >1.5s)
                valid_intervals = intervals[(intervals > 60.0/200.0) & (intervals < 60.0/40.0)] 
                if len(valid_intervals) > 0:
                    mean_interval = np.mean(valid_intervals)
                    time_domain_hr = 60.0 / mean_interval
                
                # Perhitungan Kualitas Sinyal dari variasi interval antar peak
                if len(valid_intervals) >= 2: # Butuh setidaknya 2 interval valid
                    # Koefisien variasi dari interval antar peak
                    cv_interval = np.std(valid_intervals) / (np.mean(valid_intervals) + 1e-10)
                    # Kualitas berbanding terbalik dengan variasi, skala 0-100
                    self.signal_quality = max(0.0, min(100.0, (1.0 - cv_interval * 2.0) * 100.0)) 
                elif len(peaks) > 2: # Jika ada peak tapi interval tidak banyak yg valid
                    self.signal_quality = 30.0 
                else:
                    self.signal_quality = 10.0 # Sedikit peak, kualitas rendah
            else:
                self.signal_quality = 5.0 # Tidak ada peak yang cukup

            # Frequency domain (FFT)
            fft_hr = self._fft_heart_rate(smoothed_signal, fs)
            
            # 8. Kombinasi dan Smoothing HR
            final_hr = self._combine_hr_estimates(time_domain_hr, fft_hr)
            
            # 9. Estimasi Confidence
            confidence = 0.0
            if final_hr is not None:
                # Confidence berdasarkan kualitas sinyal dan seberapa dekat estimasi time & freq domain
                quality_component = self.signal_quality / 100.0 # Normalisasi kualitas ke 0-1
                
                agreement_component = 0.0
                if time_domain_hr is not None and fft_hr is not None:
                    diff_hr = abs(time_domain_hr - fft_hr)
                    agreement_component = max(0, 1.0 - (diff_hr / 15.0)) # Jika beda < 15 BPM, agreement bagus
                elif time_domain_hr is not None or fft_hr is not None: # Jika hanya satu estimasi
                    agreement_component = 0.5 

                # Bobot: kualitas lebih penting
                confidence = (quality_component * 0.7) + (agreement_component * 0.3)
                confidence = max(0.0, min(1.0, confidence)) # Pastikan 0-1
            else: # Jika HR tidak terdeteksi, confidence & quality rendah
                self.signal_quality = 0.0
                confidence = 0.0
                
            # Pastikan signal_quality selalu ada nilainya
            # print(f"HR: {final_hr}, Conf: {confidence:.2f}, Quality: {self.signal_quality:.1f}%")
            
            # Extract respiratory signal (0.1 - 0.4 Hz)
            resp_lowcut = 0.1
            resp_highcut = 0.4
            nyq = 0.5 * fs
            
            # Create respiratory signal
            try:
                b_resp, a_resp = sg.butter(2, [resp_lowcut/nyq, resp_highcut/nyq], btype='bandpass')
                respiratory_signal = sg.filtfilt(b_resp, a_resp, signal_normalized)
            except Exception as e:
                print(f"Respiratory filter error: {e}")
                respiratory_signal = np.zeros_like(signal_normalized)
            
            # Process heart rate
            hr, confidence, quality = self._process_hr(filtered_signal, fs)
            
            print(f"Processed - HR: {hr}, Quality: {quality}")  # Debug print
            
            # Ensure we always return a valid numpy array for respiratory signal
            if respiratory_signal is None:
                respiratory_signal = np.zeros_like(signal_normalized)
            
            return hr, confidence, quality, respiratory_signal
            
        except Exception as e:
            print(f"SignalProcessor Error: {e}")
            # Return zero array instead of None
            return None, 0.0, 0.0, np.zeros(len(signal))

    def _remove_outliers(self, signal_data):
        """Versi lain dari remove outlier menggunakan IQR atau kliping sederhana."""
        # Metode sederhana: kliping berdasarkan persentil
        # Ini kurang canggih dari z-score tapi lebih tahan terhadap distribusi non-normal
        # Atau kamu bisa tetap pakai z-score yang sudah ada
        
        # Menggunakan metode IQR yang lebih robust
        q1 = np.percentile(signal_data, 25)
        q3 = np.percentile(signal_data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        # Ganti outlier dengan nilai batas, atau bisa juga dengan median/mean dari non-outlier
        cleaned_signal = np.clip(signal_data, lower_bound, upper_bound)
        return cleaned_signal

    def _fft_heart_rate(self, signal_data, fs):
        """Estimasi HR menggunakan FFT dengan metode Welch."""
        try:
            n = len(signal_data)
            if n < fs * 2: # Butuh minimal 2 detik data untuk FFT yang berarti
                # print("FFT: Data tidak cukup untuk FFT yang reliable.")
                return None

            # Gunakan metode Welch untuk estimasi Power Spectral Density (PSD)
            # nperseg bisa diatur, misal panjang jendela 4-8 detik data
            win_len_sec = min(8.0, n / fs) # Maksimal 8 detik atau seluruh sinyal
            nperseg_val = int(win_len_sec * fs)
            if nperseg_val < 1: nperseg_val = n # Jaga-jaga jika nperseg_val terlalu kecil
            
            freqs, psd = sg.welch(signal_data, fs, nperseg=nperseg_val, scaling='density', window='hann')
            
            # Cari peak di rentang frekuensi jantung (0.7 Hz - 4 Hz atau 42-240 BPM)
            valid_freq_mask = (freqs >= 0.7) & (freqs <= 4.0)
            
            if not np.any(valid_freq_mask) or len(psd[valid_freq_mask]) == 0 :
                return None

            relevant_freqs = freqs[valid_freq_mask]
            relevant_psd = psd[valid_freq_mask]
            
            if len(relevant_psd) == 0:
                return None

            # Cari peak utama di PSD
            # Jarak antar peak di domain frekuensi, misal minimal 0.3 Hz
            # Tinggi peak bisa relatif terhadap max PSD di rentang itu
            fft_peaks_indices, _ = sg.find_peaks(relevant_psd, 
                                                 height=np.max(relevant_psd) * 0.1, 
                                                 distance=int(0.3 / (freqs[1]-freqs[0])) if len(freqs)>1 and freqs[1]-freqs[0]>0 else 3) 
            
            if len(fft_peaks_indices) > 0:
                # Ambil peak dengan power tertinggi
                dominant_peak_index_in_relevant = fft_peaks_indices[np.argmax(relevant_psd[fft_peaks_indices])]
                peak_freq = relevant_freqs[dominant_peak_index_in_relevant]
                return peak_freq * 60  # Convert Hz to BPM
            else: # Jika tidak ada peak yang signifikan, coba ambil max saja
                dominant_peak_index_in_relevant = np.argmax(relevant_psd)
                peak_freq = relevant_freqs[dominant_peak_index_in_relevant]
                return peak_freq*60
                
        except Exception as e:
            print(f"FFT Error: {e} at line {sys.exc_info()[-1].tb_lineno}")
            return None
    
    def _combine_hr_estimates(self, time_domain_hr, freq_domain_hr):
        """Kombinasi estimasi HR dari domain waktu dan frekuensi."""
        # Prioritaskan frekuensi domain jika tersedia, karena cenderung lebih stabil
        if freq_domain_hr is not None:
            hr_candidate = freq_domain_hr
        elif time_domain_hr is not None:
            hr_candidate = time_domain_hr
        else:
            return None # Tidak ada estimasi valid

        # Jika kedua estimasi ada dan bedanya jauh, mungkin ada masalah
        if time_domain_hr is not None and freq_domain_hr is not None:
            if abs(time_domain_hr - freq_domain_hr) > 15 and self.last_hr is not None:
                # Jika beda jauh, pilih yang lebih dekat dengan HR terakhir (jika ada)
                if abs(time_domain_hr - self.last_hr) < abs(freq_domain_hr - self.last_hr):
                    hr_candidate = time_domain_hr
                else:
                    hr_candidate = freq_domain_hr
            elif abs(time_domain_hr - freq_domain_hr) > 15: # Jika beda jauh dan tidak ada histori
                hr_candidate = freq_domain_hr # Default ke FFT
            # Jika tidak beda jauh, bisa dirata-rata atau pilih FFT
            # Untuk sekarang, kita sudah pilih FFT di atas jika tersedia
            
        # Smoothing dengan histori (median filter)
        self.hr_history.append(hr_candidate)
        if len(self.hr_history) > self.max_history:
            self.hr_history.pop(0)
        
        if len(self.hr_history) > 0:
            # Gunakan median dari beberapa HR terakhir untuk stabilitas
            # Ambil 3-5 sampel terakhir jika tersedia
            window_median = min(len(self.hr_history), 5) 
            if window_median >=1 : # Setidaknya 1 data untuk median
                 smoothed_hr = np.median(self.hr_history[-window_median:])
            else: # Seharusnya tidak terjadi jika hr_history tidak kosong
                smoothed_hr = hr_candidate
        else: # Seharusnya tidak terjadi jika hr_candidate ada
            smoothed_hr = hr_candidate
            
        self.last_hr = smoothed_hr
        return smoothed_hr

    def _process_hr(self, filtered_signal, fs):
        """Process heart rate from filtered signal."""
        try:
            # Find peaks for heart rate calculation
            min_peak_dist = fs / (240.0 / 60.0)  # Max HR 240 BPM
            peaks, properties = sg.find_peaks(
                filtered_signal,
                distance=min_peak_dist,
                height=0.1 * np.std(filtered_signal) if np.std(filtered_signal) > 1e-5 else 0.01,
                prominence=0.1 * np.std(filtered_signal) if np.std(filtered_signal) > 1e-5 else 0.01
            )

            # Calculate HR from peak intervals
            if len(peaks) > 1:
                intervals = np.diff(peaks) / fs  # Convert to seconds
                valid_intervals = intervals[(intervals > 60.0/200.0) & (intervals < 60.0/40.0)]
                
                if len(valid_intervals) > 0:
                    mean_interval = np.mean(valid_intervals)
                    hr = 60.0 / mean_interval
                    
                    # Calculate confidence based on interval consistency
                    interval_std = np.std(valid_intervals)
                    confidence = 1.0 - min(interval_std / mean_interval, 0.5)
                    
                    return hr, confidence, self.signal_quality
            
            # If peak detection fails, try FFT method
            fft_hr = self._fft_heart_rate(filtered_signal, fs)
            if fft_hr is not None:
                return fft_hr, 0.5, self.signal_quality  # Lower confidence for FFT method
                
            return None, 0.0, self.signal_quality
            
        except Exception as e:
            print(f"Error in _process_hr: {e}")
            return None, 0.0, 0.0