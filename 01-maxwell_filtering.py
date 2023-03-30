"""
===================================
01. Maxwell filter using MNE-python
===================================

The data are Maxwell filtered using tSSS/SSS.

It is critical to mark bad channels before Maxwell filtering.

Open issues:
    1. SSS or tSSS? -> Consult Alex G.?
    
"""  # noqa: E501

import os.path as op
import os
# import sys
import numpy as np
import pandas as pd
import seaborn as sns
from fpdf import FPDF  #TODO: ask to add this package to the HPC

import mne
from mne.preprocessing import find_bad_channels_maxwell
import matplotlib.pyplot as plt

from config import site_id, subject_id, data_path, file_names, out_path
from config import cal_path, method, st_duration


def run_maxwell_filter(method = 'sss'):
    # stdout_obj = sys.stdout                 # store original stdout 
    # sys.stdout = open(op.join(out_path,     # open log file
    # os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    # Load the fine calibration file (which encodes site-specific information 
    # about sensor orientation and calibration) as well as a crosstalk 
    # compensation file (which reduces interference between Elekta’s co-located
    # magnetometer and paired gradiometer sensor units)
    crosstalk_file = op.join(cal_path, "ct_sparse_" + site_id + ".fif")
    fine_cal_file = op.join(cal_path, "sss_cal_" + site_id + ".dat")
    
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
        raw_fname_in = op.join(data_path, file_name + '.fif')
        raw = mne.io.read_raw_fif(
            raw_fname_in,
            allow_maxshield=True,
            preload=False,
            verbose=True)
        
        # Detect bad channels
        raw.info['bads'] = []
        raw_check = raw.copy()
        auto_noisy_chs, auto_flat_chs, auto_scores = find_bad_channels_maxwell(
            raw_check, 
            cross_talk=crosstalk_file, 
            calibration=fine_cal_file,
            return_scores=True,
            verbose=True)
        raw.info['bads'].extend(auto_noisy_chs + auto_flat_chs)
        
        # Append bad channels to the list 
        df = df.append({'run': run,
                        'noisy': auto_noisy_chs, 
                        'flat': auto_flat_chs},
                        ignore_index=True)        
        
        # Visualize the scoring used to classify channels as noisy or flat
        ch_type = 'grad'
        fig = viz_badch_scores(auto_scores, ch_type)
        fname_fig = op.join(out_path,
                            "01_r%s_badchannels_%sscore.png" % (run,ch_type))
        fig.savefig(fname_fig)
        plt.close()
        ch_type = 'mag'
        fig = viz_badch_scores(auto_scores, ch_type)
        fname_fig = op.join(out_path,
                            "01_r%s_badchannels_%sscore.png" % (run,ch_type))
        fig.savefig(fname_fig)
        plt.close()
        
        # Fix Elekta magnetometer coil types
        raw.fix_mag_coil_types()
        
        # Perform tSSS/SSS and Maxwell filtering
        raw_sss = mne.preprocessing.maxwell_filter(
            raw,
            cross_talk=crosstalk_file,
            calibration=fine_cal_file,
            st_duration=st_duration,
            #coord_frame="meg", #only for empy room, comment it if using HPI
            verbose=True)
        
        # Show original and filtered signals
        fig = raw.copy().pick(['meg']).plot(duration=5,
                                            start=100,
                                            butterfly=True)        
        fname_fig = op.join(out_path,
                            '01_r%s_plotraw.png' % run)
        fig.savefig(fname_fig)
        plt.close()
        fig = raw_sss.copy().pick(['meg']).plot(duration=5,
                                                start=100,
                                                butterfly=True)
        fname_fig = op.join(out_path,
                            '01_r%s_plotraw%s.png' % (run,method))
        fig.savefig(fname_fig)
        plt.close()
        
        # Show original and filtered power
        fig1 = raw.plot_psd(picks = ['meg'],fmin = 1,fmax = 100)
        fname_fig1 = op.join(out_path,
                            '01_r%s_plot_psd_raw100.png' % run)
        fig1.savefig(fname_fig1)
        plt.close()
        fig2 = raw_sss.plot_psd(picks = ['meg'],fmin = 1,fmax = 100)
        fname_fig2 = op.join(out_path,
                            '01_r%s_plot_psd_raw100%s.png' % (run,method))
        fig2.savefig(fname_fig2)
        plt.close()
        
        # Add figures to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_name)
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Power Spectrum of Raw MEG Data', 'B', ln=1)
        pdf.image(fname_fig1, 0, 45, pdf.epw)
        pdf.ln(120)
        pdf.cell(0, 10, 'Power Spectrum of Filtered MEG Data', 'B', ln=1)
        pdf.image(fname_fig2, 0, 175, pdf.epw)
        
        # Save filtered data
        fname_out = op.join(out_path,
                            file_name + '_' + method + '.fif')
        raw_sss.save(fname_out, overwrite=True)
        
    # Save bad channel list
    df.to_csv(op.join(out_path,
                      '01_rAll_meg_badch_list.csv'),
              index=False)
    
    # Save report
    pdf.output(op.join(out_path,
                       os.path.basename(__file__) + '-report.pdf'))
    
    # sys.stdout.close()      # close log file
    # sys.stdout = stdout_obj # restore command prompt


