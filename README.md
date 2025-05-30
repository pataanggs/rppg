# RPPG Heart Rate Monitor and Respiration Rate Monitor

<div align="center">
  <img src="rppg/assets/banner-rppg.png" alt="RPPG Heart Rate Monitor Banner" width="1920">
</div>

<div align="justify">
This repository contains Python code for a remote photoplethysmography (rPPG) heart rate and respiration rate monitor that uses a standard webcam to measure heart rate in real-time.
</div>

## 📋 Description
<div align="justify">
The **rPPG Heart Rate Monitor** is an innovative, non-invasive application that leverages remote photoplethysmography (rPPG) to estimate heart rate and respiration rate using a regular camera. By analyzing subtle color changes in facial skin caused by blood flow, and the movement of your shoulders for respiration, the system provides contactless heart rate and respiration rate monitoring without requiring specialized hardware.
</div>

### Key Features

- 💓 **Real-Time Heart Rate Monitoring**: Displays heart rate with live visual feedback.
- 📊 **Dynamic Signal Visualization**: Modern UI with real-time signal plotting.
- 📈 **Historical Data Tracking**: Stores and analyzes heart rate data over time.
- 📱 **User-Friendly Interface**: Intuitive design with dark mode support.
- 🔍 **Advanced Signal Processing**: Robust algorithms for accurate heart rate estimation.
- 💾 **Data Export**: Save heart rate data for further analysis.

## 📁 Project Structure

```plaintext
rppg-project/
├── .gitignore
├── README.md
├── requirements.txt
├── run.py 
├── LICENSE             # Main entry point
├── rppg/
│   ├── __init__.py
│   ├── main.py        # Application initialization
│   ├── assets/        # Static assets (e.g., audio files)
│   │   └── alarm.wav
│   ├── core/          # Core functionality
│   │   ├── __init__.py
│   │   ├── sound.py
│   │   └── utils.py
│   ├── signal/        # Signal processing modules
│   │   ├── __init__.py
│   │   ├── signal_processing.py
│   │   └── signal_processor.py
│   ├── threads/       # Thread management
│   │   ├── __init__.py
│   │   └── rppg_threads.py
│   ├── ui/            # User interface components
│   │   ├── __init__.py
│   │   ├── camera_selector.py
│   │   ├── components.py
│   │   ├── main_window.py
│   │   ├── plot_canvas.py
│   │   ├── settings_dialog.py
│   │   └── styles.py
│   └── utils/         # Utility functions
```

## 👥 Team Members

| Full Name             | Student ID | GitHub Profile                                   |
|-----------------------|------------|--------------------------------------------------|
| Fathan Andi Kartagama | 122140055  | [@pataanggs](https://github.com/pataanggs)       |
| Rahmat Aldi Nasda     | 122140077  | [@urbaee](https://github.com/urbaee)             |
| Chandra Budi Wijaya   | 122140093  | [@ChandraBudiWijaya](https://github.com/ChandraBudiWijaya) |

## 📝 Weekly Logbook

| Week | Date            | Activities                                                                 | Progress |
|------|-----------------|---------------------------------------------------------------------------|----------|
| 1    | May 3, 2024     | Initialized project, set up folder structure, and created repository.      | 20% - Basic structure and environment established. |
| 2    | May 5, 2024     | Implemented face detection (MediaPipe), camera selection, rPPG estimation, UI with heart rate graph, alarm with mute, and settings panel. | 60% - Core functionality and UI completed. |
| 3    | May 17, 2025    | Refactored code, updated README, added signal processing module, plot canvas, utils module, camera selector, and improved maintainability. | 80% - Enhanced code organization and visualization. |
| 4    | May 25, 2025    | Drafted initial report and removed redundant files.                       | 85% - Report initiated, minor maintenance completed. |
| 5    | May 28–29, 2025 | Refactored code, fixed issues, optimized box and sound functions, added respiration plot, improved export, and implemented bandpass filtering. | 95% - Major performance and feature enhancements. |
| 6    | May 30, 2025    | Finalized project and completed report in Overleaf.                       | 100% - Project and documentation completed. |

## 💻 Installation

### Prerequisites

- **Python**: Version 3.8 or higher
- **Webcam**: Integrated or external camera
- **Operating System**: Windows, macOS, or Linux

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/pataanggs/rppg.git
   cd rppg
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   For a more efficient setup, we recommend using the `uv` virtual environment tool:
   ```bash
   uv pip install -r requirements.txt
   ```
   Don't have `uv` installed? Follow the [Installation | uv](https://docs.astral.sh/uv/getting-started/installation/)

3. **Run the Application**:
   ```bash
   python run.py
   ```

## 🚀 Usage

1. Launch the application using `python run.py`.
2. Select a webcam from the camera selector interface.
3. Ensure your face is well-lit and visible to the camera.
4. The application will display real-time heart rate, respiration rate data and visualizations.
5. Use the settings dialog to adjust signal processing parameters or enable/disable features like alarms.
6. Export heart rate data for further analysis using the export functionality.

## 📜 License

This project is licensed under the [MIT License](LICENSE).

## 🙌 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) for face detection capabilities.
- The open-source community for providing valuable libraries and tools.

---
