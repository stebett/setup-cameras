import json
import time
import argparse
from pwm_py.arduino_pwm import Arduino_PWM

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-f",
                    help="Name of the config file", 
                    dest="filename",
                    default="tmp_configs.json")

args = parser.parse_args()
filename = str(args.filename)

with open(filename, "r") as f:
    c = json.load(f)

ser = Arduino_PWM("/dev/ttyACM0",
        timeout=.1,
        frequency=c["pwm"]["frequency"],
        chunk_size=c["pwm"]["chunk_size"],
        chunk_pause=c["pwm"]["chunk_pause"])

ser.start_pwm()

try:
    while True:
        time.sleep(.1)
except KeyboardInterrupt:
    print("Hit ctrl-C")
finally:
    print("Cleaning up")
    ser.close()
