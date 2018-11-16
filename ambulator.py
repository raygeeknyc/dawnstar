# The motor controller portion of a K9
# Talks to a device over i2c that presumably controls 2 variable speed drive trains

import logging
_DEBUG=logging.DEBUG
_DEBUG=logging.INFO

import os
import sys
import time
import smbus

I2C_BUS = 1
DEVICE_ADDRESS = 0x15 #7 bit address (will be left shifted to add the read write bit)

class Ambulator():
    def __init__(self, slave_device):
        self._bus = smbus.SMBus(I2C_BUS)
        self._slave_device = slave_device

    def forward(self, speed):
        self._send_command(CMD_RIGHT, speed)
        self._send_command(CMD_LEFT, speed)

    def backward(self, speed):
        self._send_command(CMD_RIGHT, -1*speed)
        self._send_command(CMD_LEFT, -1*speed)

    def right(self, speed):
        self._send_command(CMD_RIGHT, speed)

    def left(self, speed):
        self._send_command(CMD_LEFT, speed)

    def _send_command(self, command, value):
        self._bus.write_word_data(self._slave_device, command, value)

    def get_value(self, label):
        command = '?'
        self._bus.write_word_data(self._slave_device, command, value)
        value = self._bus.read_word_data(self._slave_device, 0x00)
        logging.info("get_value {} returned {}".format(label, value))
        return value

def main():
  walker = Ambulator(DEVICE_ADDRESS)
  sys.exit(0)

if __name__ == "__main__":
  main()
