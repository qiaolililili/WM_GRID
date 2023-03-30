# -*- coding: utf-8 -*-
"""
===========
Config file
===========

Configurate the parameters of the study.
"""

import os
import os.path as op


# =============================================================================
# SESSION-SPECIFIC SETTINGS
# =============================================================================
experiment_id = 1
subject_id = '035'

# Set user-specific params
user = os.getlogin()  #TODO: @Ling the command "os.environ['USER']" doesn0t work on Win. Can you try this other one?

if user in ['oscfe', 'ferranto']:               # Oscar
    data_path = r'Z:\Real_data\Exp2\SA110\meg\20201126_b51f\201126'
    # data_path = r'Z:\Real_data\Exp1\SA110\meg\20201118_b4eb\201118'
    cal_path = r'Z:\MaxFilter'
    site_id = 'SA'
elif user in ['root']:                                # Ling
    data_path = r'/Users/ling/Documents/work/Cogitate/data/SB035_V1'
    cal_path = r'/Users/ling/Documents/work/Cogitate/data_analysis/Maxfilter'
    site_id = 'SB'

# Set filename based on experiment number
if experiment_id == 1:
    file_exts = ['%s_MEEG_V1_DurR1',
                 '%s_MEEG_V1_DurR2',
                 '%s_MEEG_V1_DurR3',
                 '%s_MEEG_V1_DurR4',
                 '%s_MEEG_V1_DurR5']
    file_names = [f % (site_id+subject_id) for f in file_exts]
elif experiment_id == 2:
    file_exts = ['%s_MEEG_V2_VGR1',
                 '%s_MEEG_V2_VGR2',
                 '%s_MEEG_V2_VGR3',
                 '%s_MEEG_V2_VGR4']#,
                 # '%s_MEEG_V2_ReplayR1',
                 # '%s_MEEG_V2_ReplayR2']
    file_names = [f % (site_id+subject_id) for f in file_exts]


# =============================================================================
# GENERAL SETTINGS
# =============================================================================

# Set out_path folder or create it if it doesn't exist
out_path = op.join(data_path, "out_path")
if not op.exists(out_path):
    os.mkdir(out_path)
        
# Remove participant without EEG from EEG analysis (WIP, only works for exp1 atm)
if site_id == 'SA':
    if experiment_id == 1:
        no_eeg_sbj = ['101', '102', '103', '104']
    elif experiment_id == 2:
        no_eeg_sbj = ['104', '106']
elif site_id == 'SB':
    if experiment_id == 1:
        no_eeg_sbj = []
    elif experiment_id == 2:
        no_eeg_sbj = []


# =============================================================================
# MAXWELL FILTERING SETTINGS
# =============================================================================

# Set filtering method
method='sss'
if method == 'tsss':
    st_duration = 10
else:
    st_duration = None


# =============================================================================
# FILTERING AND DOWNSAMPLING SETTINGS
# =============================================================================

# Filter and resampling params
l_freq = 1
h_freq = 40
sfreq = 200


# =============================================================================
# EPOCHING SETTINGS
# =============================================================================

# Set timewindow
tmin = -0.75
tmax = 2.25

# Epoch rejection criteria
reject_meg_eeg = dict(grad=4000e-13,    # T / m (gradiometers)
                      mag=4e-12,        # T (magnetometers)
                      eeg=200e-6       # V (EEG channels)
                      )
reject_meg = dict(grad=4000e-13,    # T / m (gradiometers)
                  mag=4e-12         # T (magnetometers)
                  )

# Set epoching event ids
if experiment_id == 1:
    events_id = {}
    types = ['face','object','letter','false']
    for j,t in enumerate(types):
        for i in range(1,21):
            events_id[t+str(i)] = i + j * 20
elif experiment_id == 2:
    events_id = {}
    events_id['blank'] = 50
    types = ['face','object']
    for j,t in enumerate(types):
        for i in range(1,11):
            events_id[t] = i + j * 20


# =============================================================================
# ICA SETTINGS
# =============================================================================

ica_method = 'fastica'
n_components = 0.99
max_iter = 800
random_state = 1688


# =============================================================================
#  FACTOR AND CONDITIONS OF INTEREST
# =============================================================================

if experiment_id == 1:
    # factor = 'Category'
    # conditions = ['face', 'object', 'letter', 'false']
    
    factor = 'Duration'
    conditions = ['500ms', '1000ms', '1500ms']
    
    # factor = 'Relevance'
    # conditions = ['Relevant target','Relevant non-target','Irrelevant']
elif experiment_id == 2:
    factor = 'Category'
    conditions = ['face', 'object']
    
    
# =============================================================================
# TIME-FREQUENCY REPRESENTATION SETTINGS
# =============================================================================

baseline_w = [-0.5, -0.25]     #only for plotting
freq_band = 'both' #can be 'low', 'high' or 'both'

