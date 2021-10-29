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
c["framerate"] = "15/1"


