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

def run_wsclean(input_fitsimage,input_fitspol,startvis,endvis):
    msname = II('$MS')

    if input_fitspol == 0:
        subprocess.check_call(['wsclean','-predict','-name',input_fitsimage,'-interval',str(int(startvis)),str(int(endvis)),msname])
    else:
        subprocess.check_call(["wsclean","-predict","-name",input_fitsimage,"-interval",str(int(startvis)),str(int(endvis)),"-pol","I,Q,U,V","-no-reorder",msname])

def copy_to_outcol(output_column):
    msname = II('$MS')

    tab=pt.table(msname,readonly=False)
    model_data = tab.getcol('MODEL_DATA')
    tab.putcol(output_column,model_data)
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




