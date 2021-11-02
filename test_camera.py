import gi
import os
import sys
import json
import logging

from camera import Camera

gi.require_version("Gst", "1.0")
from gi.repository import Gst 

class TestCamera(Camera):
    def __init__(self, config_path):
        super().__init__(config_path)
        self.livedisplay = True 
        self.configs = Configs(config_path)
        logging.basicConfig(level=logging.WARNING) 


    def initialize(self):
        """Initialize the camera"""
        self.Set_Image_Callback(lambda x: x)
        self.open_device(self.configs.general)
        logging.info("Succesfully initialized")

    def capture(self):
        """Start capturing videos"""
        try:
            self.createPipeline()
            self.setcaps(self.configs.general)
            self.pipeline.set_state(Gst.State.PLAYING)
            self.test()
        except KeyboardInterrupt:
            logging.error("Stopped manually by user")
        finally:
            self.stopPipeline()

    def test(self):
        while True:
            # os.system("clear")
            self.print_config_list()

            i, v = self.input_index_and_value()
            self.change_config(i, v)


    def print_config_list(self):
        print("\nConfigurations (press Enter to save)")
        for i, k, v, m in zip(self.configs.indexes, self.configs.keys, self.configs.values, self.configs.modified):
            check = "[x]" if m else ""
            print(f'[{i}]{check} {k}: {v}')

    def save_config(self):
        inp = input(f"Destination path:\n(default={self.config_path})\n> ")
        filename = self.config_path if inp == "" else inp

        self.configs.list_to_dict()
        self.configs.save(filename)

    def input_index_and_value(self):
        v = None
        i = None
        while True:
            i = input("Property number: ")
            if i == "":
                self.save_config()
                sys.exit()

            try:
                i = int(i)
                v = input("Property value: ")
            except ValueError:
                print("You have to input a number!")

            break

        return i, v

    def change_config(self, i, v):
        k = self.configs.keys[i]

        
        try:
            self.setProperty(k, v)
        except Exception:
            print(f"The value {v} is not adeguate to property {k}")

        self.configs.values[i] = v


class Configs:
    def __init__(self, config_path):
        self.config_path = config_path
        self.read_configs()

        self.pwm = self.configs["pwm"]
        self.general = self.configs["general"]
        self.properties = self.configs["properties"]
        self.dict_to_list()



    def read_configs(self):
        """Read the configuration file"""
        with open(self.config_path) as json_file:
            self.configs = json.load(json_file)

    def dict_to_list(self):
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
        self.values = list(pwm_values) + list(general_values) + list(properties_values)
        self.parent = ["pwm" for _ in range(pwm_len)] + \
                      ["general" for _ in range(general_len)] + \
                      ["properties" for _ in range(properties_len)]

    def list_to_dict(self):
        for parent, value, key in zip(self.parent, self.values, self.keys):
            self.configs[parent][key] = value

    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.configs, f, indent=4)

