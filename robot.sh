#!/bin/bash
pico2wave -l en-US --wave "/tmp/ohgee_update.wav" "i can't wait to be a robot";aplay "/tmp/ohgee_update.wav"
sudo python dawnstar.py
