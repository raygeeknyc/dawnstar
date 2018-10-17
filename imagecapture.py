import logging
# Used only if this is run as main
_DEBUG = logging.DEBUG

# Import the packages we need for drawing and displaying images
from PIL import Image, ImageDraw

from picamera import PiCamera

import multiprocessing
from multiprocessingloghandler import ChildMultiProcessingLogHandler
from random import randint
import io
import sys
import os
import time
import signal
import Queue
import threading

# This is the desired resolution of the Pi camera
RESOLUTION = (600, 400)
CAPTURE_RATE_FPS = 2
# This is over an observed covered camera's noise
TRAINING_SAMPLES = 5
# This is how much the green channel has to change to consider a pixel changed
PIXEL_SHIFT_SENSITIVITY = 30

# This is how long to sleep in various threads between shutdown checks
POLL_SECS = 0.1

def signal_handler(sig, frame):
    global STOP
    if STOP:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.debug("SIGINT")
    STOP = True
signal.signal(signal.SIGINT, signal_handler)

EMPTY_LABELS = []

class ImageProducer(multiprocessing.Process):
    def __init__(self, vision_queue, log_queue, logging_level):
        multiprocessing.Process.__init__(self)
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._exit = multiprocessing.Event()
        self._vision_queue, _ = vision_queue
        self._stop_capturing = False
        self._stop_analyzing = False
        self._last_frame_at = 0.0
        self._frame_delay_secs = 1.0/CAPTURE_RATE_FPS

    def stop(self):
        logging.debug("***analysis received shutdown")
        self._exit.set()

    def _init_logging(self):
        handler = ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._logging_level)

    def _capture_camera_frame(self):
        s=time.time()
        self._image_buffer.seek(0)
        self._camera.capture(self._image_buffer, format="jpeg", use_video_port=True)
        self._image_buffer.seek(0)
        image = Image.open(self._image_buffer)
        image_pixels = image.load()
        self._image_buffer.seek(0)
        image = self._image_buffer.getvalue()
        self._last_frame_at = time.time()
        logging.debug("_capture_camera_frame took {}".format(time.time()-s))
        return (image, image_pixels)

    def get_next_frame(self):
        delay = (self._last_frame_at + self._frame_delay_secs) - time.time()
        if delay > 0:
            time.sleep(delay)
        self._current_frame = self._capture_camera_frame()

    def calculate_image_difference(self):
        "Detect changes in the green channel."
        changed_pixels = 0
        for x in xrange(self._camera.resolution[0]):
            for y in xrange(self._camera.resolution[1]):
                if abs(self._current_frame[1][x,y][1] - self._prev_frame[1][x,y][1]) > PIXEL_SHIFT_SENSITIVITY:
                    changed_pixels += 1
        self._prev_frame = self._current_frame
        return changed_pixels

    def is_image_difference_over_threshold(self, changed_pixels_threshold):
        "Detect changes in the green channel."
        s=time.time()
        changed_pixels = 0
        for x in xrange(self._camera.resolution[0]):
            for y in xrange(self._camera.resolution[1]):
                if abs(self._current_frame[1][x,y][1] - self._prev_frame[1][x,y][1]) > PIXEL_SHIFT_SENSITIVITY:
                    changed_pixels += 1
            if changed_pixels >= changed_pixels_threshold:
                break
        self._prev_frame = self._current_frame
        logging.debug("is_image_difference_over_threshold took {}".format(time.time()-s))
        return changed_pixels >= changed_pixels_threshold

    def _train_motion(self):
        logging.debug("Training motion")
        trained = False
        try:
            self._camera.start_preview(fullscreen=False, window=(100,100,self._camera.resolution[0], self._camera.resolution[1]))
            self._motion_threshold = 9999
            self.get_next_frame()
            self._prev_frame = self._capture_camera_frame()
            for i in range(TRAINING_SAMPLES):
                self.get_next_frame()
                motion = self.calculate_image_difference()
                self._motion_threshold = min(motion, self._motion_threshold)
            trained = True
        finally:
            self._camera.stop_preview()
        logging.debug("Trained {}".format(trained))
        return trained

    def run(self):
        self._init_logging()
        self._init_camera()
        self._attempt_motion_training()
        try:
            self._stop_capturing = False
            self._capturer = threading.Thread(target=self._capture_frames)
            self._capturer.start()
            while not self._exit.is_set():
                time.sleep(POLL_SECS)
            logging.debug("Shutting down threads")
            self._stop_capturing = True
            self._capturer.join()
        except Exception, e:
            logging.exception("Error in vision main thread")
        finally:
            logging.debug("Exiting vision")
            sys.exit(0)

    def _init_camera(self):
        self._image_buffer = io.BytesIO()
        self._camera = PiCamera()
        self._camera.resolution = RESOLUTION
        self._camera.vflip = True

    def _attempt_motion_training(self):
        logging.info("Training motion detection")
        for retry in xrange(3):
            if self._train_motion():
                break
        logging.info("Trained motion detection {}".format(self._motion_threshold))
    def _capture_frames(self):
        while not self._stop_capturing:
            try:
                self.get_next_frame()
                if self.is_image_difference_over_threshold(self._motion_threshold):
                    logging.debug("Motion detected")
                    self._vision_queue.send(self._current_frame)
                    self.get_next_frame()
                    self._prev_frame = self._current_frame
            except Exception, e:
                logging.error("Error in analysis: {}".format(e))
        logging.debug("Exiting vision capture thread")
        self._cleanup()

def _cleanup(self):
    logging.debug("cleanup")
    self._camera.close()
    self._vision_queue.close()


def main():
  try:
    log_stream = sys.stderr
    log_queue = multiprocessing.Queue(100)
    handler = ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_queue)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(_DEBUG)

    image_queue = multiprocessing.Pipe()
    image_producer = ImageProducer(image_queue, log_queue, logging.getLogger('').getEffectiveLevel())
    image_producer.start()
    unused, _ = image_queue
    unused.close()
  except Exception, e:
    logging.exception("Error raised in main()")
    sys.exit(-1)

if __name__ == '__main__':
  main()
