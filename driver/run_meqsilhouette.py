# coding: utf-8
import time
import Pyxis
from Pyxis.ModSupport import *
import ms
import im.argo as argo
import glob
import os
import sys
import pyrap.tables as pt
import framework
from framework.process_input_config import setup_keyword_dictionary, load_json_parameters_into_dictionary
from framework.create_ms import create_ms
from framework.SimCoordinator import SimCoordinator
from framework.meqtrees_funcs import make_dirty_image_lwimager
from framework.comm_functions import *


config = sys.argv[1]
#def run_vlbi_sim(config):
if (1):
    """
    Standard VLBI simulation script to perform interferometric simulation,
    variables prefixed by v. indicate new global variables.
    """
    start = time.time()

    ### load input configuration file parameters ###
    config_abspath = os.path.abspath(config)
    parameters = load_json_parameters_into_dictionary(config_abspath)
    ms_dict = setup_keyword_dictionary('ms_', parameters)
    im_dict = setup_keyword_dictionary('im_', parameters)
    trop_dict = setup_keyword_dictionary('trop_', parameters)
    
    ms_config_string = str(ms_dict['antenna_table'].split('/')[-1]) + '_' \
            + str(parameters['input_fitsimage'].split('/')[-1]\
                                                      .replace('.fits','')) \
            + '_RA%.0fdeg_DEC%.0fdeg_%.0fGHz-BW%iMHz-%ichan-%is-%.0fhrs'\
            %(ms_dict['RA'],ms_dict['DEC'],ms_dict['nu'],ms_dict['dnu']*1e3,\
                         ms_dict['nchan'],ms_dict['tint'],ms_dict['obslength'])
                       # attached to base (output_msname_base ) to name MS
    
    
    ### set directory paths ###
    v.CODEDIR = os.environ['MEQS_DIR']
    v.FRAMEWORKDIR = os.path.dirname(framework.__file__)
    v.OUTDIR = os.path.join(v.CODEDIR,parameters['outdirname']) # full output path of current simulation
    v.PLOTDIR = os.path.join(v.OUTDIR,'plots')
    v.MS = os.path.join(v.OUTDIR, ms_config_string \
                        + '.MS')  # name of output Measurement Set
    input_fitsimage = os.path.join(v.CODEDIR,parameters['input_fitsimage'])
    
    info('Loaded input configuration file: \n%s'%config_abspath)
    info('Input FITS image: \n%s'%input_fitsimage)
    print_simulation_summary(ms_dict,im_dict)

    time.sleep(3) # brief pause for visual review
                            
    
### catch input parameter user errors 
    if not os.path.exists(v.PLOTDIR):
        os.makedirs(v.PLOTDIR)


