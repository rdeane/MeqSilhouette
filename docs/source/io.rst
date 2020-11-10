==================
Inputs and Outputs
==================

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

Each line consists of the station name and a tuple **(bpass_ampl_pol1, bpass_ampl_pol2)** for each representative frequency.

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

* If the sky model is frequency-variable, then the sky model directory contains a series of FITS images named *t0000-xxxx-model.fits*, where xxxx=0000, 0001, ... This must be equal to
  the value of the input parameter **input_changroups** in the input *settings.json* file.

.. note:: Following **WSClean**, **MeqSilhouette** does not care about the actual frequencies in the FITS files. This means that the input channels will be divided into **input_changroups**
 number of groups and the corresponding frequency images will be written to the appropriate channel group, regardless of the frequencies in the FITS files. This may change in the future to
 accommodate any relevant changes to the behaviour of **WSClean**.

* Putting all of the above together, a time and frequency varible polarised sky model will consist of a series of FITS files named *txxxx-yyyy-[I,Q,U,V]-model.fits*, where
  xxxx=0000, 0001, .... (as many as needed) and yyyy=0000, 0001, .... (must be equal to the value of **input_changroups**).

.. note:: The total number of unique times (i.e., correlator dumps) are divided evenly between the input FITS images which are simulated into the column indicated by
 the parameter *ms_datacolumn* in the input JSON file (see `input/settings.json`_). Since **WSClean** can predict visibilities only into the MODEL_DATA column, MeqSilhouette will retain
 them in MODEL_DATA, while copying the same into *ms_datacolumn*, after which the signal corruptions are applied only to *ms_datacolumn*. Hence, the uncorrupted visibilities are available
 in MODEL_DATA column.

If the input is a *.txt/.lsm.html* file, it must be compatible with **MeqTrees**.

.. image:: LSM.png
    :width: 764px
    :align: center
    :height: 579px
    :alt: MeqTrees compatible LSM format

.. note:: It is recommended to use FITS images as inputs. ASCII sky models are only used for testing and specific experiments. 
 MeqTrees can potentially offset the sources by +/-1 uas due to precision errors which is an outstanding issue as of now.

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
* **g[RL]_mean, g[RL]_std** Mean and standard deviation of the normal distribution from which to draw time-varying real/imag parts of the G-Jones terms for R and L feeds
* **d[RL]_mean, d[RL]_std** Mean and standard deviation of the normal distribution from which to draw time-and-frequency-varying real/imag parts of the D-Jones terms for R and L feeds
* **feed_angle[deg]** Initial feed angle offset in degrees
* **mount** Mount type of each station; valid values are ALT-AZ, ALT-AZ+NASMYTH-R, ALT-AZ+NASMYTH-L

input/settings.json
-------------------

The configuration file is a *.json* file with parameters that are loosely grouped into the following groups:

*    general parameters (paths, output options, etc.)
*    measurement set parameters (prefixed with *ms_*)
*    imaging parameters (prefixed with *im_*)
*    tropospheric parameters (prefixed with *trop_*)
*    antenna pointing error parameters (prefixed with *pointing_*)

Each parameter is explained below:

* **outdirname** Name of the output directory in which to write all the output products of MeqSilhouette, with path relative to $MEQS_DIR

* **input_fitsimage** Name of the directory containing input fits images named using the naming convention explained in `input/sky_models`_, with path relative to $MEQS_DIR

* **input_fitspol**  Toggle 0 or 1 for polarisation simulation; integer or boolean.

  .. note:: This does not apply when **input_fitsimage** is a *.txt/.lsm.html* file, since any polarisation info is read by MeqTrees automatically.

* **input_changroups** The number of groups into which the frequency channels of the dataset must be divided; used for simulating frequency-dependent source structure; integer.

* **output_to_logfile** Toggle 0 or 1 to create 'logfile.txt' within **outdirname**; integer or boolean.

* **add_thermal_noise** Toggle 0 or 1 to add baseline-dependent thermal noise, calculated using station SEFDs obtained from *station_info*; integer or boolean.

* **make_image** Toggle 0 or 1 to make a dirty image using lwimager; integer or boolean. Other imagers such as WSClean and PyMORESANE to be used in the future.

* **exportuvfits** Toggle 0 or 1 to export MS to UVFITS; integer or boolean

* **station_info** Name of the file containing individual station info such as SEFD, coherence time, primary beam model etc., with path relative to $MEQS_DIR

* **bandpass_enabled** Toggle 0 or 1 to add complex bandpass corruptions (phases currently randomised to between -30 to +30 deg); integer or boolean

* **bandpass_table** Name of the *.txt* file containing bandpass gain amplitudes for each station for a set of frequencies, with path relative to $MEQS_DIR

* **bandpass_freq_interp_order** Order of spline interpolation; integer between 1 and 5

* **bandpass_makeplots** Toggle 0 or 1 to make bandpass plots; integer or boolean

* **elevation_limit** Flag visibilities below this elevation limit given in radians.

