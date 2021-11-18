"Create a config file with default parameters from a camera serial."
import os
import json
import argparse
import subprocess

parser = argparse.ArgumentParser(__doc__)
# parser.add_argument("serial",
                    # help="Serial number of camera")
parser.add_argument("-o", "--output",
                    help="Name of the config file",
                    dest="filename",
                    default="configs.json")

args = parser.parse_args()
# serial = str(args.serial)
filename = str(args.filename)

ps = subprocess.Popen(('tcam-ctrl', '-l'), stdout=subprocess.PIPE)
serials = subprocess.check_output(("awk", "{print $5}"), stdin=ps.stdout)
ps.wait()
serials = serials.decode(encoding='UTF-8').split('\n')[:-1]

for s in serials:
    os.system(f"tcam-ctrl --save {s} > {s}_conf.json")


all_confs = []
for s in serials:
    with open(f"{s}_conf.json", "r") as f:
        all_confs.append(json.load(f))

for s in serials:
    os.system(f"rm {s}_conf.json")

for c in all_confs:
    properties = c.pop("properties")
    
c = {}
c["color"] = "false"
c["width"] = 1440
c["height"] = 1080
c["framerate"] = "30"

pwm = {}
pwm["frequency"] = 15
pwm["chunk_size"] = 50
pwm["chunk_pause"] = 3000


x = {}
x["properties"] = properties
x["pwm"] = pwm
x["general"] = c
x["cam_specific"] = []

for cam_confs in all_confs:
    tmp = {}
    tmp["general"] = cam_confs
    tmp["properties"] = {}
    x["cam_specific"].append(tmp)
    

with open(filename, "w") as f:
    json.dump(x, f, indent=4)
