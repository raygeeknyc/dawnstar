# If we're not a a Pi (i.e. testing on a laptop) minimally mock up the Servo class
_ON_PI = False
if _ON_PI:
  from gpiozero import Servo
else:
  class Servo(object):
    def __init__(self, pin, min_pulse_width, max_pulse_width, frame_width):
      self._pin = pin
      self._min_pulse = min_pulse_width
      self._max_pulse = max_pulse_width
      self._frame = frame_width
      self.value = None
      self._attached = True

    def detach(self):
      self._attached = False

import logging
import time

logging.getLogger().setLevel(logging.DEBUG)

# Describe our hardware setup, pin numbers are BCM indices
PAN_PIN = 14
TILT_PIN = 15

PULSE_MIN = 0.9/1000
PULSE_MAX = 1.9/1000
SERVO_STEPS = 20
_PULSE_STEP = (PULSE_MAX - PULSE_MIN) / SERVO_STEPS
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

def pointTo(pan_tilt_directions, servo_state):
    "Adjust servo state (pan,tilt) by pan_tilt_directions (pan, tilt) steps."
    if servo_state[0] == None:
        servo_state[0] = PULSE_MIN
        servo_state[1] = PULSE_MIN
    if (pan_tilt_directions[0] == 0 and pan_tilt_directions[1] == 0): return
    new_pan = servo_state[0] + pan_tilt_directions[0] * _PULSE_STEP
    new_tilt = servo_state[1] + pan_tilt_directions[1] * _PULSE_STEP
    if new_pan < PULSE_MIN:
        new_pan = PULSE_MIN
    if new_pan > PULSE_MAX:
        new_pan = PULSE_MAX
    if new_tilt	 < PULSE_MIN:
        new_tilt = PULSE_MIN
    if new_tilt > PULSE_MAX:
        new_tilt = PULSE_MAX
    servo_state[0] = new_pan
    servo_state[1] = new_tilt
    
def demo():
    panToPercentage(0)
    tiltToPercentage(0)
    time.sleep(2)
    for x in range(0, 105, 5):
      panToPercentage(x)
      time.sleep(0.1)
    time.sleep(2)
    for x in range(0, 105, 5):
      tiltToPercentage(x)
      time.sleep(0.1)
    for x in range(100, -5, -5):
      panToPercentage(x)
      time.sleep(0.1)
    tiltToPercentage(50)
    panToPercentage(50)
    time.sleep(0.2)
    pan_servo.detach()
    tilt_servo.detach()

global tilt_servo
global pan_servo

if __name__ == '__main__':
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
