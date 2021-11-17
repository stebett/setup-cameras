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
from pathlib import Path
gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa E402


class Camera(TIS.TIS):
    """The object managing the camera.

    :param config: Config object that contains configuration
    :param path_to_output: directory where videos and logs should be saved
    """

    def __init__(self, config, logger, path_to_output='videos', gst_debug_level=1):
        "Initialize the Camera object."
        super().__init__(gst_debug_level)
        self.path_to_output = Path(path_to_output)
        self.config = config
        self.logger = logger
        self.pipeline = None
        self.queue = None
        self.livedisplay = False

    def capture(self):
        "Start capturing videos."
        self.create_callback()
        try:
            self.loop()
        except KeyboardInterrupt:
            self.logger.error("Stopped manually by user")
        finally:
            self.stop_pipeline()
            self.queue.estimate_framerate()
            self.queue.save_timestamps()

    def loop(self):
        "Manage creation and realease of videos."
        self.queue.livedisplay = False
        while True:
            self.queue.new_video()
            self.logger.info(f"New video: {self.queue.video_name}")

            self.create_pipeline()
            self.init_pipeline(video_path=self.queue.video_name)
            self.apply_properties()
            self.logger.info("Created new pipeline")

            self.pipeline.set_state(Gst.State.PLAYING)
            self.logger.info("Started pipeline")

            self.queue.time_of_last_frame = time.time()
            self.queue.check_delay()
            self.queue.go = True

            self.stop_pipeline()
            self.queue.estimate_framerate()
            self.queue.save_timestamps()

    def create_callback(self):
        "Define function to call when a frame is received."
        self.queue = Queue(self.path_to_output,
                           self.config.pwm['chunk_pause'],
                           self.config.pwm['chunk_size'],
                           self.logger)
        self.set_image_callback(add_frame, self.queue)

    def apply_properties(self):
        "Apply properties to camera."
        for k, v in self.config.properties.items():
            self.set_property(k, v)

def add_frame(tis, queue):
    "Write a timestamp and increases the counter."
    if queue.busy:
        queue.logger.error("[!] Frame dropped!")
        return
    queue.busy = True
    t = time.time()
    queue.timestamps[queue.counter] = t
    queue.time_of_last_frame = t
    queue.counter += 1
    queue.logger.info(f"Adding frame {queue.counter} to the queue")
    queue.busy = False

class Queue:
    """An object to manage video naming and checks the delay between triggers.

    : param path_to_output: Directory where videos and logs should be saved
    : param timeout_delay: The timeout (in s) for starting an new video
    : param expected_frames: The expected number of frame for each video

    """

    def __init__(self, path_to_output, chunk_pause, expected_frames, logger):
        "Initialize the queue object."
        # TODO: Find a better way to define timeout_delay
        self.timeout_delay = chunk_pause / 1000 - 1
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output
        self.logger = logger

        self.videos = []
        self.video_name = ""
        self.timestamps = {}
        self.counter = 0  # Current frame number (total across videos)
        self.relative_zero = 0  #  1st frame number in the current video
        self.go = True
        self.busy = False

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
                self.logger.info("Timeout delay exceeded")
                self.go = False
            else:
                time.sleep(0.001)

    def log_frame_number_warning(self):
        "Log a warning with the actual and expected frame numbers."
        frames_chunk = self.counter - self.relative_zero + self.expected_frames
        self.logger.warning(f"[!] Video:                     {self.video_name}")
        self.logger.warning(f"[!] Number of frames:          {self.counter}")
        self.logger.warning(f"[!] Expected number of frames: {self.relative_zero}")
        self.logger.warning(f"[!] Frames in chunk:           {frames_chunk}")
        self.logger.warning(f"[!] Expected in chunk:         {self.expected_frames}")

    def new_video(self):
        "Create new video name based on number of first frame."
        self.relative_zero = self.expected_frames * len(self.videos)
        self.logger.info(f"relative zero: {self.relative_zero}")

        if (self.expected_frames > 0) & (self.counter != self.relative_zero):
            self.log_frame_number_warning()

        self.counter = self.relative_zero

        self.video_name = f"{self.path_to_output}/{self.counter :06d}.avi"
        self.videos.append(self.video_name)

    def estimate_framerate(self):
        estimate = len(self.timestamps) / (self.time_of_last_frame - self.timestamps[self.relative_zero])
        self.logger.info(f"Estimated framerate for the last video: {estimate:.2f}Hz")

    def save_timestamps(self):
        "Write timestamps to disk in pickle format."
        if self.video_started:
            with open(f'{self.video_name[:-4]}.pickle', 'wb') as handle:
                pickle.dump(self.timestamps, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)
            self.logger.info("Timestamps saved")
            self.timestamps = {}
