"Start a recording from a toml parameters file to an output folder."
import sys
import signal
import argparse
from shutil import copyfile
from pathlib import Path

from tiscam.helpers import clean_output_dir, get_logger
from tiscam.camera import Camera
from tiscam.config import Config, read_config

# TODO refractor configs

def record(experiment_config, serial):
    config = experiment_config["tiscam"]

    camera_prefix = config["path"]["prefix"]
    overwrite = config["path"]["overwrite"]

    stream_log_level = config["logging"]["stream_level"]
    gst_debug_level = config["logging"]["gst_level"]
    file_log_level = config["logging"]["file_level"]

    compression_level = config["pipeline"]["compression_level"]
    max_buffers_queue = config["pipeline"]["max_buffers_queue"]

    session = Path(experiment_config["experiment"]["session"]).expanduser().absolute()
    block = experiment_config["experiment"]["block"]
    cam =  f"{camera_prefix}_{serial}"
    output_path = session / block / "video" / cam

    if not clean_output_dir(output_path, overwrite):
        sys.exit()
    logger = get_logger(f"cam_{serial}", stream_log_level, file_log_level, output_path / f"cam_{serial}.log") 


    camera_config = Config(experiment_config, serial)
    c = Camera(camera_config,
               logger=logger,
               path_to_output=output_path,
               gst_debug_level=gst_debug_level,
               compression_level=compression_level,
               max_buffers_queue=max_buffers_queue)

    c.start_capture()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-c", "--config_path",
                        help="Path to the state file of the camera",
                        dest="config_path", default="config.toml",
                        type=lambda x: Path(x).expanduser().absolute())
    parser.add_argument("-s", "--serial",
                        help="Serial of camera",
                        dest="serial", default=False)

    args = parser.parse_args()
    config_path = args.config_path
    experiment_config = read_config(config_path)
    serial = args.serial

    config_copy_path = output_path / config_path.name
    copyfile(config_path, config_copy_path)

    def terminate(*args):
        "Stop the capture and clean up."
        global c
        c.stop_capture()
        sys.exit()
    signal.signal(signal.SIGINT, terminate)

    camera_config = Config(experiment_config, serial)
    c = Camera(camera_config,
               logger=logger,
               path_to_output=output_path,
               gst_debug_level=gst_debug_level,
               compression_level=compression_level,
               max_buffers_queue=max_buffers_queue)

    c.start_capture()
