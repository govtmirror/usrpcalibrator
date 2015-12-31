# TODO:
#
# 1) connect to the desired 50-ohm-terminated USRP
# 2) Use default sample rate
# 3) Use half gain
# 4)

from __future__ import division, print_function

import numpy as np

from gnuradio import fft

from utils import octaves

# CONSTS
SAMPLE_RATE = 10e6    # 10 MS/s
NBINS = 2**12         # 4096
DELTA_F = SAMPLE_RATE / NBINS
FLATTOP_WIN = np.array(fft.window.flattop(NBINS))
ENBW = SAMPLE_RATE * sum(FLATTOP_WIN**2) / sum(FLATTOP_WIN)**2
NENBW = ENBW / DELTA_F
RBW = NENBW * DELTA_F # RBW = ENBW for discrete systems
