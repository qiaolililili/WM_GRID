"""
===================================
02. Find bad EEG sensors
===================================

EEG bad sensors are found using a simplified version of the PREP pipeline procedure.

"""  # noqa: E501

import os.path as op
import os
# import sys
import numpy as np
import pandas as pd
from fpdf import FPDF

import mne
from mne.time_frequency import psd_multitaper
import matplotlib.pyplot as plt
import scipy.stats

from config import site_id, subject_id, file_names, out_path
from config import no_eeg_sbj, method


def find_bad_eeg():
    # stdout_obj = sys.stdout                 # store original stdout 
    # sys.stdout = open(op.join(out_path,     # open log file
    #                           os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    # Create empty dataframe for bad channel list
    df = pd.DataFrame()
    
    # Prepare PDF report
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    
    print("Processing subject: %s" % subject_id)
    run = 0
    for file_name in file_names:
        run = run + 1
        print("  File: %s" % file_name)
        
        # Read raw data
        raw_fname_in = op.join(out_path,
                               file_name + '_' + method + '.fif')
        raw = mne.io.read_raw_fif(
            raw_fname_in, 
            preload=True, 
            verbose='error')
        
        # Check if there are EEG data
        try:
            raw.copy().pick('eeg')
        except Exception as e:
            print(e)
            raise ValueError("Error: there is no EEG recording for this participant (%s)" % (site_id+subject_id))
        
        ##############################################
        # PHASE 1 : Estimate the true signal average #
        ##############################################
        
        # Select EEG data
        raw_eeg = raw.copy().pick('eeg')
        
        # Reset bads
        raw_eeg.info['bads'] = []
        
        # Plot EEG data
        fig = raw.copy().pick('eeg').plot(bad_color=(1., 0., 0.),
                                          scalings = dict(eeg=10e-5),
                                          duration=5,
                                          start=100)
        fname_fig = op.join(out_path,
                            '02_r%s_bad_egg_0raw.png' % run)
        fig.savefig(fname_fig)
        plt.close()
        
        # Plot EEG power spectrum
        fig1 = viz_psd(raw_eeg)
        fname_fig1 = op.join(out_path,
                            '02_r%s_bad_egg_0pow.png' % run)
        fig1.savefig(fname_fig1)
        plt.close()
        
        # Add figure to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_name)
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Power Spectrum of Raw EEG Data', 'B', ln=1)
        pdf.image(fname_fig1, 0, 45, pdf.epw)
        
        # Init temporary copy of EEG
        raw_eeg_temp = raw_eeg.copy()
        
        # Init average reference
        ref_temp = np.median(raw_eeg_temp._data.copy(), axis=-2, keepdims=True)
        
        # Apply initial average reference
        raw_eeg_temp._data -= ref_temp
        
        # Init bad channel list
        bad_channels = []
        
        # Set max number of iterations and init iteration
        iteration_max = 100
        
        # Detect bad channels and recalculate the reference based on their interpolation
        for i in range(iteration_max):
            # Actual bad channel detection
            bads_temp = []
            bads_temp = find_bad_channels_eeg(raw_eeg_temp)
            
            # Exit loop if no new bad channels are found
            if all(bad in bad_channels for bad in bads_temp):
                break
            else:
                # Add new bad channel to the list
                bad_channels += bads_temp
                
                # Set bad channels
                raw_eeg_temp.info['bads'].extend(bads_temp)
                
                # Interpolate bad channels from the original data
                raw_eeg_temp = raw_eeg_temp.interpolate_bads(reset_bads=True)
                
                # Get the new average reference
                ref_temp = raw_eeg_temp._data.copy().mean(-2, keepdims=True)
                
                # Get new temp data by removing the new reference from the orignal data
                raw_eeg_temp._data = raw_eeg._data.copy() - ref_temp
        
        # Mark loop bad channels in a new copy of the data
        raw_eeg_bad = raw_eeg.copy()
        raw_eeg_bad.info['bads'].extend(bad_channels)
        
        # Interpolate loop bad channels
        raw_eeg_bad = raw_eeg_bad.interpolate_bads(reset_bads=False)
        
        # Get the true average reference
        ref_true = raw_eeg_bad._data.copy().mean(-2, keepdims=True)
        
        ############################################################################
        # PHASE 2 : Find the bad channels relative to true average and interpolate #
        ############################################################################
        
        # Remove true average reference from original EEG data
        eeg_idx = mne.pick_types(raw.info, meg=False, eeg=True, exclude=[])
        raw._data[..., eeg_idx, :] -= ref_true
        
        # Plot true referenced EEG data
        fig = raw.copy().pick('eeg').plot(bad_color=(1., 0., 0.),
                                          scalings = dict(eeg=10e-5),
                                          duration=5,
                                          start=100)
        fname_fig = op.join(out_path,
                            '02_r%s_bad_egg_1true.png' % run)
        fig.savefig(fname_fig)
        plt.close()
        
        # Find true bad channels
        bads_true = find_bad_channels_eeg(raw.copy().pick('eeg'))
        
        # Append true bad channels to the list 
        df = df.append({'run': run,
                        'bad': bads_true}, 
                        ignore_index=True)
        
        # Mark true bad channels
        raw.info['bads'].extend(bads_true)
        
        # Interpolate true bad channels
        raw = raw.interpolate_bads(reset_bads=False)
        
        # Plot interpolated EEG data
        fig = raw.copy().pick('eeg').plot(bad_color=(1., 0., 0.),
                                          scalings = dict(eeg=10e-5),
                                          duration=5,
                                          start=100)
        fname_fig = op.join(out_path,
                            '02_r%s_bad_egg_2intrp.png' % run)
        fig.savefig(fname_fig)
        plt.close()
        
        # Remove the new average reference to correct for the previous referencing
        raw.set_eeg_reference(ref_channels='average', projection=False)  #if projection=True, the reference is added as a projection and is not applied to the data (it can be applied afterwards with the apply_proj method)
        
        # Get reference correction
        ref_corr = raw.copy().pick('eeg')._data.mean(-2, keepdims=True)
        
        # Add correction to reference signal stored in raw
        ref_true += ref_corr  #TODO: where in raw is the ref stored?
        
        # Plot referenced EEG data
        fig = raw.copy().pick('eeg').plot(bad_color=(1., 0., 0.),
                                          scalings = dict(eeg=10e-5),
                                          duration=5,
                                          start=100)
        fname_fig = op.join(out_path,
                            '02_r%s_bad_egg_3refer.png' % run)
        fig.savefig(fname_fig)
        plt.close()
        
        # Plot referenced EEG power spectrum
        fig2 = viz_psd(raw)
        fname_fig2 = op.join(out_path,
                            '02_r%s_bad_egg_Ipow.png' % run)
        fig2.savefig(fname_fig2)
        plt.close()
        
        # Add figures to report
        pdf.ln(120)
        pdf.cell(0, 10, 'Power Spectrum of Filtered EEG Data', 'B', ln=1)
        pdf.image(fname_fig2, 0, 175, pdf.epw)
        
        # Reset bads
        raw.info['bads'] = []
        
        # Save data
        fname_out = op.join(out_path,
                            file_name + '_intpl.fif')
        raw.save(fname_out, overwrite=True)
        
    # Save bad channel list
    df.to_csv(op.join(out_path,
                      '02_rAll_eeg_badch_list.csv'),
              index=False)
    
    # Save report
    pdf.output(op.join(out_path,
                       os.path.basename(__file__) + '-report.pdf'))
    
    # sys.stdout.close()      # close log file
    # sys.stdout = stdout_obj # restore command prompt


