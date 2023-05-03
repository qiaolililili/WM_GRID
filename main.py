import os.path as op
import os
# import sys
import numpy as np
import pandas as pd
import mne

data_path='/data/pt_02783/memory_grid/rawdir/mg99a'

raw_fname_in=op.join(data_path,'mg99a01'+'.fif')

raw = mne.io.read_raw_fif(
    raw_fname_in,
    allow_maxshield=True, 
    preload=False, 
    verborse= True)

