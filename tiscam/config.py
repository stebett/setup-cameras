"Handle configuration formatting and storage."
import os
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
        tmp = self.config["cam_specific"][self.cam_id]
        for key, value in tmp["general"].items():
            self.config["general"][key] = value

        for key, value in tmp["properties"].items():
            self.config["properties"][key] = value

        self.config.pop("cam_specific")


    def read_config(self):
        "Read the configuration file."
        try:
            with self.config_path.open("r") as json_file:
                self.config = json.load(json_file)
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
            json.dump(self.config, f, indent=4)


class DefaultConfig():
    "A class to store default configurations."

    def __init__(self, serial=49020441):
        "Create a default configuration in trigg mode."
        self.pwm = {'frequency': 15,
                    'chunk_size': 50,
                    'chunk_pause': 5000,
                    'timeout_delay': 100}
        self.general = {'serial': str(serial),
                        'version': 'v0.1',
                        'color': False,
                        'width': 1440,
                        'height': 1080,
                        'framerate': '120/1'}
        self.properties = {'Auto Functions ROI Control': True,
                           'Auto Functions ROI Preset': 'Center 50%',
                           'Brightness': 0,
                           'Exposure Auto': False,
                           'Exposure Auto Lower Limit': 1,
                           'Exposure Auto Reference': 128,
                           'Exposure Auto Upper Limit': 33333,
                           'Exposure Auto Upper Limit Auto': False,
                           'Exposure Time (us)': 10000,
                           'GPIn': 0,
                           'GPOut': 1,
                           'Gain': 4,
                           'Gain Auto': False,
                           'Gain Auto Lower Limit': 0,
                           'Gain Auto Upper Limit': 480,
                           'Highlight Reduction': False,
                           'IMX Low-Latency Mode': False,
                           'Offset Auto Center': True,
                           'Offset X': 0,
                           'Offset Y': 0,
                           'Override Scanning Mode': 1,
                           'Reverse X': False,
                           'Reverse Y': False,
                           'Strobe Delay': 0,
                           'Strobe Duration': 100,
                           'Strobe Enable': False,
                           'Strobe Exposure': True,
                           'Strobe Polarity': False,
                           'Trigger Delay (us)': 0,
                           'Trigger Exposure Mode': 'Frame Start',
                           'Trigger Global Reset Release': False,
                           'Trigger Mode': True,
                           'Trigger Polarity': 'Rising Edge'}

        self.config = {'properties': self.properties,
                       'general': self.general,
                       'pwm': self.pwm}


def create_config(filename):
    "Create a config file with default parameters from a camera serial."
    ps = subprocess.Popen(('tcam-ctrl', '-l'), stdout=subprocess.PIPE)
    serials = subprocess.check_output(("awk", "{print $5}"), stdin=ps.stdout)
    ps.wait()
    serials = serials.decode(encoding='UTF-8').split('\n')[:-1]

    for s in serials:
        os.system(f"tcam-ctrl --save {s} > {s}_conf.json")


    all_confs = []
    for s in serials:
        with open(f"{s}_conf.json", "r") as f:
            all_confs.append(json.load(f))

    for s in serials:
        os.system(f"rm {s}_conf.json")

    for c in all_confs:
        properties = c.pop("properties")
        
    c = {}
    c["color"] = False
    c["width"] = "1440"
    c["height"] = "1080"
    c["framerate"] = "120"

    pwm = {}
    pwm["frequency"] = 15
    pwm["chunk_size"] = 50
    pwm["chunk_pause"] = 3000


    x = {}
    x["properties"] = properties
    x["pwm"] = pwm
    x["general"] = c
    x["cam_specific"] = []

    for cam_confs in all_confs:
        tmp = {}
        tmp["general"] = cam_confs
        tmp["properties"] = {}
        x["cam_specific"].append(tmp)
        

    with open(filename, "w") as f:
        json.dump(x, f, indent=4)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-o", "--output",
                        help="Name of the config file",
                        dest="filename",
                        default="configs.json")

    args = parser.parse_args()
    filename = str(args.filename)
    create_config(filename)
