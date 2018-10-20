# The tracker portion of a K9

REFRESH_DELAY_SECS = 2

import logging
logging.getLogger('').setLevel(logging.DEBUG)

import os
import subprocess
import time

from display import DisplayInfo, Display

class Dawnstar(object):
  _IP_CMD = 'hostname -I | cut -d\" \" -f1'

  def __init__(self):
    self._ip_address = None

  def get_ip_address(self):
    self._ip_address = subprocess.check_output(Dawnstar._IP_CMD, shell = True )
    return self._ip_address

robot = Dawnstar()
print('Ip address: {}'.format(robot.get_ip_address()))

info = DisplayInfo()
screen = Display(info)

while True:
  info.ip = robot.get_ip_address()
  logging.debug('Ip address: {}'.format(info.ip))

  screen.refresh(info)
  time.sleep(REFRESH_DELAY_SECS)
