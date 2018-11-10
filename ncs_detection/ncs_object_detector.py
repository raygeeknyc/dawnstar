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

	def predict(self, image):
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

			# extract the image width and height and clip the boxes to the
			# image size in case network returns boxes outside of the image
			# boundaries
			(h, w) = image.shape[:2]
			x1 = max(0, int(output[base_index + 3] * w))
			y1 = max(0, int(output[base_index + 4] * h))
			x2 = min(w,	int(output[base_index + 5] * w))
			y2 = min(h,	int(output[base_index + 6] * h))

			# grab the prediction class label, confidence (i.e., probability),
			# and bounding box (x, y)-coordinates
			pred_class = int(output[base_index + 1])
			pred_conf = output[base_index + 2]
			pred_boxpts = ((x1, y1), (x2, y2))

			# create prediciton tuple and append the prediction to the
			# predictions list
			prediction = (pred_class, pred_conf, pred_boxpts)
			predictions.append(prediction)

		# return the list of predictions to the calling function
		return predictions
