import numpy as np

from gnuradio import uhd


class RadioInterface():
    def __init__(self, profile):
        self.profile = profile
        
        ip_address = "addr=" + profile.usrp_ip_address
        stream_args = uhd.stream_args(profile.usrp_stream_args)
        self.usrp = uhd.usrp_source(device_addr=ip_address,
                                    stream_args=stream_args)

        self.usrp.set_auto_dc_offset(False)
        self.usrp.set_clock_rate(profile.usrp_clock_rate)
        self.usrp.set_samp_rate(profile.usrp_sample_rate)
        for gain_type, value in profile.usrp_gain.items():
            self.usrp.set_gain(value, gain_type)

        tune_request = uhd.tune_request(profile.usrp_center_freq,
                                        profile.usrp_lo_offset)
        if profile.usrp_use_integerN_tuning:
            tune_request.args = uhd.device_addr('mode_n=integer')

        tune_result = self.usrp.set_center_freq(tune_request)
        print(tune_result.to_pp_string())

    def acquire_samples(self):
        total_samples = self.profile.nskip + self.profile.nsamples
        acquired_samples = self.usrp.finite_acquisition(total_samples)
        data = np.array(acquired_samples[self.profile.nskip:])
        return data
