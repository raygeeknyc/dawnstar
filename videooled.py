import time
import numpy
import cv2
import io
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)

from picamera import PiCamera

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image

RESOLUTION = (600, 400)

RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

camera = PiCamera()
camera.resolution = RESOLUTION
camera.vflip = False
image_buffer = io.BytesIO()

disp.begin()
disp.clear()
disp.display()

try:
    while True:
        image_buffer.seek(0)
        camera.capture(image_buffer, format="jpeg")
        image_buffer.seek(0)
        pil_image = Image.open(image_buffer)
        cv2_image = numpy.array(pil_image)
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2GRAY)
        (thresh, cv2_image) = cv2.threshold(cv2_image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        cv2_image = cv2.resize(cv2_image, (disp.width, disp.height))

        display_image = Image.fromarray(cv2_image).convert('1')
        disp.image(display_image)
        disp.display()
except KeyboardInterrupt:
        logging.info("interrupted, exiting")
        camera.close()
        sys.exit()
