# rppg/threads/rppg_threads.py
import cv2
import mediapipe as mp
import threading
import time
import numpy as np
import queue
from PyQt6.QtCore import pyqtSignal, QObject

# GlobalSignals
class GlobalSignals(QObject):
    hr_update = pyqtSignal(float, bool, float) # HR, IsValid, Confidence
    face_detected = pyqtSignal(bool)
    signal_quality_update = pyqtSignal(float)

# CaptureThread
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
            if not ret:
                # print("CaptureThread: Failed to capture frame.")
                time.sleep(0.1) # Hindari loop ketat jika kamera gagal
                continue
            try:
                self.frame_queue.put((frame, timestamp), block=True, timeout=0.5)
            except queue.Full:
                try: self.frame_queue.get_nowait() # Buang frame lama jika penuh
                except queue.Empty: pass
                # print("CaptureThread: Frame queue full, skipping.")
        print("CaptureThread stopping...")
        if self.cap: self.cap.release()
        print("CaptureThread stopped.")

    def stop(self):
        self.running = False
        while not self.frame_queue.empty():
            try: self.frame_queue.get_nowait()
            except queue.Empty: break

# ProcessThread
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
        self.smoothed_bbox = None
        self.smoothing_alpha = 0.7
        self.has_face = False
        self.last_face_time = 0
        self.face_lost_threshold = 1.0
        self.process_width = 320
        self.process_height = 240
        self.show_face_rect = True
        self.current_hr_for_display = 0.0
        self.signals.hr_update.connect(self._update_hr_for_display)

    def _update_hr_for_display(self, hr, is_valid, confidence):
        self.current_hr_for_display = hr if is_valid else 0.0

    def _process_mp_face(self, display_frame, process_frame):
        frame_rgb = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.mp_face_detection.process(frame_rgb)
        frame_rgb.flags.writeable = True
        green_avg = None; face_found = False
        if results and results.detections:
            detection = results.detections[0]
            bbox_rel = detection.location_data.relative_bounding_box
            ih, iw, _ = process_frame.shape
            x, y, w, h = int(bbox_rel.xmin * iw), int(bbox_rel.ymin * ih), int(bbox_rel.width * iw), int(bbox_rel.height * ih)
            current_bbox = np.array([x, y, w, h], dtype=np.float32)
            if self.smoothed_bbox is None: self.smoothed_bbox = current_bbox
            else: self.smoothed_bbox = self.smoothing_alpha * current_bbox + (1 - self.smoothing_alpha) * self.smoothed_bbox
            sx, sy, sw, sh = map(int, self.smoothed_bbox)
            fx = sx + int(sw * 0.2); fy = sy + int(sh * 0.1); fw = int(sw * 0.6); fh = int(sh * 0.15)
            if 0 <= fx < iw and 0 <= fy < ih and fw > 0 and fh > 0 and (fx + fw) <= iw and (fy + fh) <= ih:
                forehead_roi = process_frame[fy:fy + fh, fx:fx + fw]
                if forehead_roi.size > 0:
                    green_avg = np.mean(forehead_roi[:, :, 1]); face_found = True
                    if self.show_face_rect: self._draw_boxes(display_frame, (sx, sy, sw, sh), (fx, fy, fw, fh), (0, 255, 0))
        return green_avg, face_found

    def _draw_boxes(self, frame, face_box, roi_box, color):
        dh, dw = frame.shape[:2]
        scale_x = dw / self.process_width; scale_y = dh / self.process_height
        sx, sy, sw, sh = face_box; fx, fy, fw, fh = roi_box
        cv2.rectangle(frame, (int(sx*scale_x), int(sy*scale_y)), (int((sx+sw)*scale_x), int((sy+sh)*scale_y)), color, 2)
        cv2.rectangle(frame, (int(fx*scale_x), int(fy*scale_y)), (int((fx+fw)*scale_x), int((fy+fh)*scale_y)), (0, 255, 255), 1)

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
            display_frame = cv2.flip(original_frame.copy(), 1)
            scale = self.process_width / original_frame.shape[1]
            ph = int(original_frame.shape[0] * scale)
            process_frame = cv2.resize(original_frame, (self.process_width, ph), interpolation=cv2.INTER_AREA)
            process_frame = cv2.flip(process_frame, 1)
            green_avg, face_detected_in_frame = self._process_mp_face(display_frame, process_frame)
            current_time = time.time()
            if face_detected_in_frame:
                if not self.has_face: self.signals.face_detected.emit(True)
                self.has_face = True; self.last_face_time = current_time
            elif self.has_face and (current_time - self.last_face_time) > self.face_lost_threshold:
                if self.has_face: self.signals.face_detected.emit(False)
                self.has_face = False; self.smoothed_bbox = None
            if green_avg is not None:
                try: self.signal_queue.put_nowait((green_avg, timestamp))
                except queue.Full: pass
            self._add_info_to_frame(display_frame)
            try: self.display_queue.put_nowait(display_frame)
            except queue.Full:
                try: self.display_queue.get_nowait()
                except queue.Empty: pass
                try: self.display_queue.put_nowait(display_frame)
                except queue.Full: pass
            self.frame_queue.task_done()
        print("ProcessThread stopped."); self.mp_face_detection.close()

    def stop(self):
        self.running = False
        while not self.signal_queue.empty():
            try: self.signal_queue.get_nowait()
            except queue.Empty: break
        while not self.display_queue.empty():
            try: self.display_queue.get_nowait()
            except queue.Empty: break

# AnalysisThread
class AnalysisThread(threading.Thread):
    def __init__(self, signal_queue, signals_obj):
        super().__init__()
        self.daemon = True
        self.signal_queue = signal_queue
        self.signals = signals_obj
        self.running = False
        self.signal_processor = None # Akan diinisialisasi di run()
        self.window_size = 90; self.min_hr = 40; self.max_hr = 180
        self.buffer = []; self.timestamps = []
        self.hr_update_interval = 1.0; self.last_hr_update_time = 0

    def run(self):
        print("AnalysisThread starting...")
        # Import dan inisialisasi SignalProcessor di dalam thread untuk menghindari masalah antar-thread
        from rppg.signal.signal_processor import SignalProcessor
        self.signal_processor = SignalProcessor()
        self.running = True
        while self.running:
            try: signal_val, timestamp = self.signal_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                if not self.running: break
                continue
            self.buffer.append(signal_val); self.timestamps.append(timestamp)
            while len(self.buffer) > self.window_size * 2:
                self.buffer.pop(0); self.timestamps.pop(0)
            current_time = time.time()
            if len(self.buffer) >= self.window_size and \
               (current_time - self.last_hr_update_time) >= self.hr_update_interval:
                hr, confidence, quality = self.signal_processor.process(
                    self.buffer[-self.window_size:], self.timestamps[-self.window_size:])
                is_valid = False; current_hr = 0.0
                if hr is not None and self.min_hr <= hr <= self.max_hr:
                    current_hr = hr; is_valid = True
                self.signals.hr_update.emit(current_hr, is_valid, confidence)
                self.signals.signal_quality_update.emit(quality)
                self.last_hr_update_time = current_time
            self.signal_queue.task_done()
        print("AnalysisThread stopped.")

    def stop(self):
        self.running = False