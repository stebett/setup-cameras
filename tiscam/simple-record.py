"Start a recording from a toml parameters file to an output folder."
import sys
import signal
import argparse
from pathlib import Path
from shutil import copyfile

from tiscam.helpers import clean_output_dir, get_logger
from tiscam.camera import Camera
from tiscam.config import Config, read_config


parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-c", "--config_path",
                    help="Path to the state file of the camera",
                    dest="config_path", default="configs.toml",
                    type=lambda x: Path(x).expanduser().absolute())
parser.add_argument("-i", "--camera-id",
                    help="Index of camera",
                    dest="cam_id", default="0")

args = parser.parse_args()
config_path = args.config_path
cam_id = args.cam_id

arguments = read_config(config_path)["arguments"]
output_parent = Path(arguments["output_parent"]).expanduser().absolute()
camera_prefix = arguments["camera_prefix"]
stdout_log_level = arguments["stdout_log_level"]
file_log_level = arguments["file_log_level"]
gst_debug_level = arguments["gst_debug_level"]
overwrite = arguments["force"]

output_path = output_parent / (camera_prefix + cam_id)

logger = get_logger(stdout_log_level, file_log_level, output_path) 
if not clean_output_dir(output_path, logger, overwrite):
    sys.exit()

copyfile(config_path, output_path / config_path.name)

def terminate(*args):
    "Stop the capture and clean up."
    global c
    c.stop_capture()
    sys.exit()
signal.signal(signal.SIGINT, terminate)


config = Config(config_path, logger, cam_id)
c = Camera(config,
           logger=logger,
           path_to_output=output_path,
           gst_debug_level=gst_debug_level)

c.start_capture()