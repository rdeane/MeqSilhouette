# coding: utf-8
from Pyxis.ModSupport import *
import pyrap.tables as pt
import os
from framework.comm_functions import *
from astropy.time import Time




def create_ms(msname, input_fits, ms_dict):
    """ create empty MS """
    x.sh(return_simms_string(msname, input_fits, **ms_dict))

    # set STATION names to same as NAME col
    antt = pt.table(os.path.join(msname, 'ANTENNA'), readonly=False,ack=False)
    antt.putcol('STATION', antt.getcol('NAME'))
    antt.close()

    # set FIELD name to input filename (minus extension)
    fieldtab = pt.table(os.path.join(msname,'FIELD'),readonly=False,ack=False)
    fieldtab.putcol('NAME',input_fits.split('/')[-1].split('.')[0])
    fieldtab.close()

    # set SOURCE name to input filename (minus extension)
    srctab = pt.table(os.path.join(msname,'SOURCE'),readonly=False,ack=False)
    srctab.putcol('NAME',input_fits.split('/')[-1].split('.')[0])
    srctab.close()

    # set SPW name to input filename (minus extension)
    spwtab = pt.table(os.path.join(msname,'SPECTRAL_WINDOW'),readonly=False,ack=False)
    spwtab.putcol('NAME',input_fits.split('/')[-1].split('.')[0])
    spwtab.close()

    # INI: Add WEIGHT_SPECTRUM and SIGMA_SPECTRUM columns to the MS
    tab = pt.table(msname,readonly=False)
    data = tab.getcol('DATA')
    tab.addcols(pt.makearrcoldesc('SIGMA_SPECTRUM',value=1.0,shape=[data.shape[1],data.shape[2]],valuetype='float'))
    tab.addcols(pt.makearrcoldesc('WEIGHT_SPECTRUM',value=1.0,shape=[data.shape[1],data.shape[2]],valuetype='float'))
    tab.close()

    info('Measurement Set %s created '%msname)



    

def return_simms_string(msname, input_fits, RA, DEC, polproducts, antenna_table, \
                        obslength, dnu, tint, nu, StartTime, nchan, \
                        nscan, scan_lag,datacolumn, makeplots, correctCASAoffset):
    """ generate simms string to create an empty MS, however,
        what is first required is a small MS to be generated 
        in order to determine spurious time offset that CASA
        inserts, and adjust SYMBA start time accordingly"""

    
    if correctCASAoffset:
        if os.path.exists(os.path.join(v.OUTDIR,'CASAcorrectedStartTime.txt')):
            with open(os.path.join(v.OUTDIR,'CASAcorrectedStartTime.txt'), 'r') as file:
               tmod_StartTime  = file.read().replace('\n', '')
        else:
            
            ### make a very short obs, single channel MS to get the start time offset
            tempms = os.path.join(v.OUTDIR,'temp_gettimeoffset.ms') # to be deleted
            strtemp = "simms -T VLBA -t casa -n %s -ra %.9fdeg -dec %.9fdeg \
               -pl '%s' -st %f -sl %f -slg %f -dt %i -f0 %fGHz -df %fGHz -nc %i  -date %s %s\
               " % ( tempms, RA, DEC, polproducts, tint*5, obslength/float(nscan), scan_lag,
                tint, nu - (dnu/2.) + (dnu/(float(nchan))/2.), dnu,
                1, StartTime, os.path.join(II('$CODEDIR'),antenna_table))

            info('running the followig simms command to generate a temp dataset:')
            info(strtemp)
            # run simms, grab actual StartTime
            os.system(strtemp) 
            tab = pt.table(tempms, readonly=True,ack=False)
            casatime = tab.getcol('TIME')
            tint_casa = tab.getcol('EXPOSURE')[0]
            tab.close()
            os.system('rm -fr %s'%tempms) # delete temp MS
    
            # get MJD of intended (i.e. specified) time in SYMBA config file
            StartTimeSplit = StartTime.split(',')[1].split('/')
            symba_time = '%s-%s-%sT%s'%(StartTimeSplit[0],StartTimeSplit[1],
                          StartTimeSplit[2],StartTimeSplit[3])
            t = Time([symba_time], format='isot', scale='utc')
            # calculate offset between CASA and intended StartTime
            offsetSec_casa_minus_symba = casatime[0] -   (t.mjd*24*60*60) - (tint_casa/2) 
            info('CASA start time is at StartTime plus %.2f seconds'
                 %offsetSec_casa_minus_symba )
            newSymbaTime_MJD = t.mjd - (offsetSec_casa_minus_symba / (24*60*60.))

            
            #  Now convert into simms StartTime format
            ## (e.g. 'UTC,2017/04/01/00:00:00.00')
            tmod = Time(newSymbaTime_MJD, format='mjd')
            tmod_str = tmod.iso[0]
            tmod_StartTime = 'UTC,'+tmod_str.replace('-','/').replace(' ','/')

            #### for save for subsequent scans (if SYMBA run)
            #np.savetxt(os.path.join(v.OUTDIR,'CASAtimeOffset.txt'),tmod_StartTime)
            with open(os.path.join(v.OUTDIR,'CASAcorrectedStartTime.txt'), 'w') as file:
               file.write(tmod_StartTime)
               file.close()
            with open(os.path.join(v.OUTDIR,'CASAtimeOffset.txt'), 'w') as file:
               file.write('%.2f'%offsetSec_casa_minus_symba)
               file.close()
    else:
        """ if no CASA offset has/should be(en) calculated, just use user-provided StartTime"""
        tmod_StartTime = StartTime
    
        ### MAIN MS simulation with update StartTime 
    s = "simms -T VLBA -t casa -n %s -ra %.9fdeg -dec %.9fdeg \
        -pl '%s' -st %f -sl %f -slg %f -dt %f -f0 %fGHz -df %fGHz -nc %i  -date %s %s\
        " % ( msname, RA, DEC, polproducts, obslength, obslength/float(nscan), scan_lag,
         tint, nu - (dnu/2.) + (dnu/(float(nchan))/2.), dnu/float(nchan),
          nchan, tmod_StartTime, os.path.join(II('$CODEDIR'),antenna_table)) 
    
    return s

    # NOTE: CASA fails if simms -T option is changed from "VLBA",
    #so this is hard-coded in.
    # It fails as it does not have a reference location for the EHT
    # referencelocation=obs_pos gives error:
    #Error Illegal Measure record in MeasureHolder::fromRecord
    #In converting Position parameter




