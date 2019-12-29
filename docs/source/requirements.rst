===========================
Requirements & Installation
===========================

Requirements:
-------------

MeqSilhouette v2 depends on the following software packages:

   * `WSClean <https://sourceforge.net/p/wsclean/wiki/Home/>`_
   * `MeqTrees <http://meqtrees.net>`_
   * `CASA (v5 or above) <https://casa.nrao.edu/casa_obtaining.shtml>`_
   * `Pyxis <https://github.com/ska-sa/pyxis/>`_
   * `simms <https://github.com/radio-astro/simms>`_
   * `AATM v0.5 <http://www.mrao.cam.ac.uk/~bn204/soft/aatm-0.5.tar.gz>`_

The following non-standard python libraries are required:

   * numpy
   * matplotlib
   * pyfits
   * pyrap
   * termcolor
   * mpltools
   * seaborn

Installation:
-------------

Add the following to the PATH enviroment variable (if they are not installed in standard locations)::

    export PATH=/path/to/simms/simms/bin:/path/to/CASA/bin:$PATH

And the following to the PYTHONPATH environment variable::

    export PYTHONPATH=/path/to/MeqSilhouette/framework:$PYTHONPATH

Add the following environment variable to point to your MeqSilhouette directory::

    export MEQS_DIR=/path/to/MeqSilhouette

Finally, add a symbolic link to the MeqTrees simulator script to the framework directory within MeqSilhouette::

    ln -s /path/to/meqtrees-cattery/Siamese/turbo-sim.py /path/to/MeqSilhouette/framework/turbo-sim.py


