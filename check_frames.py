import cv2
import numpy as np
import matplotlib.pyplot as plt

from romain_code import frames_from_video

frames = frames_from_video("/home/bettani/setup-cameras/videos/000000.avi", show_progress=True)