* **corr_quantbits** Number of bits used for quantization by the correlator (*e.g.* 2 bits for 4 levels)

* **predict_oversampling** Oversampling factor to improve the accuracy of forward modelling with WSClean. MUST BE AN ODD NUMBER (*e.g.* 8191)

* **predict_seed** Seed for random number generation with numpy. Setting seed=-1 will disable seeding

* **ms_antenna_table** Name of CASA ANTENNA table to use for creating the MS, with path relative to $MEQS_DIR

* **ms_datacolumn** Name of the MS column to write the output visibilities into: *DATA*, *CORRECTED_DATA*, or *MODEL_DATA*

* **ms_RA**  Right Ascension of the pointing centre of the observation in decimal degrees

* **ms_DEC** Declination of the pointing centre of the observation in decimal degrees

* **ms_polproducts** Specify whether the polarization feeds are circular or linear: *RR RL LR LL* or *XX XY YX YY*

* **ms_nu** Centre frequency of the bandpass in GHz

* **ms_dnu** Bandwidth of the spectral window in GHz

* **ms_nchan** Number of channels

* **ms_obslength** Duration of the observation in hours

* **ms_tint** Integration time (i.e. the correlator dump time) in seconds

* **ms_StartTime** Starting time of the observation; *e.g.* 'UTC,2017/04/01/00:00:00.00'

* **ms_nscan** Number of scans in the observation.

* **ms_scan_lag** Lag time between scans in hours

* **ms_makeplots** Toggle 0 or 1 to generate MS-related plots such as uv-coverage, uv-distance sensitivity bins etc.; integer or boolean

* **ms_correctCASAoffset** Toggle 0 or 1 to correct the spurios offset that CASA introduces to the starttime of the observation; integer or boolean

* **im_cellsize** Cell size to be used for imaging with units when **make_image=True**; *e.g.* '3e-6arcsec'

* **im_npix** Image size in pixels when **make_image=True**

* **im_stokes** Stokes parameter to image - 'I', 'Q', 'U', 'V' when **make_image=True**

* **im_weight** Weighting scheme to use for imaging when **make_image=True**; *uniform*, *natural*, or *briggs*

* **trop_enabled** Toggle 0 or 1 to enable tropospheric corruptions; integer or boolean

* **trop_wetonly** Toggle 0 or 1 to simulate only the wet component when **trop_enabled=True**; integer or boolean

* **trop_attenuate** Toggle 0 or 1 to enable tropospheric attenuation when **trop_enabled=True**; integer or boolean

* **trop_noise** Toggle 0 or 1 to include tropospheric (i.e. sky) noise when **trop_enabled=True**

* **trop_turbulence** Toggle 0 or 1 to add Kolmogorov turbulence to the visibility phases when **trop_enabled=True**

* **trop_mean_delay** Toggle 0 or 1 to add mean (i.e. non-turbulent) delay errors due to both dry and wet components when **trop_enabled=True**

* **trop_percentage_calibration_error** Unused

* **trop_fixdelays** Toggle 0 or 1 to insert time-invariant delay errors for testing purposes when **trop_enabled=True**

* **trop_fixdelay_max_picosec** Maximum absolute value of the constant delay errors in picoseconds when **trop_enabled=True** and **trop_fixdelays=True**

* **trop_makeplots** Toggle 0 or 1 to plot troposphere-related quantities such as zenith opacity, elevation-dependent transmission, zenith sky temperature against frequency
                and turbulent phase errors and delays against time; integer or boolean

* **pointing_enabled** Toggle 0 or 1 to enable pointing errors; integer or boolean

* **pointing_time_per_mispoint** Number of minutes per mispointing in minutes

* **pointing_makeplots** Toggle 0 or 1 to plot pointing offset against time; integer or boolean

* **uvjones_d_on** Switch on polarization leakage effects (D-Jones). The D-Jones matrix takes the form [[1 dR_real+1j*dR_imag], [dL_real+1j*dL_imag 1]].
  When switched on, the parallactic angle (P-Jones) effects are added automatically.

* **uvjones_g_on** Switch on complex gains (G-Jones). The G-Jones matrix takes the form [[gR_real+1j*gR_imag 0], [0 gL_real+1j*gL_imag]].

* **parang_corrected** Toggle 0 or 1. If 0, perform parallactic angle rotation before introducing the leakage (D-Jones) terms; if 1, then assume 
  that parallactic angle rotation correction has already been made and rotate by twice the field angle.

Outputs
#######

* The primary output of MeqSilhouette is a CASA Measurement Set containing the complex visibilities, with all the user-requested corruptions applied. The Measurement Set v2 definition can be
  found `here <https://casa.nrao.edu/Memos/229.html>`_.

* MeqSilhouette also saves in numpy format the numerical values of all the Jones matrices applied to the source coherency matrix. Details can be found in the *Components* section.

* A number of plots illustrating the various effects applied to the complex visibilities.
