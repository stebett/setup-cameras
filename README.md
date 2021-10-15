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

## Tiscamera software
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

## Usage

`$ python record.py -p path/to/params.json -o path/to/camera/dir`
