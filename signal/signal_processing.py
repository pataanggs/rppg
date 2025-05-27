"""
Signal Processing Utilities for rPPG Heart Rate Monitoring

This module provides signal processing functions that support heart rate
and respiration rate estimation from video signals. It includes bandpass
filtering and rate calculation functions optimized for physiological signals.
"""

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def bandpass_filter(signal, lowcut, highcut, fs, order=4):
    """
    Apply Butterworth bandpass filter to a 1D signal.
    
    This function filters the input signal to isolate frequencies within
    the specified range, which is useful for isolating physiological signals
    like heart rate (typically 0.7-4Hz) or respiration (0.1-0.5Hz).
    
    Args:
        signal (np.ndarray): Input 1D signal array
        lowcut (float): Low frequency cutoff in Hz
        highcut (float): High frequency cutoff in Hz
        fs (float): Sampling rate in Hz
        order (int, optional): Order of the filter. Higher orders have 
                              sharper transitions but may introduce artifacts.
                              Defaults to 4.
    
    Returns:
        np.ndarray: Filtered signal with frequencies outside the specified
                   range attenuated
    
    Raises:
        ValueError: If input signal is empty or None
        ValueError: If highcut frequency exceeds Nyquist frequency (fs/2)
    """
    if signal is None or len(signal) == 0:
        raise ValueError("Input signal is empty or None.")

    nyquist = 0.5 * fs
    if highcut >= nyquist:
        raise ValueError(f"Highcut frequency ({highcut}Hz) must be less than Nyquist frequency ({nyquist}Hz).")

    low = lowcut / nyquist
    high = highcut / nyquist

    b, a = butter(order, [low, high], btype='band')
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal

def calculate_heart_rate(signal, frame_rate):
    """
    Calculate heart rate in BPM from a filtered rPPG signal.
    
    This function identifies peaks in the signal that correspond to heartbeats
    and calculates the heart rate based on the number of peaks over time.
    
    Args:
        signal (np.ndarray): Filtered rPPG signal
        frame_rate (float): Sampling rate of the signal in Hz
    
    Returns:
        float: Estimated heart rate in beats per minute (BPM)
    """
    if signal is None or len(signal) == 0:
        return 0.0

    # Find peaks with adaptive prominence based on signal variance
    # Minimum distance between peaks corresponds to maximum expected heart rate
    peaks, _ = find_peaks(signal, 
                          distance=frame_rate/2,  # Corresponds to 120 BPM maximum
                          prominence=np.std(signal) * 0.3)  # Adaptive threshold
    
    duration_sec = len(signal) / frame_rate
    if duration_sec <= 0:
        return 0.0

    # Calculate BPM from peak count and duration
    heart_rate = len(peaks) * 60 / duration_sec
    return heart_rate

def calculate_respiration_rate(signal, frame_rate):
    """
    Calculate respiration rate from a filtered respiration signal.
    
    This function identifies peaks in the signal that correspond to breaths
    and calculates the respiration rate based on the number of peaks over time.
    
    Args:
        signal (np.ndarray): Filtered respiration signal
        frame_rate (float): Sampling rate of the signal in Hz
    
    Returns:
        float: Estimated respiration rate in breaths per minute
    """
    if signal is None or len(signal) == 0:
        return 0.0

    # Find peaks with adaptive prominence based on signal variance
    # Minimum distance between peaks corresponds to maximum expected respiration rate
    peaks, _ = find_peaks(signal, 
                          distance=frame_rate/5,  # Corresponds to 60 BrPM maximum
                          prominence=np.std(signal) * 0.2)  # Adaptive threshold
    
    duration_sec = len(signal) / frame_rate
    if duration_sec <= 0:
        return 0.0

    # Calculate breaths per minute from peak count and duration
    respiration_rate = len(peaks) * 60 / duration_sec
    return respiration_rate 