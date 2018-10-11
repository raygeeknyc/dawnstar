###############
#
# Module to display Dawnstar test harness info
# on a SSD1306 OLED display.
# Display:
# IP address, object detection stats, motor state
#
###############
import logging
logging.getLogger('').setLevel(logging.DEBUG)

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
  logging.debug('/setup_display')
  return disp

class DisplayInfo(object):
  def __init__():
    self.ip = "###.###.###.###"
    self.right_motor = 0
    self.left_motor = 0
    self.faces = 0
    self.tracking_bounds = (0, 0)
    self.tracking_zone = (0, 0)

def update_display(display, display_info):
  # Create blank image for drawing.
  # Make sure to create image with mode '1' for 1-bit color.
  width = disp.width
  height = disp.height
  image = Image.new('1', (width, height))
  logging.debug('display {} x {}'.format(width, height))

  # Get drawing object to draw on image.
  draw = ImageDraw.Draw(image)

  # Draw a black filled box to clear the image.
  draw.rectangle((0,0,width,height), outline=0, fill=0)

  x = 0
  y = 0

  ## Load default font.
  # font = ImageFont.load_default()
  font = graphics.Font()
  font.LoadFont('fonts/5x7.bdf')
  line_height = font.getsize()[1]
  logging.debug('Font: {} x {}'.format(font.getSize()[0], font.getSize()[1]))

  draw.rectangle((0,0,width,height), outline=0, fill=0)

  draw.text((x, y), 'IP: ' + display_info.ip,  font=font, fill=255)
  logging.debug('IP: {}'.format(str(display_info.ip)))

  faces = 0

  y += font_height + 1
  draw.text((x, y), 'Faces: {}'.format(display_info.faces), font=font, fill=255)
  logging.debug('Faces: {}'.format(display_info.faces))

  face_bounds = (0,0)
  face_zone = (0,0)

  y += font_height + 1
  draw.text((x, y), 'Tracking: {},{}  Zone: {}'.format(display_info.tracking_bounds, display_info.tracking_zone), font=font, fill=255)
  logging.debug('Faces: {}'.format(display_info.tracking_bounds, display_info.tracking_zone))

  left_motor_state = 0
  right_motor_state = 0

  y += font_height + 1
  y += font_height + 1
  draw.text((x, y), 'Left motor: {}, Right motor: {}'.format(display_info.left_motor, display_info.right_motor), font=font, fill=255)
  logging.debug('Left motor: {}, Right motor: {}: {}'.format(display_info.left_motor, display_info.right_motor))

  disp.image(image)
  disp.display()

def main():
  blank_info = DisplayInfo()
  display = setup_display()
  update_display(display, display_info)


if __name__ == "__main__":
  logging.info('display running as main')
  main()
