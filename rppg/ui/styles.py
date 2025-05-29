# rppg/ui/styles.py

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