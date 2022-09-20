=====
Usage
=====

MeqSilhouette can be run in a number of ways. They all require that a JSON parset file is passed as
the sole argument.

--------------------
On the local machine
--------------------
If MeqSilhouette is installed on the local machine, it should already have the command
*meqsilhouette* in PATH and can be run as follows::

   $ meqsilhouette obs_settings.json

This command will run the driver script *run_meqsilhouette*. 

To use an existing MS, MeqSilhouette uses another driver script called *readms_runmeqs* which can be run as follows::

   $ python </path/to/readms_runmeqs.py> </path/to/input/json/parset/file> </path/to/existing/ms>

The existing MS will be copied to *output/inputs* directory and will be regularized if necessary i.e., missing baselines for all 
timestamps in the MS will be inserted, so that the MS used for corruptions contains a regular grid of visibility values.

.. note:: If using an existing MS, care must be taken to ensure that all timestamps from the beginning to the end are present in the MS. If there are missing timestamps, then tropospheric turbulence cannot be added, since this will cause the covariance matrix to be NOT positive definite and hence its Cholesky decomposition will fail.

---------------
Via Singularity
---------------
There are two ways to run MeqSilhouette via Singularity. In both cases, it is the responsibility
of the user to ensure that the relevant paths in the JSON parset file are writable.

Interactive mode
----------------
Interactively using the *shell* option::

   $ singularity shell meqsilhouette.sif # drops the user inside the container
   > meqsilhouette obs_settings.json

Command-line mode
-----------------
Invoke the *run* option::

   $ singularity run meqsilhouette.sif obs_settings.json

----------
Via Docker
----------
There are two ways to run MeqSilhouette via Docker as well. The interactive route is a bit more
involved while the command-line mode is more straightforward.

As before, it is the responsibility of the user to ensure that the relevant paths in the JSON parset
file are writable.

Interactive mode
----------------
A docker volume is the best way to share data between the container and the host.
First copy the relevant input files to a directory with write access. Assuming that
this directory is *~/data*, start the docker container as follows::

   $ docker run -dit -P -v ~/data:/meqsdata meqsilhouette

where */meqsdata* is an arbitrary mount point in the running container to which the host
directory *~/data* is to be bound.
The above command will print the container ID which is a long string of characters (this can also
be obtained by typing *docker ps -a* on the terminal). Once started, attach to the container
using the first four characters *xxxx* of this ID::

   $ docker attach xxxx

This will drop the user into the shell from which MeqSilhouette can be run as follows::

   $ meqsilhouette /meqsdata/obs_settings.json

Since */meqsdata* is where *~/data* is mounted, any output files must be written to */meqsdata*
for them to persist after the container is stopped. If the output files are written elsewhere,
the execution will still be successful, but the files will not persist in host storage.
To avoid this, the data generated must be manually copied into */meqsdata*.

Command-line mode
-----------------
More easily, the following command on the terminal (with all the caveats about paths to 
input/output files mentioned above) executes MeqSilhouette::

   $ docker run -v ~/data:/meqsdata meqsilhouette meqsilhouette /meqsdata/obs_settings.json

Note that the first *meqsilhouette* is the name of the image to be run and the second
*meqsilhouette* is the command that must be run within the container,
since no default entrypoint/command is defined.

------------------------
IPython/Jupyter Notebook
------------------------
Running MeqSilhouette from any Python interpreter is as easy as firing up the interpreter and
typing the following::

   > from meqsilhouette.driver import run_meqsilhouette
   > run_meqsilhouette.run_meqsilhouette('/path/to/JSON/parset/file')

The above command will run the default driver script shipped with the source code. This is the same
script run by the command *meqsilhouette* on the command-line in the above cases.

To run *readms_runmeqs*::

   > from meqsilhouette.driver import readms_runmeqs
   > readms_runmeqs.readms_runmeqs(</path/to/input/json/parset/file>, </path/to/existing/ms>)

For advanced users
------------------
MeqSilhouette provides two driver scripts by default.
Advanced users can construct their own versions of the driver script by importing the *framework* module in their code directly. 
For instance, additional operations on the Measurement Set such as flagging or averaging can be performed by an enhanced driver script tailored to the needs of the user.
