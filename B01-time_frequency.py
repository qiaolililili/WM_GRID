"""
================================
08. Time-frequency decomposition
================================

The epoched data is transformed to time-frequency domain using morlet wavelets.
"""

import os.path as op
import os
import sys
import numpy as np
# import pandas as pd
import matplotlib.pyplot as plt

import mne

from config import site_id, subject_id, file_names, out_path
from config import no_eeg_sbj
#from config import study_path, out_path, site_id, no_eeg_sbj_exp1#, n_run
from config import baseline_w, freq_band, factor, conditions


def run_time_frequency(make_plot = True):

    stdout_obj = sys.stdout                 # store original stdout
    sys.stdout = open(op.join(out_path,     # open log file
                              "08-time_frequency_%s.txt" % (site_id+subject_id)),'w')
    # Load epoched data
    print("Processing subject: %s" % subject_id)
    fname_epo = op.join(out_path,
                        file_names[0][0:13] + 'ALL_epo.fif')
    epochs = mne.read_epochs(fname_epo,
                             preload=True,
                             verbose=True)
    
    ### Run time-frequency decomposition
    # TFR of low frequencoes (< 30 Hz)
    if freq_band in ['low', 'both']:
        tfrs_lofr = dict()
        # Params
        freqs = np.arange(2, 30, 1)
        n_cycles = freqs / 2.
        time_bandwidth = 2.
        # Run over each condition
        for condition in conditions:
            power = mne.time_frequency.tfr_multitaper(
                epochs['%s == "%s"' % (factor, condition)],
                freqs=freqs, 
                n_cycles=n_cycles, 
                use_fft=True,
                return_itc=False,
                average = True,
                decim=2, ###
                picks='grad', ###
                time_bandwidth=time_bandwidth,
                verbose=True)
            tfrs_lofr[str(condition)] = power
        # Save tfrs as .h5
        tfr_lofr_fname_out = op.join(out_path,
                        site_id + subject_id + '_tfr_lofr_%s.h5' % factor)
        mne.time_frequency.write_tfrs(tfr_lofr_fname_out, 
                                      list(tfrs_lofr.values()), 
                                      overwrite=True)
        # Plots
        if make_plot:
            for key, tfr in tfrs_lofr.items():
                # Apply baseline correction
                tfr.apply_baseline(baseline_w, 
                                   mode="percent")
                # Show TFRs in topography
                fig = tfr.plot_topo(baseline=baseline_w,
                                    mode='mean',
                                    vmin=-1.,
                                    vmax=1.,
                                    fig_facecolor='w',
                                    font_color='k',
                                    title='TFR of %s' % key)
                # Save figure
                fname_fig = op.join(out_path, 
                                    site_id + subject_id + "_tfr_lofr_%s" % key + '.png')
                fig.savefig(fname_fig)
                plt.close(fig)
    
    # TFR of high frequencies (> 30 Hz)
    if freq_band in ['high', 'both']:
        tfrs_hifr = dict()
        # Params
        freqs = np.arange(30, 100, 2)
        n_cycles = freqs / 4 
        time_bandwidth = 4.0
        # Run over each condition
        for condition in conditions:
            power = mne.time_frequency.tfr_multitaper(
                epochs['%s == "%s"' % (factor, condition)],
                freqs=freqs, 
                n_cycles=n_cycles, 
                use_fft=True,
                return_itc=False,
                average = True,
                decim=2, ###
                picks='grad', ###
                time_bandwidth=time_bandwidth,
                verbose=True)
            tfrs_hifr[str(condition)] = power
        # Save tfrs
        tfr_hifr_fname_out = op.join(out_path,
                        site_id + subject_id + '_tfr_hifr_%s.h5' % factor)
        mne.time_frequency.write_tfrs(tfr_hifr_fname_out, 
                                      list(tfrs_hifr.values()), 
                                      overwrite=True)
        # Plot
        if make_plot:
            for key, tfr in tfrs_hifr.items():
                # Apply baseline correction
                tfr.apply_baseline(baseline_w, 
                                   mode="percent")
                # Make topoplot
                fig = tfr.plot_topo(baseline=baseline_w,
                                    mode='mean',
                                    vmin=-1.,vmax=1.,
                                    fig_facecolor='w',
                                    font_color='k',
                                    title='TFR of %s' % key)
                # Save figure
                fname_fig = op.join(out_path, 
                                    site_id + subject_id + "_tfr_hifr_%s" % key + '.png')
                fig.savefig(fname_fig)
                plt.close(fig)    
    
    sys.stdout.close()      # close log file
    sys.stdout = stdout_obj # restore command prompt


# =============================================================================
# PARAMETERS
# =============================================================================

if subject_id in no_eeg_sbj:
    EEG = False
else:
    EEG = True
    
make_plot = True


# main()
run_time_frequency(make_plot = make_plot)
