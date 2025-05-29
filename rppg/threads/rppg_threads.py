# rppg/threads/rppg_threads.py
import cv2
import mediapipe as mp
import threading
import time
import numpy as np
import queue
from PyQt6.QtCore import pyqtSignal, QObject

# GlobalSignals tetap sama
class GlobalSignals(QObject):
    hr_update = pyqtSignal(float, bool, float) # HR, IsValid, Confidence
    face_detected = pyqtSignal(bool)
    signal_quality_update = pyqtSignal(float)

# CaptureThread tetap sama (dari kodemu)
class CaptureThread(threading.Thread):
    def __init__(self, camera_index, frame_queue):
        super().__init__()
        self.daemon = True
        self.camera_index = camera_index
        self.frame_queue = frame_queue
        self.running = False
        self.cap = None

    def _configure_camera(self):
        if not self.cap: return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def run(self):
        print(f"CaptureThread starting for camera_index: {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(self.camera_index) # Fallback
            if not self.cap.isOpened():
                print(f"Error: Unable to open camera {self.camera_index}")
                return
        self._configure_camera()
        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            timestamp = time.time()
            if not ret: time.sleep(0.1); continue
            try:
                self.frame_queue.put((frame, timestamp), block=True, timeout=0.5)
            except queue.Full:
                try: self.frame_queue.get_nowait() 
                except queue.Empty: pass
        print("CaptureThread stopping..."); 
        if self.cap: self.cap.release()
        print("CaptureThread stopped.")

    def stop(self):
        self.running = False
        while not self.frame_queue.empty():
            try: self.frame_queue.get_nowait()
            except queue.Empty: break

# --- MODIFIKASI ProcessThread ---
class ProcessThread(threading.Thread):
    def __init__(self, frame_queue, signal_queue, display_queue, signals_obj):
        super().__init__()
        self.daemon = True
        self.frame_queue = frame_queue
        self.signal_queue = signal_queue
        self.display_queue = display_queue
        self.signals = signals_obj
        self.running = False
        self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5)
        
        # Inisialisasi atribut yang dibutuhkan
        self.smoothed_bbox = None
        self.smoothing_alpha = 0.7  # Kamu bisa sesuaikan nilai alpha ini
        self.has_face = False
        self.last_face_time = 0
        self.face_lost_threshold = 1.0
        self.process_width = 320  # Target lebar untuk frame yang diproses
        # self.process_height = 240 # Target tinggi tidak dipakai langsung jika aspek rasio dijaga
        self.show_face_rect = True # Untuk menampilkan bbox atau tidak
        self.current_hr_for_display = 0.0
        
        if hasattr(self.signals, 'hr_update'): # Cek apakah sinyal ada sebelum connect
            self.signals.hr_update.connect(self._update_hr_for_display)

    def _update_hr_for_display(self, hr, is_valid, confidence):
        self.current_hr_for_display = hr if is_valid else 0.0

    def _draw_scaled_boxes(self, display_frame, process_frame_actual_shape, face_box_on_proc, roi_box_on_proc, face_color, roi_color):
        """
        Menggambar bounding box wajah dan ROI ke display_frame dengan penskalaan yang benar.
        """
        ph_proc, pw_proc = process_frame_actual_shape[:2] # Dimensi aktual process_frame
        dh_disp, dw_disp = display_frame.shape[:2]      # Dimensi display_frame

        if pw_proc == 0 or ph_proc == 0: # Hindari pembagian dengan nol
            return

        scale_x = dw_disp / pw_proc
        scale_y = dh_disp / ph_proc

        sx, sy, sw, sh = face_box_on_proc
        fx, fy, fw, fh = roi_box_on_proc

        # Gambar bbox wajah (hijau)
        cv2.rectangle(display_frame, 
                      (int(sx * scale_x), int(sy * scale_y)), 
                      (int((sx + sw) * scale_x), int((sy + sh) * scale_y)), 
                      face_color, 2)
        # Gambar bbox ROI (kuning)
        cv2.rectangle(display_frame, 
                      (int(fx * scale_x), int(fy * scale_y)), 
                      (int((fx + fw) * scale_x), int((fy + fh) * scale_y)), 
                      roi_color, 1)

    def _process_mp_face(self, display_frame, process_frame): # process_frame adalah frame_yang_sudah_diolah (resized & flipped)
        frame_rgb = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.mp_face_detection.process(frame_rgb)
        frame_rgb.flags.writeable = True
        
        green_avg = None
        face_found = False

        if results and results.detections:
            detection = results.detections[0]
            bbox_rel = detection.location_data.relative_bounding_box
            
            ph_proc, pw_proc, _ = process_frame.shape 

            x = int(bbox_rel.xmin * pw_proc)
            y = int(bbox_rel.ymin * ph_proc - 10) # Sedikit naik untuk menghindari bbox terlalu rendah
            w = int(bbox_rel.width * pw_proc)
            h = int(bbox_rel.height * ph_proc)

            # --- Penyesuaian Tinggi BBox Wajah (Hijau) ---
            # Jika dirasa "kurang tinggi", kita bisa perbesar sedikit.
            # Faktor 0.1 berarti menambah 10% dari tinggi asli (5% ke atas, 5% ke bawah)
            height_expansion_factor = 0.15 # Coba nilai antara 0.0 (tanpa ekspansi) s/d 0.3
            
            h_added = int(h * height_expansion_factor)
            y_expanded = y - (h_added // 2)
            h_expanded_total = h + h_added
            
            # Pastikan tidak keluar batas frame atas
            y_expanded = max(0, y_expanded)
            # Pastikan tidak keluar batas frame bawah setelah ditambah
            if y_expanded + h_expanded_total > ph_proc:
                h_expanded_total = ph_proc - y_expanded
            
            # Gunakan y_expanded dan h_expanded_total untuk bbox wajah
            current_bbox_on_proc = np.array([x, y_expanded, w, h_expanded_total], dtype=np.float32)
            # current_bbox_on_proc = np.array([x, y, w, h], dtype=np.float32) # << Versi Asli tanpa ekspansi tinggi


            if self.smoothed_bbox is None:
                self.smoothed_bbox = current_bbox_on_proc
            else:
                self.smoothed_bbox = self.smoothing_alpha * current_bbox_on_proc + \
                                     (1 - self.smoothing_alpha) * self.smoothed_bbox
            
            sx, sy, sw, sh = map(int, self.smoothed_bbox) # Ini bbox wajah (hijau) yang sudah di-smooth

            # --- Penyesuaian Posisi dan Ukuran ROI Dahi (Kuning) ---
            # "box kuning kurang ke atas di dahi" -> fy perlu lebih kecil (naik)
            # "box kurang tinggi" pada ROI juga bisa disesuaikan dengan fh_ratio
            
            # Persentase offset Y dari atas bbox wajah (sx,sy). Lebih kecil = lebih ke atas.
            forehead_y_offset_ratio = 0.03  
            # Persentase tinggi ROI dahi relatif terhadap tinggi bbox wajah (sh)
            forehead_height_ratio   = 0.20  # Coba: 0.15, 0.20, 0.25. Semula: 0.15
            # Persentase offset X dari kiri bbox wajah
            forehead_x_offset_ratio = 0.20  # Biasanya 0.2 - 0.25 sudah oke
            # Persentase lebar ROI dahi relatif terhadap lebar bbox wajah (sw)
            forehead_width_ratio    = 0.60  

            fx = sx + int(sw * forehead_x_offset_ratio)
            fy = sy + int(sh * forehead_y_offset_ratio) 
            fw = int(sw * forehead_width_ratio)
            fh = int(sh * forehead_height_ratio)
            
            # Pastikan ROI tetap berada dalam batas process_frame
            fx = max(0, fx); fy = max(0, fy) # Tidak boleh negatif
            if fx + fw > pw_proc: fw = pw_proc - fx 
            if fy + fh > ph_proc: fh = ph_proc - fy
            
            if fw > 0 and fh > 0 : # Hanya jika ROI valid
                forehead_roi_on_proc = process_frame[fy : fy + fh, fx : fx + fw]
                if forehead_roi_on_proc.size > 0:
                    green_avg = np.mean(forehead_roi_on_proc[:, :, 1])
                    face_found = True
                    if self.show_face_rect:
                        self._draw_scaled_boxes(display_frame, 
                                               process_frame.shape, # Dimensi aktual process_frame
                                               (sx, sy, sw, sh),    # Bbox wajah (hijau)
                                               (fx, fy, fw, fh),    # Bbox ROI (kuning)
                                               (0, 255, 0),         # Warna wajah
                                               (0, 255, 255))       # Warna ROI
        else: # Jika tidak ada deteksi wajah
            self.smoothed_bbox = None # Reset smoothed bbox

        return green_avg, face_found

    def _add_info_to_frame(self, frame):
        if self.current_hr_for_display > 0:
             cv2.putText(frame, f"HR: {self.current_hr_for_display:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def run(self):
        print("ProcessThread starting..."); self.running = True
        while self.running:
            try: frame_data = self.frame_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                if not self.running: break
                continue
            
            original_frame, timestamp = frame_data
            if original_frame is None: continue # Lewati jika frame None

            display_frame = cv2.flip(original_frame.copy(), 1)
            
            # Resize original_frame untuk process_frame dengan menjaga aspek rasio
            # Target lebar adalah self.process_width
            original_h, original_w = original_frame.shape[:2]
            if original_w == 0 or original_h == 0: continue # Lewati jika frame tidak valid

            scale_ratio = self.process_width / original_w
            ph_proc = int(original_h * scale_ratio) # Tinggi terhitung untuk process_frame
            pw_proc = self.process_width             # Lebar process_frame adalah target kita

            if ph_proc <= 0 or pw_proc <= 0: # Hindari dimensi tidak valid
                # print(f"ProcessThread: Invalid resize dimensions pw={pw_proc}, ph={ph_proc}")
                continue

            process_frame_resized = cv2.resize(original_frame, (pw_proc, ph_proc), interpolation=cv2.INTER_AREA)
            process_frame_flipped = cv2.flip(process_frame_resized, 1)
            
            green_avg, face_detected_in_frame = self._process_mp_face(display_frame, process_frame_flipped)
            
            current_time = time.time()
            if face_detected_in_frame:
                if not self.has_face: self.signals.face_detected.emit(True)
                self.has_face = True; self.last_face_time = current_time
            elif self.has_face and (current_time - self.last_face_time) > self.face_lost_threshold:
                if self.has_face: self.signals.face_detected.emit(False)
                self.has_face = False; self.smoothed_bbox = None
            
            if green_avg is not None:
                try: self.signal_queue.put_nowait((green_avg, timestamp))
                except queue.Full: pass # Abaikan jika queue sinyal penuh
                
            self._add_info_to_frame(display_frame)
            
            try: self.display_queue.put_nowait(display_frame)
            except queue.Full:
                try: self.display_queue.get_nowait()
                except queue.Empty: pass
                try: self.display_queue.put_nowait(display_frame)
                except queue.Full: pass
            
            # self.frame_queue.task_done() # task_done() tidak selalu diperlukan dengan get() biasa

        print("ProcessThread stopped."); 
        if hasattr(self.mp_face_detection, 'close'): self.mp_face_detection.close()


    def stop(self):
        self.running = False
        # Kosongkan queue untuk unblock jika ada yang menunggu
        while not self.signal_queue.empty():
            try: self.signal_queue.get_nowait()
            except queue.Empty: break
        while not self.display_queue.empty():
            try: self.display_queue.get_nowait()
            except queue.Empty: break

# AnalysisThread tetap sama (dari kodemu)
class AnalysisThread(threading.Thread):
    # ... (Salin seluruh kelas AnalysisThread kamu yang sudah benar di sini) ...
    def __init__(self, signal_queue, signals_obj):
        super().__init__()
        self.daemon = True
        self.signal_queue = signal_queue
        self.signals = signals_obj
        self.running = False
        self.signal_processor = None 
        self.window_size = 90; self.min_hr = 40; self.max_hr = 180
        self.buffer = []; self.timestamps = []
        self.hr_update_interval = 1.0; self.last_hr_update_time = 0

    def run(self):
        print("AnalysisThread starting...")
        from rppg.signal.signal_processor import SignalProcessor # Import di dalam thread
        self.signal_processor = SignalProcessor()
        self.running = True
        while self.running:
            try: signal_val, timestamp = self.signal_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                if not self.running: break
                continue
            self.buffer.append(signal_val); self.timestamps.append(timestamp)
            while len(self.buffer) > self.window_size * 2: # Jaga buffer
                self.buffer.pop(0); self.timestamps.pop(0)
            current_time = time.time()
            if len(self.buffer) >= self.window_size and \
               (current_time - self.last_hr_update_time) >= self.hr_update_interval:
                # Panggil SignalProcessor yang sudah dimodifikasi (mengembalikan 3 nilai)
                hr, confidence, quality = self.signal_processor.process(
                    self.buffer[-self.window_size:], self.timestamps[-self.window_size:])
                
                is_valid = False; current_hr_val = 0.0 # Ganti nama var agar tidak bentrok
                if hr is not None and self.min_hr <= hr <= self.max_hr:
                    current_hr_val = hr; is_valid = True
                
                self.signals.hr_update.emit(current_hr_val, is_valid, confidence)
                self.signals.signal_quality_update.emit(quality)
                self.last_hr_update_time = current_time
            # self.signal_queue.task_done() # Tidak selalu diperlukan
        print("AnalysisThread stopped.")

    def stop(self):
        self.running = False