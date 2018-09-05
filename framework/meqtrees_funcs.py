# coding: utf-8

# In[ ]:
from Pyxis.ModSupport import *
import mqt
import numpy as np
import pyrap.tables as pt
from im import lwimager 
import subprocess
import glob
from framework.comm_functions import *

def run_wsclean(input_fitsimage,output_column):
    msname = II('$MS')
    # check for I,Q,U,V fits files. If any one is missing
    if len(glob.glob(input_fitsimage+'-[I,Q,U,V]-model.fits')) != 4:
        info('Only one FITS file found. Predicting Stokes I visibilities using wsclean.')
        subprocess.check_call(["wsclean","-predict","-name",input_fitsimage,msname])
    else:
        info('FITS files for I,Q,U,V found. Predicting full polarisation visibilities using wsclean.')
        subprocess.check_call(["wsclean","-predict","-name",input_fitsimage,"-pol","I,Q,U,V",msname])

    if output_column != 'MODEL_DATA':
        tab=pt.table(msname,readonly=False)
        model_data = tab.getcol('MODEL_DATA')
        tab.putcol(output_column,model_data)
        # Set MODEL_DATA to unity
        model_data[:] = 1.0
        tab.putcol('MODEL_DATA',model_data)
        tab.close()
        
def run_turbosim(input_fitsimage,output_column,taql_string):

    options = {}
    options['ms_sel.msname'] = II('$MS')
    options['ms_sel.output_column'] = output_column
    if input_fitsimage.endswith(('.fits','.FITS')):
        options['me.sky.siamese_oms_fitsimage_sky'] = 1
        options['fitsimage_sky.image_filename'] = input_fitsimage
        options['fitsimage_sky.pad_factor'] = 2.4
    elif input_fitsimage.endswith(('.txt','.html')):
        options['me.sky.tiggerskymodel'] = 1
        options['tiggerlsm.filename'] = input_fitsimage
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




