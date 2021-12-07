"Helper functions for parsing user input."
import logging
import sys

def ask_yes_or_no(message, remaining_attempts=10):
    "Prompt a message and return True if the user confirms, False else."
    YES_VALUES = ["Y", "y", "yes", "YES", "Yes", "O", "o", "oui", "OUI", "Oui"]
    NO_VALUES = ["N", "n", "no", "NO", "No", "non", "NON", "Non"]
    user_input = str(input(message))

    if user_input in YES_VALUES:
        return True
    elif user_input in NO_VALUES:
        return False
    elif remaining_attempts == 0:
        raise ValueError("Input not undersood.")
    else:
        print("Input not understood, [Y/n] ?")
        return ask_yes_or_no("", remaining_attempts=remaining_attempts - 1)

# If files were detected, remove it if the --force option was provided
# If not, ask the user if we need to overwrite the directory's content.
def clean_output_dir(path_video_folder, overwrite):
    if path_video_folder.exists():
        files_to_remove = []
        for f in path_video_folder.iterdir():
            if f.suffix in [".mp4", ".avi", ".pickle", "mkv"]:
                files_to_remove.append(f)
        has_file = len(files_to_remove) > 0
    else:
        path_video_folder.mkdir(parents=True)
        logging.info(f"Created output directory ({path_video_folder})")
        has_file = False

    if has_file:
        message = f"Content detected in {path_video_folder}, do you wish to overwrite ? [Y/n]\n"  # noqa E501
        if overwrite or ask_yes_or_no(message):
            for f in files_to_remove:
                f.unlink()
        else:
            return False
    return True

def get_logger(name, stream_level, file_level, output_path):
    stream_numeric_level = getattr(logging, stream_level.upper(), 10)
    file_numeric_level = getattr(logging, file_level.upper(), 10)

    root_logger = logging.getLogger(name)
    root_logger.setLevel(level=logging.DEBUG)
    root_logger.propagate = False

    file_formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
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
