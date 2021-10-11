import tkinter
from tkinter import *
import gi
import numpy as np
import pandas as pd
from pandastable import Table, TableModel
import re
from enum import Enum
from gi.repository import GLib, GObject, Gst, Tcam, GstVideo
import TIS
import time
import cv2
import os
from datetime import datetime
running = False
cam = None
cameras = []
from PIL import Image, ImageTk
import GUI
import threading

lmain = None



class Cam(TIS.TIS):
    def __init__(self, serial, model, name="cam", height=1080, width=1440, framerate="120/1", livedisplay=True,
                 sink=TIS.SinkFormats.GRAY8, trigger=False, exp_auto=True, gain_auto=True, wb_auto=True,
                 exposure=None, gain=None, wb=None, brightness=None, callback=None, callback_type="video", file_type=".avi",
                 file_path="videos/", file_name="trial", file_subdir=None, video_fps=30, cam_index=0):
        TIS.TIS.__init__(self, cam_index=cam_index)
        self.serialnumber = serial
        self.model = model
        self.name = name
        self.height = height
        self.width = width
        self.framerate = framerate
        self.livedisplay = livedisplay
        self.sinkformat = sink
        self.trigger = trigger
        self.exposure_auto = exp_auto
        self.gain_auto = gain_auto
        self.wb_auto = wb_auto
        self.exposure = exposure
        self.gain = gain
        self.wb = wb
        self.brightness = brightness
        self.callback = callback
        self.callback_type = callback_type
        self.file_type = file_type
        self.file_path = file_path
        self.file_name = file_name
        self.file_subdir = file_subdir
        self.video_fps = video_fps
        self.t = None


    def initialize_cam(self):
        self.openDevice(self.serialnumber, self.width, self.height, self.framerate, self.sinkformat, self.livedisplay)
        """if self.callback is None:
            self.callback = Video(filepath=self.file_path, subdir=self.file_subdir, videoname=self.file_name,
                                  fps=self.video_fps, width=self.width, height=self.height, filetype=self.file_type)
        self.Set_Image_Callback(new_image_video, self.callback)"""
        #self.createPipeline(video_path=self.callback.videopath)
        self.createPipeline()
        
        #######################
        #self.t  = threading.Thread(target=self.startPipeline)
        #self.t.start()
        #self.startPipeline()
        self.start_capture()
        self.adjust()
        

    def adjust(self):
        self.setProperty("Trigger Mode", self.trigger)
        self.setProperty("Trigger Mode", False)
        self.setProperty("Whitebalance Auto", self.wb_auto)
        self.setProperty("Gain Auto", self.gain_auto)
        self.setProperty("Exposure Auto", self.exposure_auto)
        self.setProperty("Exposure Time (us)", self.exposure)
        self.setProperty("Gain", self.gain)
        self.setProperty("Brightness", self.brightness)
        if self.wb is not None:
            self.setProperty("Whitebalance Red", self.wb[0])
            self.setProperty("Whitebalance Green", self.wb[1])
            self.setProperty("Whitebalance Blue", self.wb[2])

    def prepare(self):
        self.stopPipeline()
        self.pipeline = None
        if self.callback_type == "video":
            if self.callback is None:
                self.callback = Video(filepath=self.file_path, subdir=self.file_subdir, videoname=self.file_name,
                                      fps=self.video_fps, width=self.width, height=self.height, filetype=self.file_type)
            self.Set_Image_Callback(new_image_video, self.callback)
        else:
            if self.callback is None:
                # TODO: IMPLEMENT IMAGE SNAPPING
                self.callback = Video(filepath=self.file_path, subdir=self.file_subdir, videoname=self.file_name,
                                      fps=self.video_fps, width=self.width, height=self.height, filetype=self.file_type)
            self.Set_Image_Callback(new_image_video, self.callback)
        #self.t.join()

        if self.callback is not None:
            self.createPipeline(video_path=self.callback.videopath)
        #camera = Gst.ElementFactory.make("tcambin")
        #camera.set_state(Gst.State.READY)

    def start_capture(self):
        if self.callback is not None:
            self.callback.capture = True
        #self.t = threading.Thread(target=self.startPipeline)
        #self.t.start()
        self.startPipeline()
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_capture(self):
        #self.t.join()
        self.stopPipeline()
        #self.callback = None





class Video:
    def __init__(self, filepath="videos/", subdir=None, videoname="trial", fps=30, width=1440, height=1080, filetype=".avi"):
        self.frame_count = 0
        self.error_count = 0
        self.filepath = filepath
        self.filetype = filetype
        if subdir is not None:
            self.filepath = self.filepath + subdir +"/"
        self.filename = videoname + "_" + video_name()
        self.videopath = self.get_video_path()
        self.fps = fps
        self.width = width
        self.height = height
        self.busy = False
        self.capture = False
        self.timestamps = []
        self.errors = []
        self.initialize_folder(self.filepath, self.filename)
        self.last_frame = None


    def initialize_folder(self, filepath , filename):
        folder_path = filepath+filename
        os.makedirs(folder_path, exist_ok=True)

    def get_video_path(self):
        return self.filepath + self.filename +"/" + self.filename + self.filetype

    def close_stream(self):
        folder_path = self.filepath + self.filename +"/"

        df_headers = ["Frame", "Timestamp"]
        df_buffer = []
        for i in range(0, len(self.timestamps)):
            df_buffer.append([i+1, self.timestamps[i]])
        df = pd.DataFrame(df_buffer, columns=df_headers)
        df.to_csv(folder_path+"frames_timestamps.csv", index=False)

        df_headers = ["Error", "Timestamp"]
        df_buffer = []
        for i in range(0, len(self.errors)):
            df_buffer.append([i + 1, self.errors[i]])
        df = pd.DataFrame(df_buffer, columns=df_headers)
        df.to_csv(folder_path + "errors_timestamps.csv", index=False)


    def new_frame(self, ts):
        self.frame_count += 1
        self.timestamps.append(ts)


    def new_error(self, ts):
        self.error_count += 1
        self.errors.append(ts)




def new_image_video(feed, video):
    if video.capture:
        if video.busy:
            video.new_error(timestamp())
            return
        video.busy = True
        video.new_frame(timestamp())
        video.busy = False


def timestamp():
    epoch = datetime(1970, 1, 1)
    now = datetime.now()
    t = (now - epoch).total_seconds()
    return '%.6f' % t

def video_name():
    now = datetime.now()
    return now.strftime("%d_%m_%Y-%H_%M_%S")


'''def on_sync_message(bus, message):
    print(message)
    if message.structure is None:
        return
    message_name = message.structure.get_name()
    if message_name == "prepare-xwindow-id":
        imagesink = message.src
        imagesink.set_property("force-aspect-ratio", True)
        imagesink.set_xwindow_id(GUI.mwin_id)
        #imagesink.set_xwindow_id(GUI.mwin_id.window.xid)'''


'''def on_sync_message(bus, message):
    print(message)
    if message.structure is None:
        return
    message_name = message.structure.get_name()
    if message_name == "prepare-xwindow-id":
        imagesink = message.src
        imagesink.set_property("force-aspect-ratio", True)
        imagesink.set_xwindow_id(GUI.mwin_id)
        #imagesink.set_xwindow_id(GUI.mwin_id.window.xid)'''

