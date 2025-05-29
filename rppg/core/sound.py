# rppg/core/sound.py
import sounddevice as sd
import soundfile as sf
import numpy as np # Hanya untuk data dummy jika file tidak ada
import os
import threading

class AudioManager:
    def __init__(self, parent=None): # Argumen parent biasanya tidak terpakai di sini
        self.is_muted = False
        self.sound_data_cache = {}  # Cache untuk data suara yang sudah di-load
        self.active_loop_threads = {} # Untuk mengelola thread suara yang looping
        
        # Tentukan base_path untuk folder assets
        # Asumsi sound.py ada di rppg/core/ dan assets ada di rppg/assets/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(current_dir, "..", "assets")
        
        print(f"AudioManager Initialized. Assets path: {self.assets_path}")
        # Kamu bisa pre-load suara di sini jika mau, atau load saat pertama kali diminta
        self._load_sound_file('alarm', 'alarm.wav') # Ganti 'alarm.wav' jika nama file beda

    def _load_sound_file(self, sound_name, filename):
        """Memuat data suara dari file dan menyimpannya di cache."""
        if sound_name in self.sound_data_cache: # Jangan load ulang jika sudah ada
            return True
            
        file_path = os.path.join(self.assets_path, filename)
        if not os.path.exists(file_path):
            print(f"[AudioManager] Error: File suara '{filename}' tidak ditemukan di '{file_path}'")
            self.sound_data_cache[sound_name] = None # Tandai sebagai gagal load
            return False
        try:
            data, samplerate = sf.read(file_path, dtype='float32')
            self.sound_data_cache[sound_name] = {'data': data, 'samplerate': samplerate}
            print(f"[AudioManager] Suara '{sound_name}' berhasil dimuat dari '{filename}'.")
            return True
        except Exception as e:
            print(f"[AudioManager] Error saat memuat file suara '{filename}': {e}")
            self.sound_data_cache[sound_name] = None
            return False

    def play_sound(self, sound_name, loop=False):
        if self.is_muted:
            print(f"[AudioManager] Muted, tidak memainkan '{sound_name}'.")
            return

        if sound_name not in self.sound_data_cache or self.sound_data_cache[sound_name] is None:
            print(f"[AudioManager] Data suara untuk '{sound_name}' tidak ada atau gagal dimuat.")
            # Coba load lagi jika belum ada
            if sound_name == 'alarm' and not self._load_sound_file('alarm', 'alarm.wav'): # Contoh spesifik untuk alarm
                return # Gagal load
            elif self.sound_data_cache.get(sound_name) is None: # Jika masih gagal
                 return


        sound_info = self.sound_data_cache[sound_name]
        data = sound_info['data']
        samplerate = sound_info['samplerate']

        if loop:
            # Hentikan loop sebelumnya jika ada untuk suara yang sama
            if sound_name in self.active_loop_threads and self.active_loop_threads[sound_name]['thread'].is_alive():
                print(f"[AudioManager] Suara '{sound_name}' sudah looping. Tidak memulai loop baru.")
                return

            stop_event = threading.Event()
            
            def _loop_sound_worker():
                print(f"[AudioManager] Thread loop untuk '{sound_name}' dimulai.")
                try:
                    while not stop_event.is_set():
                        sd.play(data, samplerate)
                        sd.wait() # Tunggu iterasi ini selesai
                        if stop_event.is_set(): # Cek lagi setelah wait
                            break
                        # Beri jeda sedikit antar loop jika perlu (misal 0.1 detik)
                        # time.sleep(0.1) # Opsional, import time jika pakai ini
                except Exception as e_loop:
                    # Tangani error jika stream ditutup saat thread masih jalan
                    if not (isinstance(e_loop, sd.PortAudioError) and "Stream is stopped" in str(e_loop)):
                        print(f"[AudioManager] Error di thread loop '{sound_name}': {e_loop}")
                finally:
                    print(f"[AudioManager] Thread loop untuk '{sound_name}' berhenti.")

            thread = threading.Thread(target=_loop_sound_worker, daemon=True)
            self.active_loop_threads[sound_name] = {'thread': thread, 'stop_event': stop_event}
            thread.start()
        else: # Tidak looping
            try:
                print(f"[AudioManager] Memainkan '{sound_name}' sekali.")
                # Mainkan di thread agar tidak block GUI untuk suara non-looping yang mungkin panjang
                def _play_once_worker():
                    sd.play(data, samplerate)
                    sd.wait()
                threading.Thread(target=_play_once_worker, daemon=True).start()
            except Exception as e:
                print(f"[AudioManager] Error memainkan '{sound_name}' sekali: {e}")

    def stop_sound(self, sound_name):
        print(f"[AudioManager] Mencoba menghentikan suara: '{sound_name}'")
        if sound_name in self.active_loop_threads:
            loop_info = self.active_loop_threads.pop(sound_name) # Ambil dan hapus dari daftar aktif
            if loop_info['thread'].is_alive():
                loop_info['stop_event'].set() # Kirim sinyal stop ke thread
                # sd.stop() # Ini akan menghentikan SEMUA playback sounddevice
                           # Lebih baik biarkan thread keluar secara alami atau stop stream spesifik jika pakai sd.Stream
                print(f"[AudioManager] Sinyal stop dikirim ke loop '{sound_name}'.")
            # sd.stop() bisa dipanggil di sini jika ingin memastikan semua playback sounddevice berhenti
            # tapi ini akan menghentikan suara non-looping juga jika ada yg sedang main via sd.play di thread lain
        else:
            # Untuk suara non-looping yang dimainkan di thread, mereka akan berhenti sendiri.
            # Jika kamu butuh menghentikan suara non-looping secara paksa, itu lebih kompleks.
            # Untuk alarm yang looping, fokus kita di atas.
            print(f"[AudioManager] Tidak ada loop aktif yang tercatat untuk '{sound_name}'. Memanggil sd.stop() global.")
            sd.stop() # Stop playback global sebagai fallback (misal jika ada sd.play yg tidak terkelola)


    def toggle_mute(self):
        self.is_muted = not self.is_muted
        print(f"[AudioManager] Tombol Mute. Status Mute: {self.is_muted}")
        if self.is_muted:
            self.stop_all_sounds()

    def is_playing(self, sound_name):
        """Cek apakah suara looping tertentu sedang aktif."""
        if sound_name in self.active_loop_threads:
            return self.active_loop_threads[sound_name]['thread'].is_alive()
        return False

    def stop_all_sounds(self):
        print("[AudioManager] Menghentikan semua suara...")
        for sound_name in list(self.active_loop_threads.keys()): # list() agar bisa di-pop saat iterasi
            self.stop_sound(sound_name)
        # sd.stop() # Panggilan global terakhir untuk memastikan semua berhenti