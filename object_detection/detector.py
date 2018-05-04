import logging
_DEBUG = logging.DEBUG
import numpy
from PIL import Image

import multiprocessingloghandler
import StringIO
import multiprocessing
import threading
from collections import deque
import time
import io
import sys
import os, signal
from utils import label_map_util

import numpy as np
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

MAIN_POLL_DELAY_SECS = 1

RESOLUTION=(640, 480)


def signal_handler(sig, frame):
    global STOP
    if STOP:
        logging.debug("KILLING")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.debug("SIGINT")
    STOP = True
signal.signal(signal.SIGINT, signal_handler)

class Detector(multiprocessing.Process):
    sys.path.append(".")
    FRAME_POLLING_DELAY_SECS = 0.1

    def __init__(self, frames_i_q, detections_o_q, log_queue, log_level):
        super(Detector,self).__init__()
        o, _ = detections_o_q
        _, i = frames_i_q
        self._exit = multiprocessing.Event()
        logging.debug("Event initially {}".format(self._exit.is_set()))
        self._log_queue = log_queue
        self._log_level = log_level
        self._output_q = o
        self._input_q = i
        self._stop_processing = False
        self._work_queue = deque()
        self.frame_counter = 0
        self.processed_counter = 0
        self._PrepareModel()

    def _initLogging(self):
        handler = multiprocessingloghandler.ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._log_level)

    def stop(self):
        logging.debug("***background received shutdown")
        self._exit.set()

    def _PrepareModel(self):
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
        
        label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
        category_index = label_map_util.create_category_index(categories)
        
    def run(self):
        try:
            self._initLogging()
            logging.debug("***background active")
            logging.debug("process %s (%d)" % (self.name, os.getpid()))
            logging.debug("creating ingester")
            self._ingester = threading.Thread(target=self.ingestFrames)
            logging.debug("creating processor")
            self._processor = threading.Thread(target=self.performWork)
            logging.debug("starting processor")
            self._processor.start()
            logging.debug("starting ingester")
            self._ingester.start()
            logging.debug("waiting for exit event")
            self._exit.wait()
            logging.debug("exit event received")
 
        except Exception, e:
            logging.error("***background exception: {}".format(e))
        logging.debug("***background terminating")
        self._stopProcessing()
        self._processor.join()
        self._exitReport()

    def _exitReport(self):
        logging.info("ingested {} frames".format(self.frame_counter))
        logging.info("processed {} frames".format(self.processed_counter))

    def _stopProcessing(self):
        self._stop_processing = True

    def ingestFrames(self):
        logging.debug("ingesting")
        try:
            while True:
                logging.debug("waiting to receive frame")
                frame = self._input_q.recv()
                self.frame_counter += 1
                logging.debug("ingested frame")
                self._work_queue.append(frame) 
            time.sleep(self.__class__.FRAME_POLLING_DELAY_SECS)
        except Exception, e:
            logging.error("Error ingesting frame {}".format(e))
        logging.debug("stopped ingesting")

    def performWork(self):
        logging.debug("performing")
        while not self._stop_processing:
            try:
                frame = self._work_queue.pop() 
                logging.debug("processed frame")
                self.processed_counter += 1
                self._output_q.send("i={}".format(frame))
            except IndexError:
                pass
        logging.debug("stopped performing")

if __name__ == '__main__':
    global STOP
    STOP = False

    log_stream = sys.stderr
    log_q = multiprocessing.Queue(100)
    handler = multiprocessingloghandler.ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_q)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(_DEBUG)

    logging.debug("starting main")
    detections_q = multiprocessing.Pipe()
    frames_q = multiprocessing.Pipe()
    background_process = Detector(frames_q, detections_q, log_q, logging.getLogger('').getEffectiveLevel())
    results_counter = 0
    try:
        _, o = detections_q
        i, _ = frames_q
        logging.debug("starting detector process")
        background_process.start()
        c = 0
        pil_image = Image.open('../phone-addicts.jpg')
        cv2_image = numpy.array(pil_image)

        i.send(cv2_image)
        i.send(cv2_image)
        i.send(cv2_image)
        while not STOP:
            logging.info("waiting for detection results")
            message = o.recv()
            results_counter += 1
            logging.info("main received message {}: {}".format(results_counter, message))
            time.sleep(MAIN_POLL_DELAY_SECS)
          
    except Exception, e:
        logging.error("Error in main: {}".format(e))
    logging.info("ending main")
    logging.debug("received {} results".format(results_counter))
    background_process.stop()
    logging.info("waiting for background process to exit")
    time.sleep(2)
    background_process.join()
    time.sleep(2)
    logging.info("logged: main done")
    logging.shutdown()
    logging.info("main post-logging")
    sys.exit() 
