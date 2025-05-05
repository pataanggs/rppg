import cv2
import mediapipe as mp
import threading
import time

class VideoThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, 30)  # Set FPS to 30
        self.running = False
        
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for close range, 1 for far range
            min_detection_confidence=0.5
        )

    def run(self):
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Print original frame shape
            print(f"Original frame shape: {frame.shape}")

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and detect faces
            results = self.face_detection.process(frame_rgb)
            
            # Draw face detections
            if results.detections:
                for detection in results.detections:
                    # Get bounding box coordinates
                    bbox = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x, y = int(bbox.xmin * iw), int(bbox.ymin * ih)
                    w, h = int(bbox.width * iw), int(bbox.height * ih)
                    
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Extract ROI (Region of Interest)
                    face_roi = frame[y:y+h, x:x+w]
                    # Print ROI shape
                    print(f"Face ROI shape: {face_roi.shape}")
            
            # Display the frame
            cv2.imshow('Face Detection', frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.stop()

    def stop(self):
        self.running = False
        self.cap.release()
        cv2.destroyAllWindows()