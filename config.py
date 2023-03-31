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
subject_id = 'mg99a'

# Set user-specific params

data_path = r'/data/pt_o2783/memory_grid'
cal_path = r'/Users/ling/Documents/work/Cogitate/data_analysis/Maxfilter'
site_id = 'SB'

# Set filename based on experiment number

file_exts = ['%s_MEEG_V2_VGR1',
             '%s_MEEG_V2_VGR2',
             '%s_MEEG_V2_VGR3',
             '%s_MEEG_V2_VGR4']#,

file_names = [f % (site_id+subject_id) for f in file_exts]


# =============================================================================
# GENERAL SETTINGS
# =============================================================================

# Set out_path folder or create it if it doesn't exist
out_path = op.join(data_path, "out_path")
if not op.exists(out_path):
    os.mkdir(out_path)
        

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
reject_meg = dict(grad=4000e-13,    # T / m (gradiometers)
                  mag=4e-12         # T (magnetometers)
                  )

# Set epoching event ids

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


factor = 'Category'
conditions = ['face', 'object']
    
    
# =============================================================================
# TIME-FREQUENCY REPRESENTATION SETTINGS
# =============================================================================

baseline_w = [-0.5, -0.25]     #only for plotting
freq_band = 'both' #can be 'low', 'high' or 'both'

