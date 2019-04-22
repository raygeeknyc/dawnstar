import logging

from ncs_detection.ncs_object_detector import NCSObjectClassifier

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
HEARTBEAT_SECS = 0.1


# This is the lowest confidence score that the classifier should return
MININUM_CONSIDERED_CONFIDENCE = 0.5

GRAPH_FILENAME = "ncs_detection/graphs/mobilenetgraph"

class ImageAnalyzer(multiprocessing.Process):
    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        super(ImageAnalyzer, self).__init__()
        self._exit = event
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._image_queue = image_queue
        self._object_queue = object_queue
        self._image_queue = image_queue


class NCSImageAnalyzer(ImageAnalyzer):
    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        super(_NCSImageAnalyzer, self).__init__()
	self._previous_predictions = []
	self._classifier = NCSObjectClassifier(GRAPH_FILENAME, MININUM_CONSIDERED_CONFIDENCE)

    def _prediction_by_key(self, predictions, prediction_key):
        for prediction in predictions:
            if prediction[0] == prediction_key:
                return prediction
        return None

    @staticmethod
    def object_center_zone(object):
        return NCSObjectClassifier.zone_for_object(object)

    @staticmethod
    def object_corrections_to_center(object):
        return NCSObjectClassifier.correction_for_object(object)

    def _apply_matches(self, persistent_object_keys, predictions, previous_predictions):
        logging.debug("previous_predictions : {}".format(previous_predictions))
        for (current_prediction_key, previous_prediction_key) in persistent_object_keys:
            logging.debug("prev key: {}".format(previous_prediction_key))
            previous_object = self._prediction_by_key(previous_predictions, previous_prediction_key)
            if not previous_object:
                raise ValueError("Missing previous prediction")
            current_object = self._prediction_by_key(predictions, current_prediction_key)
            if not current_object:
                raise ValueError("Missing current prediction")
            current_object[3] += previous_object[3]

    def _process_image(self, frame_number, image):
        logging.debug("Processing image {}".format(frame_number))
	predictions = self._classifier.get_likely_objects(image)
        logging.debug("predictions : {}".format(predictions))
        logging.debug("_previous_predictions : {}".format(self._previous_predictions))
	persistent_object_keys = self._classifier.rank_possible_matches(predictions, self._previous_predictions)
        logging.debug("Matches: {}".format(persistent_object_keys))
        logging.debug("_previous_predictions : {}".format(self._previous_predictions))
	self._apply_matches(persistent_object_keys, predictions, self._previous_predictions)
	logging.debug("Objects: {}, previous: {}, matches: {}".format(len(predictions), len(self._previous_predictions), len(persistent_object_keys)))
	interesting_object = self._classifier.get_most_interesting_object(predictions)
       	if not self._exit.is_set():
        	logging.debug("Queuing processed image {}".format(frame_number))
        	frame_envelope = (frame_number, image)
        	self._object_queue.put((frame_envelope, predictions, interesting_object))
		self._previous_predictions = predictions

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
                self._process_image(frame_number, image)
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
