import os
import json
import argparse
import subprocess

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("serial",
                    help="Serial number of camera")
parser.add_argument("-o", "--output",
                    help="Name of the config file", 
                    dest="filename",
                    default="tmp_configs.json")

args = parser.parse_args()
serial = str(args.serial)
filename = str(args.filename)

os.system(f"tcam-ctrl --save {serial} > {filename}")

with open(filename, "r") as f:
    c = json.load(f)

c["format"] = "video/x-raw"
c["pixelformat"] = "BGRx"
c["width"] = 1440
c["height"] = 1080
c["framerate"] = "2500000/10593"

pwm = {}
pwm["frequency"] = 15
pwm["chunk_size"] = 50
pwm["chunk_pause"] = 3000

c["pwm"] = pwm

with open(filename, "w") as f:
    c = json.dump(c, f, indent=4)

c_copy = c.copy()
properties = c_copy.pop("properties")
pwm = c_copy.pop("pwm")

configs = []
for k, v in properties.items():
    configs.append([k, v, " "])

for k, v in c_copy.items():
    configs.append([k, v, " "])

for k, v in pwm.items():
    configs.append([k, v, " "])

for i, x in enumerate(configs):
    print(f'[{i}]{x[2]}{x[0]}: {x[1]}')

n = input("Property number: ")
v = input("Property value: ")
p = configs[n][0]
if n >= len(properties) + len(c_copy):
    pwm[p] = v
elif n >= len(properties):
    c_copy[p] = v
else:
    properties[p] = v

configs[n][1] = v
configs[n][2] = "[x] "

self.setProperty(p, v)
