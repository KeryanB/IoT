import os
import django
import threading
import time
import RPi.GPIO as GPIO

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ton_projet.settings")  # adapte ce nom
django.setup()

from users.models import CustomUser
from presence.models import Presence, Cours
from hardware.ocr import extract_ine_from_card
from hardware.rfid import read_rfid_uid
from hardware.display import display_message
from django.utils import timezone

# GPIO
GPIO.setmode(GPIO.BCM)
GPIO_TRIGGER_PIN = 18
GPIO.setup(GPIO_TRIGGER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def rfid_loop():
    while True:
        uid = read_rfid_uid(timeout=1)
        if uid:
            user = CustomUser.objects.filter(rfid=uid).first()
            if user:
                cours = get_current_cours(user)
                if cours:
                    Presence.objects.get_or_create(eleve=user, cours=cours, defaults={
                        'validee_par_prof': False
                    })
                    display_message(f"{user.first_name} présent")
                else:
                    display_message("Pas de cours")
            else:
                display_message("Badge inconnu, scannez carte")
                ine, nom, prenom = extract_ine_from_card()
                if ine:
                    user = CustomUser.objects.filter(ine=ine).first()
                    if user:
                        user.rfid = uid
                        user.save()
                        display_message(f"{user.first_name} lié au badge")
                        cours = get_current_cours(user)
                        if cours:
                            Presence.objects.get_or_create(eleve=user, cours=cours, defaults={
                                'validee_par_prof': False
                            })
                    else:
                        display_message("INE inconnu")
                else:
                    display_message("Échec OCR")
        time.sleep(0.2)

# Déclencheur OCR si carte insérée (GPIO)
def gpio_listener():
    while True:
        if GPIO.input(GPIO_TRIGGER_PIN) == GPIO.HIGH:
            display_message("Scan carte en cours...")
            ine, nom, prenom = extract_ine_from_card()
            if ine:
                user = CustomUser.objects.filter(ine=ine).first()
                if user:
                    display_message(f"{prenom}, badgez")
                    uid = read_rfid_uid(timeout=10)
                    if uid:
                        user.rfid = uid
                        user.save()
                        display_message("Badge associé")
                    else:
                        display_message("Pas de badge")
                else:
                    display_message("Élève inconnu")
            else:
                display_message("OCR échoué")
            # Anti-rebond
            time.sleep(3)
        time.sleep(0.1)

# Obtenir le cours actuel de l’élève
def get_current_cours(user):
    now = timezone.now()
    return Cours.objects.filter(
        debut__lte=now,
        fin__gte=now,
        classe=user.classe
    ).first()

# Lancement
if __name__ == "__main__":
    try:
        display_message("Système prêt")
        threading.Thread(target=rfid_loop, daemon=True).start()
        gpio_listener()  # Bloquant
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Arrêt du système")
