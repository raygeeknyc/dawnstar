import logging
logging.getLogger('').setLevel(logging.INFO)
_DEBUG=False

from picamera import PiCamera
RESOLUTION = (640, 480)

CAPTURE_RATE_FPS = 2

SLEEPY_DELAY_SECS = 3

ROWS=3
COLS=4
ZONES=(COLS, ROWS)

# Import the packages we need for drawing and displaying images
from PIL import Image
import cv2
import numpy
CASCADE_PATH="haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Import the packages we need for reading parameters and files
import io
import sys

def calculateImageDifference(prev_image, current_imnage):
    "Detect changes in the green channel."
    changed_pixels = 0
    for x in xrange(current_image.w):
        for y in xrange(current_image.h):
            if abs(current_image[1][x,y][1] - prev_image[1][x,y][1]) > PIXEL_SHIFT_SENSITIVITY:
                changed_pixels += 1
    return changed_pixels

def trainMotion(camera):
    logging.debug("Training motion")
    try:
        camera.start_preview(fullscreen=False, window=(100,100,camera.resolution[0], camera.resolution[1]))
        self._motion_threshold = 9999
        self.getNextFrame()
        prev_image = captureImage()
        for i in range(TRAINING_SAMPLES):
            prev_image = current_image
            current_image = captureImage()
            motion = self.calculateImageDifference(prev_image, current_image)
            motion_threshold = min(motion, self._motion_threshold)
    finally:
        self._camera.stop_preview()
    logging.debug("Trained motion threshold is {}".format(motion_threshold))
    return motion_threshold

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

def lookAt(zone):
    if zone[0] == 0:
        drawImage(LOOK_RIGHT)
    elif zone[0] == COLS-1:
        drawImage(LOOK_LEFT)
    if zone[1] == 0:
        drawImage(LOOK_UP)
    elif zone[1] == ROWS-1:
        drawImage(LOOK_DOWN)
    else:
        drawImage(LOOK_HAPPY)

def turnAndFaceZone(point_zone, face_zone):
    # if we're not at the end of the servo's range, turn towards the face
    reposition_face = False
    if point_zone[0] > 0 and point_zone[0] < COLS-1:
        if face_zone[0] == 0:
            point_zone[0] -= 1
            reposition_face = True
        elif face_zone[0] == COLS-1:
            point_zone[0] += 1
            reposition_face = True
    if point_zone[1] > 0 and point_zone[1] < ROWS-1:
        if face_zone[1] == 0:
            point_zone[1] -= 1
            reposition_face = True
        elif face_zone[1] == ROWS-1:
            point_zone[1] += 1
            reposition_face = True
    lookAt(face_zone)
    if reposition_face:
        pointFace(point_zone)
        return point_zone
    else:
        return None

def pointFace(point_zone):
    x = point_zone[0]
    y = point_zone[1]

if __name__ == '__main__':
    logging.info("finding a face")
    camera = getCamera()
    frame_delay_secs = 1.0/CAPTURE_RATE_FPS
    rgb_image = captureImage(camera)
    point_zone = (1,1)
    last_motion_at = 0l
    just_moved = False
    while True:
        delay = (last_frame_at + frame_delay_secs) - time.time()
        if delay > 0:
            time.sleep(delay)
        prev_image = rgb_image
        rgb_image = captureImage(camera)
        last_frame_at = time.time()
        if _DEBUG: showImage(rgb_image)
        if just_moved:
            just_moved = False
            continue
        motion = self.calculateImageDifference(prev_image, rgb_image)
        if motion < motion_threshold:
            if time.time() < (last_motion_at + SLEEPY_DELAY_SECS):
                drawImage(LOOK_SLEEPY)
            continue
        last_motion_at = time.time()
        faces = findFaces(rgb_image)
        face = findOneFace(faces)
        if not face:
            logging.debug("no face seen")
            drawImage(LOOK_LONELY)
            continue
        face_center = (face[0]+(face[2]/2), face[1]+(face[3]/2))
        face_zone = findZone(face_center)
        logging.info("face is in zone[{}][{}]".format(face_zone[0], face_zone[1]))
        new_point_zone = turnAndFaceZone(point_zone, face_zone)
        if new_point_zone:
            point_zone = new_point_zone
            just_moved = True
