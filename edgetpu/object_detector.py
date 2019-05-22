import argparse
import io
import time

import numpy as np
import picamera

from edgetpu.detection.engine import DetectionEngine



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
      '--model', help='File path of Tflite model.', required=True)
    parser.add_argument(
      '--label', help='File path of label file.', required=True)
    args = parser.parse_args()

    with open(args.label, 'r', encoding="utf-8") as f:
        pairs = (l.strip().split(maxsplit=1) for l in f.readlines())
        labels = dict((int(k), v) for k, v in pairs)

    engine = DetectionEngine(args.model)

    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 30
        _, width, height, channels = engine.get_input_tensor_shape()
        try:
            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream,
                                                 format='rgb',
                                                 use_video_port=True,
                                                 resize=(width, height)):
                stream.truncate()
                stream.seek(0)
                frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)
                start_ms = time.time()
  		results = engine.DetectWithImage(frame, threshold=0.05, keep_aspect_ratio=True,
                    relative_coord=False, top_k=10)

                elapsed_ms = time.time() - start_ms
                if results:
                    logging.info("frame has {} objects".format(len(results)))
                    for detected_object in results:
                        logging.info("label: {}, score: {}, bounds: {}".format(labels[detected_object.label_id], detected_object.score, obj.bounding_box.flatten().tolist()))
        finally:
            logging.info("done capturing")


if __name__ == '__main__':
    main()
