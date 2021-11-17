"Handle configuration formatting and storage."
import json
import input_helpers
from pathlib import Path


class Config:
    "A class to store configuration file and ensure right formatting."

    def __init__(self, config_path, logger):
        "Initialize the object with a configuration path."
        self.config_path = Path(config_path).expanduser()
        self.logger = logger
        self.read_config()
        self.pwm = self.config["pwm"]
        self.general = self.config["general"]
        self.properties = self.config["properties"]
        self.check_exposure_time()
        self.dict_to_list()

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
        if self.properties["Trigger Mode"] == "true":
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
