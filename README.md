# 🎓 EduBadge – Attendance System with RFID & OCR

EduBadge is an embedded and web-based attendance system built using Django, RFID scanning, OCR, and GPIO control on Raspberry Pi. It allows students to mark attendance using RFID badges, and associates them with their identity cards via image recognition.

## 🚀 Features

### 🔐 Authentication & User Roles
- Custom user model with roles: `admin`, `prof`, `secretaire`, `eleve`
- Role-based access to views and dashboards
- Profile management and password update

### 🖥️ Web Interface (Django)
- Separate dashboards for students, teachers, secretaries, and admins
- Real-time attendance list and validation
- Export attendance reports to PDF
- Class management and calendar integration via iCal

### 📸 Raspberry Pi Hardware Integration
- GPIO-triggered camera capture for OCR on student cards
- Continuous RFID badge detection
- OLED display feedback
- Neopixel LED feedback for scan result

### 📷 OCR Recognition
- Automatic image preprocessing (contrast, threshold, cropping)
- Text extraction using Tesseract OCR
- INE code parsing and database matching

### 📡 RFID Integration
- MFRC522 module support
- Live badge scanning and UID extraction
- User association with RFID badge

## 🧰 Tech Stack

| Component       | Tech Used                          |
|----------------|------------------------------------|
| Backend        | Django 4.x                         |
| Frontend       | Bootstrap 5, HTML, JS              |
| OCR            | OpenCV, Tesseract                  |
| RFID           | mfrc522 + SPI                      |
| Display        | OLED 0.96" 128x64 (SSD1306)        |
| Hardware       | Raspberry Pi (tested on 3B+)       |

## 📂 Project Structure

```bash
├── badgeuse/            # Django main project
├── users/               # CustomUser model + admin
├── cours/               # Courses & iCal import
├── presence/            # Attendance model
├── hardware/            # GPIO, RFID, OCR scripts
├── templates/           # Web UI
├── static/              # CSS / images / JS
├── crontab/             # Crontab files
└── manage.py
````

## 🛠️ Setup Instructions

### 🐍 Python & Django

```bash
git clone https://github.com/KeryanB/eduBadge.git
cd edubadge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 🧪 Raspberry Pi (OCR + RFID)

* Enable SPI and I2C from `raspi-config`
* Place hardware scripts in `/home/pi/edubadge/hardware/`
* Run main loop:

```bash
python3 hardware/main.py
```

### 📅 iCal Course Import

Import daily lessons from EDT or Moodle calendars:

```bash
python manage.py import_courses
```

### 🕒 Crontab Setup (Automatic Launch & Course Import)
To ensure that all key services run automatically without manual intervention, EduBadge uses two crontab files:

One for launching Django and background tasks (as a regular user)

One for hardware interactions (as root)

These crontabs allow:

✅ Automatic system launch at boot

✅ Automatic iCal course import every day at 7:00 AM

✅ Seamless background operation of RFID + OCR on Raspberry Pi


### 📁 Crontab Files

```bash
crontab/
├── crontab_user.txt   # Tasks run by the current user (e.g., pi)
└── crontab_sudo.txt   # Tasks run with root privileges (e.g., GPIO, LED)
```

### 🔧 1. User Crontab (`crontab_user.txt`)

This file should be installed with the standard user crontab (e.g., `edubadge`). It typically starts the Django server.

To install it:

```bash
crontab crontab/crontab_user.txt
```

### 🔐 2. Root Crontab (`crontab_sudo.txt`)

This file is used for commands that require `sudo`, such as direct GPIO control.

To install it:

```bash
sudo crontab crontab/crontab_sudo.txt
```

## 📸 Example

[![Video Demo](https://img.youtube.com/vi/7I3YGaCoWns/0.jpg)](https://youtu.be/7I3YGaCoWns)


## 📃 License

This project is licensed under License – see the [LICENSE](LICENSE) file for details.

## ✨ Credits

Developed by Keryan Belahcene and Thomas Consiglio
INSA Strasbourg — 2025

