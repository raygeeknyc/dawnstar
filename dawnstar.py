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
IP_ADDRESS_RESOLUTION_DELAY_SECS = 1

from display import DisplayInfo, Display
import imagecapture
import imageanalyzer

def signal_handler(sig, frame):
    global STOP
    if STOP:
        logging.info("Robot SIGTERM")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.info("Robot STOP")
    STOP = True
signal.signal(signal.SIGINT, signal_handler)

class Dawnstar():
  def __init__(self, object_queue):
    global STOP

    self.ip_address = None
    self.frames = 0
    self._screen = Display()
    self._object_queue = object_queue
    print('Ip address: {}'.format(self._get_ip_address()))

  def startup(self):
    global STOP

    self._object_consumer = threading.Thread(target = self._process_objects, args=())
    self._object_consumer.start()

    self._screen_updater = threading.Thread(target = self._maintain_display, args=())
    self._screen_updater.start()

    while not STOP and not self.ip_address:
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
    global STOP
    prev_frames = None
    prev_ip_address = None
    while not STOP:
      if self.ip_address != prev_ip_address or self.frames != prev_frames:
        info = DisplayInfo()
        info.ip = self.ip_address
        info.frames = self.frames
        prev_frames = self.frames
        prev_ip_address = self.ip_address
        self._screen.refresh(info)

  def _process_objects(self):
    global STOP
    logging.debug("object consumer started")
    while not STOP:
      try:
        objects = self._object_queue.get(False)
      except Empty:
        continue 
      self.frames += 1
      logging.info("Objects[{}] received".format(self.frames))
    logging.debug("Done consuming objects")

def main():
  global STOP
  STOP = False
  image_producer = None

  try:
    log_stream = sys.stderr
    log_queue = multiprocessing.Queue(100)
    handler = ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_queue)
    logging.getLogger("").addHandler(handler)
    logging.getLogger("").setLevel(_DEBUG)

    image_queue = multiprocessing.Queue()

    object_queue = multiprocessing.Queue()
    robot = Dawnstar(object_queue)

    image_analyzer = imageanalyzer.ImageAnalyzer(image_queue, object_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.debug("Starting image analyzer")
    image_analyzer.start()

    image_producer = imagecapture.frame_provider(image_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.debug("Starting image producer")
    image_producer.start()

    logging.info("Starting Robot")
    robot.startup()

    logging.info("Robot running")
    while not STOP:
        time.sleep(REFRESH_DELAY_SECS)
    logging.debug("STOP seen in main")
 
  except Exception, e:
    logging.exception("Error raised in main()")
  finally:
    logging.info("Ending")
    if image_producer:
      image_producer.stop()
      logging.debug("Waiting for image producer process")
      image_producer.join()
      logging.debug("image producer process returned")
    if image_analyzer:
      image_analyzer.stop()
      logging.debug("Waiting for analyzer process")
      image_analyzer.join()
      logging.debug("analyzer process returned")
  sys.exit(0)

if __name__ == "__main__":
  main()
