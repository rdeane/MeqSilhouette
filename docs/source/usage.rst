=====
Usage
=====

To run MeqSilhouette, a driver script (e.g. *driver/run_meqsilouette.py*) and a JSON configuration file (e.g. *input/eht230.json*) are needed.

There are two ways to run MeqSilhouette:

1. Through the terminal::

    $ python driver/run_meqsilhouette.py input/eht230.json

2. In a Juypter (ipython) Notebook::

    from run_meqsilhouette import *
    config = '/path/to/config.json' sim = run_meqsilhouette(config)

