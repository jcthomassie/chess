# -*- coding: utf-8 -*-
import io, os
from setuptools import setup, find_packages

from chess import name, __author__, __version__

# Package meta-data.
NAME = name
VERSION = __version__
AUTHOR = __author__
DESCRIPTION = "Pythonic chess interface with commandline game handler and GUI."
URL = "https://github.com/jcthomassie/chess"
REQUIRES_PYTHON = ">=3.5"
REQUIRED = [ "pygame",
            ]
PACKAGES = find_packages()

print("\n* * * * * * * * * Installing Package(s) * * * * * * * * *")
print("* Name = {}".format(NAME))
print("* Version = {}".format(VERSION))
print("* Author = {}".format(AUTHOR))
print("* \n* {}\n* ".format(DESCRIPTION))
print("* Requirements:\n*     {}\n* ".format("\n*     ".join(REQUIRED)))
print("* * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

# Import the README and use it as the long-description.
here = os.path.abspath(os.path.dirname(__file__))
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

############################
#        RUN SETUP         #
############################
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=PACKAGES,
    install_requires=REQUIRED,
    package_data={"chess": ["icons/*.png"]},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        ],
)

print("\n********** Finished Installing '{}' **********".format(NAME))