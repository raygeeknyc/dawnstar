# The motor controller portion of a K9
# Talks to a device over i2c that presumably controls 2 variable speed
# drive trains

import time
import logging
_DEBUG=logging.INFO
_DEBUG=logging.DEBUG
MAX_SPEED = 2048
MIN_SPEED = -1 * MAX_SPEED
REST_SPEED = 0
NUDGE_SPEED =  (MAX_SPEED - REST_SPEED) / 4 + REST_SPEED

import sys
import smbus
import struct

I2C_BUS = 1
SLAVE_DEVICE_ADDRESS = 0x15 #7 bit address (will be left shifted to add the read write bit)

_CMD_RIGHT = ord('R')
_CMD_LEFT = ord('L')

class Ambulator():
    def __init__(self, slave_device_address = SLAVE_DEVICE_ADDRESS):
        self._bus = smbus.SMBus(I2C_BUS)
        self._slave_device_address = slave_device_address
        logging.info("Motor controller at {} device# {}".format(I2C_BUS, slave_device_address))

    def stop(self):
        self.right(REST_SPEED)
        self.left(REST_SPEED)

    def forward(self, speed):
        self.left(speed)
        self.right(speed)

    def backward(self, speed):
        self.right(-1*speed)
        self.left(-1*speed)

    def right(self, speed):
        speed = min(speed, MAX_SPEED)
        speed = max(speed, MIN_SPEED)
        self._send_command(_CMD_RIGHT, speed)

    def left(self, speed):
        speed = min(speed, MAX_SPEED)
        speed = max(speed, MIN_SPEED)
        self._send_command(_CMD_LEFT, speed)

    def nudge_left(self):
        self.right(NUDGE_SPEED)
        self.left(-1 * NUDGE_SPEED)

    def nudge_right(self):
        self.left(NUDGE_SPEED)
        self.right(-1 * NUDGE_SPEED)

    def _send_command(self, command, value):
        high_byte = value & 0xFF
        low_byte = (value >> 8) & 0xFF
        self._bus.write_i2c_block_data(self._slave_device_address, command, [high_byte, low_byte])

    def get_values(self):
        command = 0
        bytes = self._bus.read_i2c_block_data(self._slave_device_address, command)
        logging.debug("Received {} bytes".format(len(bytes)))
        values = []
        for position in range(0, len(bytes), 2):
            value = struct.unpack('<h', ''.join([chr(i) for i in bytes[position:position+2]]))[0]
            values.append(value)
        return values

def main():
  walker = Ambulator()
  walker.backward(127)
  values = walker.get_values()
  logging.debug("Values: {}".format(values))
  left_speed = values[0]
  right_speed = values[1]
  walker.left(678)
  walker.right(-105)
  values = walker.get_values()
  logging.debug("Values: {}".format(values))
  walker.left(-1000)
  walker.right(-3000)
  values = walker.get_values()
  logging.debug("Values: {}".format(values))
  sys.exit(0)

logging.getLogger().setLevel(_DEBUG)
if __name__ == "__main__":
  main()