def find_bad_channels_eeg(raw):
    ''' 
    Find bad EEG channels using on four criteria:
        - deviation criterion
        - correlation critetion
        - noisiness criterion
    '''
    
    #######################
    # DEVIATION CRITERION #
    #######################
        
    # Get eeg signal
    amps = raw.copy().pick('eeg')._data
    
    # Remove offset
    amps = amps - amps.mean(axis=1)[:,None]
    
    # Normalize (z-score) channel-specific amplitude
    amps_z= scipy.stats.zscore(amps, axis=None)
        
    # Average channel-specific amplitude
    amp_z_a = amps_z.mean(axis=1)
    
    # Find channels with amplitude above threshold
    thr = 5
    bad_by_deviation = np.where(amp_z_a > thr)[0]
    
    #########################
    # CORRELATION CRITERION #
    #########################
    
    # Low-pass eeg data to 50 Hz
    lowpass_signal = raw.copy().pick('eeg').filter(None, 50)
    
    # Compute channel-to-channel correlation
    data_for_corr = pd.DataFrame(np.transpose(lowpass_signal._data))
    all_corr = data_for_corr.corr()
    
    # Get max correlation of each channel  #TODO: store nr of datapoints and corr matrix
    all_corr[all_corr == 1] = 0
    max_cor = all_corr.max(axis=1)
    
    # Find channels with max correlation below threshold
    thr = .4
    bad_by_correlation = np.where(max_cor < thr)[0]
    
    #######################
    # NOISINESS CRITERION #
    #######################
    
    # Divide low and high frequency signals at 50 Hz
    lowpass_signal = raw.copy().pick('eeg').filter(None, 50)
    
    highpass_signal = raw.copy().pick('eeg').filter(50, 100)
    
    # Compute power
    low_power, _ = psd_multitaper(lowpass_signal)
    low_power = np.sum(low_power, axis=1)
    
    high_power, _ = psd_multitaper(highpass_signal)
    high_power = np.sum(high_power, axis=1)
    
    # Get the high/low ratio
    pow_ratio = high_power/low_power
    
    # Normalize ratio
    pow_ratio_z = scipy.stats.zscore(pow_ratio, axis=None)
    pow_ratio_z = abs(pow_ratio_z)
    
    # Find channels with ratio above threshold
    thr = 5
    bad_by_HF_noise = np.where(pow_ratio_z > thr)[0]
    
    ####################
    # BAD CHANNEL LIST #
    ####################

    # Concatenate bad channel list and exclude repetitions
    b = np.unique(np.concatenate((bad_by_deviation, bad_by_correlation, bad_by_HF_noise)))
    bads = []
    for i in range(len(b)):
        bads.append("EEG0%02d"%(b[i]+1))
    return bads


