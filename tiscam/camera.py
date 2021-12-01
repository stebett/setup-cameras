"""
Manage video acquisition, requiring config path as input.

Allows to specify the output directory, timeout_delay and expected frames

Author: Stefano BETTANI, October 2021, Modified by Romain FAYAT
Adapted from Romain FAYAT's and Romain SALA's code
"""
import gi
import sys
import time
import pickle
from pathlib import Path

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "0.1")

from gi.repository import GObject, Gst, Tcam


class TIS:
    "The Imaging Source Camera"
    def __init__(self, gst_debug_level):
        "Constructor of TIS object"
        self.gst_debug_level = gst_debug_level
        self.logger = None
        Gst.init(["record.py", f"--gst-debug-level={self.gst_debug_level}"])

    def create_pipeline(self):
        "Creates a Gstreamer pipeline"
        p = "tcambin name=source ! identity name=id"
        # WARNING: Do not change position of identity plugin

        if self.config.general["color"]:
            p += " ! capsfilter name=bayercaps"
            p += " ! bayer2rgb ! videoconvert"

        p += " ! capsfilter name=rawcaps ! videoconvert"

        if self.livedisplay:
            p += " ! videoscale method=0 add-borders=false"
            p += " ! video/x-raw,width=640,height=360"
            p += " ! fpsdisplaysink sink=ximagesink"
        else:
            p += " ! x264enc quantizer=0 qp-min=0 qp-max=0 qp-step=0"
            p += " ! avimux"
            p += " ! queue name=queue"
            p += " ! filesink name=fsink"

        self.logger.debug(f"Gst pipeline: {p}")
        self.pipeline = Gst.parse_launch(p)

    def init_pipeline(self, video_path):
        "Initializes the Gstreamer pipeline"
        self.source = self.pipeline.get_by_name("source")
        self.source.set_property("serial", self.config.general["serial"])
        self.logger.debug(f"Serial: {self.config.general['serial']}")
        self.logger.debug(self.config.config)

        self.identity = self.pipeline.get_by_name("id")
        self.identity.connect("handoff", self.on_new_buffer)

        if self.config.general["color"] == "true":
            self.bayerfilter = self.pipeline.get_by_name("bayercaps")
            self.bayerfilter.set_property("caps", self.get_caps(bayer=True))

        self.rawfilter = self.pipeline.get_by_name("rawcaps")
        self.rawfilter.set_property("caps", self.get_caps(bayer=False))

        if not self.livedisplay:
            try:
                self._queue = self.pipeline.get_by_name("queue")
                self._queue.set_property("max-size-buffers", 0)
                self._queue.set_property("max-size-bytes", int(1.5e9))
                self._queue.set_property("max-size-time", 0)

            except Exception:
                self.logger.warning("No queue was found")
            
            self.filesink = self.pipeline.get_by_name("fsink")
            self.filesink.set_property("location", video_path)

            self.filesink = self.pipeline.get_by_name("fsink")
            self.filesink.set_property("location", video_path)

    def stop_pipeline(self):
        "Stops the pipeline"
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.set_state(Gst.State.NULL)

    def set_image_callback(self, function, *data):
        "Sets the specific function called when a frame is received"
        self.image_callback = function
        self.image_callback_data = data

    def on_new_buffer(self, *args):
        "Set the generic ffunction called when a frame is received"
        self.image_callback(self, *self.image_callback_data);
        return False

    def get_caps(self, bayer=False):
        "Get pixel and sink format and frame rate"
        self.logger.debug("Creating caps")
        if bayer:
            fmt = "video/x-bayer,format=rggb,"
        else:
            fmt = "video/x-raw,format=BGRx,"

        fmt += f"width={self.config.general['width']},"
        fmt += f"height={self.config.general['height']},"
        fmt += f"framerate={self.config.framerate}/1"
                   # Maximum accepted framerate, set it high

        self.logger.debug(f"Caps: {fmt}")
        caps = Gst.Caps.new_empty()
        structure = Gst.Structure.new_from_string(fmt)
        caps.append_structure(structure)
        structure.free()
        return caps

    def set_property(self, property_name, value):
        "Set properties, trying to convert the values to the appropriate types"
        self.logger.debug(f"Setting property {property_name} at {value}")
        try:
            prop = self.source.get_tcam_property(property_name)
            if prop.type == 'double':
                value = float(value)
            if prop.type == 'integer':
                value = int(value)
            if prop.type == 'boolean':
                if (value == "True") or (value == "true") or (value is True):
                    value = True
                elif (value == "False") or (value == "false") or (value is False):
                    value = False
                else:
                    raise

            result = self.source.set_tcam_property(property_name, GObject.Value(type(value),value))
            if result is False:
                self.logger.warning("Failed to set {} to value {}. value type is {} prop type is {}, range is {}-{}".format(property_name, value, type(value), prop.type, prop.min, prop.max))
        except Exception as error:
            self.logger.error("Error set Property {0}: {1}", property_name, format(error))
            raise


