# coding: utf-8
from Pyxis.ModSupport import *
import pyrap.tables as pt
import numpy as np
import os
from meqsilhouette.utils.comm_functions import *
from astropy.time import Time
from casatools import simulator, table, measures

sm = simulator()
tb = table()
me = measures()


def convertra(RA):
    '''
    Convert RA from degrees to hours
    '''
    ra_in_hours = RA/15.
    if ra_in_hours>0:
        ra_hr = int(np.floor(ra_in_hours))
        tmpmin = (ra_in_hours-ra_hr)*60
    else:
        ra_hr = int(np.ceil(ra_in_hours))
        tmpmin = (ra_hr-ra_in_hours)*60
    ra_min = int(np.floor(tmpmin))
    ra_sec = (tmpmin-ra_min)*60
    
    return f"{ra_hr}h{ra_min}m{ra_sec}"

def convertdec(dec):
    if dec>0:
        dec_deg = int(np.floor(dec))
        tmpmin = (dec-dec_deg)*60
    else:
        dec_deg = int(np.ceil(dec))
        tmpmin = (dec_deg-dec)*60
    dec_min = int((np.floor(tmpmin)))
    dec_sec = (tmpmin-dec_min)*60
    return f"{dec_deg}.{dec_min}.{dec_sec}"


def genms(msname, input_fits, antenna_table, starttime, obslength_in_sec, RA, DEC, \
        stokes, tint, nu, dnu, nchan, nscan, scan_lag, datacolumn):
    '''
    setup ms configuration
    '''

    # set antenna config -- station locations are contained in a casa antenna table
    telname = "VLBA" # hardcoded to VLBA, a known VLBI array for CASA
    tb.open(antenna_table)
    station_name = tb.getcol("STATION")
    dish_diameter = tb.getcol("DISH_DIAMETER")
    station_mount = tb.getcol("MOUNT")
    x, y, z = tb.getcol("POSITION")
    tb.close()
    coords = 'global' # CASA antenna tables use ITRF by default
    obspos = me.observatory(telname)
    me.doframe(obspos)

    sm.open(msname)

    # set autocorr -- do not write autocorrelations
    sm.setauto(autocorrwt=0.0)

    nant = len(list(station_name))
    sm.setconfig(telescopename=telname, x=x, y=y, z=z, \
            dishdiameter=list(dish_diameter), mount=list(station_mount), antname=list(station_name), \
            padname=list(station_name), coordsystem=coords, referencelocation=obspos)

    # set feed - 'perfect R L' by default; no need to set manually
    #sm.setfeed(mode="perfect R L")

    # set limits for flagging
    sm.setlimits(shadowlimit=0.0, elevationlimit=0.0)

    # set spectral windows
    startfreq = nu - dnu/2.
    deltafreq = dnu/nchan
    spwname = f"{int(startfreq)}GHz_BAND"
    sm.setspwindow(spwname=spwname, freq=f"{startfreq}GHz", \
            deltafreq=f"{deltafreq}GHz", freqresolution=f"{deltafreq}GHz", \
            nchannels=nchan, stokes=stokes)

    # set obs fields
    sourcename = input_fits.split('/')[-1].split('.')[0]
    RAstr = convertra(RA)
    DECstr = convertdec(DEC)
    dir0 = me.direction("J2000", RAstr, DECstr)
    sm.setfield(sourcename=sourcename, sourcedirection=dir0)

    # set obs times
    obs_starttime = starttime.split(',')
    sm.settimes(integrationtime=tint, usehourangle=False, referencetime=me.epoch(*obs_starttime))

    # observe
    scanlength = obslength_in_sec/nscan
    for ii in range(nscan):
        if ii == 0:
            relstarttime = 0
            relstarttime_str = f"{relstarttime}s"
        else:
            relstarttime = relstoptime + scan_lag
            relstarttime_str = f"{relstarttime}s"

        relstoptime = relstarttime + scanlength
        relstoptime_str = f"{relstoptime}s"

        sm.observe(sourcename=sourcename, spwname=spwname, starttime=relstarttime_str, stoptime=relstoptime_str)

    # clean up
    sm.close()


