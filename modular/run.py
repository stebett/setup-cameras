import TIS
import cv2
import json
from collections import deque
from time import time
import logging
# TODO: put the log in the right place 
logging.basicConfig(filename='run.log', level=logging.DEBUG)

class Properties:
    def __init__(self, path):
        self.path = path
        self.properties = {}
        self.read_configs()

    def read_configs(self):
        with open(self.path) as json_file:
            self.properties = json.load(json_file)
            json_file.close()



class Camera(TIS.TIS):
    def __init__(self, properties, timeout_delay=1, expected_frames=0, path_to_output='.'):
        super().__init__()
        self.properties = properties
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output
        self.pipeline = None
        self.queue = None

    def open_device(self):
        self.openDevice(self.properties['serial'],
                        self.properties['width'],
                        self.properties['height'],
                        self.properties['framerate'],
                        TIS.SinkFormats.fromString(self.properties['serial']),
                        False)


    def apply_properties(self):
        for p in self.properties['properties']:
            self.Set_Property(p['property'], p['value'])


    def create_callback(self):
        self.queue = Queue(self.path_to_output, self.timeout_delay, self.expected_frames)
        self.Set_Image_Callback(self.queue.add_frame) # may throw error
        self.createPipeline(video_path=self.callback.path_to_video) # this as well

    def start_capture(self):
        self.open_device()
        self.apply_properties()
        self.create_callback()
        # self.startPipeline(self)
        # self.pipeline.set_state(Gst.State.PLAYING) # TODO?

    def stop_capture(self):
        self.stopPipeline()


class Queue:
    def __init__(self, path_to_output, expected_frames):
        self.path_to_output = path_to_output
        self.expected_frames = expected_frames
        self.frames = deque()
        self.timestamps = list() #TODO: write them 
        self.counter = 0
        self.videos = []
        self.time_of_last_frame = time() - self.timeout_delay

    def loop(self):
        while True:
            if time() - self.time_of_last_frame > self.timeout_delay:
                self.new_video()

            if len(self.frames) > 0:
                self.videos[-1].write(self.frames.popleft())
                self.time_of_last_frame = time()
            else:
                sleep(1e-6)
                

    def add_frame(self, camera):
        self.frame.append(camera.Get_image())
        self.timestamps.append(time())
        self.counter += 1

    def new_video(self):
        name = self.new_video_name()
        if len(self.videos) > 0:
            self.videos[-1].release


        self.videos.append(Video(name)) # TODO

    def new_video_name(self):
        expected_frames = self.expected_frames*len(self.videos)

        if (self.expected_frames > 0) & (self.counter != expected_frames):
            logging.warning(f"""
[!] Video:                     {self.videos[-1].path_to_video}
[!] Number of frames:          {self.counter}
[!] Expected number of frames: {expected_frames}""")
            self.frames = self.expected_frames

        return f"{self.path_to_output}/{self.counter + 1 :06d}.avi"

        
class Video(cv2.VideoWriter):
    def __init__(self, path_to_video, fps, width, height, fourcc_str="XVID"):
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        self.path_to_video = path_to_video
        super().__init__(self.path_to_video, self.fourcc, fps, (width, height))


