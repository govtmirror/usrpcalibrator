# Measurement parameters

nskip = 1000000
nsamples = 1000
scale_factor = 1
nmeasurements = 72
time_between_measurements = 600 # seconds


# Device settings

usrp_device_name = "USRP N210 SBX"
usrp_serial = "EBR13WBUP"
usrp_ip_address = '192.168.130.148'
usrp_clock_rate = 100e6
usrp_sample_rate = 1e6
usrp_stream_args = 'fc32'
usrp_gain = {'PGA0': 15}
usrp_center_freq = 1.7e6
usrp_lo_offset = sample_rate / 2.0
usrp_use_integerN_tuning = False

siggen_visa_connect_str = 'TCPIP0::192.168.130.76::5025::SOCKET'
siggen_center_freq = 1.7e6
siggen_amplitude = -10
siggen_amplitude_check = False
siggen_scpi_rf_on_cmd = ':OUTPut:STATe ON'
siggen_scpi_rf_off_cmd = ':OUTPut:STATe OFF'

powermeter_visa_connect_str = 'TCPIP0::192.168.130.175::INSTR'
powermeter_scpi_measure_cmd = 'MEAS1:POW:AC? -10DBM,2,(@1)'

switchdriver_visa_connect_str = 'TCPIP0::192.168.130.173::INSTR'
switchdriver_scpi_select_meter_cmd = 'ROUTe:OPEn (@109)'
switchdriver_scpi_select_radio_cmd = 'ROUTe:CLOSe (@109)'
