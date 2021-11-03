"""
Helpers for handling video.
Author: Romain Fayat, June 2020
"""
import cv2
import numpy as np
from tqdm import tqdm

# Properties of video capture objects
CAPTURE_PROPS = [
    "POS_MSEC", "POS_FRAMES", "POS_AVI_RATIO", "FRAME_WIDTH", "FRAME_HEIGHT",
    "FPS", "FOURCC", "FRAME_COUNT", "FORMAT", "MODE", "BRIGHTNESS", "CONTRAST",
    "SATURATION", "HUE", "GAIN", "EXPOSURE", "CONVERT_RGB",
    "WHITE_BALANCE_BLUE_U", "RECTIFICATION", "MONOCHROME", "SHARPNESS",
    "AUTO_EXPOSURE", "GAMMA", "TEMPERATURE", "TRIGGER", "TRIGGER_DELAY",
    "WHITE_BALANCE_RED_V", "ZOOM", "FOCUS", "GUID", "ISO_SPEED", "BACKLIGHT",
    "PAN", "TILT", "ROLL", "IRIS", "SETTINGS", "BUFFERSIZE", "AUTOFOCUS",
    "SAR_NUM", "SAR_DEN", "BACKEND", "CHANNEL", "AUTO_WB", "WB_TEMPERATURE",
    "CODEC_PIXEL_FORMAT", "BITRATE"
]


def to_uint8(arr):
    "Rescale an array and convert it to uint8."
    arr = arr.astype(np.float)  # Avoid computation issues (rounding...)
    arr = 255 * (arr - arr.min()) / (arr.max() - arr.min())
    return np.round(arr).astype(np.uint8)


def fig_to_array(fig):
    """Draw a matplotlib figure and convert it to an image as a uint8 numpy
    array.
    """
    fig.canvas.draw()
    arr = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep="")
    arr = arr.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return arr


def get_capture_props(capture):
    """Get the video properties from a video capture.
    Inputs
    ------
    capture, cv2.VideoCapture or str
        Video capture (video opened with opencv) or path to a video.
    Returns
    -------
    props, dict
        Dictionary with format {"property_name": property_value}. In opencv,
        the capture properties's names start with "CAP_PROP_", it is not the
        case here.
    Example
    -------
    >>> props = get_capture_props("path/to/video.avi")
    >>> print(props["FPS"])
    30.0
    Notes
    -----
    A list of the available properties can be found at:
    https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
    """  # noqa E501
    # Argument parsing
    if isinstance(capture, cv2.VideoCapture):
        pass
    elif isinstance(capture, str):
        capture = cv2.VideoCapture(capture)
    else:
        raise(ValueError(
            f"""Input must but be a VideoCapture object or the path to a video.
            Got {type(capture)} instead."""))  # noqa E501

    props = {}
    for prop_name in CAPTURE_PROPS:
        try:
            prop_accessor = getattr(cv2, "CAP_PROP_" + prop_name)
        except AttributeError:
            continue  # Go to the next prop

        props[prop_name] = capture.get(prop_accessor)

    return props


class VideoCaptureRGB(cv2.VideoCapture):
    "Same as opencv VideoCapture but RGB by default."

    def read(self):
        "Read the next frame and convert it to RGB before returning it."
        ret, img = super().read()
        return ret, np.flip(img, 2)  # BGR to RGB

    def grab_properties(self):
        """Grab the width, height and number of frames of the video and store
        them as attributes.
        """
        props = get_capture_props(self)
        self.w = int(props["FRAME_WIDTH"])  # width of the frames
        self.h = int(props["FRAME_HEIGHT"])  # height of the frames
        self.n_frames = int(props["FRAME_COUNT"])  # number of frames


