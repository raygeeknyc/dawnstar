_DEBUG=True
import logging
import sys
import numpy
from PIL import Image, ImageDraw

import findoneface
from findoneface import lbp_classifier, lbp_alt_classifier, loadImage, findOneFace, findFaces, frameFace, showImage
logging.getLogger('').setLevel(logging.INFO)
RESOLUTION=(320,240)
classifier = findoneface.lbp_classifier
profile_classifier = findoneface.lbp_alt_classifier

faces_found = 0
images = 0
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
        face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
        logging.debug("face center is {}".format(face_center))
        frameFace(rgb_image, face)
        faces_found += 1
        if _DEBUG: showImage(rgb_image)
logging.info("Images {}, found faces in {}".format(images, faces_found))
