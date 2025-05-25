"""
Audio Management for rPPG Heart Rate Monitoring Application

This module handles audio playback for the application, including alarm sounds
for heart rate threshold alerts and notification sounds for other events.
"""

import os
import sys
from PyQt6 import QtMultimedia, QtCore, QtWidgets


class AudioManager:
    """
    Manages audio playback for the application with support for multiple sounds.
    
    This class handles loading, playing, and controlling various audio files
    including alarm sounds and notification sounds.
    """
    
    def __init__(self, window, volume=0.75):
        """
        Initialize the audio manager.
        
        Args:
            window: Main application window for UI updates
            volume (float, optional): Default volume (0.0 to 1.0). Defaults to 0.75.
        """
        self.window = window
        self.sounds = {}
        self.active_sounds = set()
        self.is_muted = False
        self.default_volume = max(0.0, min(1.0, volume))  # Ensure volume is in valid range
        
        # Load standard sounds
        self._load_sounds()
    
    def _load_sounds(self):
        """Load all required sound files into memory."""
        try:
            # Define the sounds we need - only using alarm sound
            sound_files = {
                'alarm': 'alarm.wav',
                # Removed unused sound files
            }
            
            # Find the assets directory
            assets_dir = self._find_assets_directory()
            
            # Load each sound file
            for sound_id, filename in sound_files.items():
                sound_path = os.path.join(assets_dir, filename)
                if os.path.exists(sound_path):
                    sound = QtMultimedia.QSoundEffect()
                    sound.setSource(QtCore.QUrl.fromLocalFile(sound_path))
                    sound.setVolume(self.default_volume)
                    sound.setLoopCount(1)  # Default to single play
                    self.sounds[sound_id] = sound
                    print(f"Loaded sound: {sound_id} from {sound_path}")
                else:
                    print(f"Warning: Sound file not found: {sound_path}")
        
        except Exception as e:
            print(f"Error loading sounds: {e}")
    
    def _find_assets_directory(self):
        """
        Find the assets directory containing sound files.
        
        Returns:
            str: Path to the assets directory
            
        Raises:
            FileNotFoundError: If assets directory cannot be found
        """
        # Try different possible locations for the assets directory
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"),
            os.path.join(os.getcwd(), "assets")
        ]
        
        # Check if running as a packaged application (e.g., PyInstaller)
        if getattr(sys, 'frozen', False):
            possible_paths.append(os.path.join(sys._MEIPASS, "assets"))
        
        # Find the first valid path
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        
        # If not found, use the first path and create the directory if needed
        os.makedirs(possible_paths[0], exist_ok=True)
        return possible_paths[0]
    
    def play(self, sound_id, loop=False, volume=None):
        """
        Play a specific sound.
        
        Args:
            sound_id (str): Identifier for the sound to play
            loop (bool, optional): Whether to loop the sound. Defaults to False.
            volume (float, optional): Volume override (0.0 to 1.0). If None, uses default.
                
        Returns:
            bool: True if sound started playing, False otherwise
        """
        if self.is_muted:
            return False
            
        if sound_id not in self.sounds:
            print(f"Warning: Sound '{sound_id}' not found")
            return False
        
        sound = self.sounds[sound_id]
        
        # Set custom volume if provided
        if volume is not None:
            sound.setVolume(max(0.0, min(1.0, volume)))
        
        # Set loop count
        if loop:
            sound.setLoopCount(QtMultimedia.QSoundEffect.Infinite)
        else:
            sound.setLoopCount(1)
        
        # Play the sound
        sound.play()
        self.active_sounds.add(sound_id)
        
        return True
    
    def stop(self, sound_id=None):
        """
        Stop a specific sound or all sounds.
        
        Args:
            sound_id (str, optional): Identifier for the sound to stop.
                                     If None, stops all sounds.
        """
        if sound_id is None:
            # Stop all active sounds
            for active_id in list(self.active_sounds):
                if active_id in self.sounds:
                    self.sounds[active_id].stop()
            self.active_sounds.clear()
        elif sound_id in self.sounds:
            # Stop specific sound
            self.sounds[sound_id].stop()
            self.active_sounds.discard(sound_id)
    
    def toggle_mute(self):
        """
        Toggle the mute state of all sounds.
        
        Returns:
            bool: New mute state (True = muted, False = unmuted)
        """
        self.is_muted = not self.is_muted
        
        # Update UI mute button if it exists
        if hasattr(self.window, 'mute_button'):
            sound_icon = QtWidgets.QApplication.style().standardIcon(
                QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted if self.is_muted else
                QtWidgets.QStyle.StandardPixmap.SP_MediaVolume
            )
            self.window.mute_button.setIcon(sound_icon)
            self.window.mute_button.setToolTip(f"Toggle sound (currently {'OFF' if self.is_muted else 'ON'})")
        
        # Stop all sounds if muted
        if self.is_muted:
            self.stop()
        
        # Update status label if it exists
        if hasattr(self.window, 'status_label'):
            self._update_status_label()
            
        return self.is_muted
    
    def _update_status_label(self):
        """Update the status label based on mute state."""
        status_text = self.window.status_label.text()
        if "Muted" in status_text:
            self.window.status_label.setText(status_text.replace(" (Sound Muted)", ""))
        elif self.is_muted:
            self.window.status_label.setText(f"{status_text} (Sound Muted)")
    
    def set_volume(self, volume, sound_id=None):
        """
        Set volume for a specific sound or all sounds.
        
        Args:
            volume (float): Volume level from 0.0 to 1.0
            sound_id (str, optional): Specific sound to adjust.
                                     If None, sets volume for all sounds.
        """
        volume = max(0.0, min(1.0, volume))  # Ensure volume is in valid range
        
        if sound_id is None:
            # Set volume for all sounds
            for sound in self.sounds.values():
                sound.setVolume(volume)
            self.default_volume = volume
        elif sound_id in self.sounds:
            # Set volume for specific sound
            self.sounds[sound_id].setVolume(volume)


# Backward compatibility with existing API
class AlarmSound:
    """Legacy class for backward compatibility."""
    def __init__(self, window):
        self.window = window
        self.audio_manager = AudioManager(window)
        self.alarm_playing = False
        self.is_muted = False
        
    def play(self):
        """Play the alarm sound if it's not muted."""
        if not self.is_muted:
            success = self.audio_manager.play('alarm', loop=True)
            if success:
                self.alarm_playing = True
                print("Alarm sound started.")
                
    def stop(self):
        """Stop the alarm sound."""
        self.audio_manager.stop('alarm')
        self.alarm_playing = False
        print("Alarm sound stopped.")
        
    def toggle(self):
        """Toggle the mute state of the alarm sound."""
        self.is_muted = self.audio_manager.toggle_mute()
        
        # Stop alarm if muted
        if self.is_muted and self.alarm_playing:
            self.stop()


def setup_alarm_sound(window):
    """Setup alarm sound for heart rate alerts."""
    alarm = AlarmSound(window)
    window.alarm_sound = alarm
    return alarm


def toggle_alarm_sound(window):
    """Toggle alarm sound on/off."""
    window.alarm_sound.toggle() 