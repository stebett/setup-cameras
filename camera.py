"""
Manage video acquisition, requiring config path as input.

Allows to specify the output directory, timeout_delay and expected frames

Author: Stefano BETTANI, October 2021, Modified by Romain FAYAT
Adapted from Romain FAYAT's and Romain SALA's code
"""
import gi
import TIS
import time
import pickle
from configs import Configs
import logging
from pathlib import Path
gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa E402


class Camera(TIS.TIS):
    """The object managing the camera.

    :param config_path: path of configuration file
    :param path_to_output: directory where videos and logs should be saved
    """

    def __init__(self, config_path, path_to_output='videos'):
        "Initialize the Camera object."
        super().__init__()
        self.config_path = config_path
        self.path_to_output = Path(path_to_output)
        self.configs = Configs(config_path)
        self.pipeline = None
        self.queue = None
        self.livedisplay = False

        # logging.basicConfig(filename=path_to_output + '/run.log',
        #                     level=logging.INFO)
        logging.basicConfig(level=logging.INFO)

    def create_output_dir(self):
        "Create the output directory if needed."
        if not self.path_to_output.exists():
            self.path_to_output.mkdir(parents=True)
            logging.info(f"Created output directory ({self.path_to_output})")

    def initialize(self):
        "Initialize the camera."
        self.create_callback()
        self.open_device()
        logging.info("Succesfully initialized")

    def capture(self):
        "Start capturing videos."
        try:
            self.queue.loop()
        except KeyboardInterrupt:
            logging.error("Stopped manually by user")
        finally:
            self.stopPipeline()
            if self.queue.received_frames:
                self.queue.save_timestamps()

    def create_callback(self):
        "Define function to call when a frame is received."
        self.queue = Queue(self,
                           self.path_to_output,
                           self.configs.pwm['timeout_delay'] / 1000,
                           self.configs.pwm['chunk_size'])
        self.Set_Image_Callback(self.queue.add_frame)

    def apply_properties(self):
        "Apply properties to camera."
        for k, v in self.configs.properties.items():
            self.setProperty(k, v)


class Queue:
    """An object to manage video naming and checks the delay between triggers.

    : param camera: The Camera object from which data is streamed
    : param path_to_output: Directory where videos and logs should be saved
    : param timeout_delay: The timeout (in s) for starting an new video
    : param expected_frames: The expected number of frame for each video

    """

    def __init__(self, camera, path_to_output, timeout_delay, expected_frames):
        "Initialize the queue object."
        # Not Ideal to have both objects imbricated (camera has a queue and
        # queue has a camera) but if there is no workaround so be it
        self.camera = camera
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output

        self.videos = []
        self.video_name = ""
        self.timestamps = {}
        self.counter = 0  # Current frame number (total across videos)
        self.relative_zero = 0  #  1st frame number in the current video
        self.go = True

    @property
    def received_frames(self):
        "Return True if frames were received by the queue."
        return self.counter > 0

    def loop(self):
        "Manage creation and realease of videos."
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

    @property
    def video_started(self):
        "Return True if a video started."
        return self.counter > self.relative_zero

    @property
    def timeout_is_exceeded(self):
        "Return True if the timeout delay was exceeded."
        time_since_last_frame = time.time() - self.time_of_last_frame
        return time_since_last_frame > self.timeout_delay

    def check_delay(self):
        "Interrupts video when timeout_delay is exceeded."
        while self.go:
            if self.video_started and self.timeout_is_exceeded:
                logging.info("Timeout delay exceeded")
                self.go = False
            else:
                self.log_acquisition_status()

    def log_acquisition_status(self):
        "Log debugging acquisition informations."
        logging.debug(
            f"Buffers in queue: {self.camera.gstqueue.get_property('current-level-buffers')}")
        logging.debug(
            f"Time in queue: {self.camera.gstqueue.get_property('current-level-time')}")
        logging.debug(
            f"Bytes in queue: {self.camera.gstqueue.get_property('current-level-bytes')}")
        time.sleep(0.25)

    def add_frame(self, camera):
        "Write a timestamp and increases the counter."
        t = time.time()
        self.timestamps[self.counter] = t
        self.time_of_last_frame = t
        self.counter += 1
        logging.info(f"Adding frame {self.counter} to the queue")

    def log_frame_number_warning(self):
        "Log a warning with the actual and expected frame numbers."
        logging.warning(
            "\n\n\n"
            f"[!] Video:                     {self.video_name}\n"
            f"[!] Number of frames:          {self.counter}\n"
            f"[!] Expected number of frames: {self.relative_zero}\n"
        )

    def new_video(self):
        "Create new video name based on number of first frame."
        self.relative_zero = self.expected_frames * len(self.videos)
        logging.warning(f"relative zero: {self.relative_zero}")

        if (self.expected_frames > 0) & (self.counter != self.relative_zero):
            self.log_frame_number_warning()
            self.counter = self.relative_zero

        self.video_name = f"{self.path_to_output}/{self.counter :06d}.avi"
        self.videos.append(self.video_name)

    def save_timestamps(self):
        "Write timestamps to disk in pickle format."
        with open(f'{self.video_name[:-4]}.pickle', 'wb') as handle:
            pickle.dump(self.timestamps, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)
        self.timestamps = {}
