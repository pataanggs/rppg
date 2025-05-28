# rppg/signal/signal_processing.py
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks # Pastikan scipy.signal diimport sebagai sg atau langsung

def bandpass_filter(signal_data, lowcut, highcut, fs, order=4): # Ganti nama argumen signal ke signal_data
    """
    Apply Butterworth bandpass filter to a 1D signal.
    
    Args:
        signal_data (np.ndarray): Input 1D signal array
        lowcut (float): Low frequency cutoff in Hz
        highcut (float): High frequency cutoff in Hz
        fs (float): Sampling rate in Hz
        order (int, optional): Order of the filter. Defaults to 4.
    
    Returns:
        np.ndarray: Filtered signal
    """
    if signal_data is None or len(signal_data) == 0:
        # raise ValueError("Input signal_data is empty or None.") # Sebaiknya kembalikan array kosong atau None
        return np.array([])


    nyquist = 0.5 * fs
    # Perbaiki pengecekan, highcut harus lebih KECIL dari nyquist
    if highcut >= nyquist: 
        print(f"Warning: highcut {highcut} >= nyquist {nyquist}. Adjusting highcut.")
        highcut = nyquist * 0.99 # Adjust agar sedikit di bawah nyquist
    if lowcut <=0:
        print(f"Warning: lowcut {lowcut} <= 0. Adjusting lowcut.")
        lowcut = 0.1 # Batas bawah minimal
    if lowcut >= highcut:
        print(f"Warning: lowcut {lowcut} >= highcut {highcut} after adjustments. Returning original signal.")
        return signal_data


    low = lowcut / nyquist
    high = highcut / nyquist

    # Pastikan low dan high valid setelah normalisasi
    if not (0 < low < 1 and 0 < high < 1 and low < high):
        print(f"Warning: Invalid normalized frequencies low={low}, high={high}. Returning original signal.")
        return signal_data

    try:
        b, a = butter(order, [low, high], btype='band')
        filtered_signal = filtfilt(b, a, signal_data)
        return filtered_signal
    except ValueError as e:
        print(f"Error in bandpass_filter: {e}. Returning original signal.")
        return signal_data


def calculate_heart_rate(signal_data, frame_rate): # Ganti nama argumen signal ke signal_data
    """
    Calculate heart rate in BPM from a filtered rPPG signal.
    """
    if signal_data is None or len(signal_data) == 0 or frame_rate <= 0:
        return 0.0

    # Adaptif prominence dan distance
    std_dev = np.std(signal_data)
    min_height = 0.1 * std_dev if std_dev > 1e-5 else 0.01 # Hindari std_dev sangat kecil
    min_prominence = 0.1 * std_dev if std_dev > 1e-5 else 0.01
    min_peak_distance = frame_rate / (240.0/60.0) # Max HR 240 bpm -> min distance = fr / 4

    peaks, _ = find_peaks(signal_data, 
                          distance=min_peak_distance,
                          height=min_height,
                          prominence=min_prominence) 
    
    duration_sec = len(signal_data) / frame_rate
    if duration_sec <= 0:
        return 0.0

    heart_rate = len(peaks) * 60.0 / duration_sec
    return heart_rate

def calculate_respiration_rate(signal_data, frame_rate): # Ganti nama argumen signal ke signal_data
    """
    Calculate respiration rate from a filtered respiration signal.
    """
    if signal_data is None or len(signal_data) == 0 or frame_rate <= 0:
        return 0.0

    std_dev = np.std(signal_data)
    min_height = 0.1 * std_dev if std_dev > 1e-5 else 0.01
    min_prominence = 0.1 * std_dev if std_dev > 1e-5 else 0.01
    # Max RR ~60 breaths/min -> 1 breath/sec. Min distance = frame_rate / 1.
    # Jarak antar peak pernapasan biasanya lebih lebar
    min_peak_distance_resp = frame_rate / (60.0/60.0) # Max RR 60 BrPM

    peaks, _ = find_peaks(signal_data, 
                          distance=min_peak_distance_resp,
                          height=min_height,
                          prominence=min_prominence)
    
    duration_sec = len(signal_data) / frame_rate
    if duration_sec <= 0:
        return 0.0

    respiration_rate = len(peaks) * 60.0 / duration_sec
    return respiration_rate