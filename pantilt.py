#
# sudo apt-get update
# sudo apt-get install pigpio python-pigpio python3-pigpio
#
import logging
import time

import pigpio
logging.getLogger().setLevel(logging.DEBUG)

pi = pigpio.pi()

# Describe our geometry
COLS = 4
ROWS = 3
DIMENSIONS=(COLS, ROWS)

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

def positionTo(zone):
    col, row = zone
    logging.debug("point to ({},{}) of [{},{}]".format(col,row,COLS,ROWS))
    pan(X_MIN + _COL_SPAN / COLS * (col + 0.5))
    tilt(Y_MIN + _ROW_SPAN / ROWS * (row + 0.5))

def pan(degrees):
    servo_write(PAN_PIN, degrees)

def tilt(degrees):
    servo_write(TILT_PIN, degrees)

def servo_write(pin, degrees):
    pi.set_servo_pulsewidth(pin, getPulseForDegrees(degrees))
    
def demo():
    logging.debug("Connecting to pigpio daemon")
    logging.debug("Connected")
    pi.set_mode(PAN_PIN, pigpio.OUTPUT)
    pi.set_mode(TILT_PIN, pigpio.OUTPUT)

    tilt(0)
    time.sleep(2)
    tilt(10)
    for x in range(DEGREE_MIN, DEGREE_MAX, 10):
      pan(x)
      time.sleep(0.2)
    tilt(90)
    for x in range(DEGREE_MAX, DEGREE_MIN, -10):
      pan(x)
      time.sleep(0.2)
    tilt(40)
    pan(60)
    pi.stop()


demo()
