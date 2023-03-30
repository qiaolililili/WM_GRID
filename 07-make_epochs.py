"""
====================
07. Make epochs
====================

Open issues:
    - baseline correction -> removed
    - apply (SSP) projections?
    - separate MEG and EEG in two different FIF files?
    - Exp.2: separate VG and replay in two different files?
    - detrand required for EEG data: when do we apply it? to epochs or to events?
    - remove peak-to-peak rejection?
    
"""

import os.path as op
import os
# import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

import mne

from config import site_id, subject_id, file_names, out_path
from config import no_eeg_sbj
from config import events_id, tmin, tmax, reject_meg_eeg, reject_meg


def run_epochs():

    # stdout_obj = sys.stdout                 # store original stdout 
    # sys.stdout = open(op.join(out_path,     # open log file
    #                            os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    # Prepare PDF report
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    
    print("Processing subject: %s" % subject_id)
    
    # Create empty lists
    raw_list = list()
    events_list = list()
    metadata_list = list()
    
    print("Processing subject: %s" % subject_id)
    run = 0
    for file_name in file_names:
        run = run + 1
        print("  File: %s" % file_name)
        
        # Read raw data
        raw_fname_in = op.join(out_path,
                               file_name + '_ica.fif')
        raw_tmp = mne.io.read_raw_fif(
            raw_fname_in, 
            preload=False, 
            verbose='error')
        
        # Read events
        events_tmp = mne.read_events(op.join(out_path,
                                             file_name + '-eve.fif'))                           
        # Read metadata
        metadata_tmp = pd.read_csv(op.join(out_path,
                                           file_name + '-meta.csv'))
        
        # Append read data to list
        raw_list.append(raw_tmp)
        events_list.append(events_tmp)
        metadata_list.append(metadata_tmp)

    # Concatenate raw instances as if they were continuous
    raw, events = mne.concatenate_raws(raw_list,
                                       events_list=events_list)
    del raw_list
    
    # Concatenate metadata tables
    metadata = pd.concat(metadata_list)
    metadata.to_csv(op.join(out_path,
                            file_name[0:14] + 'ALL-meta.csv'),
                    index=False)
    
    # Set reject criteria
    if EEG:
        reject = reject_meg_eeg
    else:
        reject = reject_meg
    
    # Select sensor types
    picks = mne.pick_types(raw.info,
                           meg = True,
                           eeg = EEG,
                           stim = True,
                           eog = EEG,
                           ecg = EEG,
                           )
    
    # Epoch raw data
    epochs = mne.Epochs(raw,
                        events, 
                        events_id,
                        tmin, tmax,
                        baseline=None,
                        proj=True,
                        picks=picks,
                        # detrend=1,
                        reject=reject,
                        reject_by_annotation=False,
                        verbose=True)
    
    # epochs.metadata = metadata
    
    del raw
    
    # Add metadata
    epochs.metadata = metadata
    
    # Drop bad epochs based on peak-to-peak magnitude
    epochs.drop_bad()
    
    # Plot percentage of rejected epochs per channel
    fig1 = epochs.plot_drop_log()
    fname_fig1 = op.join(out_path,
                        '07_rAll_epoch_drop.png')
    fig1.savefig(fname_fig1)
    plt.close()
    
    # Add figure to report
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, file_name)
    pdf.ln(20)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Percentage of rejected epochs', 'B', ln=1)
    pdf.image(fname_fig1, 0, 45, pdf.epw)

    # Plot evoked by epoch
    fig2 = epochs.plot(picks='meg',
                      title='meg',
                      n_epochs=10)
    fname_fig2 = op.join(out_path,
                        '07_rAll_epoch_evk.png')
    fig2.savefig(fname_fig2)
    plt.close(fig2)
    
    # Add figures to report
    pdf.ln(120)
    pdf.cell(0, 10, 'Epoched data', 'B', ln=1)
    pdf.image(fname_fig2, 0, 175, pdf.epw)
    
    # Count the number of epochs defined by different events
    num = {}
    for key in events_id:
        num[key] = len(epochs[key])
    df = pd.DataFrame(num,
                      index = ["Total"])
    df.to_csv(op.join(out_path,
                      file_name[0][0:13] + 'ALL_epo.csv'),  
              index=False)
    print(df)
    
    # Save epoched data
    epochs.save(op.join(out_path,
                        file_names[0][0:13] + 'ALL_epo.fif'),                           
                    overwrite=True)
    
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


run_epochs()
