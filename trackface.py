_DEBUG=True
import logging
logging.getLogger('').setLevel(logging.INFO)

pan_tilt_state = [None, None]
faces = 0
frames = 0
# loop over video frames here
    frames += 1
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
