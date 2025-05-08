from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

def display_message(message, duration=3):
    with canvas(device) as draw:
        draw.text((5, 25), message, fill="white")
    device.show()
    time.sleep(duration)
    device.clear()
