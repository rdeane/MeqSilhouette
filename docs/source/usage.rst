=====
Usage
=====

To run MeqSilhouette, a driver script (e.g. *driver/run_meqsilouette.py*) and a JSON configuration file (e.g. *input/eht230.json*) are needed. Scripts and input files necessary for a basic MeqSilhouette run are provided with the source code. There are multiple ways to run MeqSilhouette.

.. note:: When passing FITS images as input sky models, ensure that the sky model directory (the value of the parameter *input_fitsimage* in *obs_settings.json*) is writable.

1. Via the terminal::

    $ python driver/run_meqsilhouette.py input/eht230.json

2. Via Singularity.

Interactively using the *shell* option::

   $ singularity shell meqsilhouette.sif # drops the user inside the container
   $ python /opt/MeqSilhouette/driver/run_meqsilhouette.py obs_settings.json

By invoking the *run* option::

   $ singularity run meqsilhouette.sif obs_settings.json

3. In a Juypter (ipython) Notebook::

    from driver.run_meqsilhouette import *
    config = '/path/to/config.json' sim = run_meqsilhouette(config)
