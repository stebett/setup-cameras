"Start a recording from a json parameters file to an output folder."
import argparse
from pathlib import Path
from camera import Camera, TestCamera
from config import Config, DefaultConfig



parser = argparse.ArgumentParser(__doc__)
parser.add_argument("-c", "--config_",
                    help="Path to the state file of the camera",
                    dest="config_path", default="default")
parser.add_argument("-o", "--output",
                    help="Path to the output video folder.",
                    dest="path_video_folder", default=Path("./videos"),
                    type=lambda x: Path(x).expanduser())
parser.add_argument("-t", "--test",
                    help="Start in test mode",
                    dest="test_mode", action="store_true")

args = parser.parse_args()
config_path = args.config_path
path_video_folder = args.path_video_folder.absolute()
test_mode = args.test_mode

if config_path == "default":
    if test_mode:
        raise Exception("Cannot run in test mode with default configuration")
    config = DefaultConfig()
else:
    config = Config(Path(config_path).expanduser().absolute())


    
if test_mode:
    from test_camera import TestCamera
    c = TestCamera(config_path)
    c.initialize()
    c.capture()
else:
    c = Camera(config, path_to_output=path_video_folder)
    c.initialize()
    c.capture()
