import json
import time
import argparse
from configs import Configs
from pwmpy.arduino_pwm import Arduino_PWM

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("filename",
                    help="Name of the config file")

args = parser.parse_args()
filename = str(args.filename)

configs = Configs(filename)

ser = Arduino_PWM("/dev/ttyACM0",
        timeout=.1,
        frequency=configs.pwm["frequency"],
        chunk_size=configs.pwm["chunk_size"],
        chunk_pause=configs.pwm["chunk_pause"])

ser.start_pwm()

try:
    while True:
        time.sleep(.1)
except KeyboardInterrupt:
    print("Hit ctrl-C")
finally:
    print("Cleaning up")
    ser.close()
