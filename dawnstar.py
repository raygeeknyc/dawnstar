# The tracker portion of a K9

import logging
_DEBUG=logging.DEBUG
_DEBUG=logging.INFO
logging.getLogger('').setLevel(logging.DEBUG)

import os
import sys
import signal
import subprocess
import time
import threading

import multiprocessing
from multiprocessingloghandler import ParentMultiProcessingLogHandler

REFRESH_DELAY_SECS = 2

from display import DisplayInfo, Display
import imagecapture

def signal_handler(sig, frame):
    global STOP
    if STOP:
        logging.debug("SIGTERM")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.debug("STOP")
    STOP = True
signal.signal(signal.SIGINT, signal_handler)

class Dawnstar(object):
  _IP_CMD = 'hostname -I | cut -d\" \" -f1'

  def __init__(self):
    self._ip_address = None
    self._info = DisplayInfo()
    self._screen = Display()
    print('Ip address: {}'.format(self.get_ip_address()))

  def get_ip_address(self):
    self._ip_address = subprocess.check_output(Dawnstar._IP_CMD, shell = True )
    return self._ip_address

  def maintain_display(self):
   self._info.ip = self.get_ip_address()
   logging.debug('Ip address: {}'.format(self._info.ip))
   self._screen.refresh(self._info)

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
  image_producer = None

  try:
    log_stream = sys.stderr
    log_queue = multiprocessing.Queue(100)
    handler = ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_queue)
    logging.getLogger("").addHandler(handler)
    logging.getLogger("").setLevel(_DEBUG)

    robot = Dawnstar()

    image_queue = multiprocessing.Pipe()
    image_producer = imagecapture.frame_provider(image_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    image_producer.start()

    unused, _ = image_queue
    unused.close()

    image_consumer = threading.Thread(target = consume_images, args=(image_queue,))
    image_consumer.start()
    logging.info("waiting for stop signal")
    while not STOP:
        robot.maintain_display()
        time.sleep(REFRESH_DELAY_SECS)
    logging.info("STOP seen in main")
 
  except Exception, e:
    logging.exception("Error raised in main()")
  finally:
    logging.debug("Ending")
    if image_producer:
      image_producer.stop()
      image_producer.join()
      logging.debug("background process returned, exiting main process")
    sys.exit(0)

if __name__ == "__main__":
  main()
