#!/bin/bash
ffmpeg -framerate 20 -i /home/bettani/cameras/data/test/one/right_%04d.jpg -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p output.mp4
mpv output.mp4
rm output.mp4

