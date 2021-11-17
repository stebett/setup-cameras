"Create a config file with default parameters from a camera serial."
import os
import json
import argparse

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("serial",
                    help="Serial number of camera")
parser.add_argument("-o", "--output",
                    help="Name of the config file",
                    dest="filename",
                    default="configs.json")

args = parser.parse_args()
serial = str(args.serial)
filename = str(args.filename)

os.system(f"tcam-ctrl --save {serial} > {filename}")

with open(filename, "r") as f:
    c = json.load(f)

c["color"] = "false"
c["width"] = 1920
c["height"] = 1080
c["framerate"] = "30"

pwm = {}
pwm["frequency"] = 15
pwm["chunk_size"] = 50
pwm["chunk_pause"] = 3000

properties = c.pop("properties")

x = {}
x["properties"] = properties
x["pwm"] = pwm
x["general"] = c

with open(filename, "w") as f:
    json.dump(x, f, indent=4)
