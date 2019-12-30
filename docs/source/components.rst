==========
Components
==========

Inputs
######

MeqSilhouette accepts as inputs various telescope, sky, and observation parameters. These are input in various formats and can be found in the *input* subdirectory.
Each subdirectory and its contents are explained in detail below. Samples for each category can be found in the source code.

input/antenna_tables
--------------------

The *antenna_tables* directory contains information on antennas participating in the observation, in the CASA ANTENNA table format.
Each interferometer array is a directory and can be opened and examined using the CASA tool *browsetable*.

input/jones_info
----------------

This directory contains information on individual Jones matrices that require detailed information. Currently, this is restricted to bandpass amplitudes for each station
and representative frequency in *.txt* format.

input/sky_models
----------------

This directory contains sky models in two different formats that are recognisable by MeqSilhouette: *.fits* and *.txt/.lsm.html*. The *.lsm.html* format is
compatible with **Tigger**, a software package that is part of the **MeqTrees** software suite.

Sky models in FITS image formats are forward-modelled using **WSClean** under the hood.
All FITS images corresponding to a single sky model are collected in a single subdirectory within the *sky_models* subdirectory.
The following naming convention applies to the individual FITS images:

* If there is no time-variability or polarization, the sky model directory contains only one FITS image named *t0000-model.fits*.

* If the sky model is time-variable, then the sky model directory contains a series of FITS images named *txxxx-model.fits*, where xxxx=0000, 0001, ...

* If the sky model is polarised, the FITS images are named *txxxx-[IQUV]-model.fits*, representing each Stokes component I, Q, U, V. Note that all Stokes components
  must be present.

.. note:: The total number of unique times (i.e., correlator dumps) are divided evenly between the input FITS images which are simulated into the column indicated by
 the parameter *ms_datacolumn* in the input JSON file (see `input/settings.json`_). Since **WSClean** can predict visibilities only into the MODEL_DATA column, MeqSilhouette will retain
 them in MODEL_DATA, while copying the same into *ms_datacolumn*, after which the signal corruptions are applied only to *ms_datacolumn*.

If the input is a *.txt/.lsm.html* file, it must be compatible with **MeqTrees**.

input/station_info
------------------

This directory contains *.txt* files that correspond to the arrays found in *input/antenna_tables*, with information on the following instrument/site/weather parameters
corresponding to each antenna in the array.

* **station** Station name/code
* **sefd[Jy]** System Equivalent Flux Density (SEFD) in Jansky
* **pwv[mm]** Precipitable water vapour in mm
* **gpress[mb]** Ground pressure at site in millibars
* **gtemp[K]** Ground temperature at site in Kelvin
* **c_time[sec]** atmospheric coherence time in seconds
* **ptg_rms[arcsec]** RMS error in pointing in arcseconds
* **PB_FWHM230[arcsec]** FWHM of the primary beam in arcseconds
* **PB_model** Geometric model to be used for the primary beam (hardwired to *gaussian* for now in the code regardless of the value of this parameter)
* **ap_eff** Aperture efficiency
* **gain[RL]_real, gain[RL]_imag** Real and imaginary parts of the RR and LL gain terms
* **leak[RL]_real, leak[RL]_imag** Real and imaginary parts of the complex polarization leakage for RR and LL
* **feed_angle[deg]** Initial feed angle offset in degrees
* **mount** Mount type of each station; valid values are ALT-AZ, ALT-AZ+NASMYTH-R, ALT-AZ+NASMYTH-L

input/settings.json
-------------------

* **outdirname** Name of the output directory in which to write all the output products of MeqSilhouette, with relative path to $MEQS_DIR

* **input_fitsimage** Name of the directory containing input fits images named using the naming convention explained in `input/sky_models`_, with relative path to $MEQS_DIR

* **input_fitspol**  Toggle 0 or 1 for polarisation simulation; integer or boolean

  .. note:: This does not apply when **input_fitsimage** is a *.txt/.lsm.html* file, since any polarisation info is read by MeqTrees automatically.

* **output_to_logfile** Toggle 0 or 1 to create 'logfile.txt' within **outdirname**; integer or boolean

* **add_thermal_noise** Toggle 0 or 1 to add baseline-dependent thermal noise, calculated using station SEFDs obtained from *station_info*; integer or boolean

* **make_image** Toggle 0 or 1 to make a dirty image using lwimager; integer or boolean. Other imagers such as WSClean and PyMORESANE to be used in the future.

* **exportuvfits** Toggle 0 or 1 to export MS to UVFITS; integer or boolean

* **station_info** Name of the file containing individual station info such as SEFD, coherence time, primary beam model etc., with relative path to $MEQS_DIR

* **bandpass_enabled** Toggle 0 or 1 to add complex bandpass corruptions (phases currently randomised to between -30 to +30 deg); integer or boolean

* **bandpass_table** Name of the *.txt* file containing bandpass gain amplitudes for each station for a set of frequencies, with relative path to $MEQS_DIR

* **bandpass_freq_interp_order** Order of spline interpolation; integer between 1 and 5

* **bandpass_makeplots** Toggle 0 or 1 to make bandpass plots; integer or boolean

* **elevation_limit** Flag visibilities below this elevation limit given in radians.

corr_quantbits: Number of bits used for quantization by the correlator -- for instance, 2 bits for 4 level quantization.
                Format: integer
                Units: bits
                e.g.: 2

predict_oversampling: Oversampling factor to improve the accuracy of forward modelling with wsclean. MUST BE AN ODD NUMBER.
                 Format: integer
                 e.g.: 8191

predict_seed:   Value of the seed for random number generation with numpy. Setting seed=-1 will disable seeding.
                Format: integer
                Units: none
                e.g.: 42

ms_antenna_table:       Input CASA antenna table to use for creating the Measurement Set. Samples can be found in input/antenna_tables
                        Format: string
                        e.g.: 'input/antenna_Tables/EHT2017_ANTENNA'

ms_datacolumn:  Specify the column in the Measurement Set in which to write the output visibilities.
                Format: string
                e.g.: 'DATA'

ms_RA:  Right Ascension of the pointing centre of the observation.
        Format: float
        Units: Degrees
        e.g.: 266.416837

ms_DEC: Declination of the pointing centre of the observation.
        Format: float
        Units: Degrees
        e.g.: -29.000781

ms_polproducts: Indicate how to interpret the polarization information of the 2 x 2 complex visibilities, based on whether the polarization feeds
                are circular or linear.
                Format: string
                e.g.: 'RR RL LR LL' or 'XX XY YX YY'

ms_nu:  Specify the centre frequency of the bandpass.
        Format: float

