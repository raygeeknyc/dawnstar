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

# This is the number of zones that we place objects into on each axis
Y_ZONES = 4
X_ZONES = 6

# The classes of objects that we track, mapped to their priority, 1==highest
INTERESTING_CLASSES = {"cat":2, "dog":2, "person":1, "car":3, "bicycle":3, "bird":4}

# This is the lowest confidence score that the classifier should return
MININUM_CONSIDERED_CONFIDENCE = 0.5

GRAPH_FILENAME = "ncs_detection/graphs/mobilenetgraph"

class ProcessedFrame(object):
    def __init__(self, image, sequence_number, objects, interesting_object):
        self.image = image
        self.sequence_number = sequence_number
        self.objects = objects
        self.interesting_object = interesting_object


class ImageAnalyzer(multiprocessing.Process):
    UNKNOWN = 0
    NCS = 1
    TPU_ACCELERATOR = 2
    
    @staticmethod
    def create(engine, event, image_queue, object_queue, log_queue, logging_level):
        if engine == ImageAnalyzer.NCS:
            return _NCSImageAnalyzer(event, image_queue, object_queue, log_queue, logging_level)
        elif engine == ImageAnalyzer.TPU_ACCELERATOR:
            return _EdgeTPUImageAnalyzer(event, image_queue, object_queue, log_queue, logging_level)
        else:
            raise ValueError('Unknown engine type {}'.format(engine))

    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        super(ImageAnalyzer, self).__init__()
        self._exit = event
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._image_queue = image_queue
        self._object_queue = object_queue
        self._image_queue = image_queue
	self._previous_detected_objects = []

    @staticmethod
    def center(box):
        point1, point2 = box
        return ((point2[0] + point1[0]) /2, (point2[1] + point1[1]) / 2)

    @staticmethod
    def area(box_point1, box_point2):
        area = (box_point2[0] - box_point1[0]) * (box_point2[1] - box_point1[1])
        return max(0, area)

    @staticmethod
    def zone_for_object(object):
        center = NCSObjectClassifier.center(object[0][1])
        x_zone = (center[0] / NCSObjectClassifier._X_ZONE_SIZE) + (1 if center[0] % NCSObjectClassifier._X_ZONE_SIZE else 0)
        y_zone = (center[1] / NCSObjectClassifier._Y_ZONE_SIZE) + (1 if center[1] % NCSObjectClassifier._Y_ZONE_SIZE else 0)
        logging.debug("Box: {} Zone: {}, {}".format(object[0], x_zone, y_zone))
        return (x_zone, y_zone)

    @staticmethod
    def overlap_area(prediction_1, prediction_2):
        (_, pred_1_box), _, _, _ = prediction_1
        (_, pred_2_box), _, _, _ = prediction_2
        overlap_region = ((max(pred_1_box[0][0], pred_2_box[0][0]),
                max(pred_1_box[0][1], pred_2_box[0][1])),
                (max(pred_1_box[1][0], pred_2_box[1][0]),
                max(pred_1_box[1][1], pred_2_box[1][1])))
        overlap_area = ImageAnalyzer.area(overlap_region[0], overlap_region[1])

        return overlap_area

    @staticmethod
    def area_ratio(prediction_1, prediction_2):
        _, _, _, pred_1_area, _ = prediction_1
        _, _, _, pred_2_area, _ = prediction_2
        relative_size = max(pred_area_1, pred_area_2) / min(pred_area_1, pred_area_2)
        return relative_size

    @staticmethod
    def get_most_interesting_object(self, predictions):
        prioritized_objects = {}
        for object in predictions:
                (_class, _bound_box), _confidence, _, _ = object
                if _class not in NCSObjectClassifier.INTERESTING_CLASSES.keys():
                        continue
                if NCSObjectClassifier.INTERESTING_CLASSES[_class] not in prioritized_objects.keys():
                        prioritized_objects[NCSObjectClassifier.INTERESTING_CLASSES[_class]] = [object]
                else:
                        prioritized_objects[NCSObjectClassifier.INTERESTING_CLASSES[_class]].append(object)
        if not prioritized_objects:
                return None
        highest_priority = sorted(prioritized_objects.keys())[0]
        highest_priority_objects = prioritized_objects[highest_priority]
        max_area = 0
        for important_object in highest_priority_objects:
                (_, _), _, area, _  = important_object
                if area > max_area:
                        max_area = area
                        largest_object = important_object
        if max_area == 0:
                return []
        return largest_object


class _EdgeTPUImageAnalyzer(ImageAnalyzer):
    pass

class _NCSImageAnalyzer(ImageAnalyzer):
    PREPROCESS_DIMENSIONS = (300, 300)
    _X_ZONE_SIZE = PREPROCESS_DIMENSIONS[0] / X_ZONES
    _Y_ZONE_SIZE = PREPROCESS_DIMENSIONS[1] / Y_ZONES
    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        super(_NCSImageAnalyzer, self).__init__(event, image_queue, object_queue, log_queue, logging_level)

	self._classifier = NCSObjectClassifier(GRAPH_FILENAME, MININUM_CONSIDERED_CONFIDENCE, self.__class__.PREPROCESS_DIMENSIONS, INTERESTING_CLASSES)

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

    def _get_likely_objects(self, image):
	confident_predictions = self._classifier.get_confident_predictions(image)
	likely_objects = []
	object_generations_tracked = 1
	for prediction in confident_predictions:
		object_bounds = prediction[1]
		object_area = self.area(object_bounds[0], object_bounds[1])
		likely_object = [(prediction[0], object_bounds), prediction[2], object_area, object_generations_tracked]
		likely_objects.append(likely_object)
	return likely_objects
	
    def _process_image(self, frame_number, image):
        logging.debug("Processing image {}".format(frame_number))
	detected_objects = self._get_likely_objects(image)
        logging.debug("objects : {}".format(detected_objects))
        logging.debug("_previous_detected_objects : {}".format(self._previous_detected_objects))
	persistent_object_keys = self._classifier.rank_possible_matches(detected_objects, self._previous_detected_objects)
        logging.debug("Matches: {}".format(persistent_object_keys))
        logging.debug("_previous_detected_objects : {}".format(self._previous_detected_objects))
	self._apply_matches(persistent_object_keys, detected_objects, self._previous_detected_objects)
	logging.debug("Objects: {}, previous: {}, matches: {}".format(len(detected_objects), len(self._previous_detected_objects), len(persistent_object_keys)))
	interesting_object = self._classifier.get_most_interesting_object(detected_objects)
       	if not self._exit.is_set():
        	logging.debug("Queuing processed image {}".format(frame_number))
        	frame_envelope = (frame_number, image)
		frame = ProcessedFrame(image, frame_number, detected_objects, interesting_object)
        	self._object_queue.put(frame)
		self._previous_detected_objects = detected_objects

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
