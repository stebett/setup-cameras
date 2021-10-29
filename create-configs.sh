import os
import json
import argparse

parser = argparse.ArgumentParser(__doc__)
parser.add_argument("filename",
					help="Name of the config file", default="tmp_configs.json")

args = parser.parse_args()
filename = str(args.filename)


os.
tcam-ctrl --save $1 > tmp_configs.json
