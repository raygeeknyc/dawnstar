import cv2
import numpy

# Import the packages we need for drawing and displaying images
from PIL import Image, ImageDraw

CASCADE_PATH = "lbpcascade_frontalface_improved.xml"
ALT_CASCADE_PATH = "lbpcascade_profileface.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)
altCascade = cv2.CascadeClassifier(ALT_CASCADE_PATH)

# Import the packages we need for reading parameters and files
import io
import sys

def loadImageFile(filename):
# Loads the image into memory
# Return the image way content
    with io.open(filename, 'rb') as image_file:
        content = image_file.read()
    return content

def findFaces(gray_image):
    # Tell the vision service to look for faces in the image
    faces = cascade.detectMultiScale(
        image,
        minNeighbors=5,
        scaleFactor=1.2
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

# Process the filenames specified on the command line
for image_filename in sys.argv[1:]:
    content = loadImageFile(image_filename)
    image = Image.open(io.BytesIO(content))
    cv2_image = numpy.array(image)
    cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2GRAY)
    faces = findFaces(cv2_image)
    im.show()
