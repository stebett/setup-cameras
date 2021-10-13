import argparse
from pathlib import Path
from camera import Camera


parser = argparse.ArgumentParser(__doc__)
parser.add_argument("config_path",
                    help="Path to the state file of the camera")
parser.add_argument("-o", "--output",
                    help="Path to the output video folder.",
                    dest="path_video_folder", default="./videos")

args = parser.parse_args()
config_path = str(args.config_path)
path_video_folder = str(Path(args.path_video_folder).absolute())

c = Camera(config_path, expected_frames=50, timeout_delay=.5, path_to_output=path_video_folder)
c.initialize()
c.start_capture()


