import os
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect

# rppg/core/sound.py
# Ini adalah placeholder AudioManager dari kode yang kamu berikan
# Kamu mungkin punya implementasi yang lebih lengkap

class AudioManager:
    def __init__(self, parent=None):
        self.is_muted = False
        self.current_sounds = {}
        
        # Initialize simple sound effect
        self.sound_effect = QSoundEffect(parent)
        
        try:
            base_path = Path(__file__).parent.parent
            alarm_path = base_path / "assets" / "alarm.wav"
            self.sound_effect.setSource(QUrl.fromLocalFile(str(alarm_path)))
            self.sound_effect.setVolume(0.5)
            print("AudioManager initialized")
        except Exception as e:
            print(f"Audio initialization error: {e}")
            self.sound_effect = None

    def play_sound(self, sound_name, loop=False):
        if self.is_muted or self.sound_effect is None:
            return
        try:
            if loop:
                self.sound_effect.setLoopCount(0)  # 0 means infinite loop for QSoundEffect
            else:
                self.sound_effect.setLoopCount(1)
            self.sound_effect.play()
            self.current_sounds[sound_name] = True
        except Exception as e:
            print(f"Error playing sound: {e}")

    def stop_sound(self, sound_name):
        if self.sound_effect is not None:
            self.sound_effect.stop()
            self.current_sounds[sound_name] = False

    def is_playing(self, sound_name):
        if self.sound_effect is not None:
            return self.sound_effect.isPlaying()
        return False

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop_all_sounds()

    def stop_all_sounds(self):
        if self.sound_effect is not None:
            self.sound_effect.stop()
            self.current_sounds.clear()