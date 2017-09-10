import time
import io
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.INFO)

from picamera import PiCamera

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image

RESOLUTION = (160, 100)
CAMERA_ERROR_DELAY_SECS = 1
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
    frame_count = 0
    fps = 0
    last_report_at = time.time()
    last_start = time.time()
    s = time.time()
    for _ in camera.capture_continuous(image_buffer, format='jpeg', use_video_port=True):
        try:
            image_buffer.truncate()
            image_buffer.seek(0)
            logging.debug("Camera capture took {}".format(time.time()-s))
            s = time.time()
        except Exception, e:
            logging.exception("Error capturing image")
            time.sleep(CAMERA_ERROR_DELAY_SECS)
            continue
        display_image = Image.open(image_buffer).resize((disp.width, disp.height), Image.ANTIALIAS).convert('1')
        image_buffer.seek(0)
        logging.debug("Image processing took {}".format(time.time()-s))
        s = time.time()
        disp.image(display_image)
        disp.display()
        logging.debug("Display took {}".format(time.time()-s))
        frame_frequency = time.time() - last_start
        last_start = time.time()
        frame_rate = 1/frame_frequency
        fps += frame_rate
        frame_count += 1
        if last_start - last_report_at >= 1.0:
            fps /= frame_count
            frame_count = 0
            logging.info("frame rate: {} fps".format(fps))
            fps = 0
            last_report_at = last_start 
        s = time.time()
except KeyboardInterrupt:
        logging.info("interrupted, exiting")
        camera.close()
        sys.exit()
