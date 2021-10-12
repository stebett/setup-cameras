import TIS
import cv2
import json
from collections import deque
import time
import logging
import numpy as np

class Configs:
    def __init__(self, path):
        self.path = path
        self.configs = {}
        self.read_configs()

    def read_configs(self):
        with open(self.path) as json_file:
            self.configs = json.load(json_file)
            json_file.close()


a = Configs("configs.json")
b = Camera(a.configs)
b.start_capture()
time.sleep(3)
b.stop_capture()
b.queue.loop()
b.queue.videos[-1].release()

frames = []
for f in b.queue.frames:
    frames.append(f[:, :, 1])

import numpy as np
import cv2
v = cv2.VideoWriter('output2.avi', cv2.VideoWriter_fourcc(*'XVID'), 30, (1440, 1080), False)
for f in frames:
    v.write(f)
v.release()

data = np.random.randint(0, 256, (1440, 1080), dtype='uint8')
data2 = b.queue.frames[1]

import numpy as np
import cv2
size = 1440, 1080
duration = 2
fps = 25
out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (1080, 1440), False)
for _ in range(fps * duration):
    data = np.random.randint(0, 256, size, dtype='uint8')
    out.write(data)
out.release()

class Camera(TIS.TIS):
    def __init__(self, configs, timeout_delay=1, expected_frames=0, path_to_output='.'):
        super().__init__()
        self.configs = configs
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.path_to_output = path_to_output
        self.pipeline = None
        self.queue = None

    def open_device(self):
        self.openDevice(self.configs['serial'],
                        self.configs['width'],
                        self.configs['height'],
                        self.configs['framerate'],
                        TIS.SinkFormats.fromString(self.configs['serial']),
                        False)


    def apply_properties(self):
        for p in self.configs['properties']:
            self.Set_Property(p['property'], p['value'])


    def create_callback(self):
        self.queue = Queue(self.configs, self.path_to_output, self.timeout_delay, self.expected_frames)
        self.Set_Image_Callback(self.queue.add_frame) # may throw error

    def start_capture(self):
        self.open_device()
        self.create_callback()
        self.Start_pipeline()
        self.apply_properties()
        # self.queue.loop()
        # self.pipeline.set_state(Gst.State.PLAYING) # TODO?

    def stop_capture(self):
        self.Stop_pipeline()


class Queue:
    def __init__(self, configs, path_to_output, timeout_delay, expected_frames):
        self.configs = configs
        self.path_to_output = path_to_output
        self.timeout_delay = timeout_delay
        self.expected_frames = expected_frames
        self.frames = deque()
        self.timestamps = list() #TODO: write them 
        self.counter = 0
        self.videos = []
        self.time_of_last_frame = time.time() - self.timeout_delay
        logging.basicConfig(filename=path_to_output + '/run.log', level=logging.DEBUG)

    def loop(self):
        # while True:
        for _ in range(50):
            print("Checking for frames")
            print(len(self.frames))

            if time.time() - self.time_of_last_frame > self.timeout_delay:
                self.new_video()
                print("New video")

            if len(self.frames) > 0:
                frame = self.frames.popleft()[:, :, 1]
                # frame = np.random.randint(0, 256, (1440, 1080), dtype='uint8')
                self.videos[-1].write(frame)
                self.time_of_last_frame = time.time()
                print("Frame sent to video")
            else:
                time.sleep(1e-6)
                print("Sleeping")
                

    def add_frame(self, camera):
        self.frames.append(camera.Get_image())
        self.timestamps.append(time.time())
        print("Adding frame")
        self.counter += 1

    def new_video(self):
        name = self.new_video_name()
        if len(self.videos) > 0:
            self.videos[-1].release

        # TODO: fix framerate
        # self.videos.append(Video(name, 30, self.configs["width"], self.configs["height"]))
        self.videos.append(cv2.VideoWriter(name, cv2.VideoWriter_fourcc(*'mp4v'), 30, (self.configs["width"], self.configs["height"]), False))

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
    def __init__(self, path_to_video, fps, width, height, fourcc_str="mp4v"):
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        self.path_to_video = path_to_video
        super().__init__(self.path_to_video, self.fourcc, fps, (height, width), False)
