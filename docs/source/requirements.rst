===========================
Requirements & Installation
===========================

Ubuntu 18.04 + Python 2.7
-------------------------
  
It is recommended to install the dependencies via the `KERN-6 <https://kernsuite.info>`_ software suite::

   $ sudo apt-get install software-properties-common
   $ sudo add-apt-repository -s ppa:kernsuite/kern-6
   $ sudo apt-add-repository multiverse
   $ sudo apt-add-repository restricted
   $ sudo apt-get update

Install the following dependencies via *apt-get*::

   $ sudo apt-get install meqtrees meqtrees-timba tigger tigger-lsm python-astro-tigger \
   python-astro-tigger-lsm casalite wsclean pyxis python-casacore

Install the following non-standard python libraries::

   $ pip install mpltools seaborn astLib astropy termcolor numpy matplotlib pyfits simms

*AATM v0.5* can be obtained from `here <http://www.mrao.cam.ac.uk/~bn204/soft/aatm-0.5.tar.gz>`_. AATM cannot create the executables necessary for running MeqSilhouette without the *boost* libraries. In Ubuntu 18.04, ensure that the packages *libboost-program-options-dev*, *libboost-program-options1.65-dev*, and *libboost-program-options1.65.1* are installed. Once these are installed, proceed as follows::

   $ cd /path/to/aatm-source-code
   $ ./configure --prefix=/path/to/aatm-installation
   $ make
   $ make install
   $ export PATH=$PATH:/path/to/install/aatm-installation/bin

Optionally, install Latex (for creating paper-quality plots)::

  $ sudo apt-get install texlive-latex-extra texlive-fonts-recommended dvipng

If using a virtual environment, the following steps are necessary (skip if not using virtualenv)::

   $ virtualenv /path/to/env
   $ source /path/to/env/bin/activate
   $ pip install -U pip setuptools wheel # recommended

  .. note:: If --system-site-packages is not passed to virtualenv, the global packages installed via apt-get above will not be available and must be installed manually from source.

Now, check out MeqSilhouette `version 2.7 <https://github.com/rdeane/MeqSilhouette/tree/v2.7>`_ from GitHub::

   $ git clone --branch v2.7 https://github.com/rdeane/MeqSilhouette.git
   $ cd MeqSilhouette
   $ pip install .   

The *turbo-sim.py* script from MeqTrees is included in the *framework* directory. If you do not have it, add a symbolic link to the copy in your *meqtrees-cattery* installation::

   $ ln -s /path/to/meqtrees-cattery/Cattery/Siamese/turbo-sim.py /path/to/MeqSilhouette/framework/turbo-sim.py

Building Singularity & Docker images
------------------------------------

MeqSilhouette can be run via *Singularity* and *Docker*, which ensures portability and reproducibility.

The singularity definition file *singularity.def* is shipped with the repository. If you do not have Singularity installed on your system, follow the installation instructions on the `Singularity website <https://sylabs.io/guides/3.5/admin-guide/installation.html>`_. Once Singularity is installed, the singularity image file (SIF) can be created as follows::

   $ sudo singularity build meqsilhouette.sif singularity.def

.. todo:: Add instructions for Docker

Known installation issues
-------------------------

1. If MeqTrees cannot see the *TiggerSkyModel* module that ought to load when *turbo-sim.py* is run (i.e. when an ASCII sky model is used), the parent directory of *Tigger* must be added to PYTHONPATH. Bear in mind that this may cause python version conflicts with other packages. In that case, it is recommended to have Tigger installed in a separate directory such as /opt/Tigger. For manual installation of `Tigger <https://github.com/ska-sa/tigger>`_ and `tigger-lsm <https://github.com/ska-sa/tigger-lsm>`_, refer to their respective repositories. Without this, MeqSilhouette will still work with FITS images as input sky models.

2. If MeqSilhouette cannot find aatm, modify LD_LIBRARY_PATH as follows::

    export LD_LIBRARY_PATH=/path/to/aatm-0.5/lib:$LD_LIBRARY_PATH

3. If the error *Incorrect qhull library called* is thrown, ensure **scipy==0.17** is installed.

4. MeqSilhouette will soon be ported to *astropy.fits* and *pyfits* will no longer be a dependency. As of now though, *pyfits* is still required. If *pyfits* throws an ImportError for the modules *gdbm/winreg*, a quick and dirty fix is to open the following file::

    /path-to-virtualenv/lib/python2.7/site-packages/pyfits/extern/six.py

   and comment out the lines::

    MovedModule("dbm_gnu", "gdbm", "dbm.gnu")
    MovedModule("winreg", "_winreg")
