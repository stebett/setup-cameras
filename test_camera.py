"Code for interactively change properties of the camera."
from gi.repository import Gst
import gi
import sys
import logging
from camera import Camera
from pathlib import Path
gi.require_version("Gst", "1.0")


class TestCamera(Camera):
    "Extend Camera to interactively change properties of the camera."

    def __init__(self, config):
        "Create the camera object."
        super().__init__(config)
        self.livedisplay = True
        self.config = config

    def initialize(self):
        "Initialize the camera."
        self.Set_Image_Callback(lambda x: x)
        logging.info("Succesfully initialized")

    def capture(self):
        "Start capturing videos."
        try:
            self.createPipeline()
            self.initPipeline(None)
            self.pipeline.set_state(Gst.State.PLAYING)
            self.test()
        except KeyboardInterrupt:
            logging.error("Stopped manually by user")
        finally:
            self.stopPipeline()

    def test(self):
        """Main loop for changing configuration."""
        while True:
            # os.system("clear") # Uncomment when debugged
            self.print_config_list()

            i, v = self.input_index_and_value()
            self.change_config(i, v)

    def print_config_list(self):
        """Display current configuration values on terminal.

        A checkbox is added if the have been changed already.
        """
        print("\nConfigurations (press Enter to save)")
        for i, k, v, m in zip(self.config.indexes,
                              self.config.keys,
                              self.config.values,
                              self.config.modified):
            check = "[x]" if m else ""
            print(f'[{i}]{check} {k}: {v}')

    def save_config(self):
        "Save the current configuration."
        inp = input("Destination path:\n(default=./config.json)\n> ")
        file_path = Path("./config.json") if inp == "" else inp
        self.config.list_to_dict()
        self.config.save(file_path)

    def input_index_and_value(self):
        "Asks for index and value of configuration to change."
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
        "Apply a property to the camera."
        k = self.config.keys[i]

        try:
            self.setProperty(k, v)
        except Exception:
            print(f"The value {v} is not adeguate to property {k}")

        self.config.values[i] = v
