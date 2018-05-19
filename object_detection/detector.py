import logging
_DEBUG = logging.DEBUG

import sys
sys.path.append("..")
import numpy
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
import sys
import tarfile
import tensorflow as tf
import zipfile

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
    sys.path.append(".")
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
        self._detection_graph = tf.Graph()
        with self._detection_graph.as_default():
          od_graph_def = tf.GraphDef()
          with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
        
        
        # ## Loading label map
        # Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine
        
        label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)
        
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
                        output_dict = self._run_inference_for_single_image(frame)
                        self.processed_counter += 1
                        logging.debug("processed frame {}, stop: {}".format(self.processed_counter, self._stop_processing))
                        self._output_q.send((input_seq, frame, output_dict))
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
        with self._detection_graph.as_default():
            logging.debug("Setting up inference")
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
    
                logging.debug("Getting default tf graph")
                image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')
                # Run inference
                logging.debug("Running inference")
                output_dict = sess.run(tensor_dict,
                    feed_dict={image_tensor: np.expand_dims(image, 0)})
                logging.debug("Adjusting inference output")
    
                # all outputs are float32 numpy arrays, so convert types as appropriate
                output_dict['num_detections'] = int(output_dict['num_detections'][0])
                output_dict['detection_classes'] = output_dict[
                    'detection_classes'][0].astype(np.uint8)
                output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
                output_dict['detection_scores'] = output_dict['detection_scores'][0]
                if 'detection_masks' in output_dict:
                    output_dict['detection_masks'] = output_dict['detection_masks'][0]
            return output_dict

def receiveResults(results_pipe, category_index):
    incoming_results, _ = results_pipe
    results_counter = 0
    while True:
        logging.debug("waiting for detection results")
        try:
            input_seq, image, detection_dict = incoming_results.recv()
        except EOFError, e:
            logging.debug("EOF on results")
            break
        results_counter += 1
        logging.info("main received result {}, input seq {}".format(results_counter, input_seq))
        showDetectionResults(image, detection_dict, category_index)
    logging.info("main received {} results".format(results_counter))

def showDetectionResults(image, output_dict, category_index):
    # Visualization of the results of a detection.
    visualization_utils.visualize_boxes_and_labels_on_image_array(
        image,
        output_dict['detection_boxes'],
        output_dict['detection_classes'],
        output_dict['detection_scores'],
        category_index,
        instance_masks=output_dict.get('detection_masks'),
        use_normalized_coordinates=True,
        line_thickness=8)
    cv2.imshow('objects', image)
    cv2.waitKey(200)

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
    _, o  = detections_q
    i, _ = frames_q
    background_process = Detector(frames_q, detections_q, log_q, logging.getLogger('').getEffectiveLevel())
    receiver = threading.Thread(target=receiveResults, args=(detections_q, background_process.category_index))
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
            cv2_image = numpy.array(pil_image)
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
