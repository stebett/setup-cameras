import json
import time
import argparse
from config import Config
from pwmpy.arduino_pwm import Arduino_PWM

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-c", "--config_path",
                    help="Path to the state file of the camera",
                    dest="config_path", default="default")

args = parser.parse_args()
config_path = args.config_path

if config_path == "default":
    if test_mode:
        raise Exception("Cannot run in test mode with default configuration")
    config = DefaultConfig()
else:
    config = Config(Path(config_path).expanduser().absolute())

ser = Arduino_PWM("/dev/ttyACM0",
        timeout=.1,
        frequency=config.pwm["frequency"],
        chunk_size=config.pwm["chunk_size"],
        chunk_pause=config.pwm["chunk_pause"])

ser.start_pwm()

try:
    while True:
        time.sleep(.1)
except KeyboardInterrupt:
    print("Hit ctrl-C")
finally:
    print("Cleaning up")
    ser.close()
