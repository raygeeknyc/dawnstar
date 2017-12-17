import time
import io
import sys
import logging
logging.getLogger().setLevel(logging.INFO)
import numpy
import cv2

from picamera import PiCamera

import Adafruit_SSD1306

from PIL import Image

RESOLUTION = (160, 100)
CAMERA_ERROR_DELAY_SECS = 1

RST=24
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

camera = PiCamera()
camera.resolution = RESOLUTION
camera.vflip = True  # Our camera is not flipped but our display is
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
        display_image = Image.open(image_buffer)
        cv2_image = numpy.array(display_image)
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2GRAY)
        cv2_image = cv2.equalizeHist(cv2_image)
        #(thresh, cv2_image) = cv2.threshold(cv2_image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # too high contrast
        cv2_image = cv2.resize(cv2_image, (disp.width, disp.height))
        display_image = Image.fromarray(cv2_image).convert('1')
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
