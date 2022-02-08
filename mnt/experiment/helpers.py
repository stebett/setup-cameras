import sys
import toml
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def read_config(path):
    "Read the configuration file."
    try:
        with path.open("r") as f:
            return toml.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("Invalid config file")


def get_logger(name, stream_level, file_level, output_path):
    stream_numeric_level = getattr(logging, stream_level.upper(), 10)
    file_numeric_level = getattr(logging, file_level.upper(), 10)

    root_logger = logging.getLogger(f"{name}")
    root_logger.setLevel(level=logging.DEBUG)
    root_logger.propagate = False

    file_formatter = logging.Formatter('%(name)s: %(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S')
    file_handler = logging.FileHandler(output_path, mode="w")
    file_handler.setLevel(level=file_numeric_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    stream_formatter = logging.Formatter('%(name)s: %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level=stream_numeric_level)
    stream_handler.setFormatter(stream_formatter)
    root_logger.addHandler(stream_handler)

    return root_logger

def parse_config_path():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-c", "--config-path",
            help="Config path",
            dest="config_path", default="configs.toml", type=lambda x: Path(x).expanduser().absolute())

    args = parser.parse_args()
    return args.config_path
