"""
Manage video acquisition, requiring config path as input

Allows to specify the output directory, timeout_delay and expected frames

Author: Stefano Bettani, October 2021, refractoring Romain Fayat's and Sala's code
"""
import gi
import os
import TIS
import json
import time
import pickle
import logging

gi.require_version("Gst", "1.0")
from gi.repository import Gst
from configs import Configs

class Camera(TIS.TIS):
    """The object managing the camera.

    :param config_path: path of configuration file
    :param timeout_delay: interval in triggering after which a new chunk is started
    :param expected_frames: expected number of frames per chunk, 0 means no expectation
    :param path_to_output: directory where videos and logs should be saved
    """
    def __init__(self, config_path, path_to_output='videos'):
        super().__init__()
        self.config_path = config_path
        self.path_to_output = path_to_output
        self.configs = Configs(config_path)
        self.pipeline = None
        self.queue = None
        self.livedisplay = False
        
        # logging.basicConfig(filename=path_to_output + '/run.log', level=logging.INFO)
        logging.basicConfig(level=logging.INFO) 


    def initialize(self):
        """Initialize the camera"""
        self.create_callback()
        self.open_device()
        logging.info("Succesfully initialized")

    def capture(self):
        """Start capturing videos"""
        try: 
            self.queue.loop()
        except KeyboardInterrupt:
            logging.error("Stopped manually by user")
        finally:
            self.stopPipeline()
            self.queue.save_timestamps()

    def create_callback(self):
        self.queue = Queue(self,
                           self.configs, 
                           self.path_to_output)
        self.Set_Image_Callback(self.queue.add_frame)

    def apply_properties(self):
        """Apply properties to camera"""
        for k, v in self.configs.properties.items():
            self.setProperty(k, v)



class Queue:
    """An object that saves frames to memory and writes them to disk as soon as possible

    :param config_path: path of configuration file
    :param timeout_delay: interval in triggering after which a new chunk is started
    :param expected_frames: expected number of frames per chunk, 0 means no expectation
    :param path_to_output: directory where videos and logs should be saved
    
    """
    def __init__(self, camera, configs, path_to_output):
        self.camera = camera
        self.configs = configs
        self.timeout_delay = self.configs.pwm['timeout_delay'] / 1000
        self.expected_frames = self.configs.pwm['chunk_size']
        self.path_to_output = path_to_output

        self.videos = []
        self.video_name = ""
        self.timestamps = {}
        self.counter = 0
        self.relative_zero = 0
        self.go = True

    def loop(self):
        """Manages creation and realease of videos"""
        self.livedisplay = False
        while True:
            self.new_video()
            logging.info(f"New video: {self.video_name}")

            self.camera.createPipeline(video_path=self.video_name)
            self.camera.apply_properties()
            logging.info("Created new pipeline")

            self.camera.pipeline.set_state(Gst.State.PLAYING)
            logging.info("Started pipeline")

            self.time_of_last_frame = time.time() 
            self.check_delay()
            self.go = True

            self.camera.stopPipeline()
            logging.info("Old pipeline stopped")

            self.save_timestamps()
            logging.info("Timestamps saved")


    def check_delay(self):
        """Writes frames from queue to disk. It interrupts when timeout_delay is exceeded"""
        while self.go:
            if (self.counter > self.relative_zero) and (time.time() - self.time_of_last_frame > self.timeout_delay):
                logging.info("Timeout delay exceeded")
                self.go = False

            else:
                logging.debug(f"Buffers in queue: {self.camera.gstqueue.get_property('current-level-buffers')}")
                logging.debug(f"Time in queue: {self.camera.gstqueue.get_property('current-level-time')}")
                logging.debug(f"Bytes in queue: {self.camera.gstqueue.get_property('current-level-bytes')}")
                time.sleep(0.25)

    def add_frame(self, camera):
        """Add frame to queue and couples them to the timestamp"""
        t = time.time()
        self.timestamps[self.counter] = t
        self.time_of_last_frame = t
        self.counter += 1
        logging.info(f"Adding frame {self.counter} to the queue")

    def new_video(self):
        """Create new video object"""
        self.new_video_name()
        self.videos.append(self.video_name)

    def new_video_name(self):
        """Create new video name based on number of first frame"""
        self.relative_zero = self.expected_frames * len(self.videos)
        logging.warning(f"relative zero: {self.relative_zero}")

        if (self.expected_frames > 0) & (self.counter != self.relative_zero):
            logging.warning(f"""
[!] Video:                     {self.video_name}
[!] Number of frames:          {self.counter}
[!] Expected number of frames: {self.relative_zero}""")
            self.counter = self.relative_zero

        self.video_name = f"{self.path_to_output}/{self.counter :06d}.avi"

    def save_timestamps(self):
        with open(f'{self.video_name[:-4]}.pickle', 'wb') as handle:
            pickle.dump(self.timestamps, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.timestamps = {}
