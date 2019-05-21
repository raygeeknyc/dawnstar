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


class VisibleObject(object):
    "An object detected by our object detection engine."
    def __init__(self, object_class, bounding_box, confidence, generations_tracked):
        self.object_class = object_class
        self.confidence = confidence
        self.generations_tracked = generations_tracked
        self.bounding_box = bounding_box
        self.object_area = ImageAnalyzer.area(bounding_box[0], bounding_box[1])


class ProcessedFrame(object):
    "An image that has been processed by an ImageAnalyzer."
    def __init__(self, image, sequence_number, objects, interesting_object):
        self.image = image
        self.sequence_number = sequence_number
        self.objects = objects
        self.interesting_object = interesting_object


class ImageAnalyzer(multiprocessing.Process):
    "The abstract Image Analyzer - subclasses should provide specific object detection and classification engines."
    UNKNOWN = 0
    NCS = 1
    TPU_ACCELERATOR = 2
    
    @staticmethod
    def create(detection_engine, event, image_queue, object_queue, log_queue, logging_level):
        if detection_engine == ImageAnalyzer.NCS:
            return _NCSImageAnalyzer(event, image_queue, object_queue, log_queue, logging_level)
        elif detection_engine == ImageAnalyzer.TPU_ACCELERATOR:
            return _EdgeTPUImageAnalyzer(event, image_queue, object_queue, log_queue, logging_level)
        else:
            raise ValueError('Unknown Detection engine type {}'.format(engine))

    def _init_logging(self):
        handler = ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._logging_level)

    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        super(ImageAnalyzer, self).__init__()
        self._exit = event
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._image_queue = image_queue
        self._object_queue = object_queue
        self._image_queue = image_queue
	self._previous_detected_objects = []
	self._classifier = None

    def _cleanup(self):
        logging.debug("Cleaning up")
        self._object_queue.close()
        self._classifier.cleanup()

    @staticmethod
    def center(box):
        point1, point2 = box
        return ((point2[0] + point1[0]) /2, (point2[1] + point1[1]) / 2)

    @staticmethod
    def area(box_point1, box_point2):
        area = (box_point2[0] - box_point1[0]) * (box_point2[1] - box_point1[1])
        return max(0, area)

    @staticmethod
    def zone_for_object(image, object):
        object_center = center(object[0][1])
        x_zone = (object_center[0] / ImageAnalyzer.get_x_zone_size(image) + (1 if object_center[0] % ImageAnalyzer.get_x_zone_size(image) else 0))
        y_zone = (object_center[1] / ImageAnalyzer.get_y_zone_size(image) + (1 if object_center[1] % ImageAnalyzer.get_y_zone_size(image) else 0))
        logging.debug("Box: {} Zone: {}, {}".format(object[0], x_zone, y_zone))
        return (x_zone, y_zone)

    @staticmethod
    def overlap_area(object_1, object_2):
        overlap_region = ((max(object_1.bounding_box[0][0], object_2.bounding_box[0][0]),
                max(object_1.bounding_box[0][1], object_2.bounding_box[0][1])),
                (max(object_1.bounding_box[1][0], object_2.bounding_box[1][0]),
                max(object_1.bounding_box[1][1], object_2.bounding_box[1][1])))
        overlap = ImageAnalyzer.area(overlap_region[0], overlap_region[1])

        return overlap

    @staticmethod
    def area_ratio(prediction_1, prediction_2):
        _, _, _, pred_1_area, _ = prediction_1
        _, _, _, pred_2_area, _ = prediction_2
        relative_size = max(pred_area_1, pred_area_2) / min(pred_area_1, pred_area_2)
        return relative_size

    @staticmethod
    def _rank_possible_matches(primary_object_set, secondary_object_set):
        eligible_matches = dict()
        for detected_object in primary_object_set:
            key_primary = (detected_object.object_class, detected_object.bounding_box)
            for potential_matching_object in secondary_object_set:
                if potential_matching_object.object_class != detected_object.object_class:
                    continue
                overlapping_area_score = ImageAnalyzer.overlap_area(detected_object, potential_matching_object)
                if overlapping_area_score:
                    key_secondary = (potential_matching_object.object_class, potential_matching_object.bounding_box)
                    eligible_matches[(key_primary, key_secondary)] = overlapping_area_score
        # At this point we have all possible matches and a score for each
        matched_primaries = []
        matched_secondaries = []
        best_matches = []
        for match_key, rank in sorted(eligible_matches.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            proposed_primary, proposed_secondary = match_key
            if proposed_primary in matched_primaries:
                continue
            if proposed_secondary in matched_secondaries:
                continue
            best_matches.append(match_key)
            matched_primaries.append(proposed_primary)
            matched_secondaries.append(proposed_secondary)
        return best_matches

    @staticmethod
    def weight_of_zone_for_segment(start, end, zone, zones, zone_length):
        if (zone+1)*zone_length < start: return 0
        elif zone*zone_length > end: return 0
        if zone == 0: zone_weight = 2.0
        elif zone == zones-1: zone_weight = -2.0
        elif zone == (zones-1)/2: zone_weight = 0.0
        elif zone == zones/2: zone_weight = 0.0
        elif zone < (zones-1)/2: zone_weight = 1.0
        elif zone > zones/2: zone_weight = -1.0
        segment_in_zone = (min(end, (zone+1)*zone_length)-max(start, zone*zone_length))
        return zone_weight * ((1.0 * segment_in_zone) / (end - start))

    @staticmethod
    def correction_for_zone(zone):
        if zone[0] > X_ZONES:
            raise ValueError("Bad X zone calculation")
        if zone[1] > Y_ZONES:
            raise ValueError("Bad Y zone calculation")
        x = -9999
        if zone[0] == 1: x = -2
        elif zone[0] == 2: x = -1
        elif zone[0] in (3,4): x = 0
        elif zone[0] == 5: x = 1
        elif zone[0] == 6: x = 2

        y = -9999
        if zone[1] == 1: y = -1
        elif zone[1] in (2,3): y = 0
        elif zone[1] == 4: y = 1

        return (x, y)

    @staticmethod
    def get_center_zone(image, object):
        object_center = ImageAnalyzer.center(object.bounding_box)
        x_zone = (object_center[0] / ImageAnalyzer.get_x_zone_size(image)) + (1 if object_center[0] % ImageAnalyzer.get_x_zone_size(image) else 0)
        y_zone = (object_center[1] / ImageAnalyzer.get_y_zone_size(image)) + (1 if object_center[1] % ImageAnalyzer.get_y_zone_size(image) else 0)
        logging.debug("Box: {} Zone: {}, {}".format(object.bounding_box, x_zone, y_zone))
        return (x_zone, y_zone)

    @staticmethod
    def get_correction_to_center(image, object):
        (x0, y0),(x1, y1) = object.bounding_box
        x_correction = 0
        y_correction = 0
        for zone in range(0, X_ZONES):
            x_correction += round(ImageAnalyzer.weight_of_zone_for_segment(x0, x1, zone, X_ZONES, ImageAnalyzer.get_x_zone_size(image)), 2)
        for zone in range(0, Y_ZONES):
            y_correction += round(ImageAnalyzer.weight_of_zone_for_segment(y0, y1, zone, Y_ZONES, ImageAnalyzer.get_y_zone_size(image)), 2)
        return (x_correction, y_correction)

    @staticmethod
    def _get_most_interesting_object(objects):
        prioritized_objects = {}
        for object in objects:
            if object.object_class not in INTERESTING_CLASSES.keys():
                continue
            if INTERESTING_CLASSES[object.object_class] not in prioritized_objects.keys():
                prioritized_objects[INTERESTING_CLASSES[object.object_class]] = [object]
            else:
                prioritized_objects[INTERESTING_CLASSES[object.object_class]].append(object)
        if not prioritized_objects:
            return None
        highest_priority = sorted(prioritized_objects.keys())[0]
        highest_priority_objects = prioritized_objects[highest_priority]
        max_area = 0
        for important_object in highest_priority_objects:
            if important_object.object_area > max_area:
                max_area = important_object.object_area
                largest_object = important_object
        if max_area == 0:
            return []
        return largest_object

    @staticmethod
    def get_x_zone_size(image):
        return image.shape[1] / X_ZONES

    @staticmethod
    def get_y_zone_size(image):
        return image.shape[0] / Y_ZONES

    def _object_by_key(self, objects, object_key):
        for detected_object in objects:
            if detected_object.object_class == object_key[0] and detected_object.bounding_box == object_key[1]:
                return detected_object
        return None

    def _apply_matches(self, persistent_object_keys, predictions, previous_predictions):
        logging.debug("previous_predictions : {}".format(previous_predictions))
        for (current_prediction_key, previous_prediction_key) in persistent_object_keys:
            logging.debug("prev key: {}".format(previous_prediction_key))
            previous_object = self._object_by_key(previous_predictions, previous_prediction_key)
            if not previous_object:
                raise ValueError("Missing previous prediction")
            current_object = self._object_by_key(predictions, current_prediction_key)
            if not current_object:
                raise ValueError("Missing current prediction")
            current_object.generations_tracked += previous_object.generations_tracked
	
    def _process_image(self, frame_number, image):
        logging.debug("Processing image {}".format(frame_number))
	detected_objects = self._get_likely_objects(image)
        logging.debug("objects : {}".format(detected_objects))
        logging.debug("_previous_detected_objects : {}".format(self._previous_detected_objects))
	persistent_object_keys = ImageAnalyzer._rank_possible_matches(detected_objects, self._previous_detected_objects)
        logging.debug("Matches: {}".format(persistent_object_keys))
	self._apply_matches(persistent_object_keys, detected_objects, self._previous_detected_objects)
	logging.debug("Objects: {}, previous: {}, matches: {}".format(len(detected_objects), len(self._previous_detected_objects), len(persistent_object_keys)))
	interesting_object = ImageAnalyzer._get_most_interesting_object(detected_objects)
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


class _EdgeTPUImageAnalyzer(ImageAnalyzer):
    pass


class _NCSImageAnalyzer(ImageAnalyzer):
    GRAPH_FILENAME = "ncs_detection/graphs/mobilenetgraph"
    PREPROCESS_DIMENSIONS = (300, 300)
    def __init__(self, event, image_queue, object_queue, log_queue, logging_level):
        super(_NCSImageAnalyzer, self).__init__(event, image_queue, object_queue, log_queue, logging_level)

	self._classifier = NCSObjectClassifier(self.__class__.GRAPH_FILENAME, MININUM_CONSIDERED_CONFIDENCE, self.__class__.PREPROCESS_DIMENSIONS)

    def _get_likely_objects(self, image):
	confident_predictions = self._classifier.get_confident_predictions(image)
	likely_objects = []
	object_generations_tracked = 1
	for prediction in confident_predictions:
		likely_object = VisibleObject(prediction[0], prediction[1], prediction[2], object_generations_tracked)
		likely_objects.append(likely_object)
	return likely_objects
