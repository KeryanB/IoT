import cv2
import pytesseract
from PIL import Image
import subprocess

def extract_ine_from_card():
    try:
        subprocess.run(["rpicam-still", "-o", "carte.jpg"], check=True)

        image = Image.open("carte.jpg")
        box = (2150, 800, 3500, 1600)
        cropped = image.crop(box)
        cropped.save("image_cropped.jpg")

        img = cv2.imread("image_cropped.jpg")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5,5), 0)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        text = pytesseract.image_to_string(thresh, lang='fra')
        # Recherche INE, nom, prénom (à adapter selon format)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        ine = next((l for l in lines if l.isdigit() and len(l) >= 10), None)
        nom = lines[1] if len(lines) > 1 else None
        prenom = lines[0] if len(lines) > 0 else None

        return ine, nom, prenom
    except Exception as e:
        print("Erreur OCR :", e)
        return None, None, None
