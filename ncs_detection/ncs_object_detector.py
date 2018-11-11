from mvnc import mvncapi as mvnc
import numpy as np
import cv2

import logging
logging.getLogger().setLevel(logging.DEBUG)

class NCSObjectClassifier(object):
	# frame dimensions should be square
	PREPROCESS_DIMS = (300, 300)

        device = None

        @classmethod
	def _init_NCS_device(cls):
		# grab a list of all NCS devices plugged in to USB
		print("finding NCS devices...")
		devices = mvnc.EnumerateDevices()

		# if no devices found, exit the script
		if len(devices) == 0:
			raise Exception("No devices found. Please plug in a NCS")

		print("found {} devices. device0 will be used. "
			"opening device0...".format(len(devices)))
		device = mvnc.Device(devices[0])
		device.OpenDevice()
		print("device opened")
		cls.device = device

	# initialize the list of class labels our network was trained to
	# detect, then generate a set of bounding box colors for each class
	CLASSES = ("background", "aeroplane", "bicycle", "bird",
		"boat", "bottle", "bus", "car", "cat", "chair", "cow",
		"diningtable", "dog", "horse", "motorbike", "person",
		"pottedplant", "sheep", "sofa", "train", "tvmonitor")

	INTERESTING_CLASSES = {"cat":2, "dog":2, "person":1, "car":3, "bicycle":3, "bird":4}

        
	def __init__(self, graph_filename, min_confidence):
		self.graph_filename = graph_filename
		self.confidence_threshold = min_confidence
                if not self.__class__.device:
			self.__class__._init_NCS_device()
		self._init_graph()

	def cleanup(self):
		# clean up the graph and device
		self._graph.DeallocateGraph()
		self.__class__.device.CloseDevice()
		self.__class__.device = None

	def _init_graph(self):
		# open the CNN graph file
		logging.info("loading the graph file into RPi memory...")
		with open(self.graph_filename, mode="rb") as f:
			graph_in_memory = f.read()

		# load the graph into the NCS
		logging.info("allocating the graph on the NCS...")
		self._graph = self.__class__.device.AllocateGraph(graph_in_memory)

	@staticmethod
	def preprocess_image(input_image):
		# preprocess the image
		preprocessed = cv2.resize(input_image, NCSObjectClassifier.PREPROCESS_DIMS)
		preprocessed = preprocessed - 127.5
		preprocessed = preprocessed * 0.007843
		preprocessed = preprocessed.astype(np.float16)

		# return the image to the calling function
		return preprocessed

	def get_most_interesting_object(self, predictions):
		prioritized_objects = {}
		for object in predictions:
			_class, _confidence, _bound_box = object
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
			_, _, _box  = important_object
			area = ((_box[1][0] - _box[0][0]) *
				(_box[1][1] - _box[0][1]))
			if area > max_area:
				max_area = area
				largest_object = important_object
		if max_area == 0:
			return []
		return largest_object

	def get_likely_objects(self, image):
		# preprocess the image
		image = self.preprocess_image(image)

		# send the image to the NCS and run a forward pass to grab the
		# network predictions
		self._graph.LoadTensor(image, None)
		(output, _) = self._graph.GetResult()

		# grab the number of valid object predictions from the output,
		# then initialize the list of predictions
		num_valid_boxes = output[0]
		predictions = []
	
		# loop over results
		for box_index in range(num_valid_boxes):
			# calculate the base index into our array so we can extract
			# bounding box information
			base_index = 7 + box_index * 7

			# boxes with non-finite (inf, nan, etc) numbers must be ignored
			if (not np.isfinite(output[base_index]) or
				not np.isfinite(output[base_index + 1]) or
				not np.isfinite(output[base_index + 2]) or
				not np.isfinite(output[base_index + 3]) or
				not np.isfinite(output[base_index + 4]) or
				not np.isfinite(output[base_index + 5]) or
				not np.isfinite(output[base_index + 6])):
				continue

			pred_conf = output[base_index + 2]
			if pred_conf >= self.confidence_threshold:
				# extract the image width and height and clip the boxes to the
				# image size in case network returns boxes outside of the image
				# boundaries
				(h, w) = image.shape[:2]
				x1 = max(0, int(output[base_index + 3] * w))
				y1 = max(0, int(output[base_index + 4] * h))
				x2 = min(w,	int(output[base_index + 5] * w))
				y2 = min(h,	int(output[base_index + 6] * h))

				pred_class = NCSObjectClassifier.CLASSES[int(output[base_index + 1])]
				pred_boxpts = ((x1, y1), (x2, y2))

				# create prediction tuple and append the prediction to the
				# predictions list
				prediction = (pred_class, pred_conf, pred_boxpts)
				predictions.append(prediction)

		# return the list of predictions to the calling function
		return predictions
