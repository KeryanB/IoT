import time
import threading
from queue import Queue, Empty
from datetime import datetime
from textwrap import wrap

import lgpio  # pour le buzzer
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont

# -------------- Buzzer (lgpio) -------------------
BUZZ_PIN = 21          # BCM 24 (phys 18)
CHIP     = 0
_handle  = lgpio.gpiochip_open(CHIP)
lgpio.gpio_claim_output(_handle, BUZZ_PIN, 0)  # 1 = silence (actif LOW)

BEEP_SHORT = 0.2  # 100 ms
BEEP_LONG  = 1  # 500 ms


def _pulse(duration: float):
    lgpio.gpio_write(_handle, BUZZ_PIN, 1)  # actif LOW
    time.sleep(duration)
    lgpio.gpio_write(_handle, BUZZ_PIN, 0)


def _buzz(kind: str):
    if kind == "success":
        for _ in range(2):
            _pulse(BEEP_SHORT)
            time.sleep(0.05)
    elif kind == "error":
        _pulse(BEEP_LONG)

# -------------- Afficheur OLED ------------------
I2C_PORT = 1
I2C_ADDR = 0x3C
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

FONT_MED = ImageFont.truetype(FONT_PATH, 14)
FONT_BIG = ImageFont.truetype(FONT_PATH, 28)

serial = i2c(port=I2C_PORT, address=I2C_ADDR)
device = sh1106(serial)

SYMBOL_SIZE, SYMBOL_TOP, TEXT_GAP = 24, 4, 2

# ---------- Helpers -----------------------------

def _txt(draw, txt, font):
    if hasattr(draw, "textbbox"):
        l, t, r, b = draw.textbbox((0, 0), txt, font=font)
        return r - l, b - t
    return draw.textsize(txt, font=font)

# ---------- Icônes ------------------------------

def _check(frame):
    x0 = (device.width - SYMBOL_SIZE)//2; y0 = SYMBOL_TOP
    mx = x0 + SYMBOL_SIZE//3; my = y0 + SYMBOL_SIZE*3//4; xe = x0 + SYMBOL_SIZE
    s1 = ((x0, my, mx, y0+SYMBOL_SIZE),)
    return [s1] if frame == 0 else [s1 + ((mx, y0+SYMBOL_SIZE, xe, y0),)]

def _cross(frame):
    x0 = (device.width - SYMBOL_SIZE)//2; y0 = SYMBOL_TOP; x1 = x0 + SYMBOL_SIZE; y1 = y0 + SYMBOL_SIZE
    s1 = ((x0, y0, x1, y1),)
    return [s1] if frame == 0 else [s1 + ((x1, y0, x0, y1),)]

def _loader(frame):
    y = SYMBOL_TOP + SYMBOL_SIZE//2; tail = SYMBOL_SIZE - 8
    x = 4 + (frame % (device.width - (tail + 8))); xe = x + tail
    return [((x, y, xe, y), (xe, y, xe - 6, y - 6), (xe, y, xe - 6, y + 6))]

SYMBOLS = {"success": _check, "error": _cross, "loader": _loader}

# ---------- Display thread -----------------------
class _Display(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q; self.cur = None; self.until = 0; self.stop_ev = threading.Event()
    def _clock(self):
        with canvas(device) as d:
            hhmm = datetime.now().strftime("%H:%M"); tw, th = _txt(d, hhmm, FONT_BIG)
            d.text(((device.width - tw)//2, (device.height - th)//2), hhmm, font=FONT_BIG, fill="white")
    def _msg(self, item, f):
        k, m = item["kind"], item["msg"]
        with canvas(device) as d:
            for segs in SYMBOLS.get(k, lambda _: [])(f):
                for s in segs:
                    d.line(s, fill="white", width=2)
            if m:
                lines = [l for p in m.split("\n") for l in wrap(p, device.width//6 or 1)]
                y = SYMBOL_TOP + SYMBOL_SIZE + TEXT_GAP
                for l in lines:
                    tw, th = _txt(d, l, FONT_MED)
                    d.text(((device.width - tw)//2, y), l, font=FONT_MED, fill="white"); y += th
    def run(self):
        f = 0
        while not self.stop_ev.is_set():
            now = time.time()
            if self.cur and now >= self.until:
                self.cur = None
            if self.cur is None:
                try:
                    self.cur = self.q.get_nowait(); self.until = now + self.cur["duration"]
                except Empty:
                    pass
            if self.cur:
                self._msg(self.cur, f)
            else:
                self._clock()
            f = (f + 1) % 60; time.sleep(0.05)
    def stop(self):
        self.stop_ev.set()

_queue = Queue(); _disp = _Display(_queue); _disp.start()

# ---------- API ---------------------------------

def _put(msg, kind, dur):
    _queue.put({"msg": msg, "kind": kind, "duration": dur})


def success(msg, duration=3):
    _put(msg, "success", duration)
    threading.Thread(target=_buzz, args=("success",), daemon=True).start()


def error(msg, duration=3):
    _put(msg, "error", duration)
    threading.Thread(target=_buzz, args=("error",), daemon=True).start()


def info(msg, duration=3, hold=False):
    _put(msg, "loader" if hold else "info", 9999 if hold else duration)


def release():
    _disp.until = 0  # libère le message hold


def stop():
    _disp.stop()
    lgpio.gpio_write(_handle, BUZZ_PIN, 1)
    lgpio.gpiochip_close(_handle)

class _Facade: pass
for _fn in (success, error, info, release, stop):
    setattr(_Facade, _fn.__name__, staticmethod(_fn))

display = _Facade()

# Compatibilité ancienne API

def display_message(msg, duration=3):
    info(msg, duration)
