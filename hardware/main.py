import os
import sys
import threading
import time
import lgpio

# ---------------- Django bootstrap ----------------
sys.path.append('/home/edubadge/Desktop/eduBadge')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "badgeuse.settings")

import django
django.setup()

# ---------------- Imports métier ------------------
from users.models import CustomUser
from presence.models import Presence, Cours
from hardware.ocr import extract_ine_from_card
from hardware.rfid import read_rfid_uid
from hardware.display import display        # API animée OLED
from hardware.led import led_on, led_off     # contrôle NeoPixel
from django.utils import timezone

# ---------------- GPIO ----------------------------
GPIO_TRIGGER_PIN = 18
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_TRIGGER_PIN, lgpio.SET_PULL_DOWN)

# ---------------- Fonctions -----------------------

def get_current_cours(user):
    """Retourne le cours en cours pour la classe de l’utilisateur, ou None."""
    now = timezone.now()
    return Cours.objects.filter(
        debut__lte=now,
        fin__gte=now,
        classes=user.classe
    ).first()


def rfid_loop():
    """Boucle non bloquante qui lit les badges RFID des élèves."""
    while True:
        uid = read_rfid_uid(timeout=1)
        if uid:
            user = CustomUser.objects.filter(rfid=uid).first()
            if user:
                cours = get_current_cours(user)
                if cours:
                    Presence.objects.get_or_create(
                        eleve=user,
                        cours=cours,
                        defaults={'validee_par_prof': False}
                    )
                    heure = timezone.localtime().strftime("%H:%M:%S")
                    display.success(f"{user.first_name} présent\n{heure}")
                else:
                    display.error("Pas de cours")
            else:
                display.error("Badge inconnu\nScannez badge")
        time.sleep(0.2)


def gpio_listener():
    """Déclenché par le bouton associe badge RFID à la carte d’étudiant."""
    while True:
        if lgpio.gpio_read(h, GPIO_TRIGGER_PIN) == 1:
            # ---------------- Scan OCR ----------------
            led_on((255, 255, 0))              # LED jaune = scan en cours
            display.info("OCR en cours", hold=True)
            ine = extract_ine_from_card()
            display.release()                 # libère le message « hold »
            if ine:
                user = CustomUser.objects.filter(ine=ine).first()
                if user:
                    # Demande à l’élève de badger son tag RFID
                    display.info(f"{user.first_name}, badgez", hold=True)
                    uid = read_rfid_uid(timeout=10)
                    display.release()
                    if uid:
                        user.rfid = uid
                        user.save()
                        display.success("Badge associé")
                    else:
                        display.error("Pas de badge")
                else:
                    display.error("Élève inconnu")
            else:
                display.error("OCR échoué")
            led_off()
        time.sleep(0.1)

# ---------------- Entrée programme ----------------
if __name__ == "__main__":
    try:
        display.info("Système prêt")
        threading.Thread(target=rfid_loop, daemon=True).start()
        gpio_listener()
    except KeyboardInterrupt:
        led_off()
        lgpio.gpiochip_close(h)
        print("Arrêt du système")
