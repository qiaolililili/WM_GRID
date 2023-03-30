"""
===========================
03. Artifact annotation
===========================

Detect and note ocular and muscle artifacts

Open issues:
    1. Eye-link annot?
    -> Ling will develop it

"""  # noqa: E501

import os.path as op
import os
# import sys
from fpdf import FPDF

import mne
from mne.preprocessing import annotate_muscle_zscore
import matplotlib.pyplot as plt

from config import site_id, subject_id, file_names, out_path
from config import no_eeg_sbj


def artifact_annotation():  
    # stdout_obj = sys.stdout                 # store original stdout 
    # sys.stdout = open(op.join(out_path,     # open log file
                              # os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    # Prepare PDF report
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    
    print("Processing subject: %s" % subject_id)
    run = 0
    for file_name in file_names:
        run = run + 1
        print("  File: %s" % file_name)
        
        # Read raw data
        raw_fname_in = op.join(out_path,
                               file_name + '_intpl.fif')
        raw = mne.io.read_raw_fif(
            raw_fname_in, 
            preload=True, 
            verbose='error')
        
        # Create empty annotations list
        annot_artifact = mne.Annotations(onset=[], 
                                         duration=[],
                                         description=[])
        
        ###########################
        # Detect ocular artifacts #
        ###########################
        
        # Resetting the EOG channel
        eog_ch = raw.copy().pick_types(meg=False, eeg=False, eog=True)
        if len(eog_ch.ch_names) < 2:
            raw.set_channel_types({'BIO002':'eog'})
            raw.rename_channels({'BIO002': 'EOG002'})
        
        if EEG:
            # Resetting the EOG channel  #TODO: test on Birmingham's data
            eog_ch = raw.copy().pick_types(meg=False, eeg=False, eog=True)
            if len(eog_ch.ch_names) < 2:
                raw.set_channel_types({'BIO002':'eog'})
                raw.rename_channels({'BIO002': 'EOG002'})
            
            # Find EOG events
            eog_events = mne.preprocessing.find_eog_events(raw)
            onsets = (eog_events[:, 0] - raw.first_samp) / raw.info['sfreq'] - 0.25
            durations = [0.5] * len(eog_events)
            descriptions = ['Blink'] * len(eog_events)
            
            # Annotate events
            annot_blink = mne.Annotations(
                onsets, 
                durations,
                descriptions)
                # orig_time=raw.info['meas_date'])
            
            # Add blinks to annotations list
            annot_artifact = annot_artifact + annot_blink
            
            # Plot blink with EEG data
            eeg_picks = mne.pick_types(raw.info, 
                                      meg=False,
                                      eeg=True,
                                      eog=True)
            fig = raw.plot(events=eog_events,
                          start=800,
                          order=eeg_picks)
            fname_fig = op.join(out_path,
                               "03_r%s_artifact_blink.png" % run)
            fig.savefig(fname_fig)
            plt.close()
        
        ###########################
        # Detect muscle artifacts #
        ###########################
        
        # Notch filter
        raw_muscle = raw.copy().notch_filter([50, 100])
        
        # The threshold is data dependent, check the optimal threshold by plotting
        # ``scores_muscle``.
        threshold_muscle = 5  # z-score
        
        # Choose one channel type, if there are axial gradiometers and magnetometers,
        # select magnetometers as they are more sensitive to muscle activity.
        annot_muscle, scores_muscle = annotate_muscle_zscore(
            raw_muscle, 
            ch_type="mag", 
            threshold=threshold_muscle, 
            min_length_good=0.2,
            filter_freq=[110, 140])
        
        # Add muscle artifacts to annotations list
        annot_artifact = annot_artifact + annot_muscle
        
        # Plot muscle z-scores across recording
        fig1, ax = plt.subplots()
        ax.plot(raw.times, scores_muscle)
        ax.axhline(y=threshold_muscle, color='r')
        ax.set(xlabel='time, (s)', ylabel='zscore', title='Muscle activity')
        fname_fig1 = op.join(out_path,
                            "03_r%s_artifact_muscle.png" % run)
        fig1.savefig(fname_fig1)
        plt.close()
        
        # Add figure to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_name)
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Muscle artifact power', 'B', ln=1)
        pdf.image(fname_fig1, 0, 45, pdf.epw)
        
        ###########################
        
        # Set annotations
        raw.set_annotations(annot_artifact)
        
        # View raw with annotations
        channel_picks = mne.pick_types(raw.info, 
                                       meg='mag', eog=True)
        fig2 = raw.plot(duration=50,
                       start=100,
                       order=channel_picks)
        fname_fig2 = op.join(out_path,
                            "03_r%s_artifact_annot.png" % run)
        fig2.savefig(fname_fig2)
        plt.close()
        
        # Add figures to report
        pdf.ln(120)
        pdf.cell(0, 10, 'Data and annotations', 'B', ln=1)
        pdf.image(fname_fig2, 0, 175, pdf.epw)
        
        # Save data with annotated artifacts
        fname_out = op.join(out_path,
                            file_name + '_artif.fif')                            
        raw.save(fname_out, overwrite=True)
    
    # Save report
    pdf.output(op.join(out_path,
                       os.path.basename(__file__) + '-report.pdf'))
    
    # sys.stdout.close()      # close log file
    # sys.stdout = stdout_obj # restore command prompt


# =============================================================================
# RUN
# =============================================================================

if subject_id in no_eeg_sbj:
    EEG = False
else:
    EEG = True


artifact_annotation()
