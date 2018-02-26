import logging
_DEBUG=True
if _DEBUG:
  logging.getLogger().setLevel(logging.DEBUG)
else:
  print "info"
  logging.getLogger().setLevel(logging.INFO)

import sys
import cv2
from followface import findFaces, findOneFace, getCenteringCorrection, frameFace, classifier, profile_classifier
pan_tilt_state = [None, None]
RESOLUTION=(640, 480)

faces = 0
frames = 0

videostream = cv2.VideoCapture(0)
videostream.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
videostream.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
if not videostream.isOpened():
  logging.error("Video camera not opened")
  sys.exit(255)

while(True):
    # Capture frame-by-frame
    ret, frame = videostream.read()
    frames += 1
    faces = findFaces(frame, classifier, profile_classifier)
    logging.info("{} faces".format(len(faces)))
    if len(faces) > 0:
        face = findOneFace(faces)
        (face_center, look_dir) = getCenteringCorrection(face, RESOLUTION)
        logging.info("face center is {}".format(face_center))
        logging.info("look direction (x,y) is {}".format(look_dir))
        frameFace(frame, face)
        pointTo(look_dir, pan_tilt_state)
        faces_found += 1
    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# When everything done, release the capture
videostream.release()
cv2.destroyAllWindows()
