import logging
_DEBUG=False
if _DEBUG:
  logging.getLogger().setLevel(logging.DEBUG)
else:
  print "info"
  logging.getLogger().setLevel(logging.INFO)

import sys
import time
import cv2
from followface import findFaces, findOneFace, getCenteringCorrection, frameFace, classifier, profile_classifier, alt_classifier, alt_profile_classifier
from pantilt import pointTo
pan_tilt_state = [None, None]
RESOLUTION=(640, 480)

def equalize_brightness(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = cv2.equalizeHist(hsv[:,:,2])
    eq_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return eq_img

def equalize_hist(img):
    eq_img = img.copy()
    for c in xrange(0, 2):
       eq_img[:,:,c] = cv2.equalizeHist(img[:,:,c])
    return eq_img

def equalize_hist_adaptive(img):
    adaptive_eq_img = img.copy()
    adaptive_eq_img = cv2.cvtColor(adaptive_eq_img, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(adaptive_eq_img)
    return adaptive_eq_img

faces = 0
frames = 0

videostream = cv2.VideoCapture(0)
videostream.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
videostream.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
if not videostream.isOpened():
  logging.error("Video camera not opened")
  sys.exit(255)
faces_time = 0.0
contrast_faces_time = 0.0
brightness_faces_time = 0.0
contrast_brightness_faces_time = 0.0
adaptive_faces_time = 0.0
alt_faces_time = 0.0

detection_faces = 0
detection_faces_contrast_brightness = 0
detection_faces_brightness = 0
detection_faces_contrast = 0
detection_faces_adaptive = 0
detection_faces_alt = 0
while(True):
    # Capture frame-by-frame
    ret, frame = videostream.read()
    frames += 1

    start_time = time.time()
    faces = findFaces(frame, classifier, profile_classifier)
    faces_time += time.time() - start_time

    start_time = time.time()
    eq_adaptive_frame = equalize_hist_adaptive(frame)
    eq_adaptive_faces = findFaces(eq_adaptive_frame, classifier, profile_classifier)
    adaptive_faces_time += time.time() - start_time

    start_time = time.time()
    tmp_frame = equalize_hist(frame)
    eq_contrast_brightness_frame = equalize_brightness(tmp_frame)
    eq_contrast_brightness_faces = findFaces(eq_contrast_brightness_frame, classifier, profile_classifier)
    contrast_brightness_faces_time += time.time() - start_time

    start_time = time.time()
    eq_contrast_frame = equalize_hist(frame)
    eq_contrast_faces = findFaces(eq_contrast_frame, classifier, profile_classifier)
    contrast_faces_time += time.time() - start_time

    start_time = time.time()
    eq_brightness_frame = equalize_brightness(frame)
    eq_brightness_faces = findFaces(eq_brightness_frame, classifier, profile_classifier)
    brightness_faces_time += time.time() - start_time

    start_time = time.time()
    alt_faces = findFaces(frame, alt_classifier, alt_profile_classifier)
    alt_faces_time += time.time() - start_time

    detection_faces += len(faces)
    detection_faces_brightness += len(eq_brightness_faces)
    detection_faces_contrast += len(eq_contrast_faces)
    detection_faces_adaptive += len(eq_adaptive_faces)
    detection_faces_contrast_brightness += len(eq_contrast_brightness_faces)
    detection_faces_alt += len(alt_faces)

    logging.info("# {}, faces {}, eq_adaptive {}, eq_contrast {}, eq_brightness {}, eq_contrast_brightness {}, alt {}".format(frames, len(faces), len(eq_adaptive_faces), len(eq_contrast_faces), len(eq_brightness_faces), len(eq_contrast_brightness_faces), len(alt_faces)))
    if len(faces) > 0:
        face = findOneFace(faces)
        (face_center, look_dir) = getCenteringCorrection(face, RESOLUTION)
        logging.info("face center is {}".format(face_center))
        logging.info("look direction (x,y) is {}".format(look_dir))
        frameFace(frame, face)
        pointTo(look_dir, pan_tilt_state)
    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# When everything done, release the capture
logging.info("faces {}, brightness {}, contrast {}, adaptive {}, contrast brightness {}, alt {}".format(detection_faces, detection_faces_brightness, detection_faces_contrast, detection_faces_adaptive, detection_faces_contrast_brightness, detection_faces_alt))
logging.info("faces time {}, brightness time {}, contrast time {}, adaptive time {} contrast brightness {} alt time {}".format(faces_time, brightness_faces_time, contrast_faces_time, adaptive_faces_time, contrast_brightness_faces_time, alt_faces_time))
videostream.release()
cv2.destroyAllWindows()
