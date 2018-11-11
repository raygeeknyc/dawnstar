_Pi = False
_Pi = True

import logging

from ncs_detection.ncs_object_detector import NCSObjectClassifier

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

# This is how long to sleep in various threads between shutdown checks
POLL_SECS = 0.1


# This is the lowest confidence score that the classifier should return
MININUM_CONSIDERED_CONFIDENCE = 0.5

GRAPH_FILENAME = "ncs_detection/graphs/mobilenetgraph"

class ImageAnalyzer(multiprocessing.Process):
    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        multiprocessing.Process.__init__(self)
        self._exit = event
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._image_queue = image_queue
        self._object_queue = object_queue
        self._image_queue = image_queue
	self._classifier = NCSObjectClassifier(GRAPH_FILENAME, MININUM_CONSIDERED_CONFIDENCE)

    def _process_image(self, image, frame_number):
        logging.debug("Processing image {}".format(frame_number))
	predictions = self._classifier.get_likely_objects(image)
	interesting_object = self._classifier.get_most_interesting_object(oredictions)
       	if not self._exit.is_set():
        	logging.debug("Queuing processed image {}".format(frame_number))
        	self._object_queue.put((image, predictions, interesting_object))

    def _get_images(self):
        logging.debug("image consumer started")
        image = None
        while not self._exit.is_set():
            try:
                t = self._image_queue.get(False)
        	if self._exit.is_set():
                    continue
                logging.debug("processing queue had an entry")
                frame_number, image = t
                logging.debug("Image {} received".format(frame_number))
            except Queue.Empty:
                if image is None:
                    logging.debug("Empty processing queue, waiting")
                    continue
        	if self._exit.is_set():
                    continue
                _, _, interesting_object = self._process_image(image, frame_number)
                image = None
            except Exception, e:
                logging.exception("error consuming images")
        logging.debug("Stopped image consumer")
 
    def _cleanup(self):
        logging.debug("Cleaning up")
        self._object_queue.close()

    def _init_logging(self):
        handler = ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._logging_level)

    def run(self):
        self._init_logging()
        logging.debug("Image analyzer running")
        try:
            self._get_images()
        except Exception, e:
            logging.exception("Error in analyzer main thread")
        finally:
            self._cleanup()
            logging.debug("Exiting image analyzer")
