from Pyxis.ModSupport import *
from meqtrees_funcs import run_turbosim
import pyrap.tables as pt
import pyrap.measures as pm, pyrap.quanta as qa
from framework.comm_functions import *
import pickle
import subprocess
import glob
from scipy.constants import Boltzmann, speed_of_light
import pylab as pl
import seaborn as sns
sns.set_style("darkgrid")
cmap = pl.cm.Set1 #viridis
from mpltools import layout
from mpltools import color
from matplotlib.patches import Circle
from matplotlib.ticker import FormatStrFormatter



class SimCoordinator():

    def __init__(self, msname, output_column, input_fitsimage, sefd, \
                 elevation_limit, trop_enabled, trop_wetonly, pwv, gpress, gtemp, \
                 coherence_time,fixdelay_max_picosec):
        info('Generating MS attributes based on input parameters')
        self.msname = msname
        tab = pt.table(msname, readonly=True,ack=False)
        self.data = tab.getcol(output_column)
        self.flag = tab.getcol('FLAG')
        self.uvw = tab.getcol("UVW")
        self.uvdist = np.sqrt(self.uvw[:, 0]**2 + self.uvw[:, 1]**2)
        self.A0 = tab.getcol('ANTENNA1')
        self.A1 = tab.getcol("ANTENNA2")
        self.time = tab.getcol('TIME')
        self.time_unique = np.unique(self.time)
        self.mjd_obs_start = self.time_unique[0]
        self.mjd_obs_end  = self.time_unique[-1]
        self.tint = self.time_unique[1]-self.time_unique[0]
        self.obslength = self.time_unique[-1]-self.time_unique[0]
        self.ant_unique = np.unique(np.hstack((self.A0, self.A1)))


        anttab = pt.table(tab.getkeyword('ANTENNA'),ack=False)
        self.station_names = anttab.getcol('NAME')
        self.pos = anttab.getcol('POSITION')
        self.Nant = self.pos.shape[0]
        self.N = range(self.Nant)
        anttab.close()

        field_tab = pt.table(tab.getkeyword('FIELD'),ack=False)
        self.direction = np.squeeze(field_tab.getcol('PHASE_DIR'))

        spec_tab = pt.table(tab.getkeyword('SPECTRAL_WINDOW'),ack=False)
        self.chan_freq = spec_tab.getcol('CHAN_FREQ').flatten()
        self.chan_width = spec_tab.getcol('CHAN_WIDTH').flatten()[0]
        self.bandwidth = self.chan_width + self.chan_freq[-1]-self.chan_freq[0]
        spec_tab.close()

        ### elevation-relevant calculation ###
        self.elevation = self.elevation_calc()
        self.baseline_dict = self.make_baseline_dictionary()
        self.write_flag(elevation_limit)
        self.elevation[self.elevation < elevation_limit] = np.nan  # This is to avoid crashing later tropospheric calculation
        self.calc_ant_rise_set_times()
                                                

        self.input_fitsimage = input_fitsimage
        self.output_column = output_column

        ### thermal noise relevant calculations ###
        self.SEFD = sefd
        self.dish_diameter = pt.table(pt.table(msname).getkeyword('ANTENNA'),ack=False).getcol('DISH_DIAMETER')
        self.dish_area = np.pi * np.power((self.dish_diameter / 2.), 2)
        self.receiver_temp = (self.SEFD * self.dish_area / (2 * Boltzmann)) / 1e26 # not used, but compare with real values

        tab.close() # close main MS table


        self.trop_enabled = trop_enabled
        if (self.trop_enabled):
            self.trop_wetonly = trop_wetonly
            self.average_pwv = pwv
            self.average_gpress = gpress
            self.average_gtemp = gtemp
            self.coherence_time = coherence_time
            self.fixdelay_max_picosec = fixdelay_max_picosec
            self.elevation_tropshape = np.expand_dims(np.swapaxes(self.elevation, 0, 1), 1) # reshaped for troposphere operations
            self.opacity, self.sky_temp = self.trop_return_opacity_sky_temp()
            self.transmission = np.exp(-1*self.opacity)
        

    def interferometric_sim(self):
        """FFT + UV sampling via the MeqTrees run function"""

        ### for static source, single input FITS image ###
        if self.input_fitsimage.endswith(('.fits','.FITS')):
            info('Input sky model is assumed static, given single input FITS image')
            run_turbosim(self.input_fitsimage,self.output_column,'')

        ### if time-variable source, input directory with > 1 fits images ###
        elif os.path.isdir(self.input_fitsimage):
            self.input_fitsimage_list = np.sort(glob.glob(os.path.join(self.input_fitsimage,'./*')))
            self.num_epochs = len(self.input_fitsimage_list)
            self.minutes_per_epoch = self.obslength/float(self.num_epochs) * 60
            self.mjd_per_epoch = (self.time_unique[-1] - self.time_unique[0]) / self.num_epochs

            info('Assuming time-variable source with %i epochs (%.1f minutes per epoch)'\
                 %(self.num_epochs,self.minutes_per_epoch))
            info('Using the following input fits images:\n' + '\n\t'.join(\
                [fitsim.split('/')[-1] for fitsim in self.input_fitsimage_list]))
            for epoch in range(self.num_epochs):
                taql_string = '"TIME IN {%.7f, %.7f}"'\
                              %(( self.mjd_obs_start + (epoch*self.mjd_per_epoch)),\
                                ( self.mjd_obs_start + ((epoch+1)*self.mjd_per_epoch)))
                info('Now simulating epoch #%i, taql_string = %s, fits image: %s'\
                     %(epoch,taql_string,self.input_fitsimage_list[epoch]))
                run_turbosim(self.input_fitsimage_list[epoch],self.output_column,taql_string)
            
        else:
            abort('Problem with input fits image(s)')
                
        tab = pt.table(self.msname, readonly=True,ack=False)
        self.data = tab.getcol(self.output_column) 
        tab.close()

    def copy_MS(self, new_name):
        x.sh('cp -r %s %s' % (self.msname, new_name))

    def save_data(self):
        """All saving of data goes through this function"""
        tab = pt.table(self.msname, readonly=False,ack=False)
        tab.putcol(self.output_column, self.data)
        tab.close()
        
    def add_receiver_noise(self, load=None):
        """ baseline dependent thermal noise only. Calculated from SEFDs, tint, dnu """
        if load:
            self.thermal_noise = np.load(II('$OUTDIR')+'/receiver_noise.npy')
        else:
            self.thermal_noise = np.zeros(self.data.shape, dtype='complex')
            size = (self.time_unique.shape[0], self.chan_freq.shape[0], 4)
            for a0 in range(self.Nant):
                for a1 in range(self.Nant):
                    if a1 > a0:
                        rms = np.sqrt(self.SEFD[a0] * self.SEFD[a1] / float(2 * self.tint * self.chan_width))

                        self.thermal_noise[self.baseline_dict[(a0, a1)]] =\
                            1 / np.sqrt(2) * (np.random.normal(0.0, rms, size=size) + 1j * np.random.normal(0.0, rms,
                                                                                                            size=size))

            np.save(II('$OUTDIR')+'/receiver_noise', self.thermal_noise)
        self.data = np.add(self.data, self.thermal_noise)
        self.save_data()
        info("Thermal noise added")

        self.weights = 1/abs(self.thermal_noise)**2
        
        tab = pt.table(self.msname, readonly=False,ack=False)
        tab.putcol("WEIGHT", self.weights[:,0,:])
        tab.close()
        info('WEIGHT column updated based on thermal noise only. '+ \
             'Weights are frequency independent at this stage. '  + \
             'WEIGHT_SPECTRUM could be written to incorporting '  + \
             'frequency dependent effects (e.g. tropopheric opacity)')




        
    def make_baseline_dictionary(self):
        return dict([((x, y), np.where((self.A0 == x) & (self.A1 == y))[0])
                    for x in self.ant_unique for y in self.ant_unique if y > x])



                                                                                                                                
    
    def elevation_calc(self):
        measure = pm.measures()
        ra = qa.quantity(self.direction[0], 'rad'); dec = qa.quantity(self.direction[1], 'rad')
        pointing = measure.direction('j2000', ra, dec)
        start_time = measure.epoch('utc', qa.quantity(self.time_unique[0], 's'))
        measure.doframe(start_time)

        elevation_ant_matrix = np.zeros((self.Nant, self.time_unique.shape[0]))

        def antenna_elevation(antenna):
            x = qa.quantity(self.pos[antenna, 0], 'm')
            y = qa.quantity(self.pos[antenna, 1], 'm')
            z = qa.quantity(self.pos[antenna, 2], 'm')
            position = measure.position('wgs84', x, y, z)
            measure.doframe(position)
            sec2rad = 2 * np.pi / (24 * 3600.)
            hour_angle = measure.measure(pointing, 'HADEC')['m0']['value'] +\
                         (self.time_unique-self.time_unique.min()) * sec2rad
            earth_radius = 6371000.0
            latitude = np.arcsin(self.pos[antenna, 2]/earth_radius)
            return np.arcsin(np.sin(latitude)*np.sin(self.direction[1])+np.cos(latitude)*np.cos(self.direction[1]) *
                             np.cos(hour_angle))

        for i in range(self.Nant):
            elevation_ant_matrix[i] = antenna_elevation(i)
    
        return elevation_ant_matrix


    def calc_ant_rise_set_times(self):
        self.mjd_ant_rise = np.zeros(self.Nant)
        self.mjd_ant_set = np.zeros(self.Nant)
        for ant in range(self.Nant):
            self.mjd_ant_rise[ant] = self.time_unique[np.logical_not(np.isnan(self.elevation[ant,:]))].min()
            self.mjd_ant_set[ant] = self.time_unique[np.logical_not(np.isnan(self.elevation[ant,:]))].max()
        
    def calculate_baseline_min_elevation(self):
        self.baseline_min_elevation = np.zeros(len(self.uvw[:,0]))
        temp_elevation = self.elevation.copy()
        temp_elevation[np.isnan(temp_elevation)] = 1000. # set nan's high. Flags used in plotting
        #elevation_mask = temp_elevation < 90.
        for ant0 in range(self.Nant):
            for ant1 in range(self.Nant):
                if (ant1 > ant0):
                    self.baseline_min_elevation[self.baseline_dict[(ant0,ant1)]] = \
                        np.min(np.vstack([temp_elevation[ant0, :], temp_elevation[ant1, :]]), axis=0)


    def calculate_baseline_mean_elevation(self):
        self.baseline_mean_elevation = np.zeros(len(self.uvw[:,0]))
        temp_elevation = self.elevation.copy()
        temp_elevation[np.isnan(temp_elevation)] = 1000. # set nan's high. Flags used in plotting
        #elevation_mask = temp_elevation < 90.
        for ant0 in range(self.Nant):
            for ant1 in range(self.Nant):
                if (ant1 > ant0):
                    self.baseline_mean_elevation[self.baseline_dict[(ant0,ant1)]] = \
                        np.mean(np.vstack([temp_elevation[ant0, :], temp_elevation[ant1, :]]), axis=0)

    
    def write_flag(self, elevation_limit):
        """ flag data if below user-specified elevation limit """
        for a0 in range(self.Nant):
            for a1 in range(self.Nant):
                if a1 > a0:
                    flag_mask = np.invert(((self.elevation[a1] > elevation_limit) &
                                           (self.elevation[a0] > elevation_limit)) > 0)
                    self.flag[self.baseline_dict[(a0, a1)]] = flag_mask.reshape((flag_mask.shape[0], 1, 1))

        tab = pt.table(self.msname, readonly=False,ack=False)
        tab.putcol("FLAG", self.flag)
        info('FLAG column re-written using antenna elevation limit(s)')
        tab.close()



    def trop_opacity_attenuate(self):
        transmission_matrix = np.exp(-1 * self.opacity / np.sin(self.elevation_tropshape))
        np.save(II('$OUTDIR')+'/transmission', transmission_matrix)

        transmission_matrix = np.expand_dims(transmission_matrix, 3)
        self.transmission_matrix = transmission_matrix
        transmission_column = np.zeros(self.data.shape)
        for a0 in range(self.Nant):
            for a1 in range(self.Nant):
                if a1 > a0:
                    transmission_column[self.baseline_dict[(a0, a1)]] = transmission_matrix[:, :, a0, :] * \
                                                                        transmission_matrix[:, :, a1, :]

        self.data = np.multiply(self.data, transmission_column)
        self.save_data()




    def trop_return_opacity_sky_temp(self):
        """ as it says on the tin """
        opacity, sky_temp = np.zeros((2, 1, self.chan_freq.shape[0], self.Nant))

        for ant in range(self.Nant):
            if not os.path.exists(II('$OUTDIR')+'/atm_output/'):
                os.makedirs(II('$OUTDIR')+'/atm_output/')

            #ATM_abs_string = './absorption --fmin %f --fmax %f --fstep %f --pwv %f --gpress %f --gtemp %f' %\
                                                 #(fmin, fmax, fstep, pwv, gpress, gtemp)
            fmin,fmax,fstep = (self.chan_freq[0]-(self.chan_width)) / 1e9,\
                              (self.chan_freq[-1] + (self.chan_width*0/2.)) / 1e9, \
                              self.chan_width/1e9    # note that fmin output != self.chan_freq
            ATM_abs_string = 'absorption --fmin %f --fmax %f --fstep %f --pwv %f --gpress %f --gtemp %f' %\
                             (fmin, fmax, fstep, self.average_pwv[ant], \
                              self.average_gpress[ant],self.average_gtemp[ant])
            
            #output = subprocess.check_output(self.ATM_absorption_string(self.chan_freq[0]-self.chan_width, self.chan_freq[-1], self.chan_width,self.average_pwv[ant], self.average_gpress[ant],self.average_gtemp[ant]),shell=True)
            output = subprocess.check_output(ATM_abs_string,shell=True)
            atmfile = open(II('$OUTDIR')+'/atm_output/ATMstring_ant%i.txt'%ant,'w')
            print>>atmfile,ATM_abs_string
            atmfile.close()
            atm_abs = file(II('$OUTDIR')+'/atm_output/%satm_abs.txt' % ant, 'w'); atm_abs.write(output); atm_abs.close()
            freq_atm,dry, wet, temp_atm = np.swapaxes(np.loadtxt(II('$OUTDIR')+'/atm_output/%satm_abs.txt'%ant, skiprows=1, usecols=[0, 1, 2, 3],
                                                        delimiter=', \t'), 0, 1)
            # the following catch is due to a bug in the ATM package
            # which results in an incorrect number of channels returned.
            # The following section just checks and corrects for that. 

            if (len(self.chan_freq) != len(freq_atm)):
                abort('!!! ERROR: THIS IS AN AATM bug. !!!\n\t'+\
                 'number of frequency channels in ATM output = %i\n\t'\
                    %len(freq_atm)+\
                'which is NOT equal to Measurement Set nchans = %i\n\t'\
                    %len(self.chan_freq)+ 'which was requested.'+\
                '\nThe AATM developers have been contacted about\n'+\
                'this bug, however, an interim workaround is to select\n'+\
                'a slightly different channel width and/or number of channels')

            if (self.trop_wetonly == 1):
                opacity[:, :, ant] = wet
            else:
                opacity[:,:,ant] = dry + wet

            sky_temp[:, :, ant] = temp_atm
        return opacity, sky_temp





    def trop_add_sky_noise(self, load=None):
        """ for non-zero tropospheric opacity, calc sky noise"""

        if load:
            """this option to load same noise not available in new MeqSilhouette version"""
            self.sky_noise = np.load(II('$OUTDIR')+'/atm_output/sky_noise.npy')

        else:

            sefd_matrix = 2 * Boltzmann / self.dish_area * (1e26*self.sky_temp * (1. - np.exp(-1.0 * self.opacity / np.sin(self.elevation_tropshape))))
            self.sky_noise = np.zeros(self.data.shape, dtype='complex')

            self.sefd_matrix = sefd_matrix
            
            for a0 in range(self.Nant):
                for a1 in range(self.Nant):
                    if a1 > a0:
                        rms = np.sqrt(sefd_matrix[:, :, a0] * sefd_matrix[:, :, a1] / (float(2 * self.tint * self.chan_width)))
                        self.temp_rms = rms
                        rms = np.expand_dims(rms, 2)
                        rms = rms * np.ones((1, 1, 4))
                        self.sky_noise[self.baseline_dict[(a0, a1)]] = 1 / np.sqrt(2) * (np.random.normal(0.0, rms) + 1j * np.random.normal(0.0, rms))
            np.save(II('$OUTDIR')+'/atm_output/sky_noise', self.sky_noise)
        self.data = np.add(self.data, self.sky_noise)
        self.save_data()
        



    def trop_generate_turbulence_phase_errors(self):  ## was calc_phase_errors(self)
        turb_phase_errors = np.zeros((self.time_unique.shape[0], self.chan_freq.shape[0], self.Nant))
        beta = 5/3.
        stddevs = np.sqrt(1/(beta**2 + 3 * beta + 2) * (self.tint/self.coherence_time)**beta)
        np.save(II('$OUTDIR')+'/turbulence_phase_std_devs', np.array(stddevs))
        for ant in range(self.Nant):
            turb_phase_errors[:, 0, ant] = np.sqrt(1/np.sin(self.elevation_tropshape[:, 0, ant])) * \
                                np.cumsum(np.random.normal(0, stddevs[ant], self.time_unique.shape[0]))

            turb_phase_errors[:, :, ant] = np.multiply(turb_phase_errors[:, 0, ant].reshape((self.time_unique.shape[0], 1)),
                                            (self.chan_freq/self.chan_freq[0]).reshape((1, self.chan_freq.shape[0])))


        np.save(II('$OUTDIR')+'/turbulent_phase_errors', turb_phase_errors)

        self.turb_phase_errors = turb_phase_errors



    def trop_calc_fixdelay_phase_offsets(self):
        """insert constant delay for each station for all time stamps. 
        Used for testing fringe fitters"""
        delay_ref_channel = 0 # NB: delay referenced is hardwired to channel 0
            # This is currently hard-wired, as we don't expect this
            # to be used extensively. 
        fixed_delays = np.random.rand(self.Nant)*(self.fixdelay_max_picosec*1e-12) \
                       - (self.fixdelay_max_picosec/2.*1e-12) # from .json file
        fixdelay_phase_errors = np.zeros((self.time_unique.shape[0], self.chan_freq.shape[0], self.Nant))

        for ant in range(self.Nant):
            phases = 2*np.pi * fixed_delays[ant] * (self.chan_freq - self.chan_freq[delay_ref_channel]) 
            fixdelay_phase_errors[:,:,ant] = phases

        np.save(II('$OUTDIR')+'/fixdelay_phase_errors_chanref%i'%delay_ref_channel, fixdelay_phase_errors)
        np.save(II('$OUTDIR')+'/fixed_delays_noreference',fixed_delays)

        info('Fixed delays min/max = %.1f pico-seconds'\
            %self.fixdelay_max_picosec )

        self.fixdelay_phase_errors = fixdelay_phase_errors



    

    def trop_ATM_dispersion(self):
        """ calculate extra path length per frequency channel """
        extra_path_length = np.zeros((self.chan_freq.shape[0], self.Nant))

        for ant in range(self.Nant):

            fmin,fmax,fstep = (self.chan_freq[0]-(self.chan_width/2.)) / 1e9,\
                              (self.chan_freq[-1] + (self.chan_width/2.)) / 1e9, \
                              self.chan_width/1e9
            ATM_disp_string = 'dispersive --fmin %f --fmax %f --fstep %f --pwv %f --gpress %f --gtemp %f' %\
                             (fmin, fmax, fstep, self.average_pwv[ant], \
                              self.average_gpress[ant],self.average_gtemp[ant])
            
            output = subprocess.check_output(ATM_disp_string,shell=True)

                #output = subprocess.check_output(self.ATM_dispersive_string(self.chan_freq[0]-self.chan_width, self.chan_freq[-1], self.chan_width,
                #  self.average_pwv[ant], self.average_gpress[ant], self.average_gtemp[ant]),shell=True)
            atm_disp = file(II('$OUTDIR')+'/atm_output/%satm_disp.txt' % ant, 'w'); atm_disp.write(output); atm_disp.close()
            wet_non_disp, wet_disp, dry_non_disp = np.swapaxes(np.genfromtxt(II('$OUTDIR')+'/atm_output/%satm_disp.txt'%ant, skip_header=1, usecols=[1, 2, 3],
                                                              delimiter=',',autostrip=True), 0, 1)
            if (self.trop_wetonly):
                extra_path_length[:, ant] = wet_disp + wet_non_disp
            else:
                extra_path_length[:, ant] = wet_disp + wet_non_disp  + dry_non_disp


            np.save(II('$OUTDIR')+'/atm_output/delay_norm_ant%i'%ant, extra_path_length[:,ant] / speed_of_light)

        np.save(II('$OUTDIR')+'/atm_output/delay_norm', extra_path_length / speed_of_light)

            
        return extra_path_length
    






    def trop_calc_mean_delays(self):
        """ insert mean delays (i.e. non-turbulent) due to dry and wet components"""
        delay = self.trop_ATM_dispersion() / speed_of_light
        self.delay_alltimes = delay / np.sin(self.elevation_tropshape)
        phasedelay_alltimes = 2*np.pi * delay / np.sin(self.elevation_tropshape) * self.chan_freq.reshape((1, self.chan_freq.shape[0], 1))
        np.save(II('$OUTDIR')+'/atm_output/phasedelay_alltimes', phasedelay_alltimes)
        np.save(II('$OUTDIR')+'/atm_output/delay_alltimes', self.delay_alltimes)

        self.phasedelay_alltimes = phasedelay_alltimes 



        

    def trop_phase_corrupt(self, normalise=True, percentage_turbulence=100, load=None):
        ### REPLACE WITH A GENERATE TROP SIM COORDINATOR, THAT COLLECTS ALL TROP COORUPTIONS """
        """only supports different channels but not different subbands"""

        if load:
            info('Loading previously saved phase errors from file:\n'+\
                 II('$OUTDIR')+'/turbulent_phases.npy')
            errors = np.load(II('$OUTDIR')+'/turbulent_phases.npy')

        else:
            errors = self.calc_phase_errors()

        errors *= percentage_turbulence/100.

        if normalise:
            errors += self.phase_normalisation()

        for a0 in range(self.Nant):
            for a1 in range(self.Nant):
                if a1 > a0:
                    # the following line was errors[:,:,a1] - errors[:,:,a0], 
                    # swopped it around to get right delay signs from AIPS
                    error_column = np.exp(1j * (errors[:, :, a0] - errors[:, :, a1]))
                    self.data[self.baseline_dict[(a0, a1)]] = np.multiply(self.data[self.baseline_dict[(a0, a1)]],
                                                                          np.expand_dims(error_column, 2))
        self.save_data()
        info('Kolmogorov turbulence-induced phase fluctuations applied')





    def apply_phase_errors(self,combined_phase_errors):
        for a0 in range(self.Nant):
            for a1 in range(self.Nant):
                if a1 > a0:
                    # the following line was errors[:,:,a1] - errors[:,:,a0],
                    # swopped it around to get right delay signs from AIPS
                    error_column = np.exp(1j * (combined_phase_errors[:, :, a0] \
                                            - combined_phase_errors[:, :,a1]))
                    self.data[self.baseline_dict[(a0, a1)]] = \
                        np.multiply(self.data[self.baseline_dict[(a0, a1)]],\
                        np.expand_dims(error_column, 2))
        self.save_data()

        

    def trop_plots(self):

        ### plot zenith opacity vs frequency (subplots)
        fig,axes = pl.subplots(self.Nant,1,figsize=(10,16))
        color.cycle_cmap(self.Nant,cmap=cmap)
        for i,ax in enumerate(axes.flatten()):
            ax.plot(self.chan_freq/1e9,self.transmission[0,:,i],label=self.station_names[i])
            ax.legend()
            ax.set_ylim(np.nanmin(self.transmission),1)
        pl.xlabel('frequency / GHz')
        pl.ylabel('transmission')
        pl.tight_layout()
        pl.savefig(os.path.join(v.PLOTDIR,'transmission_vs_freq_subplots.png'),bbox_inches='tight')
        pl.close()

        ### plot zenith opacity vs frequency
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap) 
        for i in range(self.Nant):
            pl.plot(self.chan_freq/1e9,self.transmission[0,:,i],label=self.station_names[i])
        pl.xlabel('frequency / GHz')
        pl.ylabel('zenith transmission')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'zenith_transmission_vs_freq.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()

        ### plot elevation-dependent transmission vs frequency
        pl.figure() #figsize=(10,6.8))
        for i in range(self.Nant):
            pl.imshow(self.transmission_matrix[:,:,i,0],origin='lower',aspect='auto',\
                      extent=[(self.chan_freq[0]-(self.chan_width/2.))/1e9,(self.chan_freq[-1]+(self.chan_width/2.))/1e9,0,self.obslength/3600.])
            pl.xlabel('frequency / GHz')
            pl.ylabel('relative time / hr')
            cb = pl.colorbar()
            cb.set_label('transmission')
            pl.title(self.station_names[i])
            pl.tight_layout()
            pl.savefig(os.path.join(v.PLOTDIR,'transmission_vs_freq_%s.png'%self.station_names[i]))
            pl.clf()



        ### plot zenith sky temp vs frequency
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap)
        for i in range(self.Nant):
            pl.plot(self.chan_freq/1e9,self.sky_temp[0,:,i],label=self.station_names[i])
        pl.xlabel('frequency / GHz')
        pl.ylabel('zenith sky temperature / K')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'zenith_skytemp_vs_freq.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()
                                                                                            

        ### plot tubulent phase on time/freq grid? 

        pl.figure() #figsize=(10,6.8))
        for i in range(self.Nant):
            pl.imshow(self.turb_phase_errors[:,:,i],origin='lower',aspect='auto',vmin=-180,vmax=180,\
                      extent=[(self.chan_freq[0]-(self.chan_width/2.))/1e9,(self.chan_freq[-1]+(self.chan_width/2.))/1e9,0,self.obslength/3600.])
            pl.xlabel('frequency / GHz')
            pl.ylabel('relative time / hr')
            cb = pl.colorbar()
            cb.set_label('turbulent phase / degrees')
            pl.title(self.station_names[i])
            pl.tight_layout()
            pl.savefig(os.path.join(v.PLOTDIR,'turbulent_phase_waterfall_plot_%s.png'%self.station_names[i]))
            pl.clf()
                                                                                                                            
        ### plot turbulent phase errors vs time
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap)
        for i in range(self.Nant):
            pl.plot(np.linspace(0,self.obslength,len(self.time_unique))/(60*60.),\
                    self.turb_phase_errors[:,len(self.turb_phase_errors[0,:,0])/2,i],label=self.station_names[i])
        pl.xlabel('relative time / hr')
        pl.ylabel('tubulent phase / degrees')
        pl.ylim(-180,180)
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'turbulent_phase_vs_time.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()



        ### plot delays vs time
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap)
        try:
            delay_temp = fixdelay_phase_errors # checks if fixdelays are set
        except NameError:
            delay_temp = self.delay_alltimes
        for i in range(self.Nant):
            pl.plot(np.linspace(0,self.obslength,len(self.time_unique))/(60*60.),\
                    np.nanmean(delay_temp[:,:,i],axis=1) * 1e9,label=self.station_names[i])
        pl.xlabel('relative time / hr')
        pl.ylabel('delay / nano-seconds')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'mean_delay_vs_time.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()





        ################################
        ### POINTING ERROR FUNCTIONS ###
        ################################

    def pointing_constant_offset(self,pointing_rms, pointing_timescale,PB_FWHM230):
            """this will change the pointing error for each antenna every pointing_timescale
            which one of could essentially think of as a scan length (e.g. 10 minutes)"""
            self.PB_FWHM = PB_FWHM230 / (self.chan_freq.mean() / 230e9) # convert 230 GHz PB to current obs frequency
            self.num_mispoint_epochs = int(np.floor(self.obslength / (pointing_timescale * 60.))) # could be number of scans, for example
            self.mjd_per_ptg_epoch = (self.mjd_obs_end - self.mjd_obs_start) / self.num_mispoint_epochs
            self.mjd_ptg_epoch_timecentroid = np.arange(self.mjd_obs_start,self.mjd_obs_end,
                                                        self.mjd_per_ptg_epoch) + (self.mjd_per_ptg_epoch/2.)

            
            self.pointing_offsets = pointing_rms.reshape(self.Nant,1) * np.random.randn(self.Nant,self.num_mispoint_epochs) # units: arcsec
            for ant in range(self.Nant):
                ind = (self.mjd_ptg_epoch_timecentroid < self.mjd_ant_rise[ant]) \
                    | (self.mjd_ptg_epoch_timecentroid > self.mjd_ant_set[ant])

                self.pointing_offsets[ant,ind] = np.nan # this masks out pointing offsets for stowed antennas



            PB_model = ['gaussian']*self.Nant # primary beam model set in input config file. Hardwired to Gaussian for now. 

            amp_errors = np.zeros([self.Nant,self.num_mispoint_epochs])
            for ant in range(self.Nant):
                if PB_model[ant] == 'consine3':
                    amp_errors[ant,:] = np.cos(self.pointing_offsets[ant,:]/206265.)**3 #placeholder, incorrect

                elif PB_model[ant] == 'gaussian':
                    amp_errors[ant,:] = np.exp(-0.5*(self.pointing_offsets[ant,:]/(self.PB_FWHM[ant]/2.35))**2) 

                    
            self.pointing_amp_errors = amp_errors


    def apply_pointing_amp_error(self):
            for a0 in range(self.Nant):
                for a1 in range(self.Nant):
                    if a1 > a0:
                        bl_indices = self.baseline_dict[(a0,a1)] # baseline indices only, all times
                        for mispoint_epoch in range(self.num_mispoint_epochs):
                            epoch_ind_mask = (self.time[bl_indices] > ( self.mjd_obs_start + (mispoint_epoch*self.mjd_per_ptg_epoch))) &\
                                       (self.time[bl_indices] < ( self.mjd_obs_start + (mispoint_epoch+1)*self.mjd_per_ptg_epoch))
                                        
                                         # need to add a elevation mask 
                            bl_epoch_indices = bl_indices[epoch_ind_mask]
                            
                                        
            
                            self.data[bl_epoch_indices,:,:] *= (self.pointing_amp_errors[a0,mispoint_epoch] \
                                                                * self.pointing_amp_errors[a1,mispoint_epoch])
                        #### NOTE: this applies to all pols, all frequency channels (i.e. no primary beam freq dependence)
                        #self.data[indices,0,3] *= (self.point_amp_errors[a0] * self.point_amp_errors[a1])



    def plot_pointing_errors(self):

        ### plot antenna offset vs pointing epoch
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap)
        for i in range(self.Nant):
            pl.plot(np.linspace(0,self.obslength/3600,self.num_mispoint_epochs),self.pointing_offsets[i,:],alpha=1,label=self.station_names[i])
        pl.xlabel('time since obs start / hours')
        pl.ylabel('antenna pointing offset / arcsec')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'pointing_angular_offset_vs_time.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()
                                                                                                


        ### plot pointin amp error vs pointing epoch
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap)
        for i in range(self.Nant):
            pl.plot(np.linspace(0,self.obslength/3600,self.num_mispoint_epochs),self.pointing_amp_errors[i,:],alpha=1,label=self.station_names[i])
        pl.ylim(np.nanmin(self.pointing_amp_errors[:, :]) * 0.9, 1.04)
        pl.xlabel('time since obs start / hours')
        pl.ylabel('true primary beam response') #antenna pointing amplitude error')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'pointing_amp_error_vs_time.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()


        ### plot pointing amp error vs pointing offset
        pl.figure(figsize=(10,6.8))
        color.cycle_cmap(self.Nant, cmap=cmap)
        for i in range(self.Nant):
            pl.plot(abs(self.pointing_offsets[i,:]),self.pointing_amp_errors[i,:],'o',alpha=1,label=self.station_names[i])
        pl.xlim(0,np.nanmax(abs(self.pointing_offsets))*1.1)
        pl.ylim(np.nanmin(self.pointing_amp_errors[i,:])*0.8,1.04)
        pl.xlabel('pointing offset / arcsec')
        pl.ylabel('true primary beam response') #antenna pointing amplitude error')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'pointing_amp_error_vs_angular_offset.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')
        pl.close()
 
                  


    def make_ms_plots(self):
        """uv-coverage, uv-dist sensitivty bins, etc. All by baseline colour"""
        info('making MS inspection plots')

        ### uv-coverage plot, different color baselines, legend, uv-annuli ###
        pl.figure(figsize=(16,16))
        #from mpltools import color
        cmap = pl.cm.Set1
        color.cycle_cmap(self.Nant, cmap=cmap)
        fig, ax = pl.subplots()
        for ant0 in range(self.Nant):
            for ant1 in range(self.Nant):
                if (ant1 > ant0) and \
                        not ((self.station_names[ant0]=='JCMT') or (self.station_names[ant1] == 'JCMT')):

                    temp_mask = np.logical_not(self.flag[self.baseline_dict[(ant0,ant1)],0,0])
                    temp_u = self.uvw[self.baseline_dict[(ant0,ant1)][temp_mask], 0]\
                         / (speed_of_light/self.chan_freq.mean())/1e9
                    temp_v = self.uvw[self.baseline_dict[(ant0,ant1)][temp_mask], 1]\
                         / (speed_of_light/self.chan_freq.mean())/1e9
                    #if (np.sqrt((temp_u.max()**2 + temp_v.max()**2)) > 0.1):
                    pl.plot(np.hstack([temp_u,np.nan, -temp_u]), np.hstack([temp_v,np.nan, -temp_v]), \
                            lw=2.5,label='%s-%s'%(self.station_names[ant0],self.station_names[ant1]))
            #pl.plot(-self.uvw[np.logical_not(self.flag[:, 0, 0]), 0], -self.uvw[np.logical_not(self.flag[:, 0, 0]), 1], \
            #        label=self.station_names[i])
        lgd = pl.legend(bbox_to_anchor=(1.02, 1), loc=2, shadow=True,fontsize='small')
        ax = pl.gca()

        uvbins_edges = np.arange(0, 11, 1)  # uvdistance units: Giga-lambda
        uvbins_centre = (uvbins_edges[:-1] + uvbins_edges[1:]) / 2.
        numuvbins = len(uvbins_centre)
        binwidths = uvbins_edges[1] - uvbins_edges[0]
        for b in range(numuvbins):
            p = Circle((0, 0), uvbins_edges[b + 1], edgecolor='k', ls='solid', facecolor='none', alpha=0.5, lw=0.5)
            ax.add_artist(p)
        pl.xlabel('$u$ /  G$\,\lambda$')
        pl.ylabel('$v$ /  G$\,\lambda$')
        pl.xlim(-10, 10)
        pl.ylim(-10, 10)
        ax.set_aspect('equal')
        pl.savefig(os.path.join(v.PLOTDIR, 'uv-coverage_legend.png'), \
                   bbox_extra_artists=(lgd,), bbox_inches='tight')


        ### uv-coverage plot, colorize by minimun elevation, uv-annuli ###
        self.calculate_baseline_min_elevation() # calc min elevation in the two e for every baseline and every timestep
        self.calculate_baseline_mean_elevation()# as above, but for mean

        pl.figure(figsize=(16,16))
        #from mpltools import color
        cmap = pl.cm.Set1
        #color.cycle_cmap(self.Nant, cmap=cmap)
        fig, ax = pl.subplots()
        #temp_elevation = self.elevation.copy()
        #temp_elevation[np.isnan(temp_elevation)] = 1000.
        #elevation_mask = temp_elevation < 90.
        # converted from nan and set arbitrarily high
        for ant0 in range(self.Nant):
            for ant1 in range(self.Nant):
                if (ant1 > ant0) and \
                        not ((self.station_names[ant0]=='JCMT') or (self.station_names[ant1] == 'JCMT')):

                    temp_mask = np.logical_not(self.flag[self.baseline_dict[(ant0,ant1)],0,0])
                    self.temp_u = self.uvw[self.baseline_dict[(ant0,ant1)][temp_mask], 0]\
                         / (speed_of_light/self.chan_freq.mean())/1e9
                    self.temp_v = self.uvw[self.baseline_dict[(ant0,ant1)][temp_mask], 1]\
                         / (speed_of_light/self.chan_freq.mean())/1e9
                    temp_minelev = self.baseline_min_elevation[self.baseline_dict[(ant0,ant1)][temp_mask]]

                    pl.scatter(np.hstack([self.temp_u, -self.temp_u]), np.hstack([self.temp_v, -self.temp_v]), \
                            c=np.hstack([temp_minelev,temp_minelev])*180./np.pi,\
                               s=10,cmap="viridis",edgecolors="None",vmin=0,vmax=30) #
        cb = pl.colorbar()
        cb.set_label("min baseline elevation / degrees")
        ax = pl.gca()
        for b in range(numuvbins):
            p = Circle((0, 0), uvbins_edges[b + 1], edgecolor='k', ls='solid', facecolor='none', alpha=0.5, lw=0.5)
            ax.add_artist(p)
        pl.xlabel('$u$ /  G$\,\lambda$')
        pl.ylabel('$v$ /  G$\,\lambda$')
        pl.xlim(-10, 10)
        pl.ylim(-10, 10)
        ax.set_aspect('equal')
        pl.savefig(os.path.join(v.PLOTDIR, 'uv-coverage_colorize_min_elevation.png'), \
                    bbox_inches='tight')



        pl.figure(figsize=(16,16))
        #from mpltools import color
        cmap = pl.cm.Set1
        #color.cycle_cmap(self.Nant, cmap=cmap)
        fig, ax = pl.subplots()
        #temp_elevation = self.elevation.copy()
        #temp_elevation[np.isnan(temp_elevation)] = 1000.
        #elevation_mask = temp_elevation < 90.
        # converted from nan and set arbitrarily high
        for ant0 in range(self.Nant):
            for ant1 in range(self.Nant):
                if (ant1 > ant0) and \
                        not ((self.station_names[ant0]=='JCMT') or (self.station_names[ant1] == 'JCMT')):

                    temp_mask = np.logical_not(self.flag[self.baseline_dict[(ant0,ant1)],0,0])
                    self.temp_u = self.uvw[self.baseline_dict[(ant0,ant1)][temp_mask], 0]\
                         / (speed_of_light/self.chan_freq.mean())/1e9
                    self.temp_v = self.uvw[self.baseline_dict[(ant0,ant1)][temp_mask], 1]\
                         / (speed_of_light/self.chan_freq.mean())/1e9
                    temp_meanelev = self.baseline_mean_elevation[self.baseline_dict[(ant0,ant1)][temp_mask]]

                    pl.scatter(np.hstack([self.temp_u, -self.temp_u]), np.hstack([self.temp_v, -self.temp_v]), \
                            c=np.hstack([temp_meanelev,temp_meanelev])*180./np.pi,\
                               s=10,cmap="viridis",edgecolors="None",vmin=0,vmax=30) #
        cb = pl.colorbar()
        cb.set_label("mean baseline elevation / degrees")
        ax = pl.gca()
        for b in range(numuvbins):
            p = Circle((0, 0), uvbins_edges[b + 1], edgecolor='k', ls='solid', facecolor='none', alpha=0.5, lw=0.5)
            ax.add_artist(p)
        pl.xlabel('$u$ /  G$\,\lambda$')
        pl.ylabel('$v$ /  G$\,\lambda$')
        pl.xlim(-10, 10)
        pl.ylim(-10, 10)
        ax.set_aspect('equal')
        pl.savefig(os.path.join(v.PLOTDIR, 'uv-coverage_colorize_mean_elevation.png'), \
                    bbox_inches='tight')





        ampbins = np.zeros([numuvbins])
        stdbins = np.zeros([numuvbins])
        phasebins = np.zeros([numuvbins])
        phstdbins = np.zeros([numuvbins])
        Nvisperbin = np.zeros([numuvbins])
        corrs = [0,3] # only doing Stokes I for now

        for b in range(numuvbins):
            mask = ( (self.uvdist / (speed_of_light/self.chan_freq.mean())/1e9) > uvbins_edges[b]) & \
                   ( (self.uvdist / (speed_of_light/self.chan_freq.mean())/1e9) < uvbins_edges[b + 1]) & \
                   (np.logical_not(self.flag[:, 0, 0]))  # mask of unflagged visibilities in this uvbin
            Nvisperbin[b] = mask.sum()  # total number of visibilities in this uvbin
            ampbins[b] = np.nanmean(abs(self.data[mask, :, :])[:, :, corrs])  # average amplitude in bin "b"
            #stdbins[b] = np.nanstd(abs(self.data[mask, :, :])[:, :, corrs]) / Nvisperbin[b]**0.5  # rms of that bin
            stdbins[b] = np.nanmean(abs(np.add(self.thermal_noise[mask,:,:][:,:,corrs],\
                                              self.sky_noise[mask,:,:][:,:,corrs]))) / Nvisperbin[b]**0.5
            # next few lines if a comparison array is desired (e.g. EHT minus ALMA)
            #mask_minus1ant = (uvdist > uvbins_edges[b])&(uvdist< uvbins_edges[b+1])&(np.logical_not(flag_col[:,0,0]))& \
            # (ant1 != station_name.index('ALMA'))&(ant2 != station_name.index('ALMA'))
            # mask of unflagged visibilities in this uvbin, that don't include any ALMA baselines
            #Nvisperbin_minus1ant[b] = mask_nomk.sum()  # total number of visibilities in this uvbin
            #ampbins_minus1ant[b] = np.nanmean(abs(data[mask_nomk, :, :])[:, :, corrs])  # average amplitude in bin "b"
            #stdbins_minus1ant[b] = np.nanstd(abs(data[mask_nomk, :, :])[:, :, corrs]) / Nvisperbin_nomk[b] ** 0.5  # rms of that bin

            phasebins[b] = np.nanmean(np.arctan2(self.data[mask, :, :].imag, \
                                                 self.data[mask, :, :].real)[:, :,
                                      corrs])  # average phase in bin "b"
            phstdbins[b] = np.nanstd(np.arctan2(self.data[mask, :, :].imag, \
                                                self.data[mask, :, :].real)[:, :, corrs])  # rms of that bin

        phasebins *= (180 / np.pi)
        phstdbins *= (180 / np.pi)  # rad2deg

        def uvdist2uas(uvd):
            theta = 1. / (uvd * 1e9) * 206265 * 1e6  # Giga-lambda to uas
            return ["%.1f" % z for z in theta]

        def uas2uvdist(ang):
            return 1. / (ang / (206265. * 1e6)) / 1e9

        ### this is for a top x-axis labels, showing corresponding angular scale for a uv-distance
        angular_tick_locations = [25, 50, 100, 200]  # specify which uvdist locations you want a angular scale




        ### amp vs uvdist, with uncertainties
        fig = pl.figure(figsize=(10,6.8))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twiny()
        yerr = stdbins/np.sqrt(Nvisperbin) #noise_per_vis/np.sqrt(np.sum(Nvisperbin,axis=0)) #yerr = noise_per_vis/np.sqrt(np.sum(allsrcs[:,2,:],axis=0))
        xerr = binwidths/2. * np.ones(numuvbins)
        for b in range(numuvbins):
            ax1.plot(uvbins_centre[b],ampbins[b],'o',mec='none',alpha=1,color='#336699')
            ax1.errorbar(uvbins_centre[b],ampbins[b],xerr=xerr[b],yerr=yerr[b],ecolor='grey',lw=0.5,alpha=1,fmt='none',capsize=0)
        #ax1.vlines(uas2uvdist(shadow_size_mas),0,np.nanmax(ampbins)*1.2,linestyles='dashed')
        ax1.set_xlabel('${uv}$-distance / G$\,\lambda$')
        ax1.set_ylabel('Stokes I amplitude / Jy')
        ax1.set_ylim(0,np.nanmax(ampbins)*1.2)
        ax1.set_xlim(0,uvbins_edges.max())
        ax2.set_xlim(ax1.get_xlim())

        # configure upper x-axis

        ax2.set_xticks(uas2uvdist(np.array(angular_tick_locations))) # np.array([25.,50.,100.,200.]))) #   angular_tick_locations))
        ax2.set_xticklabels(angular_tick_locations)
        #ax2.xaxis.set_major_formatter(FormatStrFormatter('%i'))
        ax2.set_xlabel("angular scale / $\mu$-arcsec")
        #np.savetxt('uvdistplot_ampdatapts.txt',np.vstack([uvbins_centre,xerr,ampbins,yerr]))
        pl.savefig(os.path.join(v.PLOTDIR,'amp_uvdist.png'), \
                   bbox_inches='tight')



        ### percent of visibilties per bin
        percentVisperbin = Nvisperbin/Nvisperbin.sum()*100
        #percentVisperbin_minus1ant = Nvisperbin_minus1ant/Nvisperbin_minus1ant.sum()*100
        #percent_increase = (Nvisperbin/Nvisperbin_minus1ant -1) * 100

        fig = pl.figure(figsize=(10,6.8))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twiny()
        for b in range(numuvbins):
            #ax1.bar(uvbins_centre[b],percent_increase[b],width=binwidths,color='orange',alpha=1) #,label='MeerKAT included')
            ax1.bar(uvbins_centre[b],percentVisperbin[b],width=binwidths,color='orange',alpha=0.9,align='center',edgecolor='none') #,label='')
            #ax1.bar(uvbins_centre[b],percentVisperbin_minus1ant[b],width=binwidths,color='#336699',alpha=0.6,label='MeerKAT excluded')
        ax1.set_xlabel('$uv$-distance / G$\,\lambda$')
        ax1.set_ylabel('percentage of total visibilities')
        #ax1.set_ylabel('percentage increase')
        #ax1.set_ylim(0,np.nanmax(percentVisperbin)*1.2)
        #ax1.set_ylim(0,percent_increase.max()*1.2)
        ax1.set_xlim(0,uvbins_edges.max())
        #ax1.vlines(uas2uvdist(shadow_size_uarcsec),0,np.nanmax(Nvisperbin)*1.2,linestyles='dashed')
        ax2.set_xlim(ax1.get_xlim())
        # configure upper x-axis
        ax2.set_xticks(uas2uvdist(np.array(angular_tick_locations)))
        ax2.set_xticklabels(angular_tick_locations) #(angular_tick_locations))
        ax2.set_xlabel(r"angular scale / $\mu$-arcsec")
        #pl.legend()
        pl.savefig(os.path.join(v.PLOTDIR,'num_vis_perbin.png'), \
                   bbox_inches='tight')



        ### averaged sensitivity per bin
        fig = pl.figure(figsize=(10,6.8))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twiny()
        #x_vlba,y_vlba = np.loadtxt('/home/deane/git-repos/vlbi-sim/output/XMM-LSS/vlba_xmmlss_sigma_vs_uvbin.txt').T #/home/deane/git-repos/vlbi-sim/output/VLBA_COSMOS/vlba_sigma_vs_uvbin.txt',comments='#').T
        x = np.ravel(zip(uvbins_edges[:-1],uvbins_edges[1:]))
        y = np.ravel(zip(stdbins,stdbins))
        #y_minus1ant = np.ravel(zip(stdbins_minus1ant,stdbins_minus1ant))

        #ax1.plot(x_vlba,y_vlba*1e6,color='grey',alpha=1,label='VLBA',lw=3)
        ax1.plot(x,y*1e3,color='#336699',linestyle='solid',alpha=1,label='EHT',lw=3)
        #ax1.plot(x,y*1e6,color='orange',alpha=0.7,label='EVN + MeerKAT',lw=3)

        ax1.set_xlabel('$uv$-distance / G$\,\lambda$',size=16)
        ax1.set_ylabel('thermal + sky noise rms / mJy',size=16)
        #ax1.set_ylabel('percentage increase')
        ax1.set_ylim(0,np.nanmax(y)*1.2*1e3)
        ax1.set_xlim(0,uvbins_edges.max())
        #ax1.vlines(uas2uvdist(shadow_size_uarcsec),0,np.nanmax(Nvisperbin)*1.2,linestyles='dashed')
        ax2.set_xlim(ax1.get_xlim())
        # configure upper x-axis
        ax2.set_xticks(uas2uvdist(np.array(angular_tick_locations)))
        ax2.set_xticklabels(angular_tick_locations)
        ax2.set_xlabel(r"angular scale / $\mu$-arcsec",size=16)
        ax1.legend(loc='upper left',fontsize=16)
        pl.savefig(os.path.join(v.PLOTDIR, 'sensitivity_perbin.png'), \
             bbox_inches = 'tight')


        ### elevation vs time ###
        pl.figure(figsize=(10,6.8))
        for ant in range(self.Nant):
            if (self.station_names[ant] == 'JCMT'):
                ls = 'dashed'
            else:
                ls = 'solid'
            pl.plot(np.linspace(0,self.obslength,len(self.time_unique))/(60*60.),
                    self.elevation[ant, :]*180./np.pi, alpha=1, lw=2, \
                    ls=ls,label=self.station_names[ant])
        pl.xlabel('relative time / hr')
        pl.ylabel('elevation / degrees')
        lgd = pl.legend(bbox_to_anchor=(1.02,1),loc=2,shadow=True)
        pl.savefig(os.path.join(v.PLOTDIR,'antenna_elevation_vs_time.png'),\
                   bbox_extra_artists=(lgd,), bbox_inches='tight')


