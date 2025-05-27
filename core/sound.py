"""
Pengelolaan Audio untuk Aplikasi Pemantauan Detak Jantung rPPG

Modul ini menangani pemutaran audio untuk aplikasi, termasuk suara alarm
untuk peringatan ambang batas detak jantung dan suara notifikasi untuk kejadian lainnya.
"""

import os
import sys
from PyQt6 import QtMultimedia, QtCore, QtWidgets


class AudioManager:
    """
    Mengelola pemutaran audio untuk aplikasi dengan dukungan untuk beberapa suara.
    
    Kelas ini menangani pemuatan, pemutaran, dan kontrol berbagai file audio
    termasuk suara alarm dan suara notifikasi.
    """
    
    def __init__(self, window, volume=0.75):
        """
        Menginisialisasi manajer audio.
        
        Args:
            window: Jendela aplikasi utama untuk pembaruan UI.
            volume (float, optional): Volume default (0.0 hingga 1.0). Defaultnya 0.75.
        """
        self.window = window
        self.sounds = {}
        self.active_sounds = set() # Untuk melacak suara yang sedang diputar
        self.is_muted = False
        self.default_volume = max(0.0, min(1.0, volume))  # Memastikan volume dalam rentang yang valid
        
        # Memuat suara standar
        self._load_sounds()
    
    def _load_sounds(self):
        """Memuat semua file suara yang diperlukan ke dalam memori."""
        try:
            # Mendefinisikan suara yang kita butuhkan - hanya menggunakan suara alarm
            sound_files = {
                'alarm': 'alarm.wav',
            }
            
            # Menemukan direktori aset
            assets_dir = self._find_assets_directory()
            
            # Memuat setiap file suara
            for sound_id, filename in sound_files.items():
                sound_path = os.path.join(assets_dir, filename)
                if os.path.exists(sound_path):
                    sound = QtMultimedia.QSoundEffect()
                    sound.setSource(QtCore.QUrl.fromLocalFile(sound_path))
                    sound.setVolume(self.default_volume)
                    # Tidak ada jumlah loop default di sini; akan diatur saat memutar
                    self.sounds[sound_id] = sound
                    print(f"Loaded sound: {sound_id} from {sound_path}")
                else:
                    print(f"Warning: Sound file '{filename}' not found at {sound_path}")
        
        except Exception as e:
            print(f"Error loading sounds: {e}")
    
    def _find_assets_directory(self):
        """
        Menemukan direktori aset yang berisi file suara.
        Fungsi ini memprioritaskan penemuan 'assets' relatif terhadap akar paket 'rppg' utama.
        
        Returns:
            str: Jalur ke direktori aset
        
        Raises:
            FileNotFoundError: Jika direktori aset tidak dapat ditemukan dan tidak dibuat.
        """
        current_script_dir = os.path.dirname(os.path.abspath(__file__)) # Contoh: .../RPPG/rppg/core/
        rppg_package_root = os.path.dirname(current_script_dir)         # Contoh: .../RPPG/rppg/

        # 1. Lokasi paling umum untuk aset dalam paket Python: rppg/assets/
        expected_assets_path_1 = os.path.join(rppg_package_root, "assets") # Contoh: .../RPPG/rppg/assets/

        # 2. Kurang umum, tetapi mungkin: RPPG/assets/ (saudara dari folder paket rppg)
        # Jalur ini mungkin digunakan jika aset ditempatkan di tingkat teratas proyek.
        project_root = os.path.dirname(rppg_package_root)               # Contoh: .../RPPG/
        expected_assets_path_2 = os.path.join(project_root, "assets")    # Contoh: .../RPPG/assets/
        
        # 3. Direktori kerja saat ini tempat skrip mungkin dijalankan
        # Ini dapat bervariasi tergantung pada bagaimana skrip dijalankan (misalnya, dari IDE, terminal)
        current_working_dir_assets = os.path.join(os.getcwd(), "assets")
        
        possible_paths_to_check = [
            expected_assets_path_1,
            expected_assets_path_2,
            current_working_dir_assets
        ]

        print(f"\n--- Debugging Jalur Aset ---")
        print(f"Direktori Skrip Saat Ini (lokasi sound.py): {current_script_dir}")
        print(f"Akar Paket RPPG (folder rppg/): {rppg_package_root}")
        print(f"Akar Proyek (folder RPPG/ tingkat atas): {project_root}")
        print(f"Direktori Kerja Saat Ini: {os.getcwd()}")
        print(f"Kemungkinan Jalur Aset untuk Diperiksa:")
        for i, path in enumerate(possible_paths_to_check):
            print(f"   {i+1}. {path} (Ada sebagai dir: {os.path.exists(path) and os.path.isdir(path)})")

        # Memeriksa apakah berjalan sebagai aplikasi yang dikemas (misalnya, PyInstaller)
        if getattr(sys, 'frozen', False):
            # PyInstaller sering menempatkan aset di sys._MEIPASS
            frozen_assets_path = os.path.join(sys._MEIPASS, "assets")
            if os.path.exists(frozen_assets_path) and os.path.isdir(frozen_assets_path):
                print(f"Ditemukan direktori aset (beku): {frozen_assets_path}")
                print(f"--- Akhir Debugging Jalur Aset ---\n")
                return frozen_assets_path

        # Iterasi melalui kemungkinan jalur dan kembalikan yang pertama yang ada
        for path in possible_paths_to_check:
            if os.path.exists(path) and os.path.isdir(path):
                print(f"Mengembalikan direktori aset yang valid: {path}")
                print(f"--- Akhir Debugging Jalur Aset ---\n")
                return path

        # Jika tidak ada direktori aset yang ada ditemukan, cetak peringatan dan coba buat
        # satu di lokasi yang paling umum diharapkan (rppg/assets)
        default_creation_path = expected_assets_path_1 # Gunakan jalur relatif terhadap akar paket rppg
        print(f"Peringatan: Direktori aset tidak ditemukan di lokasi yang diharapkan.")
        print(f"Mencoba membuat direktori aset default di: {default_creation_path}")
        os.makedirs(default_creation_path, exist_ok=True)
        print(f"--- Akhir Debugging Jalur Aset ---\n")
        return default_creation_path

    def play_sound(self, sound_id, loop=False):
        """
        Memutar suara.

        Args:
            sound_id (str): ID suara yang akan diputar (misalnya, 'alarm').
            loop (bool, optional): True untuk mengulang suara tanpa batas. Defaultnya False.
        """
        if self.is_muted:
            print(f"Mencoba memutar '{sound_id}' tetapi audio di-mute.")
            return

        sound = self.sounds.get(sound_id)
        if sound:
            if sound.isPlaying():
                sound.stop()  # Hentikan jika sudah diputar untuk memulai ulang
            
            if loop:
               sound.setLoopCount(-2)
            else:
                sound.setLoopCount(1)

            sound.play()
            self.active_sounds.add(sound_id)
            print(f"Memutar suara: {sound_id} (loop: {loop})")
        else:
            print(f"Peringatan: Suara '{sound_id}' tidak ditemukan dalam suara yang dimuat.")

    def stop_sound(self, sound_id):
        """
        Menghentikan suara tertentu.

        Args:
            sound_id (str): ID suara yang akan dihentikan.
        """
        sound = self.sounds.get(sound_id)
        if sound and sound.isPlaying():
            sound.stop()
            if sound_id in self.active_sounds:
                self.active_sounds.remove(sound_id)
            print(f"Menghentikan suara: {sound_id}")
        elif sound:
            print(f"Suara '{sound_id}' tidak sedang diputar.")
        else:
            print(f"Peringatan: Mencoba menghentikan ID suara yang tidak dikenal: {sound_id}")

    def stop_all_sounds(self):
        """Menghentikan semua suara yang sedang diputar."""
        # Buat daftar dari set untuk menghindari kesalahan "Set changed size during iteration"
        for sound_id in list(self.active_sounds): 
            self.stop_sound(sound_id)
        print("Menghentikan semua suara.")

    def set_master_volume(self, volume):
        """
        Mengatur volume master untuk semua suara.

        Args:
            volume (float): Tingkat volume (0.0 hingga 1.0).
        """
        self.default_volume = max(0.0, min(1.0, volume)) # Memastikan rentang yang valid
        for sound in self.sounds.values():
            sound.setVolume(self.default_volume)
        print(f"Volume master diatur ke: {self.default_volume}")

    def toggle_mute(self):
        """Mengaktifkan atau menonaktifkan status mute untuk semua suara."""
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.stop_all_sounds() # Hentikan semua suara saat di-mute
            print("Audio di-mute.")
        else:
            print("Audio tidak di-mute.")
        # Anda mungkin ingin memancarkan sinyal di sini
        # jika ada UI yang perlu diperbarui berdasarkan status mute.

    def is_playing(self, sound_id):
        """
        Memeriksa apakah suara tertentu sedang diputar.

        Args:
            sound_id (str): ID suara yang akan diperiksa.

        Returns:
            bool: True jika suara sedang diputar, False jika sebaliknya.
        """
        sound = self.sounds.get(sound_id)
        return sound and sound.isPlaying()
