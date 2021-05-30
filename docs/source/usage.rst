=====
Usage
=====

MeqSilhouette can be run in a number of ways. They all require that a JSON parset file is passed as the sole argument.

1. If installed via pip::

   $ meqsilhouette obs_settings.json

2. Via Singularity.

Interactively using the *shell* option::

   $ singularity shell meqsilhouette.sif # drops the user inside the container
   > meqsilhouette obs_settings.json

By invoking the *run* option::

   $ singularity run meqsilhouette.sif obs_settings.json

3. Interactive mode (IPython/Jupyter Notebook)::

    from meqsilhouette.driver import run_meqsilhouette
    run_meqsilhouette('/path/to/JSON/parset/file')

For advanced users
------------------
By default, the *driver* script included with the source code will be used to parse the JSON file and generate the synthetic data. Advanced users can construct their own version of the driver script by importing the *framework* module in their code directly. For instance, additional operations on the Measurement Set such as flagging or averaging can be performed by an enhanced driver script tailored to the needs of the user.