def compute_casa_offset(msname, input_fits, ms): 
    '''
    fn to compute casa offset
    '''
    ### make a very short obs, single channel MS to get the start time offset
    info('Generating a smaller temporary MS to compute the StartTime offset introduced by CASA...')
    tempms = os.path.join(v.OUTDIR,'temp_gettimeoffset.ms') # to be deleted

    genms(tempms, input_fits, ms["antenna_table"], ms["StartTime"], min(ms["tint"]*10, ms["obslength"]*3600), ms["RA"], ms["DEC"], \
            ms["polproducts"], ms["tint"], ms["nu"], ms["dnu"], int(ms["nchan"]), ms["nscan"], ms["scan_lag"], ms["datacolumn"])

    # grab CASA generated StartTime
    tab = pt.table(tempms, readonly=True,ack=False)
    casatime = tab.getcol('TIME')
    tint_casa = tab.getcol('EXPOSURE')[0]
    tab.close()
    #os.system('rm -fr %s'%tempms) # delete temp MS

    # get MJD of expected StartTime in SYMBA config file
    StartTimeSplit = ms["StartTime"].split(',')[1].split('/')
    symba_time = '%s-%s-%sT%s'%(StartTimeSplit[0],StartTimeSplit[1],
                  StartTimeSplit[2],StartTimeSplit[3])
    t = Time([symba_time], format='isot', scale='utc')
    # calculate offset between CASA and intended StartTime
    offsetSec_casa_minus_symba = casatime[0] -   (t.mjd*24*60*60) - (tint_casa/2)
    info('CASA start time is at StartTime plus %.2f seconds'
         %offsetSec_casa_minus_symba )
    newSymbaTime_MJD = t.mjd - (offsetSec_casa_minus_symba / (24*60*60.))

    #  Now convert into CASA StartTime format
    ## (e.g. 'UTC,2017/04/01/00:00:00.00')
    tmod = Time(newSymbaTime_MJD, format='mjd')
    tmod_str = tmod.iso[0]
    tmod_StartTime = 'UTC,'+tmod_str.replace('-','/').replace(' ','/')

    #### save for subsequent scans (to assist with SYMBA run)
    with open(os.path.join(v.OUTDIR,'CASAcorrectedStartTime.txt'), 'w') as file:
       file.write(tmod_StartTime)
       file.close()
    with open(os.path.join(v.OUTDIR,'CASAtimeOffset.txt'), 'w') as file:
       file.write('%.2f'%offsetSec_casa_minus_symba)
       file.close()

    return tmod_StartTime


def create_msv2(msname, input_fits, ms):
    '''
    main fn to create MS
    '''

    # compute starttime offset for correction
    info("Computing spurious starttime offset introduced by CASA ...")
    tmod_StartTime = 0.0
    if ms["correctCASAoffset"]:
        if os.path.exists(os.path.join(v.OUTDIR,'CASAcorrectedStartTime.txt')):
            with open(os.path.join(v.OUTDIR,'CASAcorrectedStartTime.txt'), 'r') as file:
               tmod_StartTime  = file.read().replace('\n', '')
        else:
            tmod_StartTime = compute_casa_offset(msname, input_fits, ms)
    else:
        tmod_StartTime = ms["StartTime"]

    # create actual ms
    genms(msname, input_fits, ms["antenna_table"], tmod_StartTime, ms["obslength"]*3600, ms["RA"], ms["DEC"], \
            ms["polproducts"], ms["tint"], ms["nu"], ms["dnu"], int(ms["nchan"]), ms["nscan"], ms["scan_lag"], ms["datacolumn"])

    # INI: Add WEIGHT_SPECTRUM and SIGMA_SPECTRUM columns to the MS
    tab = pt.table(msname,readonly=False)
    data = tab.getcol('DATA')
    tab.addcols(pt.makearrcoldesc('SIGMA_SPECTRUM',value=1.0,shape=[data.shape[1],data.shape[2]],valuetype='float'))
    tab.addcols(pt.makearrcoldesc('WEIGHT_SPECTRUM',value=1.0,shape=[data.shape[1],data.shape[2]],valuetype='float'))
    tab.close()

    info('Measurement Set %s created '%msname)
    

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
               -pl '%s' -st %f -slg %f -dt %i -f0 %fGHz -df %fGHz -nc %i  -date %s %s\
               " % ( tempms, RA, DEC, polproducts, obslength, scan_lag,
                min(tint*10, obslength*3600), nu - (dnu/2.) + (dnu/(float(nchan))/2.), dnu,
                1, StartTime, os.path.join(II('$CODEDIR'),antenna_table))

            info('Generating a smaller temporary MS to compute the StartTime offset introduced by CASA...')
            info(strtemp)
            # run simms, grab CASA generated StartTime
            os.system(strtemp) 
            tab = pt.table(tempms, readonly=True,ack=False)
            casatime = tab.getcol('TIME')
            tint_casa = tab.getcol('EXPOSURE')[0]
            tab.close()
            os.system('rm -fr %s'%tempms) # delete temp MS
    
            # get MJD of expected StartTime in SYMBA config file
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

            #### save for subsequent scans (to assist with SYMBA run)
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




