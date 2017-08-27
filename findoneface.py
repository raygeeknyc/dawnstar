import logging
logging.getLogger('').setLevel(logging.INFO)
_DEBUG=False

from picamera import PiCamera
RESOLUTION = (640, 480)

ZONES=(4,3)
# Import the packages we need for drawing and displaying images
from PIL import Image
import cv2
import numpy
CASCADE_PATH="haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Import the packages we need for reading parameters and files
import io
import sys

def findZone(point):
    logging.debug("point[{}][{}]".format(point[0],point[1]))
    for x in range(ZONES[0]):
        x_boundary=(RESOLUTION[0]/ZONES[0]*(x+1))
        for y in range(ZONES[1]):
            y_boundary=(RESOLUTION[1]/ZONES[1]*(y+1))
            logging.debug("[{}][{}] is [{}][{}]".format(x,y,x_boundary,y_boundary))
            if point[0]<x_boundary and point[1]<y_boundary:
                logging.debug("zone[{}][{}]".format(x_boundary,y_boundary))
                return (x,y)
            

def getCamera():
    camera = PiCamera()
    camera.resolution = RESOLUTION
    camera.vflip = False
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
    while True:
        rgb_image = captureImage(camera)
        if _DEBUG: showImage(rgb_image)
        faces = findFaces(rgb_image)
        face = findOneFace(faces)
        if face:
            face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
            face_zone = findZone(face_center)
            logging.info("face is in zone[{}][{}]".format(face_zone[0], face_zone[1]))
