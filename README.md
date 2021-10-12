# Acquisition software for TheImagingSource cameras

Please Romain write the readme

### Installation

On Linux, follow the instruction to install the [tiscamera software](https://github.com/TheImagingSource/tiscamera)

Clone this repository, and run `pip install -r requirements.txt` inside it, with your virtual environment activated

If you have problems with the `gi` (PyGObject) package, you may have to link it in the site-packages of your virtual environment


### Usage

`$ python record.py -p path/to/params.json -o path/to/camera/dir`

You can activate the trigger mode from the `params.json`.
