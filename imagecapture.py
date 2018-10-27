_Pi = False
_Pi = True

import logging
# Used only if this is run as main
_DEBUG = logging.INFO

# Import the packages we need for drawing and displaying images
from PIL import Image, ImageDraw

import multiprocessing
from multiprocessingloghandler import ChildMultiProcessingLogHandler, ParentMultiProcessingLogHandler
from random import randint
import io
import sys
import os
import time
import signal
import Queue
import threading

# This is the desired resolution of the camera
RESOLUTION = (320, 240)
# This is the desired maximum frame capture rate of the camera
CAPTURE_RATE_FPS = 4.0
# This value was determined from over an observed covered camera's noise
TRAINING_SAMPLES = 5
# This is how much the green channel has to change to consider a pixel changed
PIXEL_SHIFT_SENSITIVITY = 30
# This is the portion of pixels to compare when detecting motion
MOTION_DETECT_SAMPLE = 1.0/10  # so... 10%? (Kudos to Sarah Cooper)

# This is how long to sleep in various threads between shutdown checks
POLL_SECS = 0.1

FRAME_LATENCY_WINDOW_SIZE_SECS = 1.0

def signal_handler(sig, frame):
    global STOP
    if STOP:
        logging.debug("imageproducer SIGTERM")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.debug("imageproducer STOP")
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
        self._current_frame_seq = 0
        self._frame_window_start = 0
        self._frame_latency_window_start = 0

    def stop(self):
        logging.debug("Image producer received shutdown")
        self._exit.set()

    def _init_logging(self):
        handler = ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._logging_level)

    def get_next_frame(self):
        delay = (self._last_frame_at + self._frame_delay_secs) - time.time()
        if delay > 0:
            logging.debug("frame delay: {}".format(delay))
            time.sleep(delay)
        self._current_frame = self._get_frame()
        self._last_frame_at = time.time()
        self._current_frame_seq += 1
        if time.time() > (self._frame_latency_window_start + FRAME_LATENCY_WINDOW_SIZE_SECS):
          window_fps = (self._current_frame_seq - self._frame_window_start)/(time.time() - self._frame_latency_window_start)
          logging.debug("Frame {}, window {} in {} secs, fp/s: {}, delay: {}".format(self._current_frame_seq, (self._current_frame_seq - self._frame_window_start), (time.time() - self._frame_latency_window_start), window_fps, self._frame_delay_secs))
          self._frame_window_start = self._current_frame_seq
          self._frame_latency_window_start = time.time()

    def calculate_image_difference(self, tolerance=None, sample_percentage=MOTION_DETECT_SAMPLE):
        "Detect changes in the green channel."
        s=time.time()
        changed_pixels = 0
        pixel_step = int((RESOLUTION[0] * RESOLUTION[1])/(MOTION_DETECT_SAMPLE * RESOLUTION[0] * RESOLUTION[1]))
        current_pixels = self._current_frame.reshape((RESOLUTION[0] * RESOLUTION[1]), 3)
        prev_pixels = self._prev_frame.reshape((RESOLUTION[0] * RESOLUTION[1]), 3)
        for pixel_index in xrange(0, RESOLUTION[0]*RESOLUTION[1], pixel_step):
            if abs(int(current_pixels[pixel_index][1]) - int(prev_pixels[pixel_index][1])) > PIXEL_SHIFT_SENSITIVITY:
                changed_pixels += 1
                if tolerance and changed_pixels > tolerance:
                  logging.debug("Image diff short circuited at: {}".format(time.time() - s))
                  return changed_pixels
        logging.debug("Image diff took: {}".format(time.time() - s))
        return changed_pixels

    def is_image_difference_over_threshold(self, changed_pixels_threshold):
        changed_pixels = self.calculate_image_difference(changed_pixels_threshold)
        return changed_pixels > changed_pixels_threshold

    def _train_motion(self):
        logging.debug("Training motion")
        trained = False
        try:
            self._motion_threshold = 9999
            self.get_next_frame()
            for i in range(TRAINING_SAMPLES):
                self._prev_frame = self._get_frame()
                self.get_next_frame()
                motion = self.calculate_image_difference()
                self._motion_threshold = min(motion, self._motion_threshold)
            trained = True
        except Exception, e:
            logging.exception("Error training motion")
            trained = False
            sys.exit(1)
        logging.debug("Trained {}".format(trained))
        return trained

    def run(self):
        self._init_logging()
        logging.info("Image producer running")
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
        logging.error("overide _init_camera()")

    def _attempt_motion_training(self):
        logging.info("Training motion detection")
        for retry in xrange(3):
            if self._train_motion():
                break
        logging.info("Trained motion detection {}".format(self._motion_threshold))
    def _capture_frames(self):
        try:
            self.get_next_frame()
            while not self._stop_capturing:
                self._prev_frame = self._current_frame
                self.get_next_frame()
                if self.is_image_difference_over_threshold(self._motion_threshold):
                    logging.debug("Motion detected")
                    self._vision_queue.send((self._current_frame_seq, self._current_frame))
        except Exception, e:
            logging.exception("Error in capture_frames")
        logging.debug("Exiting vision capture thread")
        self._cleanup()

    def _cleanup(self):
        logging.debug("closing image queue")
        self._vision_queue.close()

class WebcamImageProducer(ImageProducer):
  def _init_camera(self):
    self._camera = cv2.VideoCapture(0)

    if not self._camera.isOpened():
      logging.error("Video camera not opened")
      sys.exit(255)

    self._camera.set(3, RESOLUTION[0])
    self._camera.set(4, RESOLUTION[1])


  def _get_frame(self):
      _, frame = self._camera.read()
      return frame

  def _close_video(self):
      self._camera.release()

class PiImageProducer(ImageProducer):
  def _init_camera(self):
    self._camera = PiCamera()
    self._camera.resolution = RESOLUTION
    self._camera.vflip = False
    self._camera.framerate = 32
    self._raw_capture = PiRGBArray(self._camera)

  def _get_frame(self):
      self._raw_capture.truncate(0)
      self._camera.capture(self._raw_capture, "rgb", use_video_port=True)
      return self._raw_capture.array

  def _close_video(self):
      self._camera.close()

def consume_images(image_queue):
    logging.info("image consumer started")
    _, incoming_images = image_queue
    try:
        while True:
            frame_seq, image = incoming_images.recv()
            logging.info("Frame {} received".format(frame_seq))
    except EOFError:
        logging.debug("Done watching")

def main():
  global STOP
  STOP = False

  try:
    log_stream = sys.stderr
    log_queue = multiprocessing.Queue(100)
    handler = ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_queue)
    logging.getLogger("").addHandler(handler)
    logging.getLogger("").setLevel(_DEBUG)

    image_queue = multiprocessing.Pipe()
    image_producer = frame_provider(image_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    image_producer.start()

    unused, _ = image_queue
    unused.close()

    image_consumer = threading.Thread(target = consume_images, args=(image_queue,))
    image_consumer.start()
    logging.info("waiting for stop signal")
    while not STOP:
        time.sleep(POLL_SECS)
    logging.info("STOP seen in main")
 
  except Exception, e:
    logging.exception("Error raised in main()")
  finally:
    logging.debug("Ending")
    image_producer.stop()
    image_producer.join()
    logging.debug("background process returned, exiting main process")
    sys.exit(0)

if _Pi:
  logging.debug("Using PiCamera for video capture")
  from picamera import PiCamera
  from picamera.array import PiRGBArray
  frame_provider = PiImageProducer
else:
  import cv2
  frame_provider = WebcamImageProducer

if __name__ == "__main__":
  main()
