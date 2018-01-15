import logging
logging.getLogger('').setLevel(logging.INFO)
_DEBUG=False

# Import the packages we need for drawing and displaying images
from PIL import Image, ImageDraw
import cv2
import numpy
#CASCADE_PATH = "lbpcascade_frontalface_improved.xml"
CASCADE_PATH = "haarcascade_frontalface_default.xml"
ALT_CASCADE_PATH = "haarcascade_profileface.xml"
FRAME_COLOR = (0, 127, 255)
FRAME_WIDTH = 2

cascade = cv2.CascadeClassifier(CASCADE_PATH)
alt_cascade = cv2.CascadeClassifier(ALT_CASCADE_PATH)

# Import the packages we need for reading parameters and files
import io
import sys


# Take a CV2 RGB image, return a list of faces
def findFaces(cv2_image):
    grayscale_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2GRAY)
    faces = cascade.detectMultiScale(
        grayscale_image,
        scaleFactor=1.2
    )
    if len(faces):
            logging.info("Found {0} front faces!".format(len(faces)))
    else:
        logging.info("finding profile faces")
        faces = alt_cascade.detectMultiScale(
            grayscale_image,
            scaleFactor=1.2
        )
        if len(faces) > 0:
            logging.info("Found {0} profile faces!".format(len(faces)))
    for face in faces:
        logging.info(face)
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

def loadImage(filename):
    logging.info(filename)
    pil_image = Image.open(filename)
    logging.info("Dimensions {}".format(pil_image.size))
    return pil_image

def frameFace(image, face):
    logging.info("face: {}".format(face))
    canvas = ImageDraw.Draw(image)
    canvas.line((face[0], face[1], face[0]+face[2], face[1]), fill=FRAME_COLOR, width=FRAME_WIDTH)
    canvas.line((face[0]+face[2], face[1], face[0]+face[2], face[1]+face[3]), fill=FRAME_COLOR, width=FRAME_WIDTH)
    canvas.line((face[0], face[1]+face[3], face[0]+face[2], face[1]+face[3]), fill=FRAME_COLOR, width=FRAME_WIDTH)
    canvas.line((face[0], face[1], face[0], face[1]+face[3]), fill=FRAME_COLOR, width=FRAME_WIDTH)

for image_filename in sys.argv[1:]:
    rgb_image = loadImage(image_filename)
    cv2_image = numpy.array(rgb_image)
    faces = findFaces(cv2_image)
    face = findOneFace(faces)
    if face:
        face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
        logging.info("face center is {}".format(face_center))
        frameFace(rgb_image, face)
    showImage(rgb_image)
