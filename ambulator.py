# The motor controller portion of a K9
# Talks to a device over i2c that presumably controls 2 variable speed
# drive trains

import logging
_DEBUG=logging.DEBUG
_DEBUG=logging.INFO
MAX_SPEED = 1024
MIN_SPEED = -1 * MAX_SPEED
REST_SPEED = 0

import sys
import smbus

I2C_BUS = 1
SLAVE_DEVICE_ADDRESS = 0x15 #7 bit address (will be left shifted to add the read write bit)

class Ambulator():
    def __init__(self, slave_device):
        self._bus = smbus.SMBus(I2C_BUS)
        self._slave_device = slave_device

    def stop(self):
        self.right(REST_SPEED)
        self.left(REST_SPEED)

    def forward(self, speed):
        self.right(speed)
        self.left(speed)

    def backward(self, speed):
        self.right(-1*speed)
        self.left(-1*speed)

    def right(self, speed):
        speed = min(speed, MAX_SPEED)
        speed = max(speed, MIN_SPEED)
        self._send_command(CMD_RIGHT, speed)

    def left(self, speed):
        speed = min(speed, MAX_SPEED)
        speed = max(speed, MIN_SPEED)
        self._send_command(CMD_LEFT, speed)

    def _send_command(self, command, value):
        self._bus.write_i2c_block_data(self._slave_device, command, value)

    def get_values(self):
        command = 0
        value = self._bus.read_i2c_block_data(self._slave_device, command)
        logging.info("get_value returned {}".format(value))
        return value

def main():
  walker = Ambulator(SLAVE_DEVICE_ADDRESS)
  sys.exit(0)

logging.getLogger().setLevel(_DEBUG)
if __name__ == "__main__":
  main()
