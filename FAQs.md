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

### 1 frequency channel, but trop module on.
 create a catch. 

Traceback (most recent call last):
  File "driver/run_meqsilhouette.py", line 116, in <module>
      coherence_time,parameters['trop_fixdelay_max_picosec'])
        File "/home/deane/git-repos/MeqSilhouette/framework/SimCoordinator.py", line 89, in __init__
	    self.opacity, self.sky_temp = self.trop_return_opacity_sky_temp()
	      File "/home/deane/git-repos/MeqSilhouette/framework/SimCoordinator.py", line 298, in trop_return_opacity_sky_temp
	          delimiter=', \t'), 0, 1)
		    File "/home/deane/.local/lib/python2.7/site-packages/numpy/core/fromnumeric.py", line 501, in swapaxes
		        return _wrapfunc(a, 'swapaxes', axis1, axis2)
			  File "/home/deane/.local/lib/python2.7/site-packages/numpy/core/fromnumeric.py", line 57, in _wrapfunc
			      return getattr(obj, method)(*args, **kwds)
			      ValueError: bad axis2 argument to swapaxes

### Still unexplained?

MeqTrees can crash unexpected if insufficient memory is allocated. If running on a virtual machine and/or on low-powered
desktop, you may want to scale back the memory demands as a quick test.