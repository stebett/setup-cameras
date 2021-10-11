import tkinter
from tkinter import filedialog, messagebox
import json
from cam_management import Cam, Video
import TIS
import threading

protocol = None

class Protocol():
    def __init__(self):
        self.name = None
        self.experimenter = None
        self.n_camera = None
        self.cam_data = None
        self.cameras = None
        self.geometry = None
        self.save_path = None
        self.save_type = None
        self.save_ext = None
        self.save_ext = None
        self.fps = None

    def from_dict(self, data):
        self.cameras = []
        self.name = str(data["name"])
        self.experimenter = str(data["experimenter"])
        self.n_camera = int(data["n_camera"])
        self.geometry = data["geometry"]
        self.save_path = str(data["save_path"]) # path to save video / image
        self.save_type = str(data["save_type"]) # "video" or "image"
        self.save_ext = str(data["save_ext"])  # file extension
        if self.save_type == "video":
            self.fps = float(data["video_fps"])
        else:
            self.fps = 30
        self.cam_data = data["cam"]
        i = 0
        for camera in self.cam_data:
            name = camera["name"]
            model = camera["model"]
            serial = camera["serial"]
            resolution = camera["resolution"]
            width = int(resolution.split("x")[0])
            height = int(resolution.split("x")[1])
            framerate = camera["framerate"]
            sink = camera["format"]
            if sink == "GRAY8":
                sink = TIS.SinkFormats.GRAY8
            elif sink == "GRAY16_LE":
                sink = TIS.SinkFormats.GRAY16_LE
            elif sink == "BGRA":
                sink = TIS.SinkFormats.BGRA
            exposure_auto = get_bool_value(camera, "exposure_auto")
            gain_auto = get_bool_value(camera, "gain_auto")
            livedisplay = get_bool_value(camera, "livedisplay")
            wb_auto = get_bool_value(camera, "whitebalance_auto")
            trig = get_bool_value(camera, "trigger")
            exp = get_int_value(camera, "exposure")
            gain = get_int_value(camera, "gain")
            wb = (get_int_value(camera, "whitebalance_red"), get_int_value(camera, "whitebalance_green"), get_int_value(camera, "whitebalance_blue"))
            br = get_int_value(camera,"brightness")
            print((trig, exposure_auto, gain_auto,
                      wb_auto, exp, gain, wb, br))
            cam = Cam(serial, model, name, height, width, framerate, livedisplay, sink, trig, exposure_auto, gain_auto,
                      wb_auto, exp, gain, wb, br, callback=None, callback_type=self.save_type, file_type=self.save_ext,
                      file_path=self.save_path, file_subdir=name, file_name="trial", video_fps=self.fps, cam_index=i)
            self.cameras.append(cam)
            i += 1


def get_int_value(dict, label):
    try:
        return int(dict[label])
    except:
        return None

def get_bool_value(dict, label):
    try:
        return bool(int(dict[label]))
    except:
        return None


def protocol_init():
    global protocol
    if messagebox.askyesno("Loading Protocol", "Do you have a protocol to load?"):
        file = filedialog.askopenfilename(title="Load protocol", filetypes=[("prt files", "*.prt")])
        if file is not None:
            protocol = load_protocol(file)
        else:
            protocol = create_protocol()
    else:
        protocol = create_protocol()


def load_protocol(file):
    with open(file) as json_file:
        data = json.load(json_file)
        protocol = Protocol()
        protocol.from_dict(data)
        return protocol

def create_protocol():
    print("created")