def viz_psd(raw):
    # Compute averaged power
    psds, freqs = psd_multitaper(raw,fmin = 1,fmax = 40, picks=['eeg'])
    psds = np.sum(psds,axis = 1)
    psds = 10. * np.log10(psds)
    # Show power spectral density plot
    fig, ax = plt.subplots(2, 1, figsize=(12, 8))
    raw.plot_psd(picks = ["eeg"], 
                  fmin = 1,fmax = 40,
                  ax=ax[0])
    # Normalize (z-score) channel-specific average power values 
    psd = {}
    psd_zscore = scipy.stats.zscore(psds)
    for i in range(len(psd_zscore)):
        psd["EEG%03d"%(i+1)] = psd_zscore[i]
    # Plot chennels ordered by power
    ax[1].bar(sorted(psd, key=psd.get,reverse = True),sorted(psd.values(),reverse = True),width = 0.5)
    labels = sorted(psd, key=psd.get,reverse = True)
    ax[1].set_xticklabels(labels, rotation=90)
    ax[1].annotate("Average power: %.2e dB"%(np.average(psds)),(27,np.max(psd_zscore)*0.9),fontsize = 'x-large')
    return fig


# =============================================================================
# RUN
# =============================================================================

if subject_id in no_eeg_sbj:
    raise ValueError("Error: no EEG collected for this participant (%s)" % (site_id+subject_id))
else:
    find_bad_eeg()
    