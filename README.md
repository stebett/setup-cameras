# Acquisition software for TheImagingSource cameras

Please Romain write the readme

### Installation

On Linux, follow the instruction to install the [tiscamera software](https://github.com/TheImagingSource/tiscamera)

Clone this repository, and run `pip install -r requirements.txt` inside it, with your virtual environment activated

If you have problems with the **gi** (PyGObject) package, you may have to link it in the site-packages of your virtual environment

Remember to install the `pwm_py` package from Romain


### Usage

`$ python record.py -p path/to/params.json -o path/to/camera/dir`

You can activate the trigger mode from the **params.json**.

### Files

- `TIS.py` defines the class `TIS ` that connects the camera to the pipeline
- `camera.py` extends the `TIS` class in order to initialize, set configuration and capture. The `Queue` class manages the creation of new videos, checking the delay, and recording the timestamps.
- `configs.py` defines a class to contain the configuration, useful for changing it interactively
- `record.py` is the script to start acquisition
- `create_configs.py` is a script that generates configuration taking as input the serial code of the camera
- `test_camera.py` extends the `Camera` class, adding methods to interactively change the properties of the camera
- `pwm.py` is a script to start a pwm given the config file
- `check_framerate.py` is a script to check frame drops, **still under developement**
- `start_recording.sh` is an helper script to start recording and creating directories, **still under developement**


### TODO

- [x] First frame is 0
- [x] Wait at the beginning
- [] autocheck for framedrop
