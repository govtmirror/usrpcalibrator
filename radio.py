from __future__ import print_function

import sys

import numpy as np

from gnuradio import uhd


class RadioInterface():
    def __init__(self, profile):
        self.profile = profile
        
        search_criteria = uhd.device_addr_t()
        if profile.usrp_device_name is not None:
            search_criteria['name'] = profile.usrp_device_name
        if profile.usrp_device_type is not None:
            search_criteria['type'] = profile.usrp_device_type
        if profile.usrp_serial is not None:
            search_criteria['serial'] = profile.usrp_serial
        if profile.usrp_ip_address is not None:
            search_criteria['addr'] = profile.usrp_ip_address

        found_devices = uhd.find_devices(search_criteria)

        if len(found_devices) != 1:
            err =  "Found {} devices that matches USRP identification\n"
            err += "information in the test profile:\n"
            err += search_criteria.to_pp_string()
            err += "Please add/correct identifying information.\n"
            print(err, file=sys.stderr)
            for device in found_devices:
                print()
                print(device.to_pp_string())
                print()
            raise RuntimeError()
        else:
            device = found_devices[0]
            print("Found the following USRP matching test profile criteria:\n")
            print(device.to_pp_string())
            
        stream_args = uhd.stream_args(profile.usrp_stream_args)
        self.usrp = uhd.usrp_source(device_addr=device,
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
