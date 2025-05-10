import cv2
import pytesseract
import numpy as np
from PIL import Image
import subprocess

def extract_ine_from_card():
    try:
        # Prendre une photo avec libcamera-still et focus manuel à 3.0
        subprocess.run([
            "libcamera-still",
            "--autofocus-mode", "manual",
            "--lens-position", "30.0",
            "--timeout", "1000",  # délai pour que focus/expo se stabilisent
            "-o", "carte.jpg"
        ], check=True)

        # Recadrer la zone INE
        image = Image.open("carte.jpg")
        box = (2150, 2200, 3800, 2592)  # À adapter à ta résolution/carte
        cropped_image = image.crop(box)
        cropped_image.save("image_cropped.jpg")

        # Prétraitement
        img = cv2.imread("image_cropped.jpg")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        cv2.imwrite("image_preprocessed.jpg", thresh)

        # OCR
        text = pytesseract.image_to_string(thresh, lang='fra')
        print("[DEBUG OCR TEXT] ↓\n", text)

        # Extraction de l'INE (10 chiffres + 1 lettre majuscule)
        ine = text.replace('\r','').replace('\n','')[-11:]
        if ine:
            print("[INE détecté] →", ine)
            return ine
        else:
            print("[Aucun INE détecté]")
            return None

    except Exception as e:
        print("Erreur OCR :", e)
        return None
