# Synthetic data simulation package for the Event Horizon Telescope 

## Requirements

[simms](https://github.com/radio-astro/simms):  python wrapper for creating empty Measurement Sets using the CASA simulate tool

[MeqTrees](http://meqtrees.net): implements the Radio Interferometry Measurement Equation

[Pyxis](https://github.com/ska-sa/pyxis/): python-esque scripting language for MeqTrees 

[Astropy](http://www.astropy.org/): v1.3 and above

[CASA](https://casa.nrao.edu/casa_obtaining.shtml): v4.3 and above

[AATM v0.5](http://www.mrao.cam.ac.uk/~bn204/soft/aatm-0.5.tar.gz): mean atmospheric simulator (average opacities, sky brightness temp).


## List of Python modules used

- numpy
- matplotlib
- pyfits
- pyrap
- astropy
- termcolor
- time
- glob
- os
- sys
- mpltools
- seaborn

# Usage

## PATHS to set
Add the following to the PATH enviroment variable:
- /path/to/simms/simms/bin
- /path/to/CASA/bin

And the following to your PYTHONPATH:
- /path/to/MeqSilhouette/framework


Add the following environment variable to point to your MeqSilhouette directory:

export MEQS_DIR=/path/to/MeqSilhouette

Finally, add the symbolic link:

- ln -s /path/to/meqtrees-cattery/Siamese/turbo-sim.py /path/to/MeqSilhouette/framework/turbo-sim.py



## Running MeqSilhouette
To run this synthetic data generator, you need:

1. a driver script (e.g. driver/run_meqsilouette.py)
2. a configuration file (input/eht230.json is an example.)


The software can be run in three primary modes:

### 1. Through the terminal

$python driver/run_meqsilhouette.py input/eht230.json

### 2. In a Juypter (ipython) Notebook

Start up notebook

from run_meqsilhouette import *

config = '/path/to/config.json'
sim = run_meqsilhouette(config)

### In a Docker container

While setting up the required enviroment to run MeqSilhouette is just a few step process (for Ubuntu 14.04, 16.04),
one can avoid system dependencies entirely with Docker.

[add instructions here]

### Configuration file

All paths a relative to $MEQS_DIR defined above

The configuration file is a simple .json file and contains the basic observational setup which are loosely grouped into the following parameter groups:

* general parameters (paths, output options, etc.)
* measurement set parameters (pre-pended with "ms_")
* imaging parameters (pre-pended with "im_")
* tropospheric parameters (pre-pended with a "trop_")
* antenna pointing error parameters (pre-pended "pointing_")

The following two important paths are specified in the configuration file:

* "ms_antenna_table": input ANTENNA table for chosen array (CASA format)
* "station_info" input station-specific information (SEFDs, station names)

## Commonly encountered problems
1. If MeqSilhouette cannot find aatm, add the following paths to the following environment variables:

export LD_LIBRARY_PATH=/path/to/aatm-0.5/lib:$LD_LIBRARY_PATH

export PATH=/path/to/aatm-0.5/bin:$PATH

2. aatm will not compile without boost program options. In ubuntu 16.04, the relevant packages are libboost-program-options-dev, libboost-program-options1.58-dev, and libboost-program-options1.58.0


## Additional links

* Measurement Set structure and definition [link](https://casa.nrao.edu/Memos/229.html)