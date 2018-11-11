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
import imageanalyzer

class Dawnstar():
  def __init__(self, event, object_queue):
    self._process_event = event
    self.ip_address = None
    self.frames = 0
    self.trackable_objects = 0
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
        info.trackable_objects = self.trackable_objects
        info.frames = self.frames
        prev_frames = self.frames
        prev_ip_address = self.ip_address
        self._screen.refresh(info)

  def _process_objects(self):
    logging.debug("object consumer started")
    while not self._process_event.is_set():
      try:
        frame = self._object_queue.get(False)
      except Empty:
        continue 
      self.frames += 1
      logging.info("Objects[{}] received".format(self.frames))
      base_image, predictions, interesting_object = frame
      if interesting_object:
        self.trackable_objects = 1
      else:
        self.trackable_objects = 0
      for (process_image, pred) in enumerate(predictions):
        (pred_class, pred_confidence, pred_boxpts) = pred
        logging.info("Prediction class={}, confidence={}".format(pred_class, pred_confidence))
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

    image_analyzer = imageanalyzer.ImageAnalyzer(process_event, image_queue, object_queue, log_queue, logging.getLogger("").getEffectiveLevel())
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