def viz_badch_scores(auto_scores, ch_type):
    fig, ax = plt.subplots(1, 4, figsize=(12, 8))
    fig.suptitle(f'Automated noisy/flat channel detection: {ch_type}',
                  fontsize=16, fontweight='bold')
    
    #### Noisy channels ####
    ch_subset = auto_scores['ch_types'] == ch_type
    ch_names = auto_scores['ch_names'][ch_subset]
    scores = auto_scores['scores_noisy'][ch_subset]
    limits = auto_scores['limits_noisy'][ch_subset]
    bins = auto_scores['bins']  #the windows that were evaluated
    
    # Label each segment by its start and stop time (3 digits / 1 ms precision)
    bin_labels = [f'{start:3.3f} – {stop:3.3f}' 
                  for start, stop in bins]
    
    # Store  data in DataFrame
    data_to_plot = pd.DataFrame(data=scores,
                                columns=pd.Index(bin_labels, name='Time (s)'),
                                index=pd.Index(ch_names, name='Channel'))
    
    # First, plot the raw scores
    sns.heatmap(data=data_to_plot, 
                cmap='Reds', 
                cbar=False,
                # cbar_kws=dict(label='Score'),
                ax=ax[0])
    [ax[0].axvline(x, ls='dashed', lw=0.25, dashes=(25, 15), color='gray')
        for x in range(1, len(bins))]
    ax[0].set_title('Noisy: All Scores', fontweight='bold')

    # Second, highlight segments that exceeded the 'noisy' limit
    sns.heatmap(data=data_to_plot,
                vmin=np.nanmin(limits),
                cmap='Reds', 
                cbar=True, 
                # cbar_kws=dict(label='Score'), 
                ax=ax[1])
    [ax[1].axvline(x, ls='dashed', lw=0.25, dashes=(25, 15), color='gray')
        for x in range(1, len(bins))]
    ax[1].set_title('Noisy: Scores > Limit', fontweight='bold')
    
    #### Flat channels ####
    ch_subset = auto_scores['ch_types'] == ch_type
    ch_names = auto_scores['ch_names'][ch_subset]
    scores = auto_scores['scores_flat'][ch_subset]
    limits = auto_scores['limits_flat'][ch_subset]
    bins = auto_scores['bins']  #the windows that were evaluated
    
    # Label each segment by its start and stop time (3 digits / 1 ms precision)
    bin_labels = [f'{start:3.3f} – {stop:3.3f}' 
                  for start, stop in bins]
    
    # Store  data in DataFrame
    data_to_plot = pd.DataFrame(data=scores,
                                columns=pd.Index(bin_labels, name='Time (s)'),
                                index=pd.Index(ch_names, name='Channel'))
    
    # First, plot the raw scores
    sns.heatmap(data=data_to_plot, 
                cmap='Reds', 
                cbar=False,
                # cbar_kws=dict(label='Score'),
                ax=ax[2])
    [ax[2].axvline(x, ls='dashed', lw=0.25, dashes=(25, 15), color='gray')
        for x in range(1, len(bins))]
    ax[2].set_title('Flat: All Scores', fontweight='bold')

    # Second, highlight segments that exceeded the 'noisy' limit
    sns.heatmap(data=data_to_plot,
                vmax=np.nanmax(limits),
                cmap='Reds', 
                cbar=True,
                # cbar_kws=dict(label='Score'), 
                ax=ax[3])
    [ax[3].axvline(x, ls='dashed', lw=0.25, dashes=(25, 15), color='gray')
        for x in range(1, len(bins))]
    ax[3].set_title('Flat: Scores > Limit', fontweight='bold')
    
    # Fit figure title to not overlap with the subplots
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    return fig


# =============================================================================
# RUN
# =============================================================================

run_maxwell_filter(method=method)
