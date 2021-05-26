==================
Outputs
==================

The primary output product of MeqSilhouette is a CASA Measurement Set containing the complex visibilities,
with all the user-requested corruptions applied to the data. The Measurement Set v2 specification can be
found `here <https://casa.nrao.edu/Memos/229.html>`_. The tables and subtables in the MS are filled as follows:

* The value of *ms_datacolumn* in the input JSON file must correspond to an existing column in the MAIN table.
  This column is filled with the corrupted complex visibilities.

* The MODEL_DATA column is filled with uncorrupted visibilities. It is recommended not to set *ms_datacolumn='MODEL_DATA'* so
  that the uncorrupted visibilities are available to the user for later inspection.

* The SIGMA column is filled with the standard deviation of the baseline-based complex visibilities computed using the SEFD.
  If mulltiple frequency channels are present, then SIGMA_SPECTRUM is also filled with these values.

* The WEIGHT column is filled with inverse-variance weighting with the variance computed using the SIGMA values.
  If mulltiple frequency channels are present, then WEIGHT_SPECTRUM is also filled with these values.

* The ANTENNA subtable is the same as the input antenna table pointed to by *ms_antenna_table*.

Optionally, there a few other outputs that MeqSilhouette can generate for recording the synthetic data generation process
and verifying the contents of the MS. 

* The numerical values of all the Jones matrices are saved as numpy arrays.

* A number of plots illustrating the properties of the complex visibilities and the various effects applied to them.

* A preliminary image of the simulated data.

* Export the MS into UVFITS format, for compatibility with other calibration packages such as eht-imaging and AIPS.
