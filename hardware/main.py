import os
import sys
import threading
import time
from datetime import timedelta
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
from hardware.led import led_on, led_off # contrôle NeoPixel (WS281x)
from django.utils import timezone

# ---------------- Fenêtres temporelles -----------
EARLY_ALLOWED   = timedelta(minutes=15)  # on peut badger 15 min avant le début
LATE_CUTOFF     = timedelta(minutes=15)  # plus possible 15 min avant la fin
PROF_CONFIRM_S  = 5                     # prof a 10 s pour rebadger et valider

# ---------------- GPIO ----------------------------
GPIO_TRIGGER_PIN = 18
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_TRIGGER_PIN, lgpio.SET_PULL_DOWN)

# ---------------- Helpers cours -------------------

def _now():
    return timezone.now()


def badge_window_open(cours):
    now = _now()
    return cours.debut - EARLY_ALLOWED <= now < cours.fin - LATE_CUTOFF


def cours_for_eleve(user):
    now = _now()
    return Cours.objects.filter(debut__lte=now + EARLY_ALLOWED, fin__gte=now, classes=user.classe).first()


def cours_for_prof(prof):
    now = _now()
    return Cours.objects.filter(debut__lte=now, fin__gte=now, professeur=prof).first()


# ---------------- Prof validation state -----------
_last_prof_badge = {  # uid -> (timestamp, cours_id)
}

# ---------------- Boucle RFID ---------------------

def rfid_loop():
    while True:
        uid = read_rfid_uid(timeout=1)
        if not uid:
            time.sleep(0.1)
            continue

        user = CustomUser.objects.filter(rfid=uid).first()
        if not user:
            display.error("Badge inconnu\nScannez badge")
            continue

        # ----- Élève -----
        if user.role == 'eleve':
            cours = cours_for_eleve(user)
            if not cours or not badge_window_open(cours):
                display.error("Hors créneau")
                continue

            Presence.objects.get_or_create(
                eleve=user,
                cours=cours,
                defaults={'validee_par_prof': False}
            )
            heure = timezone.localtime().strftime("%H:%M:%S")
            display.success(f"{user.first_name} présent\n{heure}")
            continue

        # ----- Professeur -----
        if user.role == 'prof':
            cours = cours_for_prof(user)
            if not cours:
                display.error("Aucun cours")
                continue
            key = uid
            ts_now = time.time()
            if key in _last_prof_badge and ts_now - _last_prof_badge[key][0] <= PROF_CONFIRM_S and _last_prof_badge[key][1] == cours.id:
                # confirmé : valider toutes les présences
                Presence.objects.filter(cours=cours).update(validee_par_prof=True)
                display.release()
                display.success("Présences\nvalidées")
                del _last_prof_badge[key]
            else:
                # premier badge : montrer stats
                nb_total = CustomUser.objects.filter(role='eleve', classe__in=cours.classes.all()).count()
                nb_present = Presence.objects.filter(cours=cours).count()
                display.info(f"Présents {nb_present}/{nb_total}\nRebadgez pour OK", hold=True)
                _last_prof_badge[key] = (ts_now, cours.id)
                # auto‑release après délai dans thread
                threading.Timer(PROF_CONFIRM_S, lambda: (_last_prof_badge.pop(key, None), display.release())).start()
            continue

        # Autres rôles
        display.error("Rôle non géré")

        time.sleep(0.1)

# ---------------- Listener bouton OCR -------------

def gpio_listener():
    while True:
        if lgpio.gpio_read(h, GPIO_TRIGGER_PIN):
            led_on((255, 255, 0))
            display.info("OCR en cours", hold=True)
            ine = extract_ine_from_card()
            display.release()
            if ine:
                user = CustomUser.objects.filter(ine=ine).first()
                if user:
                    display.info(f"{user.first_name}, badgez", hold=True)
                    uid = read_rfid_uid(timeout=10)
                    display.release()
                    if uid:
                        user.rfid = uid; user.save()
                        display.success("Badge associé")
                        time.sleep(3)
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
        led_off(); lgpio.gpiochip_close(h); display.stop()
        print("Arrêt du système")
