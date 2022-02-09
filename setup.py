"Run cameras from TIScamera"
import os
from setuptools import setup, Command

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')


def read(fname):
    "Read a file in the current directory."
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name="tiscam",
        version="0.2",
        author="Stefano Bettani",
        author_email="s.bettani@tuta.io",
        description=__doc__,
        install_requires=["gobject",
            "PyGObject",
            "PyQt5",
            "matplotlib",
            "toml",
            "vext",
            "vext.gi"],
        packages=["tiscam"],
        scripts=["scripts/check_timecourse", "scripts/run_all"],
        long_description=read('README.md'),
        cmdclass={ 'clean': CleanCommand }
        )

