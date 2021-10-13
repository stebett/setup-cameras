"""
Manage video acquisition, requiring config path as input

Allows to specify the output directory, timeout_delay and expected frames

Author: Stefano Bettani, October 2021, refractoring Romain Fayat's and Sala's code
"""
import TIS
import cv2
import json
import time
import pickle
import logging
import numpy as np

from gi.repository import Gst
from collections import deque


class Camera(TIS.TIS):
    """The object managing the camera.

    :param config_path: path of configuration file
    :param timeout_delay: interval in triggering after which a new chunk is started
    :param expected_frames: expected number of frames per chunk, 0 means no expectation
    :param path_to_output: directory where videos and logs should be saved
    """
    def __init__(self, config_path, timeout_delay=2, expected_frames=0, path_to_output='.'):
        super().__init__()
        self.config_path = config_path
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output
        self.configs = None
        self.pipeline = None
        self.queue = None


    def initialize(self):
        """Initialize the camera"""
        self.read_configs()
        self.open_device()
        self.create_callback()
        self.apply_properties()
        logging.info("Succesfully initialized")

    def start_capture(self):
        """Start capturing videos"""
        self._setcaps()
        self.pipeline.set_state(Gst.State.PLAYING)
        error = self.pipeline.get_state(5000000000) 
        print(error)
        # if error[1] != Gst.State.PLAYING:
        logging.info("Waiting first frame")
        self.queue.wait_first()
        try: 
            self.queue.loop()
        except KeyboardInterrupt:
            logging.error("Stopped manually by user")
        finally:
            self.stop_capture()
            self.queue.videos[-1].release()
            self.queue.save_timestamps()

    def stop_capture(self):
        """Stop capturing videos"""
        self.Stop_pipeline()

    def create_callback(self):
        """Create queue object and set it as callback"""
        self.queue = Queue(self.configs, 
                           self.timeout_delay,
                           self.expected_frames,
                           self.path_to_output)
        self.Set_Image_Callback(self.queue.add_frame)

    def apply_properties(self):
        """Apply properties to camera"""
        for p in self.configs['properties']:
            self.Set_Property(p['property'], p['value'])

    def open_device(self):
        """Access the camera"""
        self.openDevice(self.configs['serial'],
                        self.configs['width'],
                        self.configs['height'],
                        self.configs['framerate'],
                        TIS.SinkFormats.fromString(self.configs['serial']),
                        False)

    def read_configs(self):
        """Read the configuration file"""
        with open(self.config_path) as json_file:
            self.configs = json.load(json_file)
            json_file.close()


class Queue:
    """An object that saves frames to memory and writes them to disk as soon as possible

    :param config_path: path of configuration file
    :param timeout_delay: interval in triggering after which a new chunk is started
    :param expected_frames: expected number of frames per chunk, 0 means no expectation
    :param path_to_output: directory where videos and logs should be saved
    
    """
    def __init__(self, configs, timeout_delay, expected_frames, path_to_output):
        self.configs = configs
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output

        self.videos = []
        self.video_name = ""
        self.frames = deque()
        self.timestamps = {}
        
        self.counter = 0

        self.go = False
        # logging.basicConfig(filename=path_to_output + '/run.log', level=logging.ERROR)
        logging.basicConfig(level=logging.INFO)

    def loop(self):
        """Manages creation and realease of videos"""
        while True:
            self.new_video()
            logging.info(f"New video: {self.video_name}.avi")
            self.time_of_last_frame = time.time() 
            self.listen()
            self.videos[-1].release()
            self.save_timestamps()
            self.go = True

    def wait_first(self):
        while not self.go:
            if len(self.frames) > 0:
                self.go = True
            else:
                time.sleep(0.2)

    def listen(self):
        """Writes frames from queue to disk. It interrupts when timeout_delay is exceeded"""
        while self.go | (len(self.frames) > 0):
            if time.time() - self.time_of_last_frame > self.timeout_delay:
                logging.info("Timeout delay exceeded")
                self.go = False

            if len(self.frames) > 0:
                frame = self.frames.popleft()[:, :, 0:3]
                self.videos[-1].write(frame)
                self.time_of_last_frame = time.time()
                logging.info("Frame sent to video")
            else:
                time.sleep(1e-6)
                logging.debug("Sleeping")
                

    def add_frame(self, camera):
        """Add frame to queue and couples them to the timestamp"""
        self.frames.append(camera.Get_image())
        self.timestamps[self.counter] = time.time()
        logging.info("Adding frame to the queue")
        self.counter += 1

    def new_video(self):
        """Create new video object"""
        self.new_video_name()
        if len(self.videos) > 0:
            logging.info("Releasing old video")

        self.videos.append(cv2.VideoWriter(self.video_name + ".avi", 
                                           cv2.VideoWriter_fourcc(*'XVID'),
                                           self.configs["fps"],
                                           (self.configs["width"], self.configs["height"])))

    def new_video_name(self):
        """Create new video name based on number of first frame"""
        expected_frames_adjusted = self.expected_frames * len(self.videos)

        if (self.expected_frames > 0) & (self.counter != expected_frames_adjusted):
            logging.warning(f"""
[!] Video:                     {self.video_name}
[!] Number of frames:          {self.counter}
[!] Expected number of frames: {expected_frames_adjusted}""")
            self.counter = expected_frames_adjusted

        # self.video_name = f"{self.path_to_output}/{self.counter - len(self.frames) :06d}"
        self.video_name = f"{self.path_to_output}/{self.counter :06d}"

    def save_timestamps(self):
        with open(f'{self.video_name}.pickle', 'wb') as handle:
            pickle.dump(self.timestamps, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.timestamps = {}
