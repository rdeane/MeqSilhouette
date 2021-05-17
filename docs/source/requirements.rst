===========================
Requirements & Installation
===========================

Ubuntu 18.04 + Python 2.7:
--------------------------
  
It is recommended to install the `KERN-5 <https://kernsuite.info>`_ software suite which makes it easy to install many dependencies of MeqSilhouette::

   $ sudo apt-get install software-properties-common
   $ sudo add-apt-repository -s ppa:kernsuite/kern-5
   $ sudo apt-add-repository multiverse
   $ sudo apt-add-repository restricted
   $ sudo apt-get update

Install the following dependencies via **apt-get**::

   $ sudo apt-get install meqtrees casalite wsclean simms pyxis python-casacore

`Download <http://www.mrao.cam.ac.uk/~bn204/soft/aatm-0.5.tar.gz>`_ and build AATM v0.5::

   $ cd /path/to/aatm-0.5-source-code
   $ ./configure --prefix=/path/to/aatm-0.5-installation
   $ make
   $ make install

Add the built executables to PATH::

   $ export PATH=$PATH:/path/to/install/aatm-0.5-installation/bin

Install Latex (for creating paper-quality plots)::

  $ sudo apt-get install texlive-fonts-recommended texlive-fonts-extra dvipng

The following non-standard python libraries are required and can be installed via **pip**:

  * mpltools
  * seaborn
  * astLib
  * astropy
  * termcolor
  * numpy
  * matplotlib
  * pyfits

Add the following to the PATH enviroment variable (if they are not installed in standard locations)::

    export PATH=/path/to/simms/simms/bin:/path/to/CASA/bin:$PATH

And the following to the PYTHONPATH environment variable::

    export PYTHONPATH=/path/to/MeqSilhouette/framework:$PYTHONPATH

Add the following environment variable to point to your MeqSilhouette directory::

    export MEQS_DIR=/path/to/MeqSilhouette

The **turbo-sim.py** script from MeqTrees is included in the *framework* directory. If you do not have it, add a symbolic link to the original file in your MeqTrees installation::

    ln -s /path/to/meqtrees-cattery/Siamese/turbo-sim.py /path/to/MeqSilhouette/framework/turbo-sim.py

.. todo:: MeqSilhouette + Docker/Singularity

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
