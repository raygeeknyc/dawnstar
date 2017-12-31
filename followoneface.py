import logging
import time
logging.getLogger('').setLevel(logging.DEBUG)
_DEBUG=True

from picamera import PiCamera
RESOLUTION = (640, 480)
PIXEL_SHIFT_SENSITIVITY = 30
TRAINING_SAMPLES = 5

CAPTURE_RATE_FPS = 2
SLEEPY_DELAY_SECS = 3

# Import the packages we need for drawing and displaying images
from PIL import Image
import cv2
import numpy
CASCADE_PATH="haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Import the packages we need for reading parameters and files
import io
import sys

# Import OLED support
import Adafruit_SSD1306

RST=24
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()
disp.clear()
disp.display()

def calculateImageDifference(prev_image, current_image):
    "Detect changes in the green channel."
    changed_pixels = 0
    w, h = current_image.size
    logging.debug("examining {}x{} image".format(w, h))
    current_pix = current_image.load()
    prev_pix = prev_image.load()
    for x in xrange(w):
        for y in xrange(h):
            if abs(current_pix[x,y][1] - prev_pix[x,y][1]) > PIXEL_SHIFT_SENSITIVITY:
                changed_pixels += 1
    return changed_pixels

def trainMotion(camera):
    logging.debug("Training motion")
    image_buffer = io.BytesIO()
    _motion_threshold = 9999
    current_image = None
    sample = 0
    for _ in camera.capture_continuous(image_buffer, format='jpeg', use_video_port=True):
        logging.debug("sample {}".format(sample))
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
    logging.debug("Trained motion threshold is {}".format(motion_threshold))
    return motion_threshold

def getCamera():
    camera = PiCamera()
    camera.resolution = RESOLUTION
    camera.vflip = False
    return camera

# Take a PIL RGB image, return a list of faces
def findFaces(image):
    opencv_image = numpy.array(image) 
    grayscale = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2GRAY)

    faces = cascade.detectMultiScale(
        grayscale,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags = cv2.cv.CV_HAAR_SCALE_IMAGE
    )
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
    logging.debug("Largest face:{} area:{}".format(max_face, max_face_area))
    return max_face

def showImage(image):
    image.show()

if __name__ == '__main__':
    logging.info("finding a face")
    camera = getCamera()
    motion_threshold = trainMotion(camera)
    frame_delay_secs = 1.0/CAPTURE_RATE_FPS
    last_motion_at = 0l
    last_frame_at = 0l
    just_moved = False
    display_image = None
    motion = motion_threshold
    image_buffer = io.BytesIO()

    for _ in camera.capture_continuous(image_buffer, format='jpeg', use_video_port=True):
        prev_image = display_image
        try:
            image_buffer.truncate()
            image_buffer.seek(0)
        except Exception, e:
            logging.exception("Error capturing image")
            time.sleep(CAMERA_ERROR_DELAY_SECS)
            continue
        display_image = Image.open(image_buffer)
        last_frame_at = time.time()
        if just_moved:
            just_moved = False
            continue
        if prev_image:
            motion = calculateImageDifference(prev_image, display_image)
        if motion < motion_threshold:
            if time.time() < (last_motion_at + SLEEPY_DELAY_SECS):
                pass  # indicate that we're bored or sleeping
            continue
        logging.debug("motion")
        last_motion_at = time.time()
        faces = findFaces(display_image)
        face = None
        if len(faces) > 0:
            face = findOneFace(faces)
        if not face:
            logging.debug("no face seen")
            continue
        face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
        logging.info("face center is {},{}".format(face_center[0], face_center[1]))
