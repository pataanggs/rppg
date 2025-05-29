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
        
        # Setup sound effect
        self.sound_effect = QSoundEffect()
        base_path = Path(__file__).parent.parent
        alarm_path = os.path.join(base_path, "assets", "alarm.wav")
        self.sound_effect.setSource(QUrl.fromLocalFile(alarm_path))
        self.sound_effect.setLoopCount(-1)  # Changed from QSoundEffect.Infinite to -1
        self.sound_effect.setVolume(1.0)
        print("AudioManager Initialized with QSoundEffect")

    def play_sound(self, sound_name, loop=False):
        if self.is_muted:
            return
            
        if sound_name == "alarm":
            self.sound_effect.setLoopCount(-1 if loop else 1)  # Changed from QSoundEffect.Infinite to -1
            self.sound_effect.play()
            self.current_sounds[sound_name] = True
            print(f"[AudioManager] Playing sound: {sound_name}, Loop: {loop}")

    def stop_sound(self, sound_name):
        if sound_name == "alarm":
            self.sound_effect.stop()
            self.current_sounds[sound_name] = False
            print(f"[AudioManager] Stopping sound: {sound_name}")

    def is_playing(self, sound_name):
        if sound_name == "alarm":
            return self.sound_effect.isPlaying()
        return False

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop_all_sounds()
        print(f"[AudioManager] Mute Toggled. Is Muted: {self.is_muted}")

    def stop_all_sounds(self):
        self.sound_effect.stop()
        self.current_sounds.clear()
        print("[AudioManager] Stopping all sounds")