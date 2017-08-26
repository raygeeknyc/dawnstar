import logging
logging.getLogger('').setLevel(logging.DEBUG)

from picamera import PiCamera

# Import the packages we need for drawing and displaying images
from PIL import Image
import cv2
import numpy
CASCADE_PATH="haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Import the packages we need for reading parameters and files
import io
import sys

RESOLUTION = (640, 480)

def getCamera():
    camera = PiCamera()
    camera.resolution = RESOLUTION
    camera.vflip = True
    return camera

def captureImage(camera):
    image_buffer = io.BytesIO()
    camera.capture(image_buffer, format="jpeg")
    image_buffer.seek(0)
    image = Image.open(image_buffer)
    return image

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
    logging.debug("Found {0} faces!".format(len(faces)))
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

    camera = getCamera()
    rgb_image = captureImage(camera)
    faces = findFaces(rgb_image)
    face = findOneFace(faces)
