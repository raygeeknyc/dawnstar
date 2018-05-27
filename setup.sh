#!/bin/sh
cd ../tf/models/research
export PYTHONPATH=$PYTHONPATH:`pwd`/object_detection
export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
cd -
 
