_Pi = False
_Pi = True

import logging
# Used only if this is run as main
_DEBUG = logging.INFO

# Import the packages we need for drawing and displaying images
from PIL import Image, ImageDraw

import multiprocessing
from multiprocessingloghandler import ChildMultiProcessingLogHandler, ParentMultiProcessingLogHandler
from random import randint
import io
import sys
import os
import time
import signal
import Queue
import threading

# This is how long to sleep in various threads between shutdown checks
POLL_SECS = 0.1

def signal_handler(sig, frame):
    global STOP
    if STOP:
        logging.debug("imageproducer SIGTERM")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        os.kill(os.getpid(), signal.SIGTERM)
    logging.debug("imageproducer STOP")
    STOP = True
signal.signal(signal.SIGINT, signal_handler)

class ImageAnalyzer(multiprocessing.Process):
    def __init__(self, image_queue, log_queue, logging_level):
        multiprocessing.Process.__init__(self)
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._exit = multiprocessing.Event()
        self._image_queue = image_queue
        self._stop_analyzing = False
        self._processing_queue = Queue.Queue()

    def process_image(self, image):
        logging.debug("Processing image")

    def _process_image_queue(self):
        logging.debug("image processing thread started")
        image = None
        while not self._stop_processing:
            try:
                t = self._processing_queue.get(False)
                logging.debug("processing queue had an entry")
                image, image_number = t
            except Queue.Empty:
                if not image:
                    logging.debug("Empty processing queue, waiting")
                    continue
                logging.info("Processing image {}".format(image_number))
                self.process_image(image)
                image = None
            except Exception, e:
                logging.exception("error processing")
        logging.debug("done processing")
 
    def stop(self):
        logging.debug("Image analyzer received shutdown")
        self._exit.set()

    def _init_logging(self):
        handler = ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._logging_level)

    def run(self):
        self._init_logging()
        logging.info("Image analyzer running")
        try:
            self._stop_receiving = False
            self._receiver = threading.Thread(target=self._get_images)
            self._receiver.start()

            self._stop_processing = False
            self._processor = threading.Thread(target=self._process_image_queue)
            self._processor.start()

            while not self._exit.is_set():
                time.sleep(POLL_SECS)
            logging.debug("Shutting down threads")
            self._stop_receiving = True
            self._receiver.join()
            self._stop_processing = True
            self._processor.join()
        except Exception, e:
            logging.exception("Error in analyzer main thread")
        finally:
            logging.debug("Exiting analyzer")
            sys.exit(0)

    def _cleanup(self):
        logging.debug("closing image queue")
        self._image_queue.close()

    def _get_images(self):
        "Put each incoming image on a queue, allow image processing to be asynchronous from receipt."
        logging.info("image consumer started")
        _, incoming_images = self._image_queue
        image_number = 0
        try:
            while not self._stop_receiving:
                image = incoming_images.recv()
                image_number += 1
                logging.info("Image {} received".format(image_number))
                self._processing_queue.put((image, image_number))
        except EOFError:
            logging.debug("Done receiving images")
