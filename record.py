"Start a recording from a json parameters file to an output folder."
import sys
import argparse
import logging
from pathlib import Path
from input_helpers import ask_yes_or_no
from camera import Camera
from test_camera import TestCamera
from config import Config, DefaultConfig


parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-c", "--config_path",
                    help="Path to the state file of the camera",
                    dest="config_path", default="default")
parser.add_argument("-o", "--output",
                    help="Path to the output video folder.",
                    dest="path_video_folder", default=Path("./videos"),
                    type=lambda x: Path(x).expanduser())
parser.add_argument("-t", "--test",
                    help="Start in test mode",
                    dest="test_mode", action="store_true")
parser.add_argument("-f", "--force",
                    help="Force overwritting of the output directory content",
                    dest="overwrite", action="store_true")
parser.add_argument("-l", "--log",
                    help="Set log level, possible values are debug | info | warning | error",
                    dest="log_level", default="info")
parser.add_argument("--gst-debug-level",
                    help="Gstreamer debug level, values go from 1 to 5",
                    dest="gst_debug_level", default="1")

args = parser.parse_args()
config_path = args.config_path
path_video_folder = args.path_video_folder.absolute()
test_mode = args.test_mode
overwrite = args.overwrite
log_level = args.log_level
gst_debug_level = args.gst_debug_level


# Logging

if log_level == "debug":
    level = logging.DEBUG
elif log_level == "info":
    level = logging.INFO
elif log_level == "warning":
    level = logging.WARNING
elif log_level == "error":
    level = logging.ERROR
else:
    raise Exception("Invalid log level! Run the command with argument --help to see the allowed values")

root = logging.getLogger()
root.setLevel(level)
handler = logging.FileHandler("prova.log")
handler.setLevel(level=level)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
handler.setFormatter(formatter)
root.addHandler(handler)

# List the avi and pickle files in the folder
if path_video_folder.exists():
    files_to_remove = []
    for f in path_video_folder.iterdir():
        if f.suffix in [".avi", ".pickle"]:
            files_to_remove.append(f)
    has_file = len(files_to_remove) > 0
else:
    path_video_folder.mkdir(parents=True)
    logging.info(f"Created output directory ({path_video_folder})")
    has_file = False

# If files were detected, remove it if the --force option was provided
# If not, ask the user if we need to overwrite the directory's content.
if has_file:
    message = f"Content detected in {path_video_folder}, do you wish to overwrite ? [Y/n]\n"  # noqa E501
    if overwrite or ask_yes_or_no(message):
        for f in files_to_remove:
            f.unlink()
    else:
        sys.exit()

# Run with default config if no config had been provided
# TODO: update default config
if config_path == "default":
    if test_mode:
        raise Exception("Cannot run in test mode with default configuration")
    config = DefaultConfig()
else:
    config = Config(Path(config_path).expanduser().absolute())


if test_mode:
    c = TestCamera(config, logger=root)
else:
    c = Camera(config, path_to_output=path_video_folder, logger=root, gst_debug_level=gst_debug_level)
c.capture()
