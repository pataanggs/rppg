# rPPG Heart Rate Monitor

<div align="center">
  <img src="https://i.pinimg.com/474x/01/a1/31/01a131f0c5749c9daf0a45fcc7572c2e.jpg" alt="Logo sementara aja" width="120">
  <h3>Non-invasive Heart Rate Monitoring Using Regular Camera</h3>
</div>

## 📋 Description

rPPG Heart Rate Monitor is an innovative application that uses remote photoplethysmography (rPPG) to measure heart rate in real-time using only a standard camera. The system analyzes subtle color changes in facial skin that occur with each heartbeat, allowing for contactless heart rate monitoring without specialized equipment.

### Key Features

- 💓 Real-time heart rate monitoring with visual feedback
- 📊 Dynamic signal visualization with modern UI
- 📈 Historical heart rate data tracking and analysis
- 📱 User-friendly interface with dark mode support
- 🔍 Advanced signal processing algorithms
- 💾 Data export functionality for further analysis

## 👥 Team Members

| Full Name | Student ID (NIM) | GitHub ID |
|-----------|------------------|-----------|
| FATHAN ANDI KARTAGAMA | 122140055 | @pataanggs |
| RAHMAT ALDI NASDA | 122140077 | @urbaee |
| CHANDRA BUDI WIJAYA | 122140093 | @ChandraBudiWijaya |

## 📝 Weekly Logbook

| Week | Date | Activities | Progress |
|------|------|------------|----------|
| 1 | May 3, 2024 | - Project initialization<br>- Basic folder structure setup<br>- Initial repository setup | 20% - Basic project structure and environment setup completed |
| 2 | May 5, 2024 | - Implemented face detection using MediaPipe<br>- Added camera selection<br>- Implemented rPPG heart rate estimation<br>- Created UI with heart rate graph<br>- Added alarm with mute functionality<br>- Implemented face detection feedback<br>- Added settings for signal processing and display | 60% - Core functionality implemented including face detection, heart rate monitoring and UI features |
| 3 | May 17, 2025 | - Extensive code refactoring for better organization<br>- Updated README documentation with detailed sections<br>- Added signal processing module for improved accuracy<br>- Implemented plot canvas for real-time visualization<br>- Created utils module for shared functionality<br>- Added camera selector interface<br>- Improved code structure and maintainability | 80% - Major refactoring completed with enhanced visualization, documentation and code organization |

## 💻 Installation

### Prerequisites
- Python 3.8+
- Webcam or integrated camera
- Windows, macOS, or Linux operating system

### Setup
1. Clone this repository:
   ```
   git clone https://github.com/yourusername/rppg-heart-rate-monitor.git
   cd rppg-heart-rate-monitor
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. Run the application:
   ```
   python main.py
   ```

2. Select a camera when prompted
3. Position your face in the center of the frame
4. Wait for face detection and heart rate calculation to start
5. The application will display your heart rate and signal quality in real-time
6. Use the "Start Recording" button to record heart rate data
7. Use "Export Data" to save recorded data to CSV format

## 📊 Performance Tips
- Ensure good and consistent lighting on your face
- Avoid excessive movement during measurement
- Keep a stable distance from the camera
- Use a higher quality webcam for better results
- If experiencing lag, adjust settings to lower resolution

## 🔍 Technical Architecture

The application follows a clean architecture with the following components:

- **Core Components**
  - `signal_processor.py`: Heart rate estimation algorithms
  - `signal_processing.py`: Basic signal processing utilities
  
- **UI Components**
  - `ui/main_window.py`: Main application window
  - `ui/components.py`: Reusable UI widgets
  - `ui/settings_dialog.py`: User settings interface
  - `ui/styles.py`: UI styling definitions
  
- **Background Processing**
  - `threads/video_thread.py`: Camera capture and processing in a separate thread
  
- **Utilities**
  - `utils.py`: General utility functions
  - `sound.py`: Audio feedback handling
  - `plot_canvas.py`: Signal visualization utilities
  - `camera_selector.py`: Camera detection and selection dialog

## 📄 License
[MIT License](LICENSE)

## 🙏 Acknowledgments
- This project uses OpenCV for image processing
- Face detection powered by MediaPipe
- UI built with PyQt6
