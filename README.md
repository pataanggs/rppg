# rppg
This repo contains code in python for simulating rppg using webcam as an input

RPPG-PROJECT/
├── assets/                     # Untuk gambar, font, dll.
├── rppg/                      # Modul utama aplikasi (ganti nama dari `ui` dan pindahkan beberapa file)
│   ├── __init__.py
│   ├── main.py                # Entry point aplikasi PyQt
│   ├── main_window.py         # MainWindow class
│   ├── components.py          # Widget tambahan (modular UI)
│   ├── camera_selector.py     # Dialog atau logika seleksi kamera
│   ├── plot_canvas.py         # Widget untuk plotting sinyal rPPG
│   ├── styles.py              # Style sheet PyQt
│   └── threads/
│       ├── __init__.py
│       └── video_thread.py    # QThread untuk video capture + rPPG
├── signal/                    # Modul untuk pemrosesan sinyal
│   ├── __init__.py
│   └── processing.py          # rPPG signal extraction, filtering, CHROM, dll
├── core/                      # Fungsi pendukung atau non-GUI
│   ├── __init__.py
│   ├── sound.py               # Audio feedback (opsional)
│   └── utils.py               # Fungsi umum/helper
├── requirements.txt
├── readme.md
└── run.py                     # Entry point utama (opsional untuk clean separation)