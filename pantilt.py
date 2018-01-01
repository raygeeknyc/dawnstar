#
from gpiozero import Servo
#

import logging
import time

logging.getLogger().setLevel(logging.DEBUG)

# Describe our hardware setup, pin numbers are BCM indices
PAN_PIN = 14
TILT_PIN = 15

PULSE_MIN = 0.9/1000
PULSE_MAX = 1.9/1000
PULSE_WIDTH = 20.0/1000
logging.debug("min {} max{} step {}".format(PULSE_MIN, PULSE_MAX, PULSE_WIDTH))

def panToPercentage(percent):
  global pan_servo

  logging.debug("panning to {} percent".format(percent))
  if percent == 0:
    pan_servo.value = -1.0
  else:
    value = (percent/100.0)/.5 - 1
    logging.debug(value)
    pan_servo.value = value

def tiltToPercentage(percent):
  global tilt_servo

  logging.debug("tilting to {} percent".format(percent))
  if percent == 0:
    tilt_servo.value = -1.0
  else:
    value = (percent/100.0)/.5 - 1
    logging.debug(value)
    tilt_servo.value = value

def demo():
    panToPercentage(0)
    tiltToPercentage(0)
    time.sleep(2)
    for x in range(0, 110, 10):
      panToPercentage(x)
      time.sleep(0.2)
    time.sleep(2)
    for x in range(0, 110, 10):
      tiltToPercentage(x)
      time.sleep(0.5)
    for x in range(100, -10, -10):
      panToPercentage(x)
      time.sleep(0.2)
    tiltToPercentage(50)
    panToPercentage(50)
    time.sleep(0.2)
    pan_servo.detach()
    tilt_servo.detach()

global tilt_servo
global pan_servo
tilt_servo = Servo(TILT_PIN, min_pulse_width=PULSE_MIN, max_pulse_width=PULSE_MAX, frame_width=PULSE_WIDTH)
pan_servo = Servo(PAN_PIN, min_pulse_width=PULSE_MIN, max_pulse_width=PULSE_MAX, frame_width=PULSE_WIDTH)

logging.info("Starting demo loop")
while True:
    try:
        demo()
        time.sleep(10)
        pan_servo.detach()
        tilt_servo.detach()
    except KeyboardInterrupt:
        logging.info("interrupted, exiting")
        break
pan_servo.detach()
tilt_servo.detach()
logging.debug("Done")
