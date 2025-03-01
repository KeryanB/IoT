import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

class BadgeReader:
    def __init__(self):
        self.reader = SimpleMFRC522()

    def read_badge(self):
        try:
            print("Scan your badge...")
            uid, text = self.reader.read()
            return uid
        finally:
            GPIO.cleanup()
