import os
from PyQt6 import QtMultimedia, QtCore, QtWidgets


class AlarmSound:
    """Handles the alarm sound setup and playback."""
    def __init__(self, window):
        self.window = window
        self.sound_path = self._find_alarm_sound()
        self.alarm_sound = QtMultimedia.QSoundEffect()
        self.alarm_sound.setSource(QtCore.QUrl.fromLocalFile(self.sound_path))
        self.alarm_sound.setVolume(0.75)
        self.alarm_playing = False
        self.is_muted = False

    def _find_alarm_sound(self):
        """Find the alarm sound file in the correct path."""
        sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "alarm.wav")
        if not os.path.exists(sound_path):
            # Try fallback path if the file doesn't exist
            sound_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "alarm.wav")
        
        if not os.path.exists(sound_path):
            print(f"Warning: Alarm sound file not found at {sound_path}")
        return sound_path

    def play(self):
        """Play the alarm sound if it's not muted."""
        if not self.is_muted and not self.alarm_playing:
            self.alarm_sound.play()
            self.alarm_playing = True
            print("Alarm sound started.")

    def stop(self):
        """Stop the alarm sound."""
        if self.alarm_playing:
            self.alarm_sound.stop()
            self.alarm_playing = False
            print("Alarm sound stopped.")

    def toggle(self):
        """Toggle the mute state of the alarm sound."""
        self.is_muted = not self.is_muted
        sound_icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted if self.is_muted else
            QtWidgets.QStyle.StandardPixmap.SP_MediaVolume
        )
        self.window.mute_button.setIcon(sound_icon)
        self.window.mute_button.setToolTip(f"Toggle alarm sound (currently {'OFF' if self.is_muted else 'ON'})")

        # Stop alarm if muted
        if self.is_muted and self.alarm_playing:
            self.stop()

        # Update status label
        self._update_status_label()

    def _update_status_label(self):
        """Update the status label based on mute state."""
        status_text = self.window.status_label.text()
        if "Muted" in status_text:
            self.window.status_label.setText(status_text.replace(" (Alarm Muted)", ""))
        elif self.is_muted:
            self.window.status_label.setText(f"{status_text} (Alarm Muted)")

def setup_alarm_sound(window):
    """Setup alarm sound for heart rate alerts."""
    alarm = AlarmSound(window)
    window.alarm_sound = alarm
    return alarm

def toggle_alarm_sound(window):
    """Toggle alarm sound on/off."""
    window.alarm_sound.toggle()
