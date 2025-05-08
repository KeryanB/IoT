from rpi_ws281x import PixelStrip, Color

# ---------------- Paramètres ---------------------
NUM_LEDS = 20          # Total de LED sur la bande
PIN      = 12          # BCM 13 (PWM1)
BRIGHT   = 50          # 0‑255
ORDER    = Color       # WS2812 : GRB

# -------------- Initialisation -------------------
_strip = PixelStrip(NUM_LEDS, PIN, brightness=BRIGHT)
_strip.begin()

# -------------- Helpers internes ----------------

def _to_color(rgb_tuple):
    r, g, b = (int(x) & 0xFF for x in rgb_tuple)
    return ORDER(g, r, b)  # PixelStrip attend GRB si ORDER=Color GRB

# -------------- API publiques -------------------

def led_on(color=(255, 255, 0)):
    """Allume toutes les LED à la couleur RGB donnée."""
    col = _to_color(color)
    for i in range(NUM_LEDS):
        _strip.setPixelColor(i, col)
    _strip.show()


def led_off():
    """Éteint toutes les LED."""
    for i in range(NUM_LEDS):
        _strip.setPixelColor(i, 0)
    _strip.show()

# --------------- Test manuel --------------------
if __name__ == "__main__":
    import time
    try:
        led_on((0, 255, 0))  # vert
        time.sleep(1)
        led_on((255, 0, 0))  # rouge
        time.sleep(1)
    finally:
        led_off()
