"""
===============
06. Apply ICA
===============

This relies on the ICAs computed in 05-run_ica.py

Open issues:
    1. Should we automitaze EOG- and ECG-related ICs detection?
    -> up to Ling and Oscar. Do auto and cross-check afterwards
    2. Add plots?
    -> no
    3. How many comps per type should we remove?
    -> 1-2 each (if any). 2-5 in total
    4. Apply on concatenated data? -> Yes
    
"""

import os.path as op
import os
# import sys
import matplotlib.pyplot as plt
from fpdf import FPDF

import mne
from mne.preprocessing import read_ica
# from mne.preprocessing import create_eog_epochs, create_ecg_epochs

from config import site_id, subject_id, file_names, out_path
from config import no_eeg_sbj


def apply_ica(meg_ica_eog = [], meg_ica_ecg = [],
              eeg_ica_eog = [], eeg_ica_ecg = []):

    # stdout_obj = sys.stdout                 # store original stdout 
    # sys.stdout = open(op.join(out_path,     # open log file
    #                           os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    # Prepare PDF report
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    
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
        
        # Show original signal
        if EEG:
            chs = ['MEG0311', 'MEG0121', 'MEG1211', 'MEG1411', 'EEG001','EEG002', 'EOG001','EOG002']
        else:
            chs = ['MEG0311', 'MEG0121', 'MEG1211', 'MEG1411', 'EOG001','EOG002']
        chan_idxs = [raw.ch_names.index(ch) for ch in chs]
        fig1 = raw.plot(order=chan_idxs,
                       duration=50,
                       start=100)        
        fname_fig1 = op.join(out_path,
                            '06_r%s_ica_raw0.png' % run)
        fig1.savefig(fname_fig1)
        plt.close()
        
        # Add figure to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_name)
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Timecourse of input data', 'B', ln=1)
        pdf.image(fname_fig1, 0, 45, pdf.epw)
        
        ###################
        # ICA on MEG data #
        ###################
        
        if [meg_ica_eog + meg_ica_ecg] != []:
            
            # Restore ICA solution from fif file
            ica_meg_fname = op.join(out_path,
                                file_name[0:14] + 'ALL-ica_meg.fif')
            ica_meg = read_ica(ica_meg_fname)
            
            # Select EOG- and ECG-related components for exclusion
            ica_meg.exclude.extend(meg_ica_eog + meg_ica_ecg)
            
            # # Plot excluded ICs
            # if meg_ica_eog != []:
            #     # Display component properties
            #     fig = ica.plot_properties(raw, 
            #                               picks=meg_ica_eog)
            #     for i in range(len(fig)):
            #         fname_fig = op.join(out_path, 
            #                             "04_r%s_ica_meg_eog%d.png" % (run,i))
            #         fig[i].savefig(fname_fig)
            #         plt.close(fig[i])
            # if meg_ica_ecg != []:
            #     # Display component properties
            #     fig = ica.plot_properties(raw, 
            #                               picks=meg_ica_ecg)
            #     for i in range(len(fig)):
            #         fname_fig = op.join(out_path, 
            #                             "04_r%s_ica_meg_ecg%d.png" % (run,i))
            #         fig[i].savefig(fname_fig)
            #         plt.close(fig[i])
            
        ###################
        # ICA on EEG data #
        ###################
        
        if eeg_ica_eog + eeg_ica_ecg != []:
            
            # Restore ICA solution from fif file
            ica_eeg_fname = op.join(out_path,
                                file_name[0:14] + 'ALL-ica_eeg.fif')
            ica_eeg = read_ica(ica_eeg_fname)
            
            # Select EOG- and ECG-related components for exclusion
            ica_eeg.exclude.extend(eeg_ica_eog + eeg_ica_ecg)
            
            # # Plot excluded ICs
            # if eeg_ica_eog != []:
            #     # Display component properties
            #     fig = ica.plot_properties(raw, 
            #                               picks=eeg_ica_eog)
            #     for i in range(len(fig)):
            #         fname_fig = op.join(out_path, 
            #                             "04_r%s_ica_eeg_eog%d.png" % (run,i))
            #         fig[i].savefig(fname_fig)
            #         plt.close(fig[i])
            # if eeg_ica_ecg != []:
            #     # Display component properties
            #     fig = ica.plot_properties(raw, 
            #                               picks=eeg_ica_ecg)
            #     for i in range(len(fig)):
            #         fname_fig = op.join(out_path, 
            #                             "04_r%s_ica_eeg_ecg%d.png" % (run,i))
            #         fig[i].savefig(fname_fig)
            #         plt.close(fig[i])
        
        ###################
        
        # Remove selected components from the signal  #TODO: @Ling why "apply" is done in two different steps?
        raw_ica = raw.copy()
        ica_meg.apply(raw_ica)
        ica_eeg.apply(raw_ica)
        
        # Show cleaned signal
        fig_ica = raw_ica.plot(order=chan_idxs,
                               duration=50,
                               start=100)        
        fname_fig_ica = op.join(out_path,
                                '06_r%s_ica_rawICA.png' % run)
        fig_ica.savefig(fname_fig_ica)
        plt.close()
        
        # Add figures to report
        pdf.ln(120)
        pdf.cell(0, 10, 'Timecourse of output data', 'B', ln=1)
        pdf.image(fname_fig_ica, 0, 175, pdf.epw)
        
        # Save cleaned raw data
        fname_out = op.join(out_path,
                            file_name + '_ica.fif')
        raw_ica.save(fname_out,overwrite=True)
    
    # Save report  #TODO: add note about removed ICs
    pdf.output(op.join(out_path,
                       os.path.basename(__file__) + '-report.pdf'))
    
    # sys.stdout.close()      # close log file
    # sys.stdout = stdout_obj # restore command prompt


# =============================================================================
# PARAMETERS
# =============================================================================

if subject_id in no_eeg_sbj:
    EEG = False
else:
    EEG = True
    
# Manually selected ICs  #TODO: move and read these info from a separate table file
#MEG
meg_ica_eog = [0]
meg_ica_ecg = [18]
#EEG
eeg_ica_eog = [0]
eeg_ica_ecg = [6]


apply_ica(meg_ica_eog = meg_ica_eog,
          meg_ica_ecg = meg_ica_ecg,
          eeg_ica_eog = eeg_ica_eog,
          eeg_ica_ecg = eeg_ica_ecg)