class VideoCaptureToArray(VideoCaptureRGB):
    """Same as opencv VideoCapture with a method for reading a whole video.
    We also use a RGB convention by default (opencv: BGR).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grab_properties()

    def preallocate_frame_stack(self):
        """Preallocate the array that will be used to store the whole video.
        Warning: For now, return a
        Returns
        -------
        arr, array, shape: (n_frames, h, w, 3)
            uint8 array (zeros) that will be used to store the full video.
        Notes
        -----
        The shape of 3 for the last dimension corresponds to RGB, need to check
        the compatibility with B&W videos.
        """
        shape = (self.n_frames, self.h, self.w, 3)  # error for B&W ?
        arr = np.zeros(shape, dtype=np.uint8)
        return arr

    def read_all(self, show_progress=False):
        frame_all = self.preallocate_frame_stack()
        # Frame number that will iterate over
        frame_count = range(self.n_frames)
        frame_count = tqdm(frame_count) if show_progress else frame_count
        # Grab the frames one by one
        for count in frame_count:
            ret, frame = self.read()  # Capture frame-by-frame
            if ret:
                frame_all[count] = frame
            else:  # Could not read the frame
                break
        return frame_all

    def go_to_frame(self, frame_number):
        "Set a frame number to be the next one that will be read"
        if self.current_frame != frame_number:
            return super().set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        else:
            return True

    @property
    def current_frame(self):
        "Return the current frame number"
        return super().get(cv2.CAP_PROP_POS_FRAMES)


def frames_from_video(path, show_progress=False):
    "Extract the frames from a video and return a uint8 array."
    cap = VideoCaptureToArray(path)
    return cap.read_all(show_progress=show_progress)


class VideoWriterRGB(cv2.VideoWriter):
    "Same as opencv VideoWriter but for RGB input (instead of BGR)."

    def write(self, img):
        "Write a new frame to the video after converting it from RGB to BGR."
        return super().write(np.flip(img, 2))  # RGB to BGR


class VideoWriterFromArray(VideoWriterRGB):
    """Wrapper for cv2.VideoWriter with commonly used parameters.
    Instantiation
    * fps (def: 30) and fourcc (def: cv2.VideoWriter_fourcc("X", "V", "I","D"))
      args become kwargs
    * The VideoWriter object is truly instantiated when writting the first
      frame. The size argument is deduced here.
    Use
    * A iterable of numpy arrays can be used to write multiple frames at once
      using the write_stack method.
    * We use RGB instead of BGR by default.
    """

    def __init__(self, filename, fourcc_params="XVID", fps=30):
        self.filename = filename
        self.fps = fps
        self.fourcc = cv2.VideoWriter_fourcc(*fourcc_params)
        self._is_init = False

    def _init_VideoWriter(self, size, is_color):
        super().__init__(self.filename, self.fourcc, self.fps, size, is_color)
        self._is_init = True

    def write(self, img):
        "Write a new frame to the video."
        if not self._is_init:
            if not isinstance(img, np.ndarray):
                img_shape = cv2.UMat.get(img).shape
            else:
                img_shape = img.shape
            size = (img_shape[1], img_shape[0])
            is_color = len(img_shape) == 3 and img_shape[-1] == 3  # RGB
            self._init_VideoWriter(size, is_color)
        # Write the frame
        return super().write(img)  # RGB to BGR

    def write_stack(self, img_stack, release=True, show_progress=False):
        """Write a stack of frames to the video and optionaly realease the
        VideoWriter.
        Inputs
        ------
        img_stack, iterable of arrays
            Iterable containing the frames. If the data type of img_stack is
            not uint8, convert it to uint8 using a minmax scaler.
        release, bool (default: True)
            Call cv2.VideoWriter.release after writing the stack.
        show_progress, bool (default: False)
            Display a progress bar while writting the frames.
        """
        # Convert to uint8
        if img_stack.dtype != np.uint8:
            img_stack = to_uint8(img_stack)
        # Progress bar
        if show_progress:
            img_stack = tqdm(img_stack)
        # Write the frames
        for img in img_stack:
            self.write(img)
        # Release the VideoWriter
        if release:
            super().release()


def write_text_on_frame(frame, text, **kwargs):
    "Write text on a frame"
    kw = {
        "org": (50, 50),
        "fontFace": cv2.FONT_HERSHEY_SIMPLEX,
        "fontScale": 1,
        "color": (0, 255, 255),
        "thickness": 2,
        "lineType": cv2.LINE_4
    }
    kw.update(kwargs)
    # Add the text to the frame
    cv2.putText(frame, text, **kw)
    return frame


if __name__ == "__main__":
    from os.path import abspath, dirname  # noqa E402
    path = dirname(dirname(abspath(__file__)))  # IMU_analysis/imu_analysis
    path = path + "scripts/video_examples/example/example_video.avi"
    print(frames_from_video(path, show_progress=True))
