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
compression_level = arguments["compression_level"]
max_buffers_queue = arguments["max_buffers_queue"]

output_file =  camera_prefix + cam_id
output_path = output_parent / output_file

if not clean_output_dir(output_path, overwrite):
    sys.exit()
logger = get_logger(cam_id, stdout_log_level, file_log_level, output_path) 

config_copy_path = output_path / config_path.name
copyfile(config_path, config_copy_path)

def terminate(*args):
    "Stop the capture and clean up."
    global c
    c.stop_capture()
    sys.exit()
signal.signal(signal.SIGINT, terminate)


config = Config(config_path, cam_id)
c = Camera(config,
           logger=logger,
           path_to_output=output_path,
           gst_debug_level=gst_debug_level,
           compression_level=compression_level,
           max_buffers_queue=max_buffers_queue)

c.start_capture()
