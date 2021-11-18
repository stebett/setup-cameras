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

serials = os.system(tcam-ctrl -l | awk '{print $5}')

for s in serials:
    os.system(f"tcam-ctrl --save {s} > {s}_conf.json")


all_confs = []
for s in serial:
    with open(f"{s}_conf.json", "r") as f:
    all_confs.append(json.load(f))

c = {}
c["color"] = "false"
c["width"] = 1440
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
x["cams"] = []

for cam_confs in all_confs:
    tmp = {}
    tmp["general"] = cam_confs
    tmp["properties"] = {}
    x["cam_specific"].append()
    

with open(filename, "w") as f:
    json.dump(x, f, indent=4)
