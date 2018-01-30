# coding: utf-8

# In[ ]:
from Pyxis.ModSupport import *
import mqt
import numpy as np
import pyrap.tables as pt
from im import lwimager 

def run_turbosim(input_fitsimage,output_column,taql_string):

    options = {}
    options['ms_sel.msname'] = II('$MS')
    options['ms_sel.output_column'] = output_column
    options['fitsimage_sky.image_filename'] = input_fitsimage
    options['fitsimage_sky.pad_factor'] = 2.4
    options['ms_sel.tile_size'] = 1000000
    options['ms_sel.ms_taql_str'] = taql_string



    
    mqt.MULTITHREAD = 32 #max number of meqserver threads
    mqt.run(script=II('$FRAMEWORKDIR')+'/turbo-sim.py',
            config=II('$FRAMEWORKDIR')+'/tdlconf.profiles',
            section='turbo-sim',
            job='_simulate_MS',
            options=options)
# removed:                 

def make_dirty_image_lwimager(im_dict,ms_dict):
        lwimager.make_image(column=ms_dict["datacolumn"],
            dirty_image=II('${OUTDIR>/}${MS:BASE}')+'-dirty_map.fits',
                            dirty=True,**im_dict)


def make_image_wsclean():
    print('todo')

def make_image_pymoresane():
    print('todo')




