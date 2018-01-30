MeqSilhouette attempts to catch errors (user or otherwise) as much as possible.
Due to the nature of linking a number of different packages together, there are
a number of errors/warnings that may appear but don't necessarily have any adverse
effect. Furthermore, there are several types of errors that may not be easy to catch
directly. As such, we include a list below of commonly-encountered errors/warnings
and offer suggesgtions on what they might mean.


## Common errors/warnings

### 'WARNING: Partial frequency mismatch between the input image and the requested MS frequencies'

The input_fitsimage obviously has a reference frequency. This is a meqtrees warning that that
the input_fitsimage frequency is not perfectly consistent with the that used in the interferometric
simulation. This is of no concern, however, since only the latter, user-specified value is used
(from the input configuration file). This error can be ignored.


### VisDataMux



### Still unexplained?

MeqTrees can crash unexpected if insufficient memory is allocated. If running on a virtual machine and/or on low-powered
desktop, you may want to scale back the memory demands as a quick test.