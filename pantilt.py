#
# sudo apt-get update
# sudo apt-get install pigpio python-pigpio python3-pigpio
#

import pigpio
import time

PAN_PIN = 20
TILT_PIN = 21
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

print("Tilt setting to: ",pi.set_servo_pulsewidth(TILT_PIN, 1000))
print("set to: ",pi.get_servo_pulsewidth(TILT_PIN))

print("Pan setting to: ",pi.set_servo_pulsewidth(PAN_PIN, 1000))
print("set to: ",pi.get_servo_pulsewidth(PAN_PIN))

time.sleep(1)
print("Pan setting to: ",pi.set_servo_pulsewidth(PAN_PIN, 2000))
print("set to: ",pi.get_servo_pulsewidth(PAN_PIN))


time.sleep(1)

pi.stop()
