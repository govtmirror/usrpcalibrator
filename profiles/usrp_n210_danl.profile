from __future__ import division

import numpy as np

import gnuradio.fft


#
# Test profile for USRP N210 with SBX daughterboard
#

test_type = 'danl'

# Device settings

usrp_device_str = "USRP N210 SBX"    # arbitrary name used in plot title

# Applied to raw USRP samples
scale_factor = 0.247592704746

# The following will be used to find the correct device for testing.
# A value of None means "don't filter by this value"
usrp_device_name = None
usrp_device_type = "usrp2"           # uhd_find_devices --args="type=***"
usrp_serial = "F4A6C3"               # uhd_find_devices --args="serial=***"
usrp_ip_address = '192.168.130.146'  # uhd_find_devices --args="addr=***"

usrp_clock_rate = 100e6 # 100 MHz
usrp_sample_rate = 10e6 # 2 MS/s
usrp_stream_args = 'fc32'
usrp_gain = {'PGA0': 25}
usrp_lo_offset = usrp_sample_rate / 2.0
usrp_use_integerN_tuning = False

# Displayed Average Noise Level
fft_len = 2**12       # 4096
delta_f = usrp_sample_rate / fft_len
overlap = 0.25
naverages = 3000
nskip_usrp_init = int(usrp_sample_rate)
nskip_usrp_tune = int(usrp_sample_rate / 2.0)
window = np.array(gnuradio.fft.window.flattop(fftl_len))
enbw = rbw = usrp_sample_rate * sum(window**2) / sum(window)**2
nenbw = enbw / delta_f
