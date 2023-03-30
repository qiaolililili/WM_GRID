"""
===========
05. Run ICA
===========

Open issues:
    1. why the EEG-specific ICA gives only a few components?
    
"""

import os.path as op
import os
# import sys
import matplotlib.pyplot as plt
from fpdf import FPDF

import mne
from mne.preprocessing import ICA

from config import site_id, subject_id, file_names, out_path
from config import l_freq, h_freq, sfreq, no_eeg_sbj
from config import ica_method, n_components, max_iter, random_state


def run_ica(max_iter = 100, n_components = 0.99, random_state = 1):
    
    # stdout_obj = sys.stdout                 # store original stdout 
    # sys.stdout = open(op.join(out_path,     # open log file
    #                           os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    print("Processing subject: %s" % subject_id)
    run = 0
    for file_name in file_names:
        run = run + 1
        print("  File: %s" % file_name)
        
        # Read raw data
        raw_fname_in = op.join(out_path,
                               file_name + '_artif.fif')
        raw = mne.io.read_raw_fif(
            raw_fname_in, 
            preload=True, 
            verbose='error')
        
        # Downsample copy of raw
        raw_resmpl = raw.copy().resample(sfreq)
            
        # Band-pass filter raw copy
        raw_resmpl.filter(l_freq, h_freq)
            
        # Concatenate raw copies
        if run == 1:
            raw_resmpl_all = mne.io.concatenate_raws([raw_resmpl])
        else:
            raw_resmpl_all = mne.io.concatenate_raws([raw_resmpl_all, raw_resmpl])
        
        del raw, raw_resmpl
    
    ###################
    # ICA on MEG data #
    ###################
    
    # Prepare PDF report
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    
    # Define ICA settings
    ica = ICA(method=ica_method,
              random_state=random_state,
              n_components=n_components,
              verbose=True)
    
    # Run ICA on filtered raw data
    ica.fit(raw_resmpl_all,
            picks='meg',
            verbose=True)
    
    # Plot timecourse of estimated sources
    fig = ica.plot_sources(raw_resmpl_all,
                           start=100,
                           show_scrollbars=False,
                           title='ICA_MEG')
    
    # for i in range(len(fig)):
    #     fname_fig = op.join(out_path, 
    #                         '05_rAll_ica_meg_src%d' % i)
    #     fig[i].savefig(fname_fig)
    #     plt.close(fig[i])

    fname_fig = op.join(out_path, 
                      "05_rAll_ica_meg_src.png")
    fig.savefig(fname_fig)
    plt.close(fig)
    
    # Add figure to report
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, file_names[0][0:13] + ' - MEG')
    pdf.ln(20)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Timecourse of MEG ICs', 'B', ln=1)
    pdf.image(fname_fig, 0, 45, pdf.epw)
    
    # Project mixing matrix on interpolated sensor topography
    fig = ica.plot_components(title='ICA_MEG')
    for i in range(len(fig)):
        fname_fig = op.join(out_path, 
                            '05_rAll_ica_meg_cmp%d.png' % i)
        fig[i].savefig(fname_fig)
        plt.close(fig[i])
        
        # Add figure to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_names[0][0:13] + ' - MEG')
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Topography of MEG ICs', 'B', ln=1)
        pdf.image(fname_fig, 0, 45, pdf.epw)
        
    # Save files
    ica_fname = op.join(out_path,
                        file_name[0:14] + 'ALL-ica_meg.fif')
    ica.save(ica_fname)
    
    # Save report
    pdf.output(op.join(out_path,
                       os.path.basename(__file__) + '-reportMEG.pdf'))

    ###################
    # ICA on EEG data #
    ###################
    
    if EEG:
        
        # Prepare PDF report
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        
        # Define ICA settings
        ica = ICA(method=ica_method,
                  random_state=random_state,
                  n_components=n_components,
                  verbose=True)
        
        # Run ICA on filtered raw data
        ica.fit(raw_resmpl_all,
                picks='eeg',
                verbose=True)
        
        # Plot timecourse of estimated sources
        fig = ica.plot_sources(raw_resmpl_all,
                               start=100,
                               show_scrollbars=False,
                               title='ICA_EEG') 
        fname_fig = op.join(out_path, 
                            "05_rAll_ica_eeg_src.png")
        fig.savefig(fname_fig)
        plt.close(fig)
        
        # Add figure to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_names[0][0:13] + ' - EEG')
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Timecourse of EEG ICs', 'B', ln=1)
        pdf.image(fname_fig, 0, 45, pdf.epw)
        
        # Project mixing matrix on interpolated sensor topography
        fig = ica.plot_components(title='ICA_EEG')
        for i in range(len(fig)):
            fname_fig = op.join(out_path, 
                                '05_rAll_ica_eeg_cmp%d.png' % i)
            fig[i].savefig(fname_fig)
            plt.close(fig[i])
            
            # Add figure to report
            pdf.add_page()
            pdf.set_font('helvetica', 'B', 16)
            pdf.cell(0, 10, file_names[0][0:13] + ' - EEG')
            pdf.ln(20)
            pdf.set_font('helvetica', 'B', 12)
            pdf.cell(0, 10, 'Topography of EEG ICs', 'B', ln=1)
            pdf.image(fname_fig, 0, 45, pdf.epw)
        
        # Save files
        ica_fname = op.join(out_path,
                            file_name[0:14] + 'ALL-ica_eeg.fif')
        ica.save(ica_fname)
        
        # Save report
        pdf.output(op.join(out_path,
                           os.path.basename(__file__) + '-reportEEG.pdf'))
    
    # sys.stdout.close()      # close log file
    # sys.stdout = stdout_obj # restore command prompt


# =============================================================================
# PARAMETERS
# =============================================================================

if subject_id in no_eeg_sbj:
    EEG = False
else:
    EEG = True
    

run_ica(max_iter = max_iter, 
        n_components = n_components, 
        random_state = random_state)
