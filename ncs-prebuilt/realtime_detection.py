# USAGE
# python ncs_realtime_objectdetection.py --graph graphs/mobilenetgraph --display 1
# python ncs_realtime_objectdetection.py --graph graphs/mobilenetgraph --confidence 0.5 --display 1

import logging
logging.getLogger().setLevel(logging.DEBUG)

# import the necessary packages
from mvnc import mvncapi as mvnc
from imutils.video import VideoStream
from imutils.video import FPS
import argparse
import numpy as np
import time
import cv2
from ncs_object_detector import NCSObjectClassifier

# frame dimensions should be square
DISPLAY_DIMS = (900, 900)
PREPROCESS_DIMS = (300, 300)

# calculate the multiplier needed to scale the bounding boxes
DISP_MULTIPLIER = DISPLAY_DIMS[0] // PREPROCESS_DIMS[0]

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-g", "--graph", required=True,
	help="path to input graph file")
ap.add_argument("-c", "--confidence", default=.5,
	help="confidence threshold")
ap.add_argument("-d", "--display", type=int, default=0,
	help="switch to display image on screen")
args = vars(ap.parse_args())

# open a pointer to the video stream thread and allow the buffer to
# start to fill, then start the FPS counter
logging.info("starting the video stream and FPS counter...")
vs = VideoStream(usePiCamera=True).start()
time.sleep(1)
fps = FPS().start()

# loop over frames from the video file stream
classifier = NCSObjectClassifier(args["graph"], args["confidence"])
while True:
	try:
		# grab the frame from the threaded video stream
		# make a copy of the frame and resize it for display/video purposes
		frame = vs.read()
		image_for_result = frame.copy()
		image_for_result = cv2.resize(image_for_result, DISPLAY_DIMS)

		# use the NCS to acquire predictions
		predictions = classifier.predict(frame)

		# loop over our predictions
		for (i, pred) in enumerate(predictions):
			# extract prediction data for readability
			(pred_class, pred_conf, pred_boxpts) = pred

			# print prediction to terminal
			logging.info("Prediction #{}: class={}, confidence={}, "
				"boxpoints={}".format(i, NCSObjectClassifier.CLASSES[pred_class], pred_conf,
					pred_boxpts))

			# check if we should show the prediction data
			# on the frame
			if args["display"] > 0:
				# build a label consisting of the predicted class and
				# associated probability
				label = "{}: {:.2f}%".format(NCSObjectClassifier.CLASSES[pred_class],
					pred_conf * 100)

				# extract information from the prediction boxpoints
				(ptA, ptB) = (pred_boxpts[0], pred_boxpts[1])
				ptA = (ptA[0] * DISP_MULTIPLIER, ptA[1] * DISP_MULTIPLIER)
				ptB = (ptB[0] * DISP_MULTIPLIER, ptB[1] * DISP_MULTIPLIER)
				(startX, startY) = (ptA[0], ptA[1])
				y = startY - 15 if startY - 15 > 15 else startY + 15

				# display the rectangle and label text
				cv2.rectangle(image_for_result, ptA, ptB,
					COLORS[pred_class], 2)
				cv2.putText(image_for_result, label, (startX, y),
					cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS[pred_class], 3)

		# check if we should display the frame on the screen
		# with prediction data (you can achieve faster FPS if you
		# do not output to the screen)
		if args["display"] > 0:
			# display the frame to the screen
			cv2.imshow("Output", image_for_result)
			key = cv2.waitKey(1) & 0xFF

			# if the `q` key was pressed, break from the loop
			if key == ord("q"):
				logging.info("break")
				break

		# update the FPS counter
		fps.update()
	
	# if "ctrl+c" is pressed in the terminal, break from the loop
	except KeyboardInterrupt:
		logging.info("break")
		break

	# if there's a problem reading a frame, break gracefully
	except AttributeError, e:
		logging.exception("problem reading frame")
		break

# stop the FPS counter timer
fps.stop()

# destroy all windows if we are displaying them
if args["display"] > 0:
	cv2.destroyAllWindows()

# stop the video stream
vs.stop()

classifier.cleanup()

# display FPS information
logging.info("elapsed time: {:.2f}".format(fps.elapsed()))
logging.info("approx. FPS: {:.2f}".format(fps.fps()))
