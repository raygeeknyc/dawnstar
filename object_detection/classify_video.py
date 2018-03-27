# # Object Detection Demo
# Welcome to the object detection inference walkthrough!  This notebook will walk you step by step through the process of using a pre-trained model to detect objects in an image. Make sure to follow the [installation instructions](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md) before you start.

import cv2
import time
import logging
import sys
logging.getLogger().setLevel(logging.INFO)


RESOLUTION=(640, 480)
_videostream = cv2.VideoCapture(0)
_videostream.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
_videostream.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
if not _videostream.isOpened():
  logging.error("Video camera not opened")
  sys.exit(255)

def getFrame():
  _, frame = _videostream.read()

  return frame

def closeVideo():
  _videostream.release()

import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from PIL import Image

logging.info("starting")
sys.path.append("..")
from object_detection.utils import ops as utils_ops

if tf.__version__ < '1.4.0':
  raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')

from utils import label_map_util
from utils import visualization_utils as vis_util

# # Model preparation 
# 
# Any model exported using the `export_inference_graph.py` tool can be loaded here simply by changing `PATH_TO_CKPT` to point to a new .pb file.  
# 
# By default we use an "SSD with Mobilenet" model here. See the [detection model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) for a list of other models that can be run out-of-the-box with varying speeds and accuracies.

# What model to download.
MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

# ## Download Model if it's not present 
if not os.path.exists(MODEL_NAME):
  logging.info("Downloading {}".format(MODEL_FILE))
  opener = urllib.request.URLopener()
  opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
  logging.info("Unpacking {}".format(MODEL_NAME))
  tar_file = tarfile.open(MODEL_FILE)
  for file in tar_file.getmembers():
    file_name = os.path.basename(file.name)
    if 'frozen_inference_graph.pb' in file_name:
      tar_file.extract(file, os.getcwd())
  try:
    logging.info("Removing {}".format(MODEL_FILE))
    os.remove(MODEL_FILE)
  except OSError:
    logging.error("Error removing {}".format(MODEL_FILE))

# ## Load a (frozen) Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')


# ## Loading label map
# Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine

# In[87]:


label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


# ## Helper code

def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)


# # Detection
def run_inference_for_single_image(image, graph):
  with graph.as_default():
    config = tf.ConfigProto()
    with tf.Session() as sess:
      # Get handles to input and output tensors
      ops = tf.get_default_graph().get_operations()
      all_tensor_names = {output.name for op in ops for output in op.outputs}
      tensor_dict = {}
      for key in [
          'num_detections', 'detection_boxes', 'detection_scores',
          'detection_classes', 'detection_masks'
      ]:
        tensor_name = key + ':0'
        if tensor_name in all_tensor_names:
          tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
              tensor_name)
      if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[0], image.shape[1])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.5), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
      image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

      # Run inference
      start = time.time()
      output_dict = sess.run(tensor_dict,
                             feed_dict={image_tensor: np.expand_dims(image, 0)})
      inference_time = time.time() - start

      # all outputs are float32 numpy arrays, so convert types as appropriate
      output_dict['num_detections'] = int(output_dict['num_detections'][0])
      output_dict['detection_classes'] = output_dict[
          'detection_classes'][0].astype(np.uint8)
      output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
      output_dict['detection_scores'] = output_dict['detection_scores'][0]
      if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]
  return (output_dict, inference_time)

frame = getFrame()
logging.debug("images {}".format(frame.shape))
logging.debug("Capturing frames")
frames=0
capture_time = 0
inference_time = 0
detection_time = 0
per_object_time = 0
object_count = 0
while(True):
  # Capture frame-by-frame
  start = time.time()
  frame = getFrame()
  capture_time += (time.time() - start)
  frames += 1
  # the array based representation of the image will be used later in order to prepare the
  # result image with boxes and labels on it.
  image_np = frame
  # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
  image_np_expanded = np.expand_dims(image_np, axis=0)
  # Actual detection.
  start = time.time()
  output_dict, _inference_dur = run_inference_for_single_image(image_np, detection_graph)
  _detection_dur = (time.time() - start)
  inference_time += _inference_dur
  detection_time += _detection_dur
  confident_scores = [score for score in np.squeeze(output_dict['detection_scores']) if score >= 0.5]
  object_count += len(confident_scores)
  _per_detection_time = _detection_dur / len(confident_scores) if len(confident_scores) > 0 else 0
  per_object_time += _per_detection_time
  
  # Visualization of the results of a detection.
  vis_util.visualize_boxes_and_labels_on_image_array(
      image_np,
      output_dict['detection_boxes'],
      output_dict['detection_classes'],
      output_dict['detection_scores'],
      category_index,
      instance_masks=output_dict.get('detection_masks'),
      use_normalized_coordinates=True,
      line_thickness=8)
  start_time = time.time()
  cv2.imshow('frame',frame)

  if cv2.waitKey(1) & 0xFF == ord('q'):
      break
# When everything done, release the capture
closeVideo()
logging.info("frames: {}".format(frames))
logging.info("objects: {}".format(object_count))
logging.info("capture_time: {}".format(capture_time))
logging.info("detection_time: {}".format(detection_time))
logging.info("inference_time: {}".format(inference_time))
logging.info("per_frame_time: {}".format(detection_time/frames))
logging.info("average per-frame detection_time: {}".format(detection_time/frames))
logging.info("average per-frame inference_time: {}".format(inference_time/frames))
logging.info("average per-frame per_object_time: {}".format(per_object_time/frames))
cv2.destroyAllWindows()
