# The tracker portion of a K9

import logging
_DEBUG=logging.DEBUG
_DEBUG=logging.INFO

import os
import socket
import sys
import signal
import subprocess
import time
import threading

import multiprocessing
from Queue import Empty
from multiprocessingloghandler import ParentMultiProcessingLogHandler

REFRESH_DELAY_SECS = 2
POLL_SECS = 0.1
IP_ADDRESS_RESOLUTION_DELAY_SECS = 1
STOP = None

from display import DisplayInfo, Display
import imagecapture
from imageanalyzer import ImageAnalyzer

class Dawnstar():
  def __init__(self, event, object_queue):
    self._process_event = event
    self.ip_address = None
    self.frames = 0
    self.tracked_objects = 0
    self.tracked_bounds = ((0,0),(0,0))
    self.tracked_area = 0
    self.tracked_generations = 0
    self.object_count = 0
    self.corrections = None
    self._screen = Display()
    self._object_queue = object_queue
    print('Ip address: {}'.format(self._get_ip_address()))

  def startup(self):
    self._object_consumer = threading.Thread(target = self._process_objects, args=())
    self._object_consumer.start()

    self._screen_updater = threading.Thread(target = self._maintain_display, args=())
    self._screen_updater.start()

    while not self.ip_address:
      self._get_ip_address()
      time.sleep(IP_ADDRESS_RESOLUTION_DELAY_SECS)
     
  def _get_ip_address(self):
    try:
      if not self.ip_address:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip_address = s.getsockname()[0]
        s.close()
    except Exception, e:
      logging.warning("No IP address")
    finally:
      return self.ip_address

  def _maintain_display(self):
    prev_frames = None
    prev_ip_address = None
    while not self._process_event.is_set():
      if self.ip_address != prev_ip_address or self.frames != prev_frames:
        info = DisplayInfo()
        info.ip = self.ip_address
        info.object_count = self.object_count
        info.tracked_objects = self.tracked_objects
        info.tracked_generations = self.tracked_generations
        info.tracked_bounds = self.tracked_bounds
        info.frames = self.frames
        info.corrections = self.corrections
        prev_frames = self.frames
        prev_ip_address = self.ip_address
        self._screen.refresh(info)

  def _process_objects(self):
    logging.debug("object consumer started")
    predictions = []
    while not self._process_event.is_set():
      try:
        frame = self._object_queue.get(False)
      except Empty:
        continue 
      self.frames += 1
      logging.info("Frame[{}] received".format(self.frames))
      previous_predictions = predictions
      base_image, predictions, interesting_object = frame
      self.object_count = len(predictions)
      if interesting_object:
	(_, self.tracked_bounds), _, self.tracked_area, self.tracked_generations = interesting_object
	logging.info("bounds: {}".format(self.tracked_bounds))
        self.tracked_objects = 1
	self.corrections = ImageAnalyzer.corrections_to_center(interesting_object)
      else:
        self.tracked_objects = 0
	self.corrections = None
      for (process_image, pred) in enumerate(predictions):
        (pred_class, _), pred_confidence, _, tracked_generations = pred
        logging.info("Prediction class={}, confidence={}, age={}".format(pred_class, pred_confidence, tracked_generations))
    logging.debug("Done consuming objects")

def main():
  STOP = False

  image_producer = None
  image_analyzer = None

  process_event = multiprocessing.Event()
  
  try:
    log_stream = sys.stderr
    log_queue = multiprocessing.Queue(100)
    handler = ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_queue)
    logging.getLogger("").addHandler(handler)
    logging.getLogger("").setLevel(_DEBUG)

    image_queue = multiprocessing.Queue()

    object_queue = multiprocessing.Queue()
    robot = Dawnstar(process_event, object_queue)

    image_analyzer = ImageAnalyzer(process_event, image_queue, object_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.info("Starting image analyzer")
    image_analyzer.start()

    image_producer = imagecapture.frame_provider(process_event, image_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.info("Starting image producer")
    image_producer.start()

    logging.info("Starting Robot")
    robot.startup()

    logging.info("Robot running")
    try:
      while True:
        time.sleep(POLL_SECS)
    except KeyboardInterrupt, e:
        logging.info("Interrupted")
        process_event.set()
  except Exception, e:
    logging.exception("Error raised in main()")
  finally:
    logging.info("Ending")
    if image_producer:
      logging.info("Waiting for image producer process")
      image_producer.join()
      logging.info("image producer process returned")
    if image_analyzer:
      logging.info("Waiting for analyzer process")
      image_analyzer.join()
      logging.info("analyzer process returned")
  sys.exit(0)

if __name__ == "__main__":
  main()
