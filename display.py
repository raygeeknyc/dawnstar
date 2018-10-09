#
###############
# Module to display Dawnstar test harness info
# on a SSD1306 OLED display.
# IP address, object detection stats, motor state
#
###############
import time
import subprocess

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

_RST_PIN = 24

def setup_display():
  # 128x64 display with hardware I2C:
  disp = Adafruit_SSD1306.SSD1306_128_64(rst=_RST_PIN)
  disp.begin()
  # Clear display.
  disp.clear()
  disp.display()

def update_display(display):
  # Create blank image for drawing.
  # Make sure to create image with mode '1' for 1-bit color.
  width = disp.width
  height = disp.height
  image = Image.new('1', (width, height))

  # Get drawing object to draw on image.
  draw = ImageDraw.Draw(image)

  # Draw a black filled box to clear the image.
  draw.rectangle((0,0,width,height), outline=0, fill=0)

  x = 0
  y = 0

  ## Load default font.
  # font = ImageFont.load_default()
  font = graphics.Font()
  font.LoadFont("fonts/5x7.bdf")
  line_height = font.getsize()[1]

  draw.rectangle((0,0,width,height), outline=0, fill=0)

  cmd = "hostname -I | cut -d\' \' -f1"
  IP = subprocess.check_output(cmd, shell = True )
  draw.text((x, y), "IP: " + str(IP),  font=font, fill=255)

  y += font_height + 1
  draw.text((x, y), "Faces: {}".format(0), font=font, fill=255)

  y += font_height + 1
  draw.text((x, y), "Largest face: {},{}  Zone: {}".format(0,0,(0,0)), font=font, fill=255)

  y += font_height + 1
  y += font_height + 1
  draw.text((x, y), "Left motor: {}, Right motor: {}  Zone: {}".format(0,0), font=font, fill=255)

  # Display image.
  disp.image(image)
  disp.display()
