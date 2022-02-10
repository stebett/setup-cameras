"Start a recording from a toml parameters file to an output folder."
import sys
import signal
import argparse
from shutil import copyfile
from pathlib import Path

from tiscam.helpers import clean_output_dir, get_logger
from tiscam.camera import Camera
from tiscam.config import Config, read_config


parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-c", "--config_path",
                    help="Path to the state file of the camera",
                    dest="config_path", default="config.toml",
                    type=lambda x: Path(x).expanduser().absolute())
parser.add_argument("-s", "--serial",
                    help="Serial of camera",
                    dest="serial", default=False)
parser.add_argument("-o", "--output-folder",
                    help="Output directory where to save videos",
                    dest="output_folder", default=False)

args = parser.parse_args()
config_path = args.config_path
serial = args.serial

arguments = read_config(config_path)["tiscam"]

camera_prefix = arguments["path"]["prefix"]
overwrite = arguments["path"]["overwrite"]

stream_log_level = arguments["logging"]["stream_level"]
gst_debug_level = arguments["logging"]["gst_level"]
file_log_level = arguments["logging"]["file_level"]

compression_level = arguments["pipeline"]["compression_level"]
max_buffers_queue = arguments["pipeline"]["max_buffers_queue"]

output_parent = args.output_folder or arguments["path"]["output_folder"]
output_dir =  f"{camera_prefix}_{serial}"
output_path = Path(output_parent).expanduser().absolute() / output_dir

if not clean_output_dir(output_path, overwrite):
    sys.exit()
logger = get_logger(f"cam_{serial}", stream_log_level, file_log_level, output_path / f"cam_{serial}.log") 

config_copy_path = output_path / config_path.name
copyfile(config_path, config_copy_path)

def terminate(*args):
    "Stop the capture and clean up."
    global c
    c.stop_capture()
    sys.exit()
signal.signal(signal.SIGINT, terminate)


config = Config(config_path, serial)
c = Camera(config,
           logger=logger,
           path_to_output=output_path,
           gst_debug_level=gst_debug_level,
           compression_level=compression_level,
           max_buffers_queue=max_buffers_queue)

c.start_capture()
