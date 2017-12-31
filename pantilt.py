#
# sudo apt-get update
# sudo apt-get install pigpio python-pigpio python3-pigpio
#
import logging
import time

import pigpio
logging.getLogger().setLevel(logging.DEBUG)

pi = pigpio.pi()

# Describe our hardware setup, pin numbers are BCM indices
PAN_PIN = 14
TILT_PIN = 15

# Servo dependent values
PULSE_MIN = 900
PULSE_MAX = 1900
PULSE_STEP = 100
_PULSE_RANGE = PULSE_MAX + 1 - PULSE_MIN
logging.debug("pulses: {}".format(_PULSE_RANGE))

DEGREE_MIN = 0
DEGREE_MAX = 110
_DEGREE_RANGE = DEGREE_MAX + 1 - DEGREE_MIN
logging.debug("degrees: {}".format(_DEGREE_RANGE))

def getPulseForDegrees(degrees):
  pulse = int(PULSE_MIN+(((degrees - DEGREE_MIN)*1.0 / _DEGREE_RANGE
    * _PULSE_RANGE) + 1) // PULSE_STEP * PULSE_STEP)
  pulse = max(pulse, PULSE_MIN)
  pulse = min(pulse, PULSE_MAX)
  logging.debug("degree {} is pulse {}".format(degrees, pulse))
  return pulse

def panToPercentage(percent):
  logging.debug("panning to {} percent".format(percent))
  if percent == 0:
    panToDegrees(DEGREE_MIN)
  else:
    panToDegrees((percent/100.0) * _DEGREE_RANGE + DEGREE_MIN)

def tiltToPercentage(percent):
  logging.debug("tilting to {} percent".format(percent))
  if percent == 0:
    tiltToDegrees(DEGREE_MIN)
  else:
    tiltToDegrees((percent/100.0) * _DEGREE_RANGE + DEGREE_MIN)

def panToDegrees(degrees):
    servo_write(PAN_PIN, degrees)

def tiltToDegrees(degrees):
    servo_write(TILT_PIN, degrees)

def servo_write(pin, degrees):
    pi.set_servo_pulsewidth(pin, getPulseForDegrees(degrees))
    
def demo():
    logging.debug("Connecting to pigpio daemon")
    logging.debug("Connected")
    pi.set_mode(PAN_PIN, pigpio.OUTPUT)
    pi.set_mode(TILT_PIN, pigpio.OUTPUT)

    tiltToPercentage(0)
    time.sleep(2)
    tiltToPercentage(20)
    for x in range(10, 100, 10):
      panToPercentage(x)
      time.sleep(0.2)
    tiltToPercentage(50)
    for x in range(100, 0, -10):
      panToPercentage(x)
      time.sleep(0.2)
    tiltToPercentage(50)
    panToPercentage(50)
    pi.stop()

demo()
