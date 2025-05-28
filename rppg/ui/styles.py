# rppg/ui/styles.py

# Ini adalah placeholder, kamu punya implementasi yang lebih lengkap
class Colors:
    HR_NORMAL = "#a6e3a1"
    HR_LOW = "#fab387"
    HR_HIGH = "#f38ba8"
    # Tambahkan warna lain

def get_heart_rate_color(hr_value):
    if hr_value < 60:
        return Colors.HR_LOW
    elif hr_value > 100:
        return Colors.HR_HIGH
    return Colors.HR_NORMAL

# Kamu mungkin punya class Fonts, StyleSheets, Layout di sini
# class Fonts: ...
# class StyleSheets: ...
# class Layout: VIDEO_MIN_WIDTH = 480; VIDEO_MIN_HEIGHT = 360