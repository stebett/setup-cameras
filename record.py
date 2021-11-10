"Start a recording from a json parameters file to an output folder."
import sys
import argparse
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

args = parser.parse_args()
config_path = args.config_path
path_video_folder = args.path_video_folder.absolute()
test_mode = args.test_mode
overwrite = args.overwrite

# List the avi and pickle files in the folder
if path_video_folder.exists():
    files_to_remove = []
    for f in path_video_folder.iterdir():
        if f.suffix in [".avi", ".pickle"]:
            files_to_remove.append(f)
    has_file = len(files_to_remove) > 0
else:
    has_file = True

# If files were detected, remove it if the --force option was provided
# If not, ask the user if we need to overwrite the directory's content.
if has_file:
    message = f"Content detected in {path_video_folder}, do you wish to overwrite ? [Y/n]\n"  # noqa E501
    if overwrite or ask_yes_or_no(message):
        for f in files_to_remove:
            f.unlink()
    else:
        sys.exit()

if config_path == "default":
    if test_mode:
        raise Exception("Cannot run in test mode with default configuration")
    config = DefaultConfig()
else:
    config = Config(Path(config_path).expanduser().absolute())


if test_mode:
    from test_camera import TestCamera
    c = TestCamera(config)
else:
    c = Camera(config, path_to_output=path_video_folder)
c.initialize()
c.capture()
