import TIS
import cv2
from collections import deque
from time import time


class Camera(TIS.TIS):
    def __init__(self, properties, path_to_output):
        super().__init__()
        self.properties = properties
        self.path_to_output = path_to_output
        self.pipeline = None
        self.queue = None

    def apply_properties(self):
        for p in self.properties:
            self.Set_Property(p['property'], p['value'])


    def create_callback():
        self.queue = queue(self.path_to_output, 
                              self.properties["timeout_delay"],
                              self.properties["expected_frames"])
        self.Set_Image_Callback(self.queue.add_frame) # may throw error
        self.createPipeline(video_path=self.callback.path_to_video) # this as well

    def start_capture():
        self.startPipeline()
        self.pipeline.set_state(Gst.State.PLAYING) # TODO?

    def stop_capture():
        self.stopPipeline()


class Queue:
    def __init__(self, path_to_output, timeout_delay=1, expected_frames=0):
        self.path_to_output = path_to_output
        self.expected_frames = expected_frames
        self.frames = deque()
        self.timestamps = list()
        self.counter = 0
        self.video = None # maybe store the old ones
        self.time_of_last_frame = time() - self.timeout_delay

    def loop():
        while True:
            if time() - time_of_last_frame > timeout_delay:
                new_video()

            if len(self.frames) > 0:
                self.Video.write(self.frames.popleft())
                self.time_of_last_frame = time()
            else:
                sleep(1e-6)
                

    def add_frame(camera):
        self.frame.append(camera.Get_image())
        self.timestamps.append(time())
        self.counter += 1

    def new_video():
        name = new_video_name()
        if self.Video is not None:
            self.Video.release

        self.Video = Video(name)

    def new_video_name():
        # Add option to use expected frames
        return f"{self.path_to_output}/{self.number_of_frame}.avi"

        

class Video(cv2.VideoWriter):
    def __init__(self, path_to_video, fps, width, height, fourcc_str="XVID"):
        self.path_to_video = path_to_video
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        super().__init__(path, fourcc, frameRate, (width, height))
