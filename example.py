import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import time
import zipfile
import cv2

from picamera.array import PiRGBArray

import picamera

from collections import defaultdict
from io import StringIO
from PIL import Image

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

###
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017' #fast 
#MODEL_NAME = 'faster_rcnn_resnet101_coco_11_06_2017' #medium speed 
MODEL_FILE = MODEL_NAME + '.tar.gz' 
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/' 

PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb' 

PATH_TO_LABELS = os.path.join('/home/pi/Documents/workspace/tf/models/research/object_detection/data', 'mscoco_label_map.pbtxt') 
 
NUM_CLASSES = 90 
 
IMAGE_SIZE = (12, 8) 
  
fileAlreadyExists = os.path.isfile(PATH_TO_CKPT) 
if fileAlreadyExists:
     print('Frozen inference graph {} already present'.format(PATH_TO_CKPT))
else:
     print('Downloading frozen inference graph') 
     opener = urllib.request.URLopener() 
     opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE) 
     print('Downloaded frozen inference graph') 
     tar_file = tarfile.open(MODEL_FILE) 
     for file in tar_file.getmembers(): 
         file_name = os.path.basename(file.name) 
         if 'frozen_inference_graph.pb' in file_name: 
             tar_file.extract(file, os.getcwd()) 
             print('Extracted inference graph in {}'.format(os.getcwd))
###
detection_graph = tf.Graph() 
with detection_graph.as_default(): 
    od_graph_def = tf.GraphDef() 
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid: 
        serialized_graph = fid.read() 
        od_graph_def.ParseFromString(serialized_graph) 
        tf.import_graph_def(od_graph_def, name='') 

label_map = label_map_util.load_labelmap(PATH_TO_LABELS) 
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True) 
category_index = label_map_util.create_category_index(categories) 

###
camera = picamera.PiCamera()
camera.resolution = (1280, 960)
camera.framerate = 30
camera.vflip = True
rawCapture = PiRGBArray(camera, size = (1280, 960))

###
with detection_graph.as_default(): 
    with tf.Session(graph=detection_graph) as sess: 
        try:    
            for frame in camera.capture_continuous(rawCapture, format="bgr"):
                image_np = np.array(frame.array)
                     
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3] 
                image_np_expanded = np.expand_dims(image_np, axis=0) 
                     
                # Definite input and output Tensors for detection_graph 
                image_tensor = detection_graph.get_tensor_by_name('image_tensor:0') 
                     
                # Each box represents a part of the image where a particular object was detected. 
                detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0') 
                     
                # Each score represent how level of confidence for each of the objects. 
                # Score is shown on the result image, together with the class label. 
                detection_scores = detection_graph.get_tensor_by_name('detection_scores:0') 
                     
                detection_classes = detection_graph.get_tensor_by_name('detection_classes:0') 
                     
                num_detections = detection_graph.get_tensor_by_name('num_detections:0') 
                     
                print('Running detection..') 
                start = time.time()
                (boxes, scores, classes, num) = sess.run( 
                    [detection_boxes, detection_scores, detection_classes, num_detections], 
                    feed_dict={image_tensor: image_np_expanded}) 
        
                print('Detection took {} seconds'.format(time.time() - start))
                print('Visualizing..') 
                start = time.time()
                vis_util.visualize_boxes_and_labels_on_image_array( 
                      image_np, 
                      np.squeeze(boxes), 
                      np.squeeze(classes).astype(np.int32), 
                      np.squeeze(scores), 
                      category_index, 
                      use_normalized_coordinates=True, 
                      line_thickness=8) 
                print('Visualization took {} seconds'.format(time.time() - start))
        
                im = Image.fromarray(image_np)
                im.save("detected.jpeg")
                rawCapture.truncate(0)
        except KeyboardInterrupt:
            print("exiting")
    camera.close()
    print('exiting') 
