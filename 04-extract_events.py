"""
===================
04. Extract events
===================

Extract events from the stimulus channel

Open issues:
    - metadata for exp 2 needs to be created

"""

import os.path as op
import os
# import sys
import numpy as np
import pandas as pd
from fpdf import FPDF

import mne
import matplotlib.pyplot as plt

from config import experiment_id, site_id, subject_id, data_path, file_names, out_path


def run_events(experiment_id = 1):
    
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
        run_fname = op.join(data_path,
                            file_name + '.fif')
        raw = mne.io.read_raw_fif(
            run_fname,
            allow_maxshield=True,
            verbose=True)
        
        ###############
        # Read events #
        ###############
    
        # Find response events
        response = mne.find_events(raw,
                                 stim_channel='STI101',
                                 consecutive = False,
                                 mask = 65280,
                                 mask_type = 'not_and'
                                )
        response = response[response[:,2] == 255]
        
        # Find all other events
        events = mne.find_events(raw,
                                 stim_channel='STI101',
                                 consecutive = True,
                                 min_duration=0.001001,
                                 mask = 65280,
                                 mask_type = 'not_and'
                                )
        events = events[events[:,2] != 255]
        
        # Concatenate all events
        events = np.concatenate([response,events],axis = 0)
        events = events[events[:,0].argsort(),:]
        
        # Show events
        fig = mne.viz.plot_events(events)
        fname_fig = op.join(out_path,
                            "04_r%s_events.png" % run)
        fig.savefig(fname_fig)
        plt.close(fig)
        
        # Add figure to report
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, file_name)
        pdf.ln(20)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Events', 'B', ln=1)
        pdf.image(fname_fig, 0, 45, pdf.epw)
        
        # Save event array
        fname_events = op.join(out_path,
                               file_name + '-eve.fif')                            
        mne.write_events(fname_events, events)
        
        #################
        # Read metadata #
        #################
        
        # Generate metadata table
        if experiment_id == 1:
            eve = events.copy()
            events = eve[eve[:, 2] < 81].copy()
            metadata = {}
            metadata = pd.DataFrame(metadata, index=np.arange(len(events)),
                                    columns=['Stim_trigger', 'Category',
                                             'Orientation', 'Duration',
                                             'Task_relevance', 'Trial_ID',
                                             'Response', 'Response_time(s)'])
            Category = ['face', 'object', 'letter', 'false']
            Orientation = ['Center', 'Left', 'Right']
            Duration = ['500ms', '1000ms', '1500ms']
            Relevance = ['Relevant target', 'Relevant non-target', 'Irrelevant']
            k = 0
            for i in range(eve.shape[0]):
                if eve[i, 2] < 81:
                ##find the end of each trial (trigger 97)
                    t = [t for t, j in enumerate(eve[i:i + 9, 2]) if j == 97][0]
                    metadata.loc[k]['Stim_trigger'] = eve[i,2]
                    metadata.loc[k]['Category'] = Category[int((eve[i,2]-1)//20)]
                    metadata.loc[k]['Orientation'] = Orientation[[j-100 for j in eve[i:i+t,2]
                                                                  if j in [101,102,103]][0]-1]
                    metadata.loc[k]['Duration'] = Duration[[j-150 for j in eve[i:i+t,2]
                                                            if j in [151,152,153]][0]-1]
                    metadata.loc[k]['Task_relevance'] = Relevance[[j-200 for j in eve[i:i+t,2]
                                                                   if j in [201,202,203]][0]-1]
                    metadata.loc[k]['Trial_ID'] = [j for j in eve[i:i+t,2]
                                                   if (j>110) and (j<149)][0]
                    metadata.loc[k]['Response'] = True if any(eve[i:i+t,2] == 255) else False
                    if metadata.loc[k]['Response'] == True:
                        r = [r for r,j in enumerate(eve[i:i+t,2]) if j == 255][0]
                        metadata.loc[k]['Response_time(s)'] = (eve[i+r,0] - eve[i,0])
                    # miniblock = [j for j in eve[i:i+t,2] if (j>160) and (j<201)]
                    # metadata.loc[k]['Miniblock_ID'] = miniblock[0] if miniblock != [] else np.nan
                    k += 1
            # Save metadata table as csv
            metadata.to_csv(op.join(out_path,
                                file_name + '-meta.csv'),
                                index=False)
        elif experiment_id == 2:
            eve = events.copy()
            metadata = {}
            metadata = pd.DataFrame(metadata, index=np.arange(np.sum(events[:, 2] < 51)),
                                    columns=['Trial_type', 'Stim_trigger',
                                             'Stimuli_type',
                                             'Location', 'Response',
                                             'Response_time(s)'])
            types0 = ['Filler', 'Probe']
            type1 = ['Face', 'Object', 'Blank']
            location = ['Upper Left', 'Upper Right', 'Lower Right', 'Lower Left']
            response = ['Seen', 'Unseen']
            k = 0
            for i in range(eve.shape[0]):
                if eve[i, 2] < 51:
                    metadata.loc[k]['Stim_trigger'] = eve[i, 2]
                    t = int(eve[i + 1, 2] % 10)
                    metadata.loc[k]['Trial_type'] = types0[t]
                    if eve[i, 2] == 50:
                        metadata.loc[k]['Stimuli_type'] = type1[2]
                    else:
                        metadata.loc[k]['Stimuli_type'] = type1[eve[i, 2] // 20]
                        metadata.loc[k]['Location'] = location[eve[i + 1, 2] // 10 - 6]
                    if t == 1:
                        metadata.loc[k]['Response'] = response[int(eve[i + 4, 2] - 98)]
                        metadata.loc[k]['Response_time(s)'] = (eve[i + 4, 0] - eve[i + 3, 0]) #/ sfreq
                    #             miniblock = [j for j in eve[i:i+t,2] if (j>160) and (j<201)]
                    #         metadata.loc[k]['Miniblock_ID'] = miniblock[0] if miniblock != [] else np.nan
                    k += 1

            # Save metadata table as csv
            metadata.to_csv(op.join(out_path,
                                    file_name + '-meta.csv'),
                                    index=False)
    # Save report
    pdf.output(op.join(out_path,
                       os.path.basename(__file__) + '-report.pdf'))

    # sys.stdout.close()      # close log file
    # sys.stdout = stdout_obj # restore command prompt


# =============================================================================
# RUN
# =============================================================================

run_events(experiment_id=experiment_id)
