# Create a new file rppg/signal_processor.py
import numpy as np
from scipy import signal as sg
from scipy.interpolate import interp1d

class SignalProcessor:
    """Processes raw rPPG signals to extract heart rate information."""
    
    def __init__(self):
        """Initialize the signal processor."""
        self.last_hr = None
        self.hr_history = []
        self.max_history = 10
        self.signal_quality = 0.0
    
    def process(self, signal, timestamps):
        """Process a raw PPG signal to estimate heart rate.
        
        Args:
            signal: List of raw signal values (green channel averages)
            timestamps: List of timestamps corresponding to signal samples
            
        Returns:
            Tuple of (heart_rate, confidence)
        """
        if len(signal) < 60:  # Need at least 2 seconds of data at 30fps
            return None, 0.0
            
        try:
            # Calculate sampling frequency
            fs = len(signal) / (timestamps[-1] - timestamps[0])
            if fs <= 0:
                return None, 0.0
                
            # Convert to numpy arrays
            signal_array = np.array(signal)
            
            # Detect and remove outliers
            signal_array = self._remove_outliers(signal_array)
            
            # Normalize to 0-1 range
            signal_normalized = (signal_array - np.min(signal_array)) / (np.max(signal_array) - np.min(signal_array) + 1e-10)
            
            # Apply detrending to remove slow drifts
            detrended = sg.detrend(signal_normalized)
            
            # Interpolate to ensure uniform sampling
            uniform_timestamps = np.linspace(timestamps[0], timestamps[-1], len(timestamps))
            if len(timestamps) != len(detrended):
                min_len = min(len(timestamps), len(detrended))
                timestamps = timestamps[:min_len]
                detrended = detrended[:min_len]
            
            f = interp1d(timestamps, detrended, kind='cubic', bounds_error=False, fill_value="extrapolate")
            uniform_signal = f(uniform_timestamps)
            
            # Apply bandpass filter (0.7-4Hz corresponds to 42-240 BPM)
            # Ensure the cutoff frequencies are within valid range (0 < Wn < 1)
            low_cutoff = 0.7/fs*2
            high_cutoff = 4/fs*2
            
            # Validate the frequencies are in range
            if low_cutoff >= 1 or high_cutoff >= 1 or low_cutoff <= 0 or high_cutoff <= 0:
                # If frequencies are invalid, use more conservative values
                nyquist = fs/2
                low_cutoff = min(0.7/nyquist, 0.8)
                high_cutoff = min(4/nyquist, 0.9)
                print(f"Adjusted filter frequencies to valid range: {low_cutoff:.4f}, {high_cutoff:.4f}")
            
            b, a = sg.butter(3, [low_cutoff, high_cutoff], btype='bandpass')
            filtered = sg.filtfilt(b, a, uniform_signal)
            
            # Apply moving average to smooth the signal
            window_size = max(3, int(fs / 10))  # Adaptive window size based on sampling rate
            filtered_smooth = np.convolve(filtered, np.ones(window_size)/window_size, mode='same')
            
            # Find peaks in the filtered signal
            peaks, properties = sg.find_peaks(
                filtered_smooth, 
                distance=fs/4,  # Minimum distance between peaks
                height=0.01,    # Minimum height
                prominence=0.01  # Minimum prominence
            )
            
            # Alternative: Use frequency domain analysis (more robust)
            fft_hr = self._fft_heart_rate(filtered_smooth, fs)
            
            # Calculate heart rate from peak-to-peak intervals if enough peaks found
            time_domain_hr = None
            if len(peaks) > 1:
                # Calculate heart rate from peak-to-peak intervals
                peak_times = [uniform_timestamps[p] for p in peaks]
                intervals = np.diff(peak_times)
                    
                # Remove outliers (intervals that are too short or too long)
                valid_intervals = intervals[(intervals > 0.25) & (intervals < 1.5)]
                if len(valid_intervals) > 0:
                    mean_interval = np.mean(valid_intervals)
                    time_domain_hr = 60 / mean_interval
                
                # Assess signal quality based on peak regularity
                if len(valid_intervals) > 1:
                    interval_variation = np.std(valid_intervals) / np.mean(valid_intervals)
                    self.signal_quality = max(0.0, min(1.0, 1.0 - interval_variation))
                
            # Combine results and smooth with history for stability
            final_hr = self._combine_hr_estimates(time_domain_hr, fft_hr)
            
            # Calculate confidence based on peak properties, stability, and signal quality
            if len(peaks) > 0 and properties['prominences'].size > 0:
                prominence = np.mean(properties['prominences'])
                stability = 1.0 - min(1.0, np.std(self.hr_history) / 5.0) if self.hr_history else 0.0
                confidence = min(1.0, prominence * 10) * 0.5 + stability * 0.3 + self.signal_quality * 0.2
            else:
                confidence = 0.0
                
            return final_hr, confidence
            
        except Exception as e:
            print(f"Error in signal processing: {e}")
            return None, 0.0
    
    def _remove_outliers(self, signal):
        """Remove outliers from the signal using z-score method."""
        # Calculate z-scores
        z_scores = np.abs((signal - np.mean(signal)) / (np.std(signal) + 1e-10))
        
        # Replace outliers with interpolated values
        outlier_indices = np.where(z_scores > 3.0)[0]
        cleaned_signal = signal.copy()
        
        if len(outlier_indices) > 0 and len(outlier_indices) < len(signal) / 2:
            for idx in outlier_indices:
                # Find nearest non-outlier neighbors
                left_neighbors = signal[:idx]
                right_neighbors = signal[idx+1:]
                left_valid = left_neighbors[z_scores[:idx] <= 3.0]
                right_valid = right_neighbors[z_scores[idx+1:] <= 3.0]
                
                # Interpolate if we have neighbors on both sides
                if len(left_valid) > 0 and len(right_valid) > 0:
                    cleaned_signal[idx] = (left_valid[-1] + right_valid[0]) / 2
                # Otherwise use the nearest valid neighbor
                elif len(left_valid) > 0:
                    cleaned_signal[idx] = left_valid[-1]
                elif len(right_valid) > 0:
                    cleaned_signal[idx] = right_valid[0]
                    
        return cleaned_signal
    
    def _fft_heart_rate(self, signal, fs):
        """Use FFT to estimate heart rate from frequency domain."""
        try:
            # Apply window function to reduce spectral leakage
            window = sg.windows.hamming(len(signal))
            windowed_signal = signal * window
            
            # Get the power spectrum using Welch's method for better frequency resolution
            freqs, psd = sg.welch(windowed_signal, fs, nperseg=min(len(signal), int(fs*4)), 
                                 scaling='density', window='hamming')
            
            # Find the peak in the 0.7-4Hz range (42-240 BPM)
            fmask = (freqs >= 0.7) & (freqs <= 4.0)
            
            if np.any(fmask):
                # Find multiple peaks and select the most prominent one
                peak_indices = sg.find_peaks(psd[fmask], height=0.1*np.max(psd[fmask]), distance=3)[0]
                
                if len(peak_indices) > 0:
                    # Get peak frequencies and their power
                    peak_freqs = freqs[fmask][peak_indices]
                    peak_powers = psd[fmask][peak_indices]
                    
                    # Choose the peak with the highest power
                    max_peak_idx = np.argmax(peak_powers)
                    peak_freq = peak_freqs[max_peak_idx]
                    
                    # Additional verification for the selected peak
                    peak_psd_ratio = peak_powers[max_peak_idx] / np.mean(psd[fmask])
                    if peak_psd_ratio > 2.0:  # Ensure the peak is significant
                        return peak_freq * 60  # Convert Hz to BPM
                    
                # Fallback to simple maximum if peaks method didn't work
                idx = np.argmax(psd[fmask])
                peak_freq = freqs[fmask][idx]
                return peak_freq * 60  # Convert Hz to BPM
            return None
        except Exception as e:
            print(f"FFT processing error: {e}")
            return None
    
    def _combine_hr_estimates(self, time_domain_hr, freq_domain_hr):
        """Combine time and frequency domain estimates for a robust heart rate value."""
        # If only one estimate is available, use it
        if time_domain_hr is None and freq_domain_hr is None:
            return None
        elif time_domain_hr is None:
            hr = freq_domain_hr
        elif freq_domain_hr is None:
            hr = time_domain_hr
        else:
            # If we have both, use weighted combination based on history
            if self.last_hr is not None:
                # Weight more towards the estimate closer to the last heart rate
                time_diff = abs(time_domain_hr - self.last_hr)
                freq_diff = abs(freq_domain_hr - self.last_hr)
                
                # Calculate weights based on how close each estimate is to previous HR
                time_weight = 1.0 / (time_diff + 0.1)
                freq_weight = 1.0 / (freq_diff + 0.1)
                total_weight = time_weight + freq_weight
                
                # Weighted average
                hr = (time_domain_hr * time_weight + freq_domain_hr * freq_weight) / total_weight
            else:
                # With no history, bias slightly toward frequency domain (often more stable initially)
                hr = 0.4 * time_domain_hr + 0.6 * freq_domain_hr
            
            # Check if the two estimates are very different
            if abs(time_domain_hr - freq_domain_hr) > 15:
                # If large discrepancy, prefer the frequency domain for stability
                hr = freq_domain_hr
            
        # Add to history and limit size
        self.hr_history.append(hr)
        if len(self.hr_history) > self.max_history:
            self.hr_history.pop(0)
            
        # Use median filter for robustness against outliers
        if len(self.hr_history) >= 3:
            smoothed_hr = np.median(self.hr_history[-3:])
        else:
            smoothed_hr = np.mean(self.hr_history)
            
        self.last_hr = smoothed_hr
        
        return smoothed_hr