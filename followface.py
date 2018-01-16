_DEBUG=True
import logging
import sys
import numpy
from PIL import Image, ImageDraw

from findoneface import lbp_classifier, lbp_alt_classifier, loadImage, findOneFace, findFaces, frameFace, showImage
from pantilt import pointTo

logging.getLogger('').setLevel(logging.INFO)
RESOLUTION=(320,240)
classifier = findoneface.lbp_classifier
profile_classifier = findoneface.lbp_alt_classifier

def getCenteringCorrection(face, field_of_view):
    face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
    face_y_offset = face_center[1] - RESOLUTION[1]/2 
    face_x_offset = face_center[0] - field_of_view[0]/2 
    look_dir = [0, 0]
    if (face_x_offset < (-1 * face[0])):
        look_dir[0] = 1
    elif (face_x_offset > (field_of_view[0] - (face[0]+face[2]))):
        look_dir[0] = -1
    if (face_y_offset < (-1 * face[1])):
        look_dir[1] = 1
    elif (face_y_offset > (field_of_view[1] - (face[1]+face[3]))):
        look_dir[1] = -1
    return (face_center, look_dir)

faces_found = 0
images = 0
pan_tilt_state = [None, None]
for image_filename in sys.argv[1:]:
    images += 1
    rgb_image = loadImage(image_filename)
    wpercent = (RESOLUTION[0]/float(rgb_image.size[0]))
    hsize = int((float(rgb_image.size[1])*float(wpercent)))
    rgb_image = rgb_image.resize((RESOLUTION[0], hsize), Image.ANTIALIAS)

    cv2_image = numpy.array(rgb_image)
    faces = findFaces(cv2_image, classifier, profile_classifier)
    if len(faces):
        face = findOneFace(faces)
        (face_center, look_dir) = getCenteringCorrection(face, RESOLUTION)
        logging.info("face center is {}".format(face_center))
        logging.info("look direction (x,y) is {}".format(look_dir))
        frameFace(rgb_image, face)
        pointTo(look_dir, pan_tilt_state)
        faces_found += 1
        if _DEBUG: showImage(rgb_image)
logging.info("Images {}, found faces in {}".format(images, faces_found))
