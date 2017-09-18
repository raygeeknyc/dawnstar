#
# sudo apt-get update
# sudo apt-get install pigpio python-pigpio python3-pigpio
#

# Describe our geometry
COLS = 4
ROWS = 3
DIMENSIONS=(COLS, ROWS)

# Describe our hardware setup, pin numbers are BCM indices
PAN_PIN = 20
TILT_PIN = 21

# Servo dependent values
X_MIN = 1100
X_MAX = 1900
Y_MIN = 1100
Y_MAX = 1900
SERVO_DURATION_STEP = 100
_COL_SPAN = (X_MAX - X_MIN)
_ROW_SPAN = (Y_MAX - Y_MIN)

def positionTo(zone):
    col, row = zone
    logging.debug("point to ({},{}) of [{},{}]".format(col,row,COLS,ROWS))
    pan(X_MIN + _COL_SPAN / COLS * (col + 0.5))
    tilt(Y_MIN + _ROW_SPAN / ROWS * (row + 0.5))

def pan(duration):
    servo_write(PAN_PIN, duration)

def tilt(duration):
    servo_write(TILT_PIN, duration)

def servo_write(pin, duration):
    actual_duration = int(duration/SERVO_DURATION_STEP)*SERVO_DURATION_STEP
    pi.set_servo_pulsewidth(pin, actual_duration)
    
pi = pigpio.pi()
pi.set_mode(PAN_PIN, pigpio.OUTPUT)
pi.set_mode(TILT_PIN, pigpio.OUTPUT)

print ("Pan mode: ", pi.get_mode(PAN_PIN))
print("setting to: ",pi.set_servo_pulsewidth(PAN_PIN, 1500))
print("set to: ",pi.get_servo_pulsewidth(PAN_PIN))

time.sleep(1)
print ("Tilt mode: ", pi.get_mode(TILT_PIN))
print("setting to: ",pi.set_servo_pulsewidth(TILT_PIN, 1500))
print("set to: ",pi.get_servo_pulsewidth(TILT_PIN))

time.sleep(1)

print("Tilt setting to: ",pi.set_servo_pulsewidth(TILT_PIN, 1100))
print("set to: ",pi.get_servo_pulsewidth(TILT_PIN))

time.sleep(1)
print("Pan setting to: ",pi.set_servo_pulsewidth(PAN_PIN, 1100))
print("set to: ",pi.get_servo_pulsewidth(PAN_PIN))

time.sleep(1)
print("Tilt setting to: ",pi.set_servo_pulsewidth(TILT_PIN, 1900))
print("set to: ",pi.get_servo_pulsewidth(TILT_PIN))

time.sleep(1)
print("Pan setting to: ",pi.set_servo_pulsewidth(PAN_PIN, 1900))
print("set to: ",pi.get_servo_pulsewidth(PAN_PIN))


time.sleep(1)

pi.stop()
