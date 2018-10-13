import logging
logging.getLogger('').setLevel(logging.DEBUG)

import os
import subprocess

from display import DisplayInfo, Display

class Dawnstar(object):
  _IP_CMD = 'hostname -I | cut -d\" \" -f1'

  def __init__(self):
    self._ip_address = None

  def get_ip_address(self):
    if not self._ip_address:
      self._ip_address = subprocess.check_output(Dawnstar._IP_CMD, shell = True )
      logging.debug('IP {}'.format(self._ip_address))
    return self._ip_address

robot = Dawnstar()
print('Ip address: {}'.format(robot.get_ip_address()))

info = DisplayInfo()
screen = Display(info)

info.ip = robot.get_ip_address()
while True:
  screen.refresh()
