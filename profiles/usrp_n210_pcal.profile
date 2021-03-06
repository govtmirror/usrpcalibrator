from __future__ import division

#
# Test profile for USRP N210 with SBX daughterboard
#

test_type = 'pcal'

# Device settings

usrp_device_str = "USRP N210 SBX"    # arbitrary name used in plot title

# Applied to raw USRP samples
scale_factor = 1

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
usrp_center_freq = 1700e6 # 1700 MHz
usrp_lo_offset = usrp_sample_rate / 2.0
usrp_use_integerN_tuning = False

inline_attenuator = 30 # dB of attenatuation inline after siggen
siggen_visa_connect_str = 'TCPIP0::192.168.130.76::5025::INSTR'
siggen_center_freq = 1700e6 # 1700 MHz
siggen_amplitude = -10
siggen_scpi_rf_on_cmd = ':OUTPut:STATe ON'
siggen_scpi_rf_off_cmd = ':OUTPut:STATe OFF'

powermeter_visa_connect_str = 'TCPIP0::192.168.130.175::INSTR'
powermeter_scpi_measure_cmd = 'MEAS1:POW:AC? -10DBM,2,(@1)'

switchdriver_visa_connect_str = 'TCPIP0::192.168.130.173::INSTR'
switchdriver_scpi_select_meter_cmd = 'ROUTe:OPEn (@109)'
switchdriver_scpi_select_radio_cmd = 'ROUTe:CLOSe (@109)'

# Test-specific measurement parameters

# Power Cal
nskip = 1000000                    # Number of samples to drop initially
nsamples = 1000                    # Number of samples to use for power cal
nmeasurements = 72                 # Number of measurements to perform
time_between_measurements = 600    # Seconds between start of measurements
