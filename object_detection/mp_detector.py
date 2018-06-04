import logging
_DEBUG = logging.DEBUG

import sys
sys.path.append("..")
import cv2
from PIL import Image
import Queue
import multiprocessingloghandler
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

MAIN_SEND_DELAY_SECS = 2.8

RESOLUTION=(640, 480)

def stop():
    global STOP
    STOP = True

def signal_handler(sig, frame):
    global STOP
    if STOP:
        logging.debug("KILLING")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.debug("SIGINT")
    stop()
signal.signal(signal.SIGINT, signal_handler)

class Detector(multiprocessing.Process):
    FRAME_POLLING_DELAY_SECS = 0.1

    def __init__(self, frames_i_q, detections_o_q, log_queue, log_level):
        super(Detector,self).__init__()
        self._output_writeback, self._output_q = detections_o_q
        self._input_writeback, self._input_q = frames_i_q
        self._exit = multiprocessing.Event()
        logging.debug("Event initially {}".format(self._exit.is_set()))
        self._log_queue = log_queue
        self._log_level = log_level
        self._stop_processing = False
        self._work_queue = Queue.Queue()
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
        
    def run(self):
        try:
            self._initLogging()
            logging.debug("***background active")
            logging.debug("process %s (%d)" % (self.name, os.getpid()))
            logging.debug("creating ingester")
            self._ingester = threading.Thread(target=self._ingestFrames)
            logging.debug("creating processor")
            self._processor = threading.Thread(target=self._processImages)
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
        self._stopIngesting()
        self._stopProcessing()
        logging.debug("joining processor")
        self._processor.join()
        self._exitReport()

    def _exitReport(self):
        logging.info("ingested {} frames".format(self.frame_counter))
        logging.info("processed {} frames".format(self.processed_counter))

    def _stopIngesting(self):
        self._stop_ingesting = True
        self._input_writeback.close()
        logging.debug("closed ingestion Pipe")

    def _stopProcessing(self):
        self._stop_processing = True

    def _ingestFrames(self):
        logging.debug("ingesting")
        try:
            while True:
                try:
                    logging.debug("waiting for frames to ingest")
                    seq, frame = self._input_q.recv()
                except EOFError, e:
                    logging.debug("EOF ingesting frames")
                    break
                logging.debug("ingested frame {} seq {}".format(self.frame_counter, seq))
                self.frame_counter += 1
                self._work_queue.put((seq, frame))
        except Exception, e:
            logging.error("Error ingesting frame {}".format(e))
        logging.debug("stopped ingesting")

    def _processImages(self):
        logging.debug("processing")
        frame_counter = 0
        while not self._stop_processing:
            logging.debug("waiting for ingested frames to process")
            skipped_frames = 0
            input_seq = None
            frame = None
            while not self._stop_processing:
                try:
                    input_seq, frame = self._work_queue.get(block=False)
                    skipped_frames += 1
                except Queue.Empty:
                    if frame is None:
                        skipped_frames = 0
                        time.sleep(self.__class__.FRAME_POLLING_DELAY_SECS)
                    else:
                        skipped_frames -= 1
                        frame_counter += 1
                        logging.debug("processing frame {}, input seq {}, skipped {} frames".format(frame_counter, input_seq, skipped_frames))
                        results = self._run_inference_for_single_image(frame)
                        self._apply_object_visualization_to_image(results) 
                        self.processed_counter += 1
                        logging.debug("processed frame {}, stop: {}".format(self.processed_counter, self._stop_processing))
                        self._output_q.send((input_seq, results))
                        logging.debug("sent frame {}".format(self.processed_counter))
                        break
                except Exception, e:
                    logging.warning("error getting work {}".format(e))
        logging.debug("closing output q")
        self._output_q.close()
        logging.debug("closed output q")
        logging.debug("stopped processing")

    # object  Detection
    def _run_inference_for_single_image(self, image):
###
        with self._detection_graph.as_default(): 
            with tf.Session(graph=self._detection_graph) as sess: 
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
                (boxes, scores, classes, num) = sess.run( 
                    [detection_boxes, detection_scores, detection_classes, num_detections], 
                    feed_dict={image_tensor: image_expanded}) 
        
                logging.debug("Ran tf inference")
                output_dict = {}
                output_dict['image'] = image
                output_dict['boxes'] = np.squeeze(boxes)
                output_dict['classes'] = np.squeeze(classes).astype(np.int32)
                output_dict['scores'] = np.squeeze(scores)
                return output_dict

    def _apply_object_visualization_to_image(self, detection_results):
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

def receiveResults(results_pipe, category_index):
    incoming_results, _ = results_pipe
    results_counter = 0
    while True:
        logging.debug("waiting for detection results")
        try:
            input_seq, detection_results = incoming_results.recv()
            results_counter += 1
            logging.info("main received result {}, input seq {}".format(results_counter, input_seq))
            showDetectionResults(detection_results, category_index)
        except EOFError, e:
            logging.debug("EOF on results")
            break
    logging.info("main received {} results".format(results_counter))

def showDetectionResults(results_dict, category_index):
    cv2.imshow('objects', results_dict['image'])
    cv2.waitKey(200)

if __name__ == '__main__':
    global STOP
    STOP = False
    sys.path.append(".")

    log_stream = sys.stderr
    log_q = multiprocessing.Queue(100)
    handler = multiprocessingloghandler.ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_q)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(_DEBUG)

    logging.debug("starting main")
    detections_q = multiprocessing.Pipe()
    frames_q = multiprocessing.Pipe()
    _, o  = detections_q
    i, _ = frames_q
    background_process = Detector(frames_q, detections_q, log_q, logging.getLogger('').getEffectiveLevel())
    receiver = threading.Thread(target=receiveResults, args=(detections_q, background_process._category_index))
    receiver.start()
    try:
        logging.debug("starting detector process")
        background_process.start()
        o.close()
        frame_counter = 0
        for image_filename in sys.argv[1:]:
            if STOP:
                logging.info("interrupted while sending frames")
                break
            pil_image = Image.open(image_filename)
            cv2_image = np.array(pil_image)
            frame_counter += 1
            logging.debug("sending image {}".format(image_filename))
            i.send((frame_counter, cv2_image))
            logging.debug("sent image {}".format(image_filename))
            time.sleep(MAIN_SEND_DELAY_SECS)
        logging.info("done sending frames")
    except Exception, e:
        logging.error("Error in main: {}".format(e))
    i.close()
    logging.debug("main waiting")
    time.sleep(5)
    logging.debug("shutting down")
    background_process.stop()
    logging.debug("ending main")
    logging.debug("waiting for background process to exit")
    background_process.join()
    logging.debug("logged: main done")
    cv2.destroyAllWindows()
    stop()
    logging.shutdown()
    logging.info("main exiting")
    sys.exit() 
