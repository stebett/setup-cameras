import argparse
from pathlib import Path
from camera import Camera


parser = argparse.ArgumentParser(__doc__)
parser.add_argument("config_path",
                    help="Path to the state file of the camera")
parser.add_argument("-o", "--output",
                    help="Path to the output video folder.",
                    dest="path_video_folder", default="./videos")
parser.add_argument("-t", "--test",
                    help="Start in test mode",
                    dest="test_mode", action="store_true")

args = parser.parse_args()
config_path = str(args.config_path)
path_video_folder = str(Path(args.path_video_folder).absolute())
test_mode = args.test_mode

c = Camera(config_path, path_to_output=path_video_folder, test_mode=test_mode)
c.initialize()
c.capture()
