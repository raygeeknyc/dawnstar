PIXEL_SHIFT_SENSITIVITY = 30
TRAINING_SAMPLES = 5

import cv2
import logging
#CASCADE_PATH="haarcascade_frontalface_default.xml"
CASCADE_PATH = "lbpcascade_frontalface_improved.xml"
ALT_CASCADE_PATH = "lbpcascade_profileface.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)
#altCascade = cv2.CascadeClassifier(ALT_CASCADE_PATH)

def calculateImageDifference(prev_image, current_image):
    "Detect changes in the green channel."
    changed_pixels = 0
    w, h = current_image.size
    logging.info("examining {}x{} image".format(w, h))
    current_pix = current_image.load()
    prev_pix = prev_image.load()
    for x in xrange(w):
        for y in xrange(h):
            if abs(current_pix[x,y][1] - prev_pix[x,y][1]) > PIXEL_SHIFT_SENSITIVITY:
                changed_pixels += 1
    return changed_pixels

def trainMotion(camera):
    logging.info("Training motion")
    image_buffer = io.BytesIO()
    _motion_threshold = 9999
    current_image = None
    sample = 0
    for _ in camera.capture_continuous(image_buffer, format='jpeg', use_video_port=True):
        logging.info("sample {}".format(sample))
        prev_image = current_image
        try:
            image_buffer.truncate()
            image_buffer.seek(0)
        except Exception, e:
            logging.exception("Error capturing image")
            time.sleep(CAMERA_ERROR_DELAY_SECS)
            continue
        current_image = Image.open(image_buffer)
        if not prev_image: prev_image = current_image
        motion = calculateImageDifference(prev_image, current_image)
        motion_threshold = min(motion, _motion_threshold)
        sample += 1
        if sample >= TRAINING_SAMPLES: break
    logging.info("Trained motion threshold is {}".format(motion_threshold))
    return motion_threshold

# Take a cv2 grayscale image, return a list of faces
def findFaces(image):
    faces = cascade.detectMultiScale(
        image,
        scaleFactor=1.2,
        minNeighbors=5
    )
    if len(faces): logging.info("Found {0} front faces!".format(len(faces)))
    return faces
    right_profiles = altCascade.detectMultiScale(
        image,
        scaleFactor=1.2,
        minNeighbors=5
    )
    if len(right_profiles): logging.info("Found {0} right profile faces!".format(len(right_profiles)))
    flipped_image = cv2.flip(image, 0)
    left_profiles = altCascade.detectMultiScale(
        flipped_image,
        scaleFactor=1.2,
        minNeighbors=5
    )
    if len(left_profiles): logging.info("Found {0} left profile faces!".format(len(left_profiles)))
    faces += right_profiles
    faces += left_profiles
    if len(faces): logging.info("Found {0} faces!".format(len(faces)))
    return faces

def findOneFace(faces):
    max_face_area = 0
    max_face = None
    for (x, y, w, h) in faces:
        face_area = (w * h)
        if face_area >= max_face_area:
            max_face_area = face_area
            max_face = (x, y, w, h)
    logging.info("Largest face:{} area:{}".format(max_face, max_face_area))
    return max_face
