# Acquisition software for TheImagingSource cameras

Python code for setting up and launching video acquisition using TIS cameras.



## Installation
### Python requirements
Clone the repository and install the requirements **from a dedicated virtual environment**:
```bash
$ git clone https://github.com/stebett/setup-cameras.git
$ cd setup-cameras
$ pip install -r requirements.txt
```
This environment must be activated when running the tiscamera software installation.

### Tiscamera software
On Linux, install the [tiscamera software](https://github.com/TheImagingSource/tiscamera) as follows:
```bash
git clone https://github.com/TheImagingSource/tiscamera.git
cd tiscamera
sudo ./scripts/install-dependencies.sh --compilation --runtime
mkdir build
cd build
cmake -DBUILD_TOOLS=ON -DBUILD_V4L2=ON -DBUILD_LIBUSB=ON  ..
make
sudo make install
```

Troubles with the installation of the **gi module** can be solved [using one of these solutions](https://askubuntu.com/a/1045213). A few additional troubleshooting instructions are for instance available [here](https://githubmemory.com/repo/TheImagingSource/tiscamera/issues/397).


### Pwm software
Remember to install the [pwmpy](https://github.com/rfayat/PWM_Arduino) package


## Usage

`$ python record.py -p path/to/params.json -o path/to/camera/dir`

You can activate the trigger mode from the **params.json**.

## Files

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
>>>>>>> gst
