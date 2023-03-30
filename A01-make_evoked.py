"""
===============
A01. Evoked data
===============

"""

import os.path as op
import os
import sys
# import numpy as np
# import pandas as pd
import matplotlib.pyplot as plt

import mne

from mpl_toolkits.axes_grid1 import ImageGrid
import cv2
import PIL

from config import site_id, subject_id, file_names, out_path
from config import no_eeg_sbj
from config import tmin, tmax, factor, conditions


def run_evoked(make_plot = True):

    stdout_obj = sys.stdout                 # store original stdout 
    sys.stdout = open(op.join(out_path,     # open log file
                               os.path.basename(__file__) + "_%s.txt" % (site_id+subject_id)),'w')
    
    print("Processing subject: %s" % subject_id)
    
    # Read epochs
    fname_epo = op.join(out_path,
                        file_names[0][0:13] + 'ALL_epo.fif')
    epochs = mne.read_epochs(fname_epo,
                             preload=True,
                             verbose=True)
    
    #############################
    # Averaging over conditions #
    #############################
    
    # Get evoked responses by condition
    evokeds = dict()
    for condition in conditions:
        evokeds[str(condition)] = epochs['%s == "%s"' % (factor, condition)].average()
        
    # Plot
    if make_plot:
        # Compare global field power (GFP) across conditions
        figs = mne.viz.plot_compare_evokeds(evokeds,
                                            legend = 'upper right')
        # Save figure
        for i in range(len(figs)):
            fname_fig = op.join(out_path, 
                                "A01_evk-%s_compare-%s.png" % (factor, i))
            figs[i].savefig(fname_fig)
            plt.close(figs[i])
        
        # Plot joint evoked response
        # Make 3-by-3 empty figure
        fig = plt.figure(figsize=(80,40))
        axes = ImageGrid(fig, 111, nrows_ncols=(len(conditions),2), axes_pad=0.1)
        k = 0
        # Plot
        for key, evoked in evokeds.items():
            figs = evoked.plot_joint(title=key,
                                     ts_args=dict(gfp=True, time_unit='s'),
                                     topomap_args=dict(time_unit='s'))
            # Copy plot in 3-by-3 figure
            for i in range(len(figs)):
                data = save_and_get_plot(figs[i])
                axes[i+k].imshow(data) 
                plt.close(figs[i])
            k = k + 2
        
        # Save figure
        fname_fig = op.join(out_path, 
                            "A01_evk-%s.png" % factor)
        fig.savefig(fname_fig)
        plt.close(fig)
    
    # Save evoked    
    evk_fname_out = op.join(out_path,
                            file_names[0][0:14] + 'ALL_evk-%s.fif' % factor)
    mne.evoked.write_evokeds(evk_fname_out, 
                             list(evokeds.values()))
    
    sys.stdout.close()      # close log file
    sys.stdout = stdout_obj # restore command prompt

def save_and_get_plot(fig):
    fig.savefig(out_path+"test.jpg")
    img = cv2.imread(out_path+"test.jpg")
    os.remove(out_path+"test.jpg")
    return PIL.Image.fromarray(img)


# =============================================================================
# RUN
# =============================================================================

if subject_id in no_eeg_sbj:
    EEG = False
else:
    EEG = True


run_evoked()