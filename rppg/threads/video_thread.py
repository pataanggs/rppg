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
        # Changed hr_update to emit both float (HR) and bool (is_valid)
        hr_update = pyqtSignal(float, bool) 
        face_detected = pyqtSignal(bool)
        signal_quality_update = pyqtSignal(float)

    def __init__(self, camera_index=0):
        super().__init__()
        self.daemon = True  # Thread will automatically terminate when main program exits
        self.signals = self.Signals()
        self.frame_update = self.signals.frame_update
        self.hr_update = self.signals.hr_update
        self.face_detected = self.signals.face_detected
        self.signal_quality_update = self.signals.signal_quality_update
        
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print(f"Error: Unable to open camera {camera_index}")
            # It's good practice to set running to False if camera fails to open
            self.running = False 
            return
            
        # Set camera properties for higher FPS
        # Try to set camera to 60fps and higher priority
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 60)  # Request 60fps from camera
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Set smaller buffer size for lower latency
        self.running = False # Will be set to True in run()
        
        # Initialize face detection (both MediaPipe and traditional Haar cascade as fallback)
        self.mp_face_detection = self._initialize_mp_face_detection()
        self.mp_face_mesh = self._initialize_mp_face_mesh()
        self.haar_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Track which face detection method is currently active
        self.active_detector = "mediapipe"
        
        # Algorithm settings - can be adjusted via settings
        self.window_size = 90  # 3 seconds at 30fps
        self.min_hr = 40
        self.max_hr = 180
        self.show_face_rect = True
        self.show_bpm_on_frame = True
        self.show_landmarks = False
        
        # Tracking variables
        self.current_hr = 0
        self.confidence = 0
        self.has_face = False
        self.last_face_time = 0
        self.last_landmark_time = 0
        self.landmark_lost_threshold = 0.5  # seconds
        self.face_lost_threshold = 1.0  # seconds
        self.signal_processor = SignalProcessor()
        
        # ROI tracking for forehead and cheeks
        self.forehead_roi = None
        self.left_cheek_roi = None
        self.right_cheek_roi = None
        
        # Performance optimization variables
        self.frame_count = 0
        self.last_hr_update_time = 0
        self.hr_update_interval = 0.3  # Update HR less frequently (0.3s instead of 0.2s)
        
        # Start with higher frame skipping by default - process fewer frames for better performance
        self.frame_skip = 2  # Start with processing every other frame
        self.processing_times = []
        self.max_processing_times = 30
        self.target_fps = 30  # Target a higher FPS
        
        # Exposure and white balance settings
        self.auto_settings = True
        self.exposure = -1  # Auto exposure
        
        # Use lower resolution for processing to improve performance
        self.process_width = 240  # Even lower resolution for processing (was 320)
        self.process_height = 180  # Even lower resolution for processing (was 240)

        # Bounding box smoothing variables
        self.smoothed_bbox = None
        self.smoothing_alpha = 0.7 # Alpha for exponential moving average. Higher means less smoothing.
        self.mediapipe_fail_count = 0
        self.mediapipe_fallback_threshold = 15 # Number of frames MediaPipe can fail before switching to Haar
        self.haar_active_time = 0
        self.haar_switch_back_delay = 2.0 # Seconds before attempting to switch back to MediaPipe from Haar

    def _initialize_mp_face_detection(self):
        """Initialize MediaPipe face detection."""
        mp_face_detection = mp.solutions.face_detection
        return mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for close range, 1 for far range
            min_detection_confidence=0.5
        )
        
    def _initialize_mp_face_mesh(self):
        """Initialize MediaPipe face mesh for more accurate landmark tracking."""
        mp_face_mesh = mp.solutions.face_mesh
        return mp_face_mesh.FaceMesh(
            max_num_faces=1,  # We only need one face for heart rate
            refine_landmarks=False,  # Disable refinement for better performance
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def run(self):
        """Start capturing frames and processing rPPG signals."""
        self.running = True
        face_frames = []
        timestamps = []
        fps_counter = FPSCounter()
        fps_counter.avg_frames = 15  # Use fewer frames for FPS calculation
        
        if self.auto_settings:
            self._configure_camera()
        
        last_detection_time = 0
        detection_interval = 0.2  # Increase detection interval to reduce processing (was 0.1s)
        
        # Preserve FPS by limiting processing
        last_frame_time = time.time()
        fixed_time_step = 1.0 / 30.0  # Fixed time step to maintain consistent timing
        
        while self.running:
            # Calculate how long to sleep to maintain consistent timing
            current_time = time.time()
            elapsed = current_time - last_frame_time
            sleep_time = max(0, fixed_time_step - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            last_frame_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                time.sleep(0.1)  # Avoid tight loop if camera fails
                continue

            fps_counter.update()
            current_fps = fps_counter.get_fps()
            
            # More aggressive frame skipping based on performance
            self.frame_count += 1
            if self.frame_count % self.frame_skip != 0:
                continue
                
            # Capture timestamps for signal processing
            current_time = time.time()
            timestamps.append(current_time)
            
            # Measure processing time to adjust frame skipping
            process_start = time.time()
            
            # Create a smaller copy for processing - more aggressive resizing
            display_frame = frame.copy()  # Keep original for display
            if frame.shape[1] > self.process_width:
                scale = self.process_width / frame.shape[1]
                process_frame = cv2.resize(frame, (self.process_width, int(frame.shape[0] * scale)))
            else:
                process_frame = frame.copy()
            
            # Mirror the frame for more intuitive display
            display_frame = cv2.flip(display_frame, 1)
            process_frame = cv2.flip(process_frame, 1)
            
            face_detected_in_frame = False
            
            # --- Refined Detector Switching Logic ---
            # Prioritize MediaPipe. Only switch to Haar if MediaPipe consistently fails.
            # Attempt to switch back to MediaPipe after a delay if Haar is active.
            
            if self.active_detector == "mediapipe":
                frame_rgb = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
                face_results = self.mp_face_detection.process(frame_rgb)
                if face_results and face_results.detections:
                    face_detected_in_frame = self._process_face_detections(
                        display_frame, process_frame, face_results.detections, face_frames, timestamps)
                    self.mediapipe_fail_count = 0 # Reset fail count on successful detection
                else:
                    self.mediapipe_fail_count += 1
                    if self.mediapipe_fail_count > self.mediapipe_fallback_threshold:
                        print("MediaPipe failed consistently, falling back to Haar.")
                        self.active_detector = "haar"
                        self.haar_active_time = current_time # Record time of switch
            
            if self.active_detector == "haar":
                gray = cv2.cvtColor(process_frame, cv2.COLOR_BGR2GRAY)
                faces = self.haar_face_cascade.detectMultiScale(
                    gray, scaleFactor=1.2, minNeighbors=4, minSize=(30, 30))
                if len(faces) > 0:
                    face_detected_in_frame = self._process_haar_faces(
                        display_frame, process_frame, faces, face_frames, timestamps)
                
                # Attempt to switch back to MediaPipe after a delay
                if current_time - self.haar_active_time > self.haar_switch_back_delay:
                    print("Attempting to switch back to MediaPipe.")
                    self.active_detector = "mediapipe"
                    self.mediapipe_fail_count = 0 # Reset fail count for MediaPipe
            
            # --- End Refined Detector Switching Logic ---
            
            # Check if face has been lost
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
                # Reset ROIs and smoothed bbox when face is lost
                self.forehead_roi = None
                self.left_cheek_roi = None
                self.right_cheek_roi = None
                self.smoothed_bbox = None # Reset smoothed bbox
            
            # Calculate and emit heart rate at regular intervals - reduced frequency
            if len(face_frames) > self.window_size and current_time - self.last_hr_update_time > self.hr_update_interval:
                self._process_ppg_signal(face_frames[-self.window_size:], 
                                         timestamps[-self.window_size:])
                self.last_hr_update_time = current_time
            
            # Add fps and other info to frame
            self._add_info_to_frame(display_frame, current_fps)
            
            # Update GUI with the processed frame
            self.frame_update.emit(display_frame)
            
            # Trim arrays more aggressively to save memory
            if len(face_frames) > self.window_size * 1.5:
                face_frames = face_frames[-self.window_size:]
                timestamps = timestamps[-self.window_size:]
            
            # Calculate processing time and update frame skip
            process_time = time.time() - process_start
            self._update_frame_skip(process_time)
        
        self.stop()
        
    def _update_frame_skip(self, process_time):
        """Dynamically adjust frame skipping based on processing times."""
        self.processing_times.append(process_time)
        if len(self.processing_times) > self.max_processing_times:
            self.processing_times.pop(0)
            
        if len(self.processing_times) >= 10:
            avg_time = np.mean(self.processing_times)
            target_time = 1.0 / self.target_fps
            
            # More aggressive frame skipping for better performance
            if avg_time > target_time * 1.1:
                # Too slow, increase frame skipping more quickly
                self.frame_skip = min(self.frame_skip + 1, 5)  # Allow up to 5 frames to be skipped
            elif avg_time < target_time * 0.7 and self.frame_skip > 1:
                # Fast enough, decrease frame skipping slowly
                self.frame_skip = max(self.frame_skip - 1, 1)

    def _configure_camera(self):
        """Configure camera settings for optimal rPPG performance."""
        try:
            # Try to optimize camera settings for higher FPS
            
            # Disable auto focus to reduce CPU usage and increase frame rate
            if hasattr(cv2, 'CAP_PROP_AUTOFOCUS'):
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                
            # Set lower resolution format to increase frame rate
            if hasattr(cv2, 'CAP_PROP_FOURCC'):
                codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # MJPEG usually gives higher FPS
                self.cap.set(cv2.CAP_PROP_FOURCC, codec)
            
            # Set to higher framerate
            self.cap.set(cv2.CAP_PROP_FPS, 60)
            
            # Try to disable auto white balance and auto exposure for more stable color readings
            if hasattr(cv2, 'CAP_PROP_AUTO_WB'):
                self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)
            if hasattr(cv2, 'CAP_PROP_AUTO_EXPOSURE'):
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
                # Set a fixed exposure if auto exposure is disabled
                if self.exposure > 0:
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
        except Exception as e:
            print(f"Warning: Could not configure camera settings: {e}")

    def _add_info_to_frame(self, frame, fps):
        """Add information overlays to the frame."""
        # Add FPS counter
        cv2.putText(
            frame, f"FPS: {fps:.1f} (Skip: {self.frame_skip})", 
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
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
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
            
        # Add detector info
        detector_text = f"Detector: {self.active_detector}"
        cv2.putText(
            frame, detector_text, 
            (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )

    def _process_face_landmarks(self, display_frame, process_frame, landmarks, face_frames, timestamps):
        """Process face landmarks from MediaPipe face mesh."""
        if not landmarks:
            return False
            
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        
        # Draw landmarks if enabled (on display frame only)
        if self.show_landmarks:
            mp_drawing.draw_landmarks(
                display_frame,
                landmarks,
                mp.solutions.face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
            )
        
        h, w, _ = process_frame.shape
        
        # Get forehead landmarks (simplified for better performance)
        forehead_points = [10, 67, 69, 104, 108, 151, 337, 338, 380]
        
        # Get coordinates of landmarks
        landmarks_coords = []
        for landmark in landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            landmarks_coords.append((x, y))
        
        # Get coordinates of forehead points
        forehead_coords = [landmarks_coords[i] for i in forehead_points if i < len(landmarks_coords)]
        
        if not forehead_coords:
            return False
            
        # Create mask and ROI for forehead
        forehead_mask = self._create_roi_mask(process_frame, forehead_coords)
        forehead_roi = cv2.bitwise_and(process_frame, process_frame, mask=forehead_mask)
        
        # Store ROI for visualization
        self.forehead_roi = forehead_roi
        
        # Visualize ROI on display frame
        if self.show_face_rect:
            # Draw simpler visualization for better performance
            hull = cv2.convexHull(np.array(forehead_coords))
            cv2.drawContours(display_frame, [hull], 0, (0, 255, 0), 2)
        
        # Extract green channel average
        forehead_green = cv2.mean(forehead_roi, forehead_mask)[1]
        face_frames.append(forehead_green)
        
        return True

    def _create_roi_mask(self, frame, points):
        """Create a binary mask for a region of interest."""
        mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        if len(points) >= 3:  # Need at least 3 points for a polygon
            points_array = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [points_array], 255)
        return mask

    def _process_face_detections(self, display_frame, process_frame, detections, face_frames, timestamps):
        """Process the MediaPipe face detections and extract rPPG signal."""
        processed_face = False
        if not detections:
            return False

        # Get the first detection
        detection = detections[0]
        bbox = detection.location_data.relative_bounding_box
        ih, iw, _ = process_frame.shape
        x, y = int(bbox.xmin * iw), int(bbox.ymin * ih)
        w, h = int(bbox.width * iw), int(bbox.height * ih)
        
        # Apply smoothing to the bounding box
        current_bbox = np.array([x, y, w, h], dtype=np.float32)
        if self.smoothed_bbox is None:
            self.smoothed_bbox = current_bbox
        else:
            self.smoothed_bbox = self.smoothing_alpha * current_bbox + \
                                 (1 - self.smoothing_alpha) * self.smoothed_bbox
        
        # Use smoothed bounding box for drawing and ROI extraction
        smoothed_x, smoothed_y, smoothed_w, smoothed_h = map(int, self.smoothed_bbox)

        # Check if the smoothed bounding box is valid
        if smoothed_x < 0 or smoothed_y < 0 or smoothed_w <= 0 or smoothed_h <= 0 or \
           smoothed_x + smoothed_w > iw or smoothed_y + smoothed_h > ih:
            return False
        
        # Scale coordinates for display frame
        display_h, display_w = display_frame.shape[:2]
        scale_x = display_w / iw
        scale_y = display_h / ih
        
        # Draw bounding box on display frame if enabled
        if self.show_face_rect:
            display_x = int(smoothed_x * scale_x)
            display_y = int(smoothed_y * scale_y)
            display_w = int(smoothed_w * scale_x)
            display_h = int(smoothed_h * scale_y)
            cv2.rectangle(display_frame, 
                          (display_x, display_y), 
                          (display_x + display_w, display_y + display_h), 
                          (0, 255, 0), 2)
        
        # Define forehead ROI relative to the smoothed face bounding box
        forehead_x = smoothed_x + int(smoothed_w * 0.2)
        forehead_y = smoothed_y + int(smoothed_h * 0.1)
        forehead_w = int(smoothed_w * 0.6)
        forehead_h = int(smoothed_h * 0.15)
        
        # Ensure forehead ROI is valid
        if forehead_x >= 0 and forehead_y >= 0 and forehead_w > 0 and forehead_h > 0 and \
           forehead_x + forehead_w <= iw and forehead_y + forehead_h <= ih:
            
            # Extract forehead ROI from process frame
            forehead_roi = process_frame[forehead_y:forehead_y + forehead_h, 
                                         forehead_x:forehead_x + forehead_w]
            
            # Draw forehead ROI on display frame if enabled
            if self.show_face_rect:
                display_fx = int(forehead_x * scale_x)
                display_fy = int(forehead_y * scale_y)
                display_fw = int(forehead_w * scale_x)
                display_fh = int(forehead_h * scale_y)
                cv2.rectangle(display_frame, 
                              (display_fx, display_fy), 
                              (display_fx + display_fw, display_fy + display_fh), 
                              (0, 255, 255), 2)
            
            # Get signal from the forehead region (green channel average)
            if forehead_roi.size > 0:
                green_avg = np.mean(forehead_roi[:, :, 1])
                face_frames.append(green_avg)
                processed_face = True
        
        return processed_face

    def _process_haar_faces(self, display_frame, process_frame, faces, face_frames, timestamps):
        """Process faces detected by Haar cascade."""
        # Use the largest face (by area)
        if len(faces) == 0:
            return False
            
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Apply smoothing to the bounding box
        current_bbox = np.array([x, y, w, h], dtype=np.float32)
        if self.smoothed_bbox is None:
            self.smoothed_bbox = current_bbox
        else:
            self.smoothed_bbox = self.smoothing_alpha * current_bbox + \
                                 (1 - self.smoothing_alpha) * self.smoothed_bbox
        
        # Use smoothed bounding box for drawing and ROI extraction
        smoothed_x, smoothed_y, smoothed_w, smoothed_h = map(int, self.smoothed_bbox)

        # Scale coordinates for display frame
        display_h, display_w = display_frame.shape[:2]
        process_h, process_w = process_frame.shape[:2]
        scale_x = display_w / process_w
        scale_y = display_h / process_h
        
        # Draw bounding box on display frame if enabled
        if self.show_face_rect:
            display_x = int(smoothed_x * scale_x)
            display_y = int(smoothed_y * scale_y)
            display_w = int(smoothed_w * scale_x)
            display_h = int(smoothed_h * scale_y)
            cv2.rectangle(display_frame, 
                          (display_x, display_y), 
                          (display_x + display_w, display_y + display_h), 
                          (255, 0, 0), 2)
        
        # Define forehead ROI
        forehead_x = smoothed_x + int(smoothed_w * 0.25)
        forehead_y = smoothed_y + int(smoothed_h * 0.1)
        forehead_w = int(smoothed_w * 0.5)
        forehead_h = int(smoothed_h * 0.15)
        
        # Check if ROI is valid
        if forehead_x >= 0 and forehead_y >= 0 and forehead_w > 0 and forehead_h > 0 and \
           forehead_x + forehead_w < process_w and forehead_y + forehead_h < process_h:
            
            # Extract forehead ROI from process frame
            forehead_roi = process_frame[forehead_y:forehead_y + forehead_h, 
                                         forehead_x:forehead_x + forehead_w]
            
            # Draw ROI on display frame if enabled
            if self.show_face_rect:
                display_fx = int(forehead_x * scale_x)
                display_fy = int(forehead_y * scale_y)
                display_fw = int(forehead_w * scale_x)
                display_fh = int(forehead_h * scale_y)
                cv2.rectangle(display_frame, 
                              (display_fx, display_fy), 
                              (display_fx + display_fw, display_fy + display_fh), 
                              (255, 0, 255), 2)
            
            # Get signal if ROI is not empty
            if forehead_roi.size > 0:
                green_avg = np.mean(forehead_roi[:, :, 1])
                face_frames.append(green_avg)
                return True
        
        return False

    def _process_ppg_signal(self, signal, timestamps):
        """Process the PPG signal to estimate heart rate."""
        # Use SignalProcessor class for better isolation of concerns
        hr, confidence = self.signal_processor.process(signal, timestamps)
        
        is_valid_hr = False
        if hr is not None and self.min_hr <= hr <= self.max_hr:
            self.current_hr = hr
            self.confidence = confidence
            is_valid_hr = True # Set to True if HR is valid
        else:
            # If HR is not valid, reset current_hr and confidence
            self.current_hr = 0 
            self.confidence = 0
            
        # Emit both heart rate and validity flag
        self.hr_update.emit(self.current_hr, is_valid_hr)
            
        # Emit signal quality (from signal processor)
        signal_quality = self.signal_processor.signal_quality * 100  # Convert to 0-100 scale
        self.signal_quality_update.emit(signal_quality)

    def set_settings(self, settings):
        """Update thread settings."""
        self.window_size = settings.get('window_size', 90)
        self.min_hr = settings.get('min_hr', 40)
        self.max_hr = settings.get('max_hr', 180)
        self.show_face_rect = settings.get('show_face_rect', True)
        self.show_bpm_on_frame = settings.get('show_bpm_on_frame', True)
        self.show_landmarks = settings.get('show_landmarks', False)
        
        # Performance settings
        if 'target_fps' in settings:
            self.target_fps = settings['target_fps']
            
        if 'process_resolution' in settings:
            res = settings['process_resolution']
            if res == 'low':
                self.process_width, self.process_height = 320, 240
            elif res == 'medium':
                self.process_width, self.process_height = 480, 360
            elif res == 'high':
                self.process_width, self.process_height = 640, 480
        
        # Apply camera settings if provided
        if 'auto_settings' in settings:
            self.auto_settings = settings['auto_settings']
            if not self.auto_settings and 'exposure' in settings:
                self.exposure = settings['exposure']
                self._configure_camera()

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
