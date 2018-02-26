import logging

# Import the packages we need for drawing and displaying images
from PIL import Image, ImageDraw
import cv2
import numpy
HAAR_CASCADE_PATH = "haarcascade_frontalface_default.xml"
HAAR_ALT_CASCADE_PATH="haarcascade_profileface.xml"
LBP_CASCADE_PATH = "lbpcascade_frontalface_improved.xml"
LBP_ALT_CASCADE_PATH = "lbpcascade_profileface.xml"
haar_classifier = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
haar_alt_classifier = cv2.CascadeClassifier(HAAR_ALT_CASCADE_PATH)
lbp_classifier = cv2.CascadeClassifier(LBP_CASCADE_PATH)
lbp_alt_classifier = cv2.CascadeClassifier(LBP_ALT_CASCADE_PATH)
FRAME_COLOR = (0, 255, 100)
FRAME_WIDTH = 2

# Import the packages we need for reading parameters and files
import io
import sys

def compareClassifiers(cv2_image):
    haar_faces = findFaces(cv2_image, haar_classifier, haar_alt_classifier)
    haar_count = len(haar_faces)
    lbp_faces = findFaces(cv2_image, lbp_classifier, lbp_alt_classifier)
    lbp_count = len(lbp_faces)
    if lbp_count != haar_count:
        logging.debug("HAAR: {}, LBP: {}".format(haar_count, lbp_count))
    if len(haar_faces) > len(lbp_faces):
        return haar_faces
    else:
        return lbp_faces

# Take a CV2 RGB image, return a list of faces
def findFaces(cv2_image, classifier, alt_classifier):
    grayscale_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2GRAY)
    faces = classifier.detectMultiScale(
        grayscale_image,
        scaleFactor=1.1,
        minSize=(30,30)
    )
    if len(faces):
            logging.debug("Found {0} front faces!".format(len(faces)))
    else:
        logging.debug("finding right profile faces")
        faces = alt_classifier.detectMultiScale(
            grayscale_image,
            scaleFactor=1.1,
            minSize=(30,30)
        )
        if len(faces) > 0:
            logging.debug("Found {0} right profile faces!".format(len(faces)))
        else: 
            # We only look for left profiles if there were no right to avoid
            #  double-counting the same face in both orientations
            logging.debug("finding left profile faces")
            flipped_image = cv2.flip(grayscale_image, 1)
            left_faces = alt_classifier.detectMultiScale(
                flipped_image,
                scaleFactor=1.1,
                minSize=(30,30)
            )
            if len(left_faces) > 0:
                logging.debug("Found {0} left profile faces!".format(len(left_faces)))
                # We flip the X coordinate of the face on a flipped image to
                # translate it back to the original face's orientation
                for face in left_faces:
                    new_x = grayscale_image.shape[1]-face[0]-face[2]
                    logging.debug("X: {} of {} to {}".format(face[0], grayscale_image.shape[0], new_x))
                    face[0] = new_x
                if len(faces) > 0:
                    faces += left_faces
                else:
                    faces = left_faces
    for face in faces:
        logging.debug(face)
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
    if _DEBUG:
        logging.info(filename)
    pil_image = Image.open(filename)
    logging.debug("Dimensions {}".format(pil_image.size))
    return pil_image

def frameFace(image, face):
    canvas = ImageDraw.Draw(image)
    canvas.line((face[0], face[1], face[0]+face[2], face[1]), fill=FRAME_COLOR, width=FRAME_WIDTH)
    canvas.line((face[0]+face[2], face[1], face[0]+face[2], face[1]+face[3]), fill=FRAME_COLOR, width=FRAME_WIDTH)
    canvas.line((face[0], face[1]+face[3], face[0]+face[2], face[1]+face[3]), fill=FRAME_COLOR, width=FRAME_WIDTH)
    canvas.line((face[0], face[1], face[0], face[1]+face[3]), fill=FRAME_COLOR, width=FRAME_WIDTH)

if __name__ == '__main__':
    faces_found = 0
    images = 0
    for image_filename in sys.argv[1:]:
        images += 1
        rgb_image = loadImage(image_filename)
        wpercent = (320/float(rgb_image.size[0]))
        hsize = int((float(rgb_image.size[1])*float(wpercent)))
        rgb_image = rgb_image.resize((320, hsize), Image.ANTIALIAS)

        cv2_image = numpy.array(rgb_image)
        faces = compareClassifiers(cv2_image)
        if len(faces):
            face = findOneFace(faces)
            face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
            logging.debug("face center is {}".format(face_center))
            frameFace(rgb_image, face)
            faces_found += 1
            if _DEBUG: showImage(rgb_image)
    logging.info("Images {}, found faces in {}".format(images, faces_found))
