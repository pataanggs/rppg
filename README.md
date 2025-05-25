# rPPG Heart Rate Monitor

<div align="center">
  <img src="https://i.pinimg.com/474x/01/a1/31/01a131f0c5749c9daf0a45fcc7572c2e.jpg" alt="Logo sementara aja" width="120">
  <h3>Non-invasive Heart Rate Monitoring Using Regular Camera</h3>
</div>

This repo contains code in Python for simulating rPPG using a webcam as an input.

## 📋 Description

rPPG Heart Rate Monitor is an innovative application that uses remote photoplethysmography (rPPG) to measure heart rate in real-time using only a standard camera. The system analyzes subtle color changes in facial skin that occur with each heartbeat, allowing for contactless heart rate monitoring without specialized equipment.

### Key Features

- 💓 Real-time heart rate monitoring with visual feedback
- 📊 Dynamic signal visualization with modern UI
- 📈 Historical heart rate data tracking and analysis
- 📱 User-friendly interface with dark mode support
- 🔍 Advanced signal processing algorithms
- 💾 Data export functionality for further analysis

## 📁 Project Structure

```plaintext
RPPG-PROJECT/
├── assets/               # For images, fonts, etc.
├── rppg/                 # Main application module (UI, threads, etc.)
│   ├── __init__.py
│   ├── main.py           # Entry point for the PyQt application
│   ├── main_window.py    # MainWindow class definition
│   ├── components.py     # Additional UI widgets (modular UI)
│   ├── camera_selector.py# Dialog or logic for camera selection
│   ├── plot_canvas.py    # Widget for plotting rPPG signals
│   ├── styles.py         # PyQt style sheets
│   └── threads/
│       ├── __init__.py
│       └── video_thread.py # QThread for video capture + rPPG processing
├── signal/               # Module for signal processing
│   ├── __init__.py
│   └── processing.py     # rPPG signal extraction, filtering, CHROM, etc.
├── core/                 # Supporting functions or non-GUI logic
│   ├── __init__.py
│   ├── sound.py          # Audio feedback (optional)
│   └── utils.py          # General utility/helper functions
├── requirements.txt      # Python dependencies
├── readme.md             # Project documentation
└── run.py                # Main entry point (optional)
```


## 👥 Team Members

| Full Name           | Student ID (NIM) | GitHub ID         |
|---------------------|------------------|-------------------|
| FATHAN ANDI KARTAGAMA | 122140055        | [@pataanggs](https://github.com/pataanggs)     |
| RAHMAT ALDI NASDA   | 122140077        | [@urbaee](https://github.com/urbaee)         |
| CHANDRA BUDI WIJAYA | 122140093        | [@ChandraBudiWijaya](https://github.com/ChandraBudiWijaya) |

## 📝 Weekly Logbook

| Week | Date        | Activities                                                                                                                                                                                                                                                                                                                                | Progress                                                              |
|------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| 1    | May 3, 2024 | - Project initialization<br>- Basic folder structure setup<br>- Initial repository setup                                                                                                                                                                                                                                                  | 20% - Basic project structure and environment setup completed         |
| 2    | May 5, 2024 | - Implemented face detection using MediaPipe<br>- Added camera selection<br>- Implemented rPPG heart rate estimation<br>- Created UI with heart rate graph<br>- Added alarm with mute functionality<br>- Implemented face detection feedback<br>- Added settings for signal processing and display                                     | 60% - Core functionality implemented including face detection, heart rate monitoring and UI features |
| 3    | May 17, 2025 | - Extensive code refactoring for better organization<br>- Updated README documentation with detailed sections<br>- Added signal processing module for improved accuracy<br>- Implemented plot canvas for real-time visualization<br>- Created utils module for shared functionality<br>- Added camera selector interface<br>- Improved code structure and maintainability | 80% - Major refactoring completed with enhanced visualization, documentation and code organization |

## 💻 Installation

### Prerequisites
- Python 3.8+
- Webcam or integrated camera
- Windows, macOS, or Linux operating system

### Setup
1. Clone this repository:
   ```bash
   git clone [https://github.com/yourusername/rppg-heart-rate-monitor.git](https://github.com/yourusername/rppg-heart-rate-monitor.git)
   cd rppg-heart-rate-monitor