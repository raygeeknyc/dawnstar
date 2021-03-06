import logging
import argparse

_DEBUG = logging.DEBUG

import sys
import psutil
sys.path.append("..")
import Queue
import multiprocessingloghandler
import StringIO
import multiprocessing
import threading
import time
import io
import os, signal
from PIL import Image
import cv2
import numpy as np
from detector import Detector

MAIN_SEND_DELAY_SECS = 5.0

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

class DetectorWorker(multiprocessing.Process):
    FRAME_POLLING_DELAY_SECS = 0.1

    def __init__(self, frames_i_q, detections_o_q, log_queue, log_level, visualize):
        super(DetectorWorker,self).__init__()
        self._output_writeback, self._output_q = detections_o_q
        self._input_writeback, self._input_q = frames_i_q
        self._exit = multiprocessing.Event()
        self._log_queue = log_queue
        self._log_level = log_level
        self._stop_processing = False
        self._work_queue = Queue.Queue()
        self.frame_counter = 0
        self.processed_counter = 0
        self._visualize = visualize

    def _InitLogging(self):
        handler = multiprocessingloghandler.ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._log_level)

    def stop(self):
        logging.debug("***background received shutdown")
        self._exit.set()

    def run(self):
        try:
            self._InitLogging()
            logging.debug("Process %s (%d)" % (self.name, os.getpid()))
            logging.debug("Creating Detector")
            self._detector = Detector()
            logging.debug("Creating ingester")
            self._ingester = threading.Thread(target=self._IngestFrames)
            logging.debug("Creating processor")
            self._processor = threading.Thread(target=self._ProcessImages)
            logging.debug("Starting processor")
            self._processor.start()
            logging.debug("Starting ingester")
            self._ingester.start()
            logging.debug("Waiting for exit event")
            self._exit.wait()
            logging.debug("Exit event received")
 
        except Exception, e:
            logging.error("Background exception: {}".format(e))
        logging.debug("Background terminating")
        self._StopIngesting()
        self._StopProcessing()
        logging.debug("Joining processor")
        self._processor.join()
        self._ExitReport()

    def _ExitReport(self):
        logging.info("Ingested {} frames".format(self.frame_counter))
        logging.info("Processed {} frames".format(self.processed_counter))

    def _StopIngesting(self):
        self._stop_ingesting = True
        self._input_writeback.close()
        logging.debug("Closed ingestion Pipe")

    def _StopProcessing(self):
        self._stop_processing = True

    def _IngestFrames(self):
        logging.debug("Ingesting")
        try:
            while True:
                try:
                    logging.debug("Waiting for frames to ingest")
                    seq, frame = self._input_q.recv()
                except EOFError, e:
                    logging.debug("EOF ingesting frames")
                    break
                logging.debug("Ingested frame {} seq {}".format(self.frame_counter, seq))
                self.frame_counter += 1
                self._work_queue.put((seq, frame))
        except Exception, e:
            logging.error("Error ingesting frame {}".format(e))
        logging.debug("Stopped ingesting")

    def _ProcessImages(self):
        logging.debug("Processing")
        frame_counter = 0
        while not self._stop_processing:
            logging.debug("Waiting for ingested frames to process")
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
                        logging.debug("Processing frame {}, input seq {}, skipped {} frames".format(frame_counter, input_seq, skipped_frames))
                        start = time.time()
                        results = self._detector.DetectObjects(frame)
                        logging.debug("Processed frame {}, input seq {}, skipped {} frames".format(frame_counter, input_seq, skipped_frames))
                        logging.debug("Detection took {}".format(time.time()-start))
                        if self._visualize:
                            self._detector.VisualizeResults(results) 
                        self.processed_counter += 1
                        self._output_q.send((input_seq, results))
                        logging.debug("sent frame {}".format(self.processed_counter))
                        break
                except Exception, e:
                    logging.warning("error getting work {}".format(e))
        logging.debug("closing output q")
        self._output_q.close()
        logging.debug("closed output q")
        self._detector.Cleanup()
        logging.debug("stopped processing")

def ReceiveResults(results_pipe, display_objects):
    incoming_results, _ = results_pipe
    results_counter = 0
    while True:
        logging.debug("waiting for detection results")
        try:
            input_seq, detection_results = incoming_results.recv()
            results_counter += 1
            logging.info("main received result {}, input seq {}".format(results_counter, input_seq))
            if display_objects:
                showDetectionResults(detection_results)
        except EOFError, e:
            logging.debug("EOF on results")
            break
    logging.info("main received {} results".format(results_counter))

def showDetectionResults(results_dict):
    cv2.imshow('objects', results_dict['image'])
    cv2.waitKey(200)

if __name__ == '__main__':
    global STOP
    STOP = False
    arg_parser = argparse.ArgumentParser(description='Object Detector Demo')
    arg_parser.add_argument('--display', action='store_true', default=False)
    arg_parser.add_argument('--images', nargs='+')
    arg_values = arg_parser.parse_args()
    display_objects = arg_values.display
    image_filenames = arg_values.images
    logging.debug('display_objects {}'.format(display_objects))
    logging.debug('images {}'.format(image_filenames))

    sys.path.append(".")

    log_stream = sys.stderr
    log_q = multiprocessing.Queue(100)
    handler = multiprocessingloghandler.ParentMultiProcessingLogHandler(logging.StreamHandler(log_stream), log_q)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(_DEBUG)

    logging.debug("starting main")
    logging.debug("Free vmem {}".format(psutil.virtual_memory().free))
    detections_q = multiprocessing.Pipe()
    frames_q = multiprocessing.Pipe()
    _, o  = detections_q
    i, _ = frames_q
    background_process = DetectorWorker(frames_q, detections_q, log_q, logging.getLogger('').getEffectiveLevel(), display_objects)
    receiver = threading.Thread(target=ReceiveResults, args=(detections_q, display_objects,))
    receiver.start()
    try:
        logging.debug("starting detector process")
        logging.debug("Free vmem {}".format(psutil.virtual_memory().free))
        background_process.start()
        logging.debug("started detector process")
        logging.debug("Free vmem {}".format(psutil.virtual_memory().free))
        o.close()
        frame_counter = 0
        for image_filename in image_filenames:
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
    if display_objects:
        cv2.destroyAllWindows()
    stop()
    logging.shutdown()
    logging.info("main exiting")
    logging.debug("Free vmem {}".format(psutil.virtual_memory().free))
    sys.exit() 
