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
            logging.info("Checking for frames")

            if time.time() - self.time_of_last_frame > self.timeout_delay:
                self.new_video()
                logging.info("New video")

            if len(self.frames) > 0:
                frame = self.frames.popleft()[:, :, 0:3]
                self.videos[-1].write(frame)
                self.time_of_last_frame = time.time()
                logging.info("Frame sent to video")
            else:
                time.sleep(1e-6)
                logging.info("Sleeping")
                

    def add_frame(self, camera):
        self.frames.append(camera.Get_image())
        self.timestamps.append(time.time())
        logging.info("Adding frame")
        self.counter += 1

    def new_video(self):
        name = self.new_video_name()
        if len(self.videos) > 0:
            self.videos[-1].release

        # TODO: fix framerate
        self.videos.append(cv2.VideoWriter(name, 
                                           cv2.VideoWriter_fourcc(*'XVID'),
                                           30,
                                           (self.configs["width"], self.configs["height"])))

    def new_video_name(self):
        expected_frames = self.expected_frames*len(self.videos)

        if (self.expected_frames > 0) & (self.counter != expected_frames):
            logging.warning(f"""
[!] Video:                     {self.videos[-1].path_to_video}
[!] Number of frames:          {self.counter}
[!] Expected number of frames: {expected_frames}""")
            self.frames = self.expected_frames

        return f"{self.path_to_output}/{self.counter - len(self.frames) + 1 :06d}.avi"


if __name__ == "__main__":
    a = Configs("configs.json")
    b = Camera(a.configs)
    b.start_capture()
    try: 
        b.queue.loop()
    except KeyboardInterrupt:
        print("Stopped by god")
    finally:
        b.stop_capture()
        b.queue.videos[-1].release()

