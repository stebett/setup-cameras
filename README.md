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
Remember to install the [pypwm](https://github.com/rfayat/PWM_Arduino) package

## Installation

Install the package and the dependencies with `(virtualenv) $ python setup.py install clean`

## Usage

To automatically create the configuration based on your connected cameras, run  
`(virtualenv) $ python -m tiscam.config` 

To start the recording:  
`(virtualenv) $ python -m tiscam.record -c path/to/params.json -o path/to/camera/dir`


You can activate the trigger mode from the **params.json**, refer to [pypwm](https://github.com/rfayat/PWM_Arduino) for documentation on usage.


### TODO

- [ ] Configuration put union in properties and diff in specific conf
- [ ] Automatically test with different parameters and save frame loss data
- [ ] Options for MJPEG + AVI and H.264/H.265 + MP4
- [ ] don't save empty videos
- [ ] check that all metatadata is written on videos
- [x] Implement non-dropping queue (?)
- [x] create_configs with automatic serial code
- [x] don't save empty videos
- [x] fix estimate framerate bug
- [x] First frame is 0
- [x] Wait at the beginning
- [x] Solve frame count issue
- [x] Remove open_device
- [x] Remove sinkformats
- [x] color/grayscale option
- [x] comment for identity position
- [x] standardize case convention
- [x] Autocheck for framedrop
- [x] Argument to set gst log level
- [x] Argument to set python log level
- [x] Argument to set log output to file
- [x] Exposure time auto check
- [x] single config file
