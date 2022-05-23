"Handle configuration formatting and storage."
import os
import re
import toml
import json
import logging
import subprocess
import tiscam.helpers
from pathlib import Path
from collections.abc import Hashable


class Config:
    "A class to store configuration file and ensure right formatting."

    def __init__(self, config, serial):
        "Initialize the object with a configuration path."
        self.raw_config = config
        self.serial = serial
        self.apply_config()

        #self.set_real_framerate()
        self.set_fake_framerate()
        self.check_exposure_time()

    def set_fake_framerate(self):
        self.framerate = 120

    def set_real_framerate(self):
        if self.config["properties"]["Trigger Mode"]:
            self.framerate = self.config["pwm"]["frequency"]
        else:
            self.framerate = self.config["caps"]["framerate"]

    def apply_config(self):
        self.pwm = self.raw_config["pwm"]
        self.caps = {}
        self.properties = {}
        if self.serial:
            self.caps.update(self.raw_config["tiscam"]["caps"][self.serial])
            self.properties.update(self.raw_config["tiscam"]["properties"][self.serial])
        if self.raw_config["tiscam"]["caps"].get("common"):
            self.caps.update(self.raw_config["tiscam"]["caps"]["common"])
            self.properties.update(self.raw_config["tiscam"]["properties"]["common"])

        self.config = {"pwm": self.pwm,
                       "caps": self.caps,
                       "properties": self.properties}

    def check_exposure_time(self):
        "Check that exposure time is not too long for the selected framerate"
        exposure = int(self.properties["Exposure Time (us)"])
        if self.properties["Trigger Mode"]:
            fps = int(self.pwm["frequency"])
        else:
            fps = int(self.caps["framerate"])

        max_fps = 1e6 / exposure

        if fps > max_fps:
            max_exposure = 1e6 / fps
            logging.error(f"Exposure Time is too long for your framerate!")
            logging.error(f"Selected exposure: {exposure}us -> max framerate possible: {max_fps}Hz")
            logging.error(f"Desired framerate: {fps}Hz -> max exposure required: {(max_exposure):.1f}us")
            ignore = tiscam.helpers.ask_yes_or_no("Do you want to start the recording anyway? ")
            if not ignore:
                raise Exception("Excecution interrupted by user")
            
def read_config(path):
    "Read the configuration file."
    try:
        with path.open("r") as f:
            return toml.load(f)
    except FileNotFoundError:
        logging.error("Invalid config file. If you want to use the default"
                      " configuration, run record.py without argument")
        raise FileNotFoundError("Invalid config file")


def get_serials():
    "Uses tcam commands to retrieve cameras serials"
    ps = subprocess.Popen(('tcam-ctrl', '-l'), stdout=subprocess.PIPE)
    serials = subprocess.check_output(("awk", "{print $5}"), stdin=ps.stdout)
    ps.wait()
    serials = serials.decode(encoding='UTF-8').split('\n')[:-1]
    return serials

def get_camera_config(serial):
    "Uses tcam commands to retrieve cameras configurations given the serial"
    tmp_path = Path("~/.cache/tiscam").expanduser().absolute()
    tmp_path.mkdir(parents=True, exist_ok=True)
    filename = f"{serial}_conf.json"
    os.system(f"tcam-ctrl --save {serial} > {tmp_path / filename}")
    with (tmp_path / filename).open("r") as f:
            return json.load(f)

def upload_camera_config(serial):
    "Uses tcam commands to retrieve cameras configurations given the serial"
    tmp_path = Path("~/.cache/tiscam").expanduser().absolute()
    filename = f"{serial}_conf.json"
    try:
        os.system(f"tcam-ctrl --load {serial} {tmp_path / filename}")
    except FileNotFoundError as error:
        logging.error(f"File not found: {error}")


def get_caps(serial):
    "Uses tcam commands to retrieve cameras caps given the serial"
    os.system(f"tcam-ctrl --caps {serial} > {serial}_caps.txt")
    all_caps = open(f"{serial}_caps.txt").read().split('\n')[1:-1]

    caps = {"accepted_width":[], "accepted_height":[]}

    for single_caps in all_caps:
        elements = single_caps.split(',')
        width = elements[2].split('=')[1]
        height = elements[3].split('=')[1]

        caps["accepted_width"].append(int(width))
        caps["accepted_height"].append(int(height))
        caps["color"] = True if ("rggb" in elements[1]) else False

    caps["accepted_width"] = sorted(caps["accepted_width"], reverse=True)
    caps["accepted_height"] = sorted(caps["accepted_height"], reverse=True)
    caps["width"] = max(caps["accepted_width"])
    caps["height"] = max(caps["accepted_height"])
    caps["serial"] = serial
    os.system(f"rm {serial}_caps.txt")
    return caps


def get_pwm():
    "Return standard pwm parameters"
    pwm = {}
    pwm["frequency"] = 15
    pwm["chunk_size"] = 50
    pwm["chunk_pause"] = 3000
    return pwm

def get_path():
    "Return standard path parameters for cameras"
    path = {}
    path["prefix"] = "cam"
    path["overwrite"] = False
    return path

def get_logging():
    "Return standard logging parameters for cameras"
    logging = {}
    logging["stream_level"] = "info"
    logging["file_level"] = "debug"
    logging["gst_level"] = 1
    return logging

def get_pipeline():
    "Return standard pipeline parameters for cameras"
    pipeline = {}
    pipeline["max_buffers_queue"] = 30
    pipeline["compression_level"] = 0
    return pipeline


def create_config():
    "Create a config file with default parameters from a camera serial."
    serials = get_serials()
    for serial in serials:
        upload_camera_config(serial)

    config = {}
    config["serials"] = serials
    config["properties"] = {"common": {}}
    config["caps"] = {"common": {"framerate" : 120}}

    config["path"] = get_path()
    config["logging"] = get_logging()
    config["pipeline"] = get_pipeline()

    for s in serials:
        config["caps"][s] = get_caps(s)
        config["properties"][s] = get_camera_config(s)["properties"]

    common_caps = common_elements([config["caps"][s] for s in serials])
    common_properties = common_elements([config["properties"][s] for s in serials])

    for k in common_caps:
        _cap = set([config["caps"][s].pop(k) for s in serials])
        config["caps"]["common"][k] = _cap.pop()

    for k in common_properties:
        _property = set([config["properties"][s].pop(k) for s in serials])
        config["properties"]["common"][k] = _property.pop()

    return config

def common_elements(dicts):
    "Find equal key/value pairs between dictionaries and return corresponding keys"
    keys = [set(d.keys()) for d in dicts]
    common_keys = set.intersection(*keys)

    equal_pairs = set()
    for k in common_keys:
        value_by_dict = set()
        for d in dicts: 
            if isinstance(d[k], Hashable):
                value_by_dict.add(d[k])
        if len(value_by_dict) == 1:
            equal_pairs.add(k)

    return equal_pairs

def update_config(filename):
    config = read_config(filename)
    config["tiscam"] =  create_config()

    with open(filename, "w") as f:
        toml.dump(config, f)

    

def write_new_config(filename):
    "Create and write the config file"
    config = {}
    pwm_config = get_pwm()
    tiscam_config = create_config()
    config.update({"pwm": pwm_config, "tiscam": tiscam_config})

    with open(filename, "w") as f:
        toml.dump(config, f)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-o", "--output",
                        help="Path where to write the config file",
                        dest="filename", default="config.toml",
                        type=lambda x: Path(x).expanduser().absolute())

    args = parser.parse_args()
    filename = args.filename

    if os.path.isfile(filename):
        update_config(filename)
    else:
        write_new_config(filename)
