import logging
import argparse
_DEBUG = logging.DEBUG

import sys
import psutil
sys.path.append("..")
import cv2
from PIL import Image
import Queue
import StringIO
import multiprocessing
import threading
import time
import io
import os, signal
from utils import label_map_util
from utils import visualization_utils
import numpy as np
import six.moves.urllib as urllib
import tarfile
import tensorflow as tf

RESOLUTION=(640, 480)

class Detector(object):
    def __init__(self):
        super(Detector,self).__init__()
        self.processed_counter = 0
        self._PrepareModel()
        self._StartSession()

    def _PrepareModel(self):
        # By default we use an "SSD with Mobilenet" model here. See the [detection model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) for a list of other models that can be run out-of-the-box with varying speeds and accuracies.

        # What model to download.
        # List of the strings that is used to add correct label for each box.
        NUM_CLASSES = 90 
        GRAPH_FILENAME = 'frozen_inference_graph.pb'
        LABEL_FILENAME = 'mscoco_label_map.pbtxt'
        MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017' #fast 
        MODEL_FILE = MODEL_NAME + '.tar.gz' 
        DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/' 
        PATH_TO_CKPT = os.path.join(MODEL_NAME, GRAPH_FILENAME)
        PATH_TO_LABELS = os.path.join('data', LABEL_FILENAME)
        
        # ## Download Model if it's not present 
        if not os.path.exists(MODEL_NAME):
          logging.info("Downloading {}".format(MODEL_FILE))
          opener = urllib.request.URLopener()
          opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
          logging.info("done")
          sys.exit(-1)
          logging.info("Unpacking {}".format(MODEL_NAME))
          tar_file = tarfile.open(MODEL_FILE)
          for file in tar_file.getmembers():
            file_name = os.path.basename(file.name)
            if GRAPH_FILENAME in file_name:
              tar_file.extract(file, os.getcwd())
          try:
            logging.info("Removing {}".format(MODEL_FILE))
            os.remove(MODEL_FILE)
          except OSError:
            logging.error("Error removing {}".format(MODEL_FILE))
        
        self._detection_graph = tf.Graph()
        with self._detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        self._label_map = label_map_util.load_labelmap(PATH_TO_LABELS) 
        self._categories = label_map_util.convert_label_map_to_categories(self._label_map, max_num_classes=NUM_CLASSES, use_display_name=True) 
        self._category_index = label_map_util.create_category_index(self._categories) 

    def _StartSession(self):
        logging.debug("Starting tf session")
        with self._detection_graph.as_default(): 
            self._tf_session =  tf.Session(graph=self._detection_graph)
        
    def Cleanup(self):
        self._EndSession()

    def _EndSession(self):
        self._tf_session.close()
        
    def ExitReport(self):
        logging.info("Processed {} frames".format(self.processed_counter))

    def DetectObjects(self, image):
        self.processed_counter += 1
        logging.debug("processing frame {}".format(self.processed_counter))
        start = time.time()
        results = self._RunInferenceForImage(image)
        logging.debug("Detection took {}".format(time.time()-start))
        return results

    def VisualizeResults(self, results):
        logging.debug("Visualizing frame {}".format(self.processed_counter))
        start = time.time()
        self._ApplyObjectVisualizationToImage(results) 
        logging.debug("Vis took {}".format(time.time()-start))

    # object  Detection
    def _RunInferenceForImage(self, image):
###
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3] 
                image_expanded = np.expand_dims(image, axis=0) 
                     
                # Definite input and output Tensors for detection_graph 
                image_tensor = self._detection_graph.get_tensor_by_name('image_tensor:0') 
                     
                # Each box represents a part of the image where a particular object was detected. 
                detection_boxes = self._detection_graph.get_tensor_by_name('detection_boxes:0') 
                     
                # Each score represent how level of confidence for each of the objects. 
                # Score is shown on the result image, together with the class label. 
                detection_scores = self._detection_graph.get_tensor_by_name('detection_scores:0') 
                     
                detection_classes = self._detection_graph.get_tensor_by_name('detection_classes:0') 
                     
                num_detections = self._detection_graph.get_tensor_by_name('num_detections:0') 
                     
                logging.debug("Running tf inference")
                (boxes, scores, classes, num) = self._tf_session.run( 
                    [detection_boxes, detection_scores, detection_classes, num_detections], 
                    feed_dict={image_tensor: image_expanded}) 
        
                logging.debug("Ran tf inference")
                output_dict = {}
                output_dict['image'] = image
                output_dict['boxes'] = np.squeeze(boxes)
                output_dict['classes'] = np.squeeze(classes).astype(np.int32)
                output_dict['scores'] = np.squeeze(scores)
                return output_dict

    def _ApplyObjectVisualizationToImage(self, detection_results):
        logging.debug('Visualization detected objects')
        visualization_utils.visualize_boxes_and_labels_on_image_array( 
              detection_results['image'], 
              detection_results['boxes'], 
              detection_results['classes'], 
              detection_results['scores'], 
              self._category_index, 
              use_normalized_coordinates=True, 
              line_thickness=8) 
        logging.debug('Visualized detected objects')

def ShowDetectionResults(results_dict):
    cv2.imshow('objects', results_dict['image'])
    cv2.waitKey(200)

if __name__ == '__main__':
    logging.getLogger().setLevel(_DEBUG)
    arg_parser = argparse.ArgumentParser(description='Object Detector Demo')
    arg_parser.add_argument('--display', action='store_true', default=False)
    arg_parser.add_argument('--images', nargs='+')
    arg_values = arg_parser.parse_args()
    display_objects = arg_values.display
    image_filenames = arg_values.images
    logging.debug('display_objects {}'.format(display_objects))
    logging.debug('images {}'.format(image_filenames))

    sys.path.append(".")

    logging.debug("starting main")
    logging.debug("Free vmem {}".format(psutil.virtual_memory().free))
    detector = Detector()
    try:
        logging.debug("Running detection")
        frame_counter = 0
        for image_filename in image_filenames:
            pil_image = Image.open(image_filename)
            cv2_image = np.array(pil_image)
            logging.debug("Processing image {}".format(image_filename))
            results = detector.DetectObjects(cv2_image)
            if display_objects:
                detector.VisualizeResults(results)
                ShowDetectionResults(results)
        logging.info("done sending frames")
    except KeyboardInterrupt, e:
        logging.info("interrupted while sending frames")
    except Exception, e:
        logging.error("Error in main: {}".format(e))
    finally:
        detector.Cleanup()
        detector.ExitReport()
    if display_objects:
        cv2.destroyAllWindows()

    logging.info("main exiting")
    logging.debug("Free vmem {}".format(psutil.virtual_memory().free))
    sys.exit() 
