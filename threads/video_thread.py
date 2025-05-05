import cv2
import mediapipe as mp
import threading
import time
import numpy as np
from scipy import signal as sg
from PyQt6.QtCore import pyqtSignal, QObject

from signal_processor import SignalProcessor


class VideoThread(threading.Thread):
    """Thread to capture video frames and process rPPG data."""
    
    class Signals(QObject):
        frame_update = pyqtSignal(object)
        hr_update = pyqtSignal(float)
        face_detected = pyqtSignal(bool)

    def __init__(self, camera_index=0):
        super().__init__()
        self.signals = self.Signals()
        self.frame_update = self.signals.frame_update
        self.hr_update = self.signals.hr_update
        self.face_detected = self.signals.face_detected
        
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print(f"Error: Unable to open camera {camera_index}")
            return
            
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.running = False
        self.face_detection = self._initialize_face_detection()
        
        # Algorithm settings - can be adjusted via settings
        self.window_size = 90  # 3 seconds at 30fps
        self.min_hr = 40
        self.max_hr = 180
        self.show_face_rect = True
        self.show_bpm_on_frame = True
        
        # Tracking variables
        self.current_hr = 0
        self.confidence = 0
        self.has_face = False
        self.last_face_time = 0
        self.face_lost_threshold = 1.0  # seconds
        self.signal_processor = SignalProcessor()

    def _initialize_face_detection(self):
        """Initialize MediaPipe face detection."""
        mp_face_detection = mp.solutions.face_detection
        return mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for close range, 1 for far range
            min_detection_confidence=0.5
        )

    def run(self):
        """Start capturing frames and processing rPPG signals."""
        self.running = True
        face_frames = []
        timestamps = []
        fps_counter = FPSCounter()
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                time.sleep(0.1)  # Avoid tight loop if camera fails
                continue

            fps_counter.update()
            current_fps = fps_counter.get_fps()
                
            # Capture timestamps for signal processing
            timestamps.append(time.time())
            
            # Resize frame for faster processing if needed
            if frame.shape[1] > 640:
                scale = 640 / frame.shape[1]
                frame = cv2.resize(frame, (640, int(frame.shape[0] * scale)))
            
            # Convert frame to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(frame_rgb)
            
            face_detected_in_frame = False
            if results.detections:
                face_detected_in_frame = self._process_face_detections(
                    frame, results.detections, face_frames, timestamps)
            
            # Check if face has been lost
            current_time = time.time()
            if face_detected_in_frame:
                if not self.has_face:
                    print("Face detected!")
                    self.has_face = True
                    self.face_detected.emit(True)
                self.last_face_time = current_time
            elif self.has_face and (current_time - self.last_face_time) > self.face_lost_threshold:
                print("Face lost!")
                self.has_face = False
                self.face_detected.emit(False)
            
            # Add fps and other info to frame
            self._add_info_to_frame(frame, current_fps)
            
            # Update GUI with the processed frame
            self.frame_update.emit(frame.copy())
            
            # Process at most 30fps - sleep if processing is fast
            elapsed = time.time() - timestamps[-1]
            if elapsed < 1/30:
                time.sleep(1/30 - elapsed)
            
            # Break if user presses q
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.stop()

    def _add_info_to_frame(self, frame, fps):
        """Add information overlays to the frame."""
        # Add FPS counter
        cv2.putText(
            frame, f"FPS: {fps:.1f}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )
        
        # Add heart rate if available and enabled
        if self.show_bpm_on_frame and self.current_hr > 0:
            if self.confidence > 0.7:  # High confidence
                color = (0, 255, 0)  # Green
            elif self.confidence > 0.4:  # Medium confidence
                color = (0, 255, 255)  # Yellow
            else:  # Low confidence
                color = (0, 0, 255)  # Red
                
            cv2.putText(
                frame, f"HR: {self.current_hr:.1f} BPM", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
            )

    def _process_face_detections(self, frame, detections, face_frames, timestamps):
        """Process the detections and extract rPPG signal."""
        processed_face = False
        for detection in detections:
            bbox = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape
            x, y = int(bbox.xmin * iw), int(bbox.ymin * ih)
            w, h = int(bbox.width * iw), int(bbox.height * ih)
            
            # Check if the bounding box is valid
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > iw or y + h > ih:
                continue
                
            # Draw bounding box for face detection if enabled
            if self.show_face_rect:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Extract region of interest (ROI)
            face_roi = frame[y:y + h, x:x + w]
            
            if face_roi.size > 0:
                # Get signal from the face region (green channel average)
                green_avg = np.mean(face_roi[:, :, 1])
                face_frames.append(green_avg)
                processed_face = True
                
                # Process the PPG signal after gathering enough frames
                if len(face_frames) > self.window_size:
                    self._process_ppg_signal(face_frames[-self.window_size:], 
                                           timestamps[-self.window_size:])
                    
                # Limit the size of our arrays
                if len(face_frames) > self.window_size * 2:
                    face_frames = face_frames[-self.window_size:]
                    timestamps = timestamps[-self.window_size:]
            break  # Process only the first valid face
        
        return processed_face

    def _process_ppg_signal(self, signal, timestamps):
        """Process the PPG signal to estimate heart rate."""
        # Use SignalProcessor class for better isolation of concerns
        hr, confidence = self.signal_processor.process(signal, timestamps)
        
        if hr is not None and self.min_hr <= hr <= self.max_hr:
            self.current_hr = hr
            self.confidence = confidence
            self.hr_update.emit(hr)

    def set_settings(self, settings):
        """Update thread settings."""
        self.window_size = settings.get('window_size', 90)
        self.min_hr = settings.get('min_hr', 40)
        self.max_hr = settings.get('max_hr', 180)
        self.show_face_rect = settings.get('show_face_rect', True)
        self.show_bpm_on_frame = settings.get('show_bpm_on_frame', True)

    def stop(self):
        """Stop the video thread and release resources."""
        self.running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()


class FPSCounter:
    """Helper class to calculate and display framerate."""
    
    def __init__(self, avg_frames=30):
        self.avg_frames = avg_frames
        self.frame_times = []
        
    def update(self):
        """Record a new frame timestamp."""
        self.frame_times.append(time.time())
        
        # Keep only the most recent frames for averaging
        if len(self.frame_times) > self.avg_frames:
            self.frame_times.pop(0)
            
    def get_fps(self):
        """Calculate current FPS based on recorded frame times."""
        if len(self.frame_times) < 2:
            return 0.0
            
        # Calculate time difference between oldest and newest frame
        time_diff = self.frame_times[-1] - self.frame_times[0]
        if time_diff == 0:
            return 0.0
            
        # Return frames per second
        return (len(self.frame_times) - 1) / time_diff

