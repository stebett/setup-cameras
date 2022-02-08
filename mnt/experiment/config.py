import toml
import argparse
from pathlib import Path
from datetime import datetime


parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-o", "--output-path",
        help="Output path",
        dest="filename", default="configs.toml", type=lambda x: Path(x).expanduser().absolute())

args = parser.parse_args()
filename = args.filename

config = {}
experiment = {}
actuator = {}
pwm = {}

pwm["meta"] = "Parameters fed to pypwm. Time is in ms"
pwm["frequency"] = 100
pwm["chunk_size"] = 3000
pwm["chunk_pause"] = 1000

actuator["meta"] = "Parameters for the actuator process. Array contains absolute position in mm [0, 101]. Time is in seconds"
actuator["below"] = [100, 100, 100, 100]
actuator["above"] = [10, 20, 30, 40]

experiment["schedule"] = {}
experiment["schedule"]["pwm_on"] = 0
experiment["schedule"]["cue_on"] = 0.1
experiment["schedule"]["cue_off"] = 0.5
experiment["schedule"]["pump"] = 0.6
experiment["schedule"]["pwm_off"] = 1
experiment["schedule"]["move_actuator"] = 1.1

experiment["pins"] = {}
experiment["pins"]["pwm"] = 21
experiment["pins"]["cue"] = 16
experiment["pins"]["pump"] = 18


experiment["logging"] = {}
experiment["logging"]["meta"] = "Logging parameters for all the processes in the experiment (excluding tiscam)"
experiment["logging"]["stream_level"] = "debug"
experiment["logging"]["file_level"] = "debug"

config = {"experiment": experiment,
          "pwm": pwm,
          "actuator": actuator,
         }

with open(filename, "w") as f:
    toml.dump(config, f)
