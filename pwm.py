import json
import time
import argparse
from config import Config
from pwmpy.arduino_pwm import Arduino_PWM

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("filename",
                    help="Name of the config file")

args = parser.parse_args()
filename = str(args.filename)

config = Config(filename)

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
