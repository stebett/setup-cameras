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

class Camera(TIS.TIS):
    """The object managing the camera.

    :param config_path: path of configuration file
    :param timeout_delay: interval in triggering after which a new chunk is started
    :param expected_frames: expected number of frames per chunk, 0 means no expectation
    :param path_to_output: directory where videos and logs should be saved
    """
    def __init__(self, config_path, timeout_delay=2, expected_frames=0, path_to_output='videos', test_mode=False):
        super().__init__()
        self.config_path = config_path
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output
        self.configs = None
        self.pipeline = None
        self.queue = None
        self.test_mode = test_mode
        self.livedisplay = True if test_mode else False
        
        # logging.basicConfig(filename=path_to_output + '/run.log', level=logging.INFO)
        if test_mode:
            logging.basicConfig(level=logging.WARNING) 
        else:
            logging.basicConfig(level=logging.INFO) 


    def initialize(self):
        """Initialize the camera"""
        self.read_configs()
        self.apply_pwm_properties()
        self.create_callback()
        self.open_device()
        logging.info("Succesfully initialized")

    def capture(self):
        """Start capturing videos"""
        try: 
            if self.test_mode:
                self.queue.test()
            else:
                self.queue.loop()
        except KeyboardInterrupt:
            logging.error("Stopped manually by user")
        finally:
            self.stopPipeline()
            self.queue.save_timestamps()

    def create_callback(self):
        self.queue = Queue(self,
                           self.configs, 
                           self.timeout_delay,
                           self.expected_frames,
                           self.path_to_output)
        self.Set_Image_Callback(self.queue.add_frame)

    def apply_properties(self):
        """Apply properties to camera"""
        for k, v in self.configs['properties'].items():
            self.setProperty(k, v)

    def apply_pwm_properties(self):
        self.frequency = self.configs['pwm']['frequency']
        self.timeout_delay = self.configs['pwm']['chunk_pause'] // 1000 - 1
        self.expected_frames = self.configs['pwm']['chunk_size']

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
    def __init__(self, camera, configs, timeout_delay, expected_frames, path_to_output):
        self.camera = camera
        self.configs = configs
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output

        self.videos = []
        self.video_name = ""
        self.timestamps = {}
        self.counter = 0
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

    def test(self):
        self.fill_c_array()
        while True:
            self.apply_c_array()
            self.camera.createPipeline()
            self.camera.pipeline.set_state(Gst.State.PLAYING)
            os.clear()
            self.modify_conf()

        self.camera.stopPipeline()

    def fill_c_array(self):
        self.c_array = []
        self.c_copy = self.configs.copy()
        self.properties = self.c_copy.pop("properties")
        self.pwm = self.c_copy.pop("pwm")

        for k, v in self.properties.items():
            self.c_array.append([k, v, " "])

        for k, v in self.c_copy.items():
            self.c_array.append([k, v, " "])

        for k, v in self.pwm.items():
            self.c_array.append([k, v, " "])

    def apply_c_array(self):
        for x in self.c_array:
            self.camera.setProperty(x[0], x[1])
        
    def modify_conf(self):
        for i, x in enumerate(self.c_array):
            print(f'[{i}]{x[2]}{x[0]}: {x[1]}')

        n = input("Property number: ")
        v = input("Property value: ")
        p = self.c_array[n][0]
        if n >= len(self.properties) + len(self.c_copy):
            self.pwm[p] = v
        elif n >= len(self.properties):
            self.c_copy[p] = v
        else:
            self.properties[p] = v

        self.c_array[n][1] = v
        self.c_array[n][2] = "[x] "



    def check_delay(self):
        """Writes frames from queue to disk. It interrupts when timeout_delay is exceeded"""
        while self.go:

            if time.time() - self.time_of_last_frame > self.timeout_delay:
                logging.info("Timeout delay exceeded")
                self.go = False

            else:
                logging.info(f"Buffers in queue: {self.camera.gstqueue.get_property('current-level-buffers')}")
                logging.debug(f"Time in queue: {self.camera.gstqueue.get_property('current-level-time')}")
                logging.debug(f"Bytes in queue: {self.camera.gstqueue.get_property('current-level-bytes')}")
                time.sleep(1)
                

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
        expected_frames_adjusted = self.expected_frames * len(self.videos)

        if (self.expected_frames > 0) & (self.counter != expected_frames_adjusted):
            logging.warning(f"""
[!] Video:                     {self.video_name}
[!] Number of frames:          {self.counter}
[!] Expected number of frames: {expected_frames_adjusted}""")
            self.counter = expected_frames_adjusted

        self.video_name = f"{self.path_to_output}/{self.counter :06d}.avi"

    def save_timestamps(self):
        with open(f'{self.video_name[:-4]}.pickle', 'wb') as handle:
            pickle.dump(self.timestamps, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.timestamps = {}
