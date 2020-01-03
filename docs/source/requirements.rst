===========================
Requirements & Installation
===========================

Requirements
------------

MeqSilhouette depends on the following software packages:

   * `WSClean <https://sourceforge.net/p/wsclean/wiki/Home/>`_
   * `MeqTrees <http://meqtrees.net>`_
   * `CASA (v5.4 or above) <https://casa.nrao.edu/casa_obtaining.shtml>`_
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

Installation
------------

Steps to build MeqSilhouette on Ubuntu 18.04:

* Install KERN and follow the few-step instructions
* Install the following packages using apt-get: **meqtrees, casalite, simms, pyxis, wsclean**
* Build **aatm**
* Add the following paths:

  Add the following to the PATH enviroment variable (if they are not installed in standard locations)::

    export PATH=/path/to/simms/simms/bin:/path/to/CASA/bin:$PATH

  And the following to the PYTHONPATH environment variable::

    export PYTHONPATH=/path/to/MeqSilhouette/framework:$PYTHONPATH

  Add the following environment variable to point to your MeqSilhouette directory::

    export MEQS_DIR=/path/to/MeqSilhouette

* Finally, add a symbolic link to the MeqTrees simulator script to the framework directory within MeqSilhouette::

    ln -s /path/to/meqtrees-cattery/Siamese/turbo-sim.py /path/to/MeqSilhouette/framework/turbo-sim.py

.. note:: If installing in a virtual environment, a number of python packages mentioned under 'Requirements' must be installed.

Commonly encountered problems
-----------------------------

The following is a collection of the list of errors encountered while installing/running MeqSilhouette.

1. If MeqSilhouette cannot find aatm, add the following paths to the following environment variables::

    export LD_LIBRARY_PATH=/path/to/aatm-0.5/lib:$LD_LIBRARY_PATH
    export PATH=/path/to/aatm-0.5/bin:$PATH

2. AATM will not compile without *boost* libraries. In Ubuntu 18.04, the relevant packages are **libboost-program-options-dev**, **libboost-program-options1.65-dev**, and **libboost-program-options1.65.1**.

3. If the error *Incorrect qhull library called* is thrown, ensure **scipy==0.17** is installed.

4. If an ImportError is thrown by **pyfits** for the modules *gdbm/winreg*, a quick and dirty fix is to open the file::

    /path-to-virtualenv/lib/python2.7/site-packages/pyfits/extern/six.py

   and comment out the lines::

    MovedModule("dbm_gnu", "gdbm", "dbm.gnu")
    MovedModule("winreg", "_winreg")

.. note:: MeqSilhouette will soon be ported to astropy.fits and pyfits will no longer be a dependency. As of now, pyfits is still being used.
