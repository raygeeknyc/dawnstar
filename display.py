###############
# Module to display Dawnstar test harness info
# on a SSD1306 OLED display.
# Display:
# IP address, object detection stats, (L,R) motor state
###############
import logging
logging.getLogger('').setLevel(logging.INFO)

import time

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

_RST_PIN = 24

class DisplayInfo(object):
  def __init__(self):
    self.ip = '###.###.###.###'
    self.right_motor = 0
    self.left_motor = 0
    self.trackable_objects = 0
    self.objects = 0
    self.tracking_bounds = (1024, 1024)
    self.tracking_zone = (0, 0)
    self.frames = 0

class Display(object):
  @staticmethod
  def _setup_display():
    # 128x64 display with hardware I2C:
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=_RST_PIN)
    disp.begin()
    # Clear display.
    disp.clear()
    disp.display()
    logging.debug('/setup_display')
    return disp

  def __init__(self):
    self._info = None
    self._screen = Display._setup_display()

  def refresh(self, info):
    # refresh our info object
    self._info = info
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    width = self._screen.width
    height = self._screen.height
    image = Image.new('1', (width, height))
    logging.debug('display {} x {}'.format(width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    x = 0
    y = 0

    ## Load default font.
    font = ImageFont.load_default()
    #font = graphics.Font()
    #font.LoadFont('fonts/5x7.bdf')
    line_height = font.getsize(' ')[1]
    logging.debug('Font: {} x {}'.format(font.getsize(' ')[0], font.getsize(' ')[1]))

    draw.rectangle((0,0,width,height), outline=0, fill=0)

    draw.text((x, y), 'IP:{}'.format(str(self._info.ip)),  font=font, fill=255)
    logging.debug('IP:{}'.format(str(self._info.ip)))

    y += line_height + 1
    draw.text((x, y), 'Frame:{} Objs:{}'.format(self._info.frames, self._info.objects), font=font, fill=255)
    logging.debug('Frame: {}, Objects:{}'.format(self._info.frames, self._info.objects))

    y += line_height + 1
    bounds = ""
    if self._info.trackable_objects:
        bounds = self._info.tracking_bounds
    draw.text((x, y), 'Track: {}'.format(bounds), font=font, fill=255)
    logging.debug('Track:{}'.format(self._info.tracking_bounds))

    y += line_height + 1
    draw.text((x, y), '  Zone:{}'.format(self._info.tracking_zone), font=font, fill=255)
    logging.debug('Zone:{}'.format(self._info.tracking_zone))

    left_motor_state = 0
    right_motor_state = 0

    y += line_height + 1
    draw.text((x, y), 'Left:{} Right:{}'.format(self._info.left_motor, self._info.right_motor), font=font, fill=255)
    logging.debug('Left:{} Right:{}'.format(self._info.left_motor, self._info.right_motor))

    self._screen.image(image)
    self._screen.display()
