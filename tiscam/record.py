"Start a recording from a json parameters file to an output folder."
import sys
import signal
import logging
import argparse
from pathlib import Path

from tiscam.input_helpers import ask_yes_or_no
from tiscam.camera import Camera, TestCamera
from tiscam.config import Config 


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
parser.add_argument("-i", "--camera-id",
                    help="Identifier of camera",
                    dest="cam_id", default="-1",
                    type=lambda x: int(x))

args = parser.parse_args()
config_path = args.config_path
path_video_folder = args.path_video_folder.absolute()
test_mode = args.test_mode
overwrite = args.overwrite
log_level = args.log_level
cam_id = args.cam_id
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
    raise Exception("record: invalid log level!\nTry '--help' for more information.")

root_logger = logging.getLogger()
root_logger.setLevel(level=level)

# List the avi and pickle files in the folder
if path_video_folder.exists():
    files_to_remove = []
    for f in path_video_folder.iterdir():
        if f.suffix in [".avi", ".pickle"]:
            files_to_remove.append(f)
    has_file = len(files_to_remove) > 0
else:
    path_video_folder.mkdir(parents=True)
    root_logger.info(f"Created output directory ({path_video_folder})")
    has_file = False

handler = logging.FileHandler(path_video_folder / "record.log", mode="w")
handler.setLevel(level=logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
handler.setFormatter(formatter)
root_logger.addHandler(handler)

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
    raise Exception("You have to provide a configuration")
else:
    config_path = Path(config_path).expanduser().absolute()
    config = Config(config_path, root_logger, cam_id)


if test_mode:
    c = TestCamera(config, logger=root_logger)
else:
    c = Camera(config, path_to_output=path_video_folder,
               logger=root_logger, gst_debug_level=gst_debug_level)


# Attach interruption signal to stop_capture and start the recording
def cleanup(*args):
    "Stop the capture and clean up."
    global c
    c.stop_capture()
    sys.exit()


config.save(path_video_folder / config_path.name)
signal.signal(signal.SIGINT, cleanup)
c.start_capture()
