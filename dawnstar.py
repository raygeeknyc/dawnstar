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

import cv2

import multiprocessing
from Queue import Empty
from multiprocessingloghandler import ParentMultiProcessingLogHandler
WEB_SERVER_BASEPATH = "/var/www/html"
IMAGE_FRAME_NAME = "FRAME.jpg"

HEARTBEAT_SECS = 1.0
IP_ADDRESS_RESOLUTION_DELAY_SECS = 1.0

STEER_RIGHT_THRESHOLD = 0.75
STEER_LEFT_THRESHOLD = -1 * STEER_RIGHT_THRESHOLD
MIN_GENERATIONS_TO_CENTER = 2

from display import DisplayInfo, Display
import imagecapture
from imageanalyzer import ImageAnalyzer
from ambulator import Ambulator
from converser import Converser

COLORS = [(255, 200, 200), (100,100,200)]

class Dawnstar():
  def __init__(self, event, object_queue):
    self._process_event = event
    self.ip_address = None
    self.frames = 0
    self.tracked_objects = 0
    self.tracked_bounds = ((0,0),(0,0))
    self.tracked_area = 0
    self.most_interesting_generations_tracked = 0
    self.object_count = 0
    self.tracked_zone = (0, 0)
    self.corrections_to_zone = None
    self._screen = Display()
    self._ambulator = Ambulator()
    self._object_queue = object_queue
    self.frame_sequence_number = None
    logging.debug('Ip address: {}'.format(self._get_ip_address()))

  def startup(self):
    self._frame_consumer = threading.Thread(target = self._ingest_processed_frames, args=())
    self._frame_consumer.start()

    self._screen_updater = threading.Thread(target = self._maintain_display, args=())
    self._screen_updater.start()

    self._walker = threading.Thread(target = self._maintain_position, args=())
    self._walker.start()

  def _maintain_position(self):
    last_processed_frame = 0
    while not self._process_event.is_set():
      if last_processed_frame != self.frame_sequence_number:
        logging.debug("New frame")
        last_processed_frame = self.frame_sequence_number
        if not self.corrections_to_zone:
          logging.debug("Stop")
          self._ambulator.stop()
        else:
          if self.most_interesting_generations_tracked < MIN_GENERATIONS_TO_CENTER:
            logging.debug("Not turning yet")
          else:
            logging.debug("Turn")
            steering = self.corrections_to_zone[0]
            if steering < STEER_LEFT_THRESHOLD:
              logging.debug("Steering left: {}".format(steering))
              self._ambulator.nudge_left()
            elif steering > STEER_RIGHT_THRESHOLD:
              logging.debug("Steering right: {}".format(steering))
              self._ambulator.nudge_right()
            else:
              logging.debug("No correction needed")
              self._ambulator.stop()
    self._ambulator.stop()

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
        info.generations_tracked = self.most_interesting_generations_tracked
        info.tracked_bounds = self.tracked_bounds
        info.tracked_zone = self.tracked_zone
        info.frames = self.frames
        info.corrections_to_zone = "({:0.1f},{:0.1f})".format(self.corrections_to_zone[0], self.corrections_to_zone[1]) if self.corrections_to_zone else "none"
        prev_frames = self.frames
        prev_ip_address = self.ip_address
        self._screen.refresh(info)

  def _construct_info_image(self, frame, detected_objects, interesting_object):
    image_to_decorate = frame.copy()
    for object in detected_objects:
      top_left, bottom_right = object.bounding_box
      (startX, startY) = (top_left[0], top_left[1])
      y = startY - 15 if startY - 15 > 15 else startY + 15

      if object == interesting_object:
        cv2.rectangle(image_to_decorate, top_left, bottom_right,
          COLORS[0], 2)
      else:
        cv2.rectangle(image_to_decorate, top_left, bottom_right,
          COLORS[1], 1)
    image_for_display = cv2.flip(image_to_decorate, 0)
    if interesting_object:
      top_left, bottom_right = interesting_object.bounding_box
      (startX, startY) = (top_left[0], top_left[1])
      y = startY - 15 if startY - 15 > 15 else startY + 15
      label = "{}[{}]".format(interesting_object.object_class, interesting_object.generations_tracked)
      cv2.putText(image_for_display, label, (startX, y),
        cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS[0], 3)
    return image_for_display

  def _write_frame_to_server(self, debug_image):
    cv2.imwrite(os.path.join(WEB_SERVER_BASEPATH, IMAGE_FRAME_NAME), debug_image)

  def _ingest_processed_frames(self):
    logging.debug("object consumer started")
    frame = None
    while not self._process_event.is_set():
      try:
        frame = self._object_queue.get(False)
      except Empty:
        continue 
      self.frames += 1
      logging.debug("Frame[{}] received".format(self.frames))
      self.object_count = len(frame.objects)
      if frame.interesting_object:
        self.tracked_objects = 1
        self.frame_sequence_number = frame.sequence_number
        self.tracked_bounds = frame.interesting_object.bounding_box
	logging.debug("bounds: {}".format(self.tracked_bounds))
        self.tracked_area = frame.interesting_object.object_area
        self.most_interesting_generations_tracked = frame.interesting_object.generations_tracked
	self.tracked_zone = ImageAnalyzer.get_center_zone(frame.image, frame.interesting_object)
	self.corrections_to_zone = ImageAnalyzer.get_correction_to_center(frame.image, frame.interesting_object)
      else:
        self.tracked_objects = 0
	self.tracked_zone = None
        self.frame_sequence_number = frame.sequence_number
	self.corrections_to_zone = None
      for (processed_image, object) in enumerate(frame.objects):
        logging.debug("Detected object class={}, confidence={}, age={}".format(object.object_class, object.confidence, object.generations_tracked))
      debug_image = self._construct_info_image(frame.image, frame.objects, frame.interesting_object)
      self._write_frame_to_server(debug_image)
    logging.debug("Done consuming objects")

def main():
  image_source = None
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

    image_analyzer = ImageAnalyzer.create(ImageAnalyzer.NCS, process_event, image_queue, object_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.debug("Starting image analyzer")
    image_analyzer.start()

    image_source = imagecapture.frame_provider(process_event, image_queue, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.debug("Starting image producer")
    image_source.start()

    converser = Converser(process_event, log_queue, logging.getLogger("").getEffectiveLevel())
    logging.debug("Starting converser")
    converser.start()

    logging.info("Starting Robot")
    robot.startup()

    logging.info("Robot running")
    try:
      while not robot.ip_address:
        robot._get_ip_address()
        time.sleep(IP_ADDRESS_RESOLUTION_DELAY_SECS)
      logging.info("Robot connected to the internet")

      while True:
        time.sleep(HEARTBEAT_SECS)
	logging.debug("heartbeat")
    except KeyboardInterrupt, e:
        logging.info("Interrupted")
        process_event.set()
  except Exception, e:
    logging.exception("Error raised in main()")
  finally:
    logging.info("Ending")
    if converser:
      logging.debug("Waiting for converser process")
      converser.join()
      logging.debug("converser process returned")
    if image_source:
      logging.debug("Waiting for image producer process")
      image_source.join()
      logging.debug("image producer process returned")
    if image_analyzer:
      logging.debug("Waiting for analyzer process")
      image_analyzer.join()
      logging.debug("analyzer process returned")
  sys.exit(0)

if __name__ == "__main__":
  main()

