import cv2
import numpy as np
import time
import logging
import mediapipe as mp
from PyQt6 import QtCore

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Shared variables for rPPG signal and timestamps
rppg_signal = []
time_data = []

class VideoThread(QtCore.QThread):
    """Thread for capturing video and extracting rPPG signal using MediaPipe."""
    change_pixmap_signal = QtCore.pyqtSignal(object, bool)

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.show_landmarks = False
        self.show_bounding_box = False
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        
        # Define regions of interest for rPPG (similar to forehead and cheeks)
        self.roi_indices = {
            'forehead': [10, 67, 69, 104, 108, 337, 338],  # Forehead points
            'left_cheek': [116, 123, 147, 187, 207, 213],  # Left cheek
            'right_cheek': [346, 352, 376, 411, 427, 437]  # Right cheek
        }
        
        self.start_time = time.time()
        logger.info("VideoThread initialized with MediaPipe")

    def run(self):
        """Capture video and extract rPPG signal."""
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            logger.error(f"Could not open camera {self.camera_index}")
            return

        global rppg_signal, time_data
        while self.running:
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to capture frame")
                break

            # Process with MediaPipe Face Mesh
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(frame_rgb)
            face_detected = False
            roi_values = []

            # Create a copy of the frame for drawing
            display_frame = frame.copy()

            # If face landmarks detected
            if results.multi_face_landmarks:
                face_detected = True
                face_landmarks = results.multi_face_landmarks[0]
                
                # Extract bounding box coordinates
                h, w, _ = frame.shape
                landmark_points = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]
                x_min = min([p[0] for p in landmark_points])
                y_min = min([p[1] for p in landmark_points])
                x_max = max([p[0] for p in landmark_points])
                y_max = max([p[1] for p in landmark_points])
                padding = int((x_max - x_min) * 0.05)
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(w, x_max + padding)
                y_max = min(h, y_max + padding)

                # Draw bounding box if enabled
                if self.show_bounding_box:
                    cv2.rectangle(display_frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

                # Extract ROI for rPPG
                roi_values = self.extract_roi_values(frame, face_landmarks)
                
                if roi_values:
                    green_mean = np.mean(roi_values)
                    rppg_signal.append(green_mean)
                    time_data.append(time.time() - self.start_time)
                    logger.debug(f"rPPG signal: {green_mean:.2f}, Time: {time_data[-1]:.2f}")

                    max_signal_length = 1000
                    if len(rppg_signal) > max_signal_length:
                        rppg_signal.pop(0)
                        time_data.pop(0)

                # Draw landmarks if enabled (highlight ROI points)
                if self.show_landmarks:
                    for i, lm in enumerate(face_landmarks.landmark):
                        x, y = int(lm.x * w), int(lm.y * h)
                        if any(i in region for region in self.roi_indices.values()):
                            cv2.circle(display_frame, (x, y), 3, (0, 255, 0), -1)

            else:
                logger.debug("No face detected")

            self.change_pixmap_signal.emit(display_frame, face_detected)

        cap.release()

    def extract_roi_values(self, frame, face_landmarks):
        """Extract pixel values from regions of interest for rPPG using MediaPipe landmarks."""
        h, w, _ = frame.shape
        roi_values = []
        
        green_channel = frame[:,:,1]
        
        for region in self.roi_indices.values():
            for idx in region:
                lm = face_landmarks.landmark[idx]
                x, y = int(lm.x * w), int(lm.y * h)
                
                if 0 <= x < w and 0 <= y < h:
                    patch_start_x = max(0, x - 2)
                    patch_end_x = min(w, x + 3)
                    patch_start_y = max(0, y - 2)
                    patch_end_y = min(h, y + 3)
                    
                    patch_value = np.mean(green_channel[patch_start_y:patch_end_y, patch_start_x:patch_end_x])
                    roi_values.append(patch_value)
        
        return roi_values

    def stop(self):
        """Stop the video thread."""
        self.running = False
        self.wait()

    def toggle_landmarks(self):
        """Toggle facial landmarks display."""
        self.show_landmarks = not self.show_landmarks
        logger.info(f"Facial landmarks {'enabled' if self.show_landmarks else 'disabled'}")

    def toggle_bounding_box(self):
        """Toggle face bounding box display."""
        self.show_bounding_box = not self.show_bounding_box
        logger.info(f"Bounding box {'enabled' if self.show_bounding_box else 'disabled'}")
