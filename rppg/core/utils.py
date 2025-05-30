# rppg/core/utils.py
# File untuk fungsi-fungsi utilitas umum
# Contoh:
import time

class FPSCounter:
    def __init__(self, avg_frames=30):
        self.avg_frames = avg_frames
        self.frame_times = []

    def update(self):
        self.frame_times.append(time.time())
        if len(self.frame_times) > self.avg_frames:
            self.frame_times.pop(0)

    def get_fps(self):
        if len(self.frame_times) < 2:
            return 0.0
        time_diff = self.frame_times[-1] - self.frame_times[0]
        if time_diff == 0:
            return 0.0
        return (len(self.frame_times) - 1) / time_diff

# Tambahkan fungsi utilitas lain di sini jika perlu