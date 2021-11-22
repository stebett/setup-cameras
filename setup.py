"Run cameras from TIScamera"
import os
from setuptools import setup


def read(fname):
    "Read a file in the current directory."
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="tiscam",
      version="0.1",
      author="Stefano Bettani",
      author_email="s.bettani@tuta.io",
      description=__doc__,
      install_requires=["gobject",
                        "PyGObject",
                        "PyQt5",
                        "matplotlib",
                        "vext",
                        "vext.gi"],
      packages=["tiscam"],
      long_description=read('README.md'),
      )