#    else:
#        abort('Selected output directory exists! \n\t[%s]'%OUTDIR + \
#              '\n\tChange parameter <outdirname> in input configuration file:'+\
#              '\n\t[%s]'%config_abspath)
        
    if os.path.exists(input_fitsimage) == False:
        abort('NO INPUT FITS IMAGE FOUND')
        abort('CHECK "input_fitsimage" in input .json configuration file.\n\t'+
              'Note input fits images must have suffix ".fits" in lower case')

    info('Input sky model fits image: \n %s'%input_fitsimage)
    

    if (parameters['output_to_logfile']):
        v.LOG = OUTDIR + "/logfile.txt" 
    else:
        info('All output will be printed to terminal.')
        info('Print to log file by setting <output_to_logfile> parameter in input configuration file.')

    info('Loading station info table %s'%parameters['station_info'])
    sefd, pwv, gpress, gtemp, coherence_time, pointing_rms, PB_FWHM230 = \
        np.swapaxes(np.loadtxt(os.path.join(v.CODEDIR,parameters['station_info']),\
        skiprows=1,usecols=[1, 2, 3, 4, 5, 6, 7]), 0, 1)
    
    #sefd = np.loadtxt(os.path.join(v.CODEDIR,parameters['station_info']),skiprows=1,usecols=1)
    station_names_txt = np.loadtxt(os.path.join(v.CODEDIR,\
                                parameters['station_info']),\
                                usecols=[0],dtype=str,skiprows=1).tolist()
    anttab = tab=pt.table(os.path.join(v.CODEDIR,ms_dict['antenna_table'])\
                          ,ack=False)
    station_names_anttab = anttab.getcol('STATION')
    if (len(station_names_txt) != len(station_names_anttab)):
        abort('Mis-matched number of antennas in %s and %s'\
              %(parameters['station_info'],ms_dict['antenna_table']))
    if (station_names_txt != station_names_anttab):
        warn('Mis-matched station name order in %s versus %s (see comparison):'\
             %(parameters['station_info'],ms_dict['antenna_table']))
        for c1,c2 in zip(station_names_txt,station_names_anttab):
            print "%s\t\t%s" % (c1, c2)
        abort('Correct input station_info file and/or antenna table')
 

    info('Station info table %s corresponds correctly to antenna table %s'\
         %(parameters['station_info'],ms_dict['antenna_table']))

    if parameters['bandpass_enabled']:
        if not os.path.isfile(parameters['bandpass_txt']):
            abort("File '%s' does not exist. Aborting..."%(parameters['bandpass_txt']))
        station_names_txt = np.loadtxt(os.path.join(v.CODEDIR,\
                                    parameters['bandpass_txt']),\
                                    usecols=[0],dtype=str,skiprows=1).tolist()
        if (len(station_names_txt) != len(station_names_anttab)):
            abort('Mis-matched number of antennas in %s and %s'\
                  %(parameters['bandpass_txt'],ms_dict['antenna_table']))
        if (station_names_txt != station_names_anttab):
            warn('Mis-matched station name order in %s versus %s (see comparison):'\
                 %(parameters['bandpass_txt'],ms_dict['antenna_table']))
            for c1,c2 in zip(station_names_txt,station_names_anttab):
                print "%s\t\t%s" % (c1, c2)
            abort('Correct input station_info file and/or antenna table')

    bandpass_txt = os.path.join(v.CODEDIR,parameters['bandpass_txt']) 
    bandpass_freq_interp_order = parameters['bandpass_freq_interp_order']

    info('Creating empty MS with simms')
    create_ms(MS, input_fitsimage, ms_dict)

    info('Simulating sky model into %s column in %s'%(ms_dict['datacolumn'],MS))
    sim_coord = SimCoordinator(MS,ms_dict["datacolumn"],input_fitsimage, bandpass_txt, bandpass_freq_interp_order, sefd, \
                               parameters["elevation_limit"], parameters['trop_enabled'], parameters['trop_wetonly'], pwv, gpress, gtemp, \
                               coherence_time,parameters['trop_fixdelay_max_picosec'])

    sim_coord.interferometric_sim()

    if parameters['pointing_enabled']:
        info('Pointing errors are enabled, applying antenna-based amplitudes errors')
        info('Current pointing error model is a constant offset that changes on a user-specified time interval, current setting = %.1f minutes'%\
             parameters['pointing_time_per_mispoint'])
        
        sim_coord.pointing_constant_offset(pointing_rms,parameters['pointing_time_per_mispoint'],PB_FWHM230)
        sim_coord.apply_pointing_amp_error()

        if parameters['pointing_makeplots']:
            sim_coord.plot_pointing_errors()

        
    if parameters['add_thermal_noise']:
        sim_coord.add_receiver_noise()

    ### TROPOSPHERE COMPONENTS ###
    combined_phase_errors = 0 #init for trop combo choice
    if parameters['trop_enabled']:
        info('Tropospheric module is enabled, applying corruptions...')
        if parameters['trop_wetonly']:
            info('... using on the WET component')
        else:
            info('... using both the WET and DRY components')
        
        if parameters['trop_attenuate']:
            info('TROPOSPHERE ATTENUATE: using PWV-derived opacity to determine station-based attenuation')
            sim_coord.trop_opacity_attenuate() 

        if parameters['trop_noise']:
            info('TROPOSPHERE NOISE: adding sky noise from non-zero PWV')
            sim_coord.trop_add_sky_noise()

        if parameters['trop_mean_delay']:
            info('TROPOSPHERE DELAY: adding mean delay (time-variability from elevation changes)')
            sim_coord.trop_calc_mean_delays()
            combined_phase_errors += sim_coord.phasedelay_alltimes
    
            
        if parameters['trop_turbulence']:
            info('TROPOSPHERE TURBULENCE: adding Kolmogorov turbulence phase errors')
            sim_coord.trop_generate_turbulence_phase_errors()
            combined_phase_errors += sim_coord.turb_phase_errors
            
        if parameters['trop_fixdelays']:
            info('TROPOSPHERE INSERT FIXED DELAY: non-variable delay calculated')
            sim_coord.trop_calc_fixdelay_phase_offsets()
            combined_phase_errors += sim_coord.fixdelay_phase_errors

        info('TROPOSPHERE: applying desired combination of phase errors')
        sim_coord.apply_phase_errors(combined_phase_errors) 

        info('All selected tropospheric corruptions applied.')

        if parameters['trop_makeplots']:
            sim_coord.trop_plots()
            info('Generated troposphere plots')

    ### BANDPASS COMPONENTS ###
    if parameters['bandpass_enabled']:
        info('BANDPASS: incorporating bandpass (B-Jones) effects; for now, scalar B-Jones constant in time')
        sim_coord.bandpass_correct()
        info('B-Jones terms applied.')       
 
    ### IMAGING, PLOTTING, DATA EXPORT ###        
    if parameters['make_image']:
        info('Imaging the %s column'%ms_dict['datacolumn'])
        make_dirty_image(im_dict,ms_dict) #, v.OUTDIR)
        if not os.path.exists(II('${OUTDIR>/}${MS:BASE}')+'-dirty_map.fits'):
            abort('OUTPUT IMAGE NOT FOUND')
            abort('Looks like imaging, or something upstream of that failed.')

    if parameters['ms_makeplots']:
        info('Generating MS-related plots...')
        sim_coord.make_ms_plots()
    # insert new plot here of coloured baselines and legend

    if parameters['exportuvfits']:
        info('Exporting %s to uvfits file %s'%(MS,MS.replace('.ms','.uvfits')))
        im.argo.icasa('exportuvfits', mult=[{'vis': v.MS, 'fitsfile': os.path.join(OUTDIR,v.MS.replace('.ms','.uvfits').replace('.MS','.uvfits'))}])

    # #Cleanup
    info('Cleaning up...')
    if (os.path.exists('./core')): x.sh('rm core')
    finish_string = "Pipeline finished after %.1f seconds" % (time.time()-start)
    info(finish_string)



# add later
"""
    return finish_string


if __name__ == '__main__':

    conf = sys.argv[1]
    run_meqsilhouette(conf)
"""