class Camera(TIS):
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
        "Start capturing videos and handle keyboardinterrupt."
        self.create_callback()
        try:
            self.loop()
        except KeyboardInterrupt:
            self.logger.error("Stopped manually by user")
        finally:
            self.stop_capture()

    def start_capture(self):
        "Start capturing videos."
        self.logger.info("Starting to record")
        self.create_callback()
        self.loop()

    def stop_capture(self):
        "Stop the capture and cleanup."
        self.logger.info("Killing pipeline")
        self.stop_pipeline()
        self.logger.info("Recording stopped")


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

            self.logger.info("Closing pipeline")
            self.stop_pipeline()
            self.queue.close()

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
    queue.chunk_counter += 1
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
        self.chunk_counter = 0
        self.relative_zero = 0  #  1st frame number in the current video
        self.frame_loss = 0
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

    def reset_relative_zero(self):
        if self.expected_frames > 0:
            self.relative_zero = self.expected_frames * len(self.videos)
            self.logger.info(f"relative zero: {self.relative_zero}")

    def reset_counters(self):
        if self.expected_frames > 0:
            self.counter = self.relative_zero
            self.chunk_counter = 0

    def estimate_loss(self):
        if self.expected_frames > 0:
            self.frame_loss = self.expected_frames - self.chunk_counter

    def log_frame_number_warning(self):
        "Log a warning with the actual and expected frame numbers."
        self.logger.warning(f"Video:                     {self.video_name}")
        self.logger.warning(f"Number of frames:          {self.counter}")
        self.logger.warning(f"Expected number of frames: {self.relative_zero}")
        self.logger.warning(f"Frames in chunk:           {self.chunk_counter}")
        self.logger.warning(f"Expected in chunk:         {self.expected_frames}")
        self.logger.warning(f"Frame loss:                {self.frame_loss}")

    def close(self):
        "Run all estimations in the right order, resets the parameters and save the timestamps"
        self.estimate_framerate()
        self.estimate_loss()
        self.save_timestamps()
        self.reset_relative_zero()
        if self.frame_loss > 0:
            self.log_frame_number_warning()
        self.reset_counters()


    def new_video(self):
        "Create new video name based on number of first frame."
        self.video_name = f"{self.path_to_output}/{self.counter :06d}.avi"
        self.videos.append(self.video_name)

    def estimate_framerate(self):
        if self.video_started:
            t0 = sorted(self.timestamps.values())[0]
            t1 = sorted(self.timestamps.values())[-1]
            estimate = len(self.timestamps) / (t1 - t0)

            self.logger.info(
                f"Estimated framerate for the last video: {estimate:.2f}Hz")

    def save_timestamps(self):
        "Write timestamps to disk in pickle format."
        if self.video_started:
            self.timestamps["loss"] = self.frame_loss
            with open(f'{self.video_name[:-4]}.pickle', 'wb') as handle:
                pickle.dump(self.timestamps, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)
            self.logger.info("Timestamps saved")
            self.timestamps = {}
