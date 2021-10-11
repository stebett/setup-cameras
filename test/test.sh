#!/bin/bash

mkdir -p /home/bettani/cameras/data/test/one

python start_recording.py

./reproduce.sh 

rm -r /home/bettani/cameras/data/test/one
