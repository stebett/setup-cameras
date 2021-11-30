"Handle configuration formatting and storage."
import os
import re
import toml
import json
import tiscam.input_helpers
import subprocess
from pathlib import Path


class Config:
    "A class to store configuration file and ensure right formatting."

    def __init__(self, config_path, logger, cam_id):
        "Initialize the object with a configuration path."
        self.config_path = Path(config_path).expanduser()
        self.logger = logger
        self.cam_id = cam_id
        self.read_config()
        if self.cam_id >= 0 :
            self.apply_cam_specific_config()

        self.pwm = self.config["pwm"]
        self.general = self.config["general"]
        self.properties = self.config["properties"]
        #self.set_real_framerate()
        self.set_fake_framerate()
        self.check_exposure_time()
        self.dict_to_list()

    def set_fake_framerate(self):
        self.framerate = 120

    def set_real_framerate(self):
        if self.config["properties"]["Trigger Mode"]:
            self.framerate = self.config["pwm"]["frequency"]
        else:
            self.framerate = self.config["general"]["framerate"]

    def apply_cam_specific_config(self):
        tmp = self.config[f"cam_{self.cam_id}"]
        for key, value in tmp["general"].items():
            self.config["general"][key] = value

        for key, value in tmp["properties"].items():
            self.config["properties"][key] = value

        removable_keys = [key for key in self.config if re.match("cam_\d", key)]
        for key in removable_keys:
            self.config.pop(key)
        


    def read_config(self):
        "Read the configuration file."
        try:
            with self.config_path.open("r") as f:
                self.config = toml.load(f)
        except FileNotFoundError:
            logger.error("Invalid config file. If you want to use the default"
                          " configuration, run record.py without argument")
            raise FileNotFoundError("Invalid config file")

    def check_exposure_time(self):
        "Check that exposure time is not too long for the selected framerate"
        exposure = int(self.properties["Exposure Time (us)"])
        if self.properties["Trigger Mode"]:
            fps = int(self.pwm["frequency"])
        else:
            fps = int(self.general["framerate"])

        max_fps = 1e6 / exposure

        if fps > max_fps:
            max_exposure = 1e6 / fps
            self.logger.error(f"Exposure Time is too long for your framerate!")
            self.logger.error(f"Selected exposure: {exposure}us -> max framerate possible: {max_fps}Hz")
            self.logger.error(f"Desired framerate: {fps}Hz -> max exposure required: {(max_exposure):.1f}us")
            ignore = input_helpers.ask_yes_or_no("Do you want to start the recording anyway? ")
            if not ignore:
                raise Exception("Excecution interrupted by user")
            
            


    def dict_to_list(self):
        "Create a list from the dict of configs in order to display/edit them."
        pwm_keys = self.pwm.keys()
        pwm_values = [self.pwm[k] for k in pwm_keys]

        general_keys = self.general.keys()
        general_values = [self.general[k] for k in general_keys]

        properties_keys = self.properties.keys()
        properties_values = [self.properties[k] for k in properties_keys]

        pwm_len = len(pwm_keys)
        general_len = len(general_keys)
        properties_len = len(properties_keys)
        list_len = pwm_len + general_len + properties_len

        self.indexes = [i for i in range(list_len)]
        self.modified = [False for _ in range(list_len)]
        self.keys = list(pwm_keys) + list(general_keys) + list(properties_keys)
        self.values = list(pwm_values) + \
            list(general_values) + list(properties_values)
        self.parent = ["pwm" for _ in range(pwm_len)] + \
                      ["general" for _ in range(general_len)] + \
                      ["properties" for _ in range(properties_len)]

    def list_to_dict(self):
        "Push changes made on the list to the dict."
        for parent, value, key in zip(self.parent, self.values, self.keys):
            self.config[parent][key] = value

    def save(self, file_path):
        "Save the dictionary as a json file."
        with open(file_path, 'w') as f:
            toml.dump(self.config, f)


def get_serials():
    ps = subprocess.Popen(('tcam-ctrl', '-l'), stdout=subprocess.PIPE)
    serials = subprocess.check_output(("awk", "{print $5}"), stdin=ps.stdout)
    ps.wait()
    serials = serials.decode(encoding='UTF-8').split('\n')[:-1]
    return serials

def get_camera_config(serial):
    os.system(f"tcam-ctrl --save {serial} > {serial}_conf.json")
    with open(f"{serial}_conf.json", "r") as f:
            conf = json.load(f)
    os.system(f"rm {serial}_conf.json")
    return conf

def get_common_properties(configurations):
    all_properties = []
    for c in configurations.values():
        all_properties.append(c["properties"])

    common_keys = all_properties[0].keys()
    for p in all_properties:
        common_keys &= p.keys() 

    common_properties = {k:all_properties[0][k] for k in common_keys}
    return common_properties


def get_specific_caps(serial):
    os.system(f"tcam-ctrl --caps {serial} > {serial}_caps.txt")
    all_caps = open(f"{serial}_caps.txt").read().split('\n')[1:-1]

    caps_dict = {"accepted_width":[], "accepted_height":[]}

    for single_caps in all_caps:
        caps = single_caps.split(',')
        width = caps[2].split('=')[1]
        height = caps[3].split('=')[1]

        caps_dict["accepted_width"].append(int(width))
        caps_dict["accepted_height"].append(int(height))
        caps_dict["color"] = True if ("rggb" in caps[1]) else False

    caps_dict["width"] = max(caps_dict["accepted_width"])
    caps_dict["height"] = max(caps_dict["accepted_height"])
    os.system(f"rm {serial}_caps.txt")
    return caps_dict

def get_specific_properties(conf, common_properties):
    return {k:conf["properties"][k] for k in conf["properties"].keys() - common_properties.keys()} 

def get_pwm():
    pwm = {}
    pwm["frequency"] = 15
    pwm["chunk_size"] = 50
    pwm["chunk_pause"] = 3000
    return pwm

def get_general():
    general = {}
    general["framerate"] = 120
    return general

def create_config(filename):
    "Create a config file with default parameters from a camera serial."
    serials = get_serials()
    all_confs = {s:get_camera_config(s) for s in serials}

    config = {}
    config["properties"] = get_common_properties(all_confs)
    config["general"] = get_general()
    config["pwm"] = get_pwm()

    for n, s in enumerate(serials):
        key = f"cam_{n}"
        config[key] = {}
        config[key]["general"] = get_specific_caps(s)
        config[key]["general"]["serial"] = s
        config[key]["properties"] = all_confs[s]["properties"]
        # config[key]["properties"] = get_specific_properties(all_confs[s], config["properties"])

    with open(filename, "w") as f:
        toml.dump(config, f)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-o", "--output",
                        help="Name of the config file",
                        dest="filename",
                        default="configs.toml")

    args = parser.parse_args()
    filename = str(args.filename)
    create_config(filename)
