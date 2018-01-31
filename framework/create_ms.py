# coding: utf-8
from Pyxis.ModSupport import *
import pyrap.tables as pt
import os
from framework.comm_functions import *



def create_ms(msname, input_fits, ms_dict):
    """ create empty MS """
    x.sh(return_simms_string(msname, input_fits, **ms_dict))
    antt = pt.table(os.path.join(msname, 'ANTENNA'), readonly=False,ack=False)
    antt.putcol('STATION', antt.getcol('NAME'))
    antt.close()
    info('Measurement Set %s created '%msname)


def return_simms_string(msname, input_fits, RA, DEC, antenna_table, \
                        obslength, dnu, tint, nu, StartTime, nchan, \
                        nscan, scan_lag,datacolumn, makeplots):
    
    s = "simms -T VLBA -t casa -n %s -ra %.9fdeg -dec %.9fdeg \
-st %f -sl %f -slg %f -dt %i -f0 %fGHz -df %fGHz -nc %i  -date %s %s\
    " % ( msname, RA, DEC, obslength, obslength/float(nscan), scan_lag,
         tint, nu - (dnu/2.) + (dnu/(float(nchan))/2.), dnu/float(nchan), nchan, StartTime,os.path.join(II('$CODEDIR'),antenna_table)) #changed from os.path.join(II('$INDIR'),

    return s

    # NOTE: CASA fails if simms -T option is changed from "VLBA",
    #so this is hard-coded in.
    # It fails as it does not have a reference location for the EHT
    # referencelocation=obs_pos gives error:
    #Error Illegal Measure record in MeasureHolder::fromRecord
    #In converting Position parameter




