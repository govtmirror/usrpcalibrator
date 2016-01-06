from __future__ import division

import numpy as np

import gnuradio.fft


#
# Test profile for USRP B200
#

test_type = 'danl'

# Device settings

usrp_device_str = "USRP B200"        # Arbitrary name used in plot title

# Applied to raw USRP samples
scale_factor = 0.00280277061854 # 50 dB gain 5 min test

# The following will be used to find the correct device for testing.
# A value of None means "don't filter by this value"
usrp_device_name = None
usrp_device_type = "b200"            # uhd_find_devices --args="type=***"
usrp_serial = "30A9FFA"              # uhd_find_devices --args="serial=***"
usrp_ip_address = None               # uhd_find_devices --args="addr=***"

usrp_clock_rate = 40e6 # 40 MHz
usrp_sample_rate = 10e6 # 10 MS/s
usrp_stream_args = 'fc32'
usrp_gain = {'PGA': 50}
usrp_center_freq = 1700e6 # 1700 MHz
usrp_lo_offset = usrp_sample_rate / 2.0
usrp_use_integerN_tuning = False

# Test-specific measurement parameters

# Displayed Average Noise Level
fft_len = 2**12       # 4096
delta_f = usrp_sample_rate / fft_len
overlap = 0.25
naverages = 3000
nskip_usrp_init = int(usrp_sample_rate)
nskip_usrp_tune = int(usrp_sample_rate / 2.0)
window = np.array(gnuradio.fft.window.flattop(fft_len))
enbw = rbw = usrp_sample_rate * sum(window**2) / sum(window)**2
nenbw = enbw / delta_f
