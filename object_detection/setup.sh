#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$PYTHONPATH:$DIR/utils
cd $HOME/Documents/workspace/tf/models
export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
export PYTHONPATH=$HOME/Documents/workspace/ohgee/
cd $DIR
