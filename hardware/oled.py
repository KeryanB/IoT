from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306

class OLED_Display:
    def __init__(self):
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)
        self.disp.begin()
        self.disp.clear()
        self.disp.display()

    def display_message(self, message):
        self.disp.clear()
        image = Image.new('1', (self.disp.width, self.disp.height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.text((0, 0), message, font=font, fill=255)
        self.disp.image(image)
        self.disp.display()
