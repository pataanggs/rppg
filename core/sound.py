import os
from PyQt6 import QtMultimedia, QtCore, QtWidgets

def setup_alarm_sound(window):
    """Setup alarm sound for heart rate alerts."""
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "alarm.wav")
    if not os.path.exists(sound_path):
        os.makedirs(os.path.dirname(sound_path), exist_ok=True)
        print(f"Warning: Alarm sound file not found at {sound_path}")

    window.alarm_sound = QtMultimedia.QSoundEffect()
    window.alarm_sound.setSource(QtCore.QUrl.fromLocalFile(sound_path))
    window.alarm_sound.setVolume(0.75)
    window.alarm_playing = False

def toggle_alarm_sound(window):
    """Toggle alarm sound on/off."""
    window.is_muted = not window.is_muted
    sound_icon = QtWidgets.QApplication.style().standardIcon(
        QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted if window.is_muted else
        QtWidgets.QStyle.StandardPixmap.SP_MediaVolume
    )
    window.mute_button.setIcon(sound_icon)
    window.mute_button.setToolTip(f"Toggle alarm sound (currently {'OFF' if window.is_muted else 'ON'})")

    if window.is_muted and window.alarm_playing:
        window.alarm_sound.stop()
        window.alarm_playing = False

    status_text = window.status_label.text()
    if "Muted" in status_text:
        window.status_label.setText(status_text.replace(" (Alarm Muted)", ""))
    elif window.is_muted:
        window.status_label.setText(f"{status_text} (Alarm Muted)")