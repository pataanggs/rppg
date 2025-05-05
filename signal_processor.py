# Create a new file rppg/signal_processor.py
import numpy as np
from scipy import signal as sg

class SignalProcessor:
    """Processes raw rPPG signals to extract heart rate information."""
    
    def __init__(self):
        """Initialize the signal processor."""
        self.last_hr = None
        self.hr_history = []
        self.max_history = 10
    
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
            
            # Normalize to 0-1 range
            signal_normalized = (signal_array - np.min(signal_array)) / (np.max(signal_array) - np.min(signal_array) + 1e-10)
            
            # Apply detrending to remove slow drifts
            detrended = sg.detrend(signal_normalized)
            
            # Apply bandpass filter (0.7-4Hz corresponds to 42-240 BPM)
            b, a = sg.butter(3, [0.7/fs*2, 4/fs*2], btype='bandpass')
            filtered = sg.filtfilt(b, a, detrended)
            
            # Find peaks in the filtered signal
            peaks, properties = sg.find_peaks(filtered, distance=fs/4, height=0.01, prominence=0.01)
            
            if len(peaks) > 1:
                # Calculate heart rate from peak-to-peak intervals
                peak_times = [timestamps[p] for p in peaks]
                intervals = np.diff(peak_times)
                if len(intervals) == 0:
                    return None, 0.0
                    
                # Remove outliers (intervals that are too short or too long)
                valid_intervals = intervals[(intervals > 0.25) & (intervals < 1.5)]
                if len(valid_intervals) == 0:
                    return None, 0.0
                    
                mean_interval = np.mean(valid_intervals)
                heart_rate = 60 / mean_interval
                
                # Alternative: Use frequency domain analysis
                fft_hr = self._fft_heart_rate(filtered, fs)
                
                # Combine results and smooth with history for stability
                final_hr = self._update_history(heart_rate, fft_hr)
                
                # Calculate confidence based on peak properties and stability
                prominence = np.mean(properties['prominences'])
                stability = 1.0 - min(1.0, np.std(self.hr_history) / 5.0) if self.hr_history else 0.0
                confidence = min(1.0, prominence * 10) * 0.7 + stability * 0.3
                
                return final_hr, confidence
            
            return None, 0.0
            
        except Exception as e:
            print(f"Error in signal processing: {e}")
            return None, 0.0
    
    def _fft_heart_rate(self, signal, fs):
        """Use FFT to estimate heart rate from frequency domain."""
        try:
            # Get the power spectrum
            freqs, psd = sg.welch(signal, fs, nperseg=len(signal))
            
            # Find the peak in the 0.7-4Hz range (42-240 BPM)
            fmask = (freqs >= 0.7) & (freqs <= 4.0)
            
            if np.any(fmask):
                idx = np.argmax(psd[fmask])
                peak_freq = freqs[fmask][idx]
                return peak_freq * 60  # Convert Hz to BPM
            return None
        except:
            return None
    
    def _update_history(self, time_domain_hr, freq_domain_hr):
        """Update heart rate history and return smoothed estimate."""
        # Combine time and frequency domain estimates if both are available
        if freq_domain_hr is not None:
            if self.last_hr is not None:
                # Weight more towards the estimate closer to the last heart rate
                time_diff = abs(time_domain_hr - self.last_hr)
                freq_diff = abs(freq_domain_hr - self.last_hr)
                
                if time_diff < freq_diff:
                    hr = 0.8 * time_domain_hr + 0.2 * freq_domain_hr
                else:
                    hr = 0.2 * time_domain_hr + 0.8 * freq_domain_hr
            else:
                hr = 0.5 * time_domain_hr + 0.5 * freq_domain_hr
        else:
            hr = time_domain_hr
            
        # Add to history and limit size
        self.hr_history.append(hr)
        if len(self.hr_history) > self.max_history:
            self.hr_history.pop(0)
            
        # Smooth with moving average
        smoothed_hr = np.mean(self.hr_history)
        self.last_hr = smoothed_hr
        
        return smoothed_hr