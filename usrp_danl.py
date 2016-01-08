#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import math
import os
from pprint import pprint
import sys
import time

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import scipy.io as sio

import gnuradio.fft
from gnuradio import blocks
from gnuradio import gr
from gnuradio import uhd

from instruments.radio import RadioInterface
from usrpcalibrator import (controller_cc,
                            bin_statistics_ff,
                            stitch_fft_segments_ff)
import utils


class DANLTest(gr.top_block):
    def __init__(self, freqs, usrp, profile):
        gr.top_block.__init__(self)

        self.freqs = freqs
        self.usrp = usrp
        self.profile = profile


        # TODO: determine if profile.scale_factor needs to be corrected for
        #       gain to make this step correct
        #atten = usrp.get_gain_range().stop() - usrp.get_gain()
        #self.adjusted_scale_factor = profile.scale_factor * (10**(atten/20))

        nsamples_each_cfreq = profile.fft_len * profile.naverages
        self.ctrl = controller_cc(self.usrp,
                                  freqs.center_freqs,
                                  profile.usrp_lo_offset,
                                  profile.nskip_usrp_init,
                                  profile.nskip_usrp_tune,
                                  nsamples_each_cfreq,
                                  profile.usrp_use_integerN_tuning)
        self.ctrl.set_exit_after_complete(True)

        stream_to_fft_vec = blocks.stream_to_vector(gr.sizeof_gr_complex,
                                                    profile.fft_len)
        fft_vec_to_stream = blocks.vector_to_stream(gr.sizeof_float,
                                                    profile.fft_len)

        scale = blocks.multiply_const_cc(profile.scale_factor,
                                         profile.fft_len)

        forward = True
        shift = True
        fft = gnuradio.fft.fft_vcc(profile.fft_len,
                                   forward,
                                   profile.window,
                                   shift)

        window_pwr = profile.fft_len * sum(tap*tap for tap in profile.window)

        c2mag_sq = blocks.complex_to_mag_squared(profile.fft_len)
        impedance = 50 # ohms
        power_scalar = -10.0 * math.log10(window_pwr * impedance)

        W2dBm = blocks.nlog10_ff(10.0, profile.fft_len, 30 + power_scalar)

        stats = bin_statistics_ff(profile.fft_len, profile.naverages)

        stitch_vlen = int(freqs.nsegments * profile.fft_len)
        stream_to_stitch_vec = blocks.stream_to_vector(gr.sizeof_float,
                                                       stitch_vlen)
        stitch = stitch_fft_segments_ff(profile.fft_len,
                                        freqs.nsegments,
                                        profile.overlap,
                                        freqs.nvalid_bins)

        data_vlen = int(freqs.nsegments * freqs.nvalid_bins)
        self.data_sink = blocks.vector_sink_f(data_vlen)

        self.connect(self.usrp, self.ctrl)
        self.connect(self.ctrl, stream_to_fft_vec)
        self.connect(stream_to_fft_vec, scale)
        self.connect(scale, fft)
        self.connect(fft, c2mag_sq)
        self.connect(c2mag_sq, stats)
        self.connect(stats, W2dBm)
        self.connect(W2dBm, fft_vec_to_stream)
        self.connect(fft_vec_to_stream, stream_to_stitch_vec, stitch)
        self.connect(stitch, self.data_sink)


class Frequencies(object):
    def __init__(self, octave, overlap, fft_len, delta_f, sample_rate):
        """Calculate and cache frequencies used in stitching FFT segments"""
        self.start, self.stop = octave

        # Check invariants
        assert self.start < self.stop        # low freq is lower than high freq
        assert 0 <= overlap < 1              # overlap is percentage
        assert math.log(fft_len, 2) % 2 == 0 # fft_len is power of 2

        self.span = self.stop - self.start
        self.nvalid_bins = int((fft_len - (fft_len * overlap))) // 2 * 2

        usable_bw = sample_rate * (1 - overlap)
        self.step = int(round(usable_bw / delta_f) * delta_f)

        self.center_freqs = self.cache_center_freqs()
        self.nsegments = len(self.center_freqs)

        self.bin_freqs = self.cache_bin_freqs(delta_f)

        self.bin_start = int(fft_len * (overlap / 2))
        self.bin_stop = int(fft_len - self.bin_start)
        self.max_plotted_bin = utils.find_nearest(self.bin_freqs, self.stop) + 1
        self.bin_offset = (self.bin_stop - self.bin_start) / 2

    def cache_center_freqs(self):
        min_fc = self.start + (self.step / 2)
        tmp_nsegments = math.floor(self.span / self.step)
        max_fc = min_fc + (tmp_nsegments * self.step)
        return np.arange(min_fc, max_fc + 1, self.step)

    def cache_bin_freqs(self, delta_f):
        max_fc = self.center_freqs[-1]
        max_bin_freq = max_fc + (self.step / 2)
        return np.arange(self.start, max_bin_freq, delta_f)


# Matplotlib.ticker.FuncFormatter compatible Hz to MHz with 0 decimal places.
format_mhz = lambda x, _: "{:.0f}".format(x / float(1e6))


def main(args):
    raw_profile = {}
    execfile(args.filename, {}, raw_profile)

    print("Using following profile:")
    pprint(raw_profile)
    print()

    profile = utils.DictDotAccessor(raw_profile)

    print("Initializing USRP")
    usrp = RadioInterface(profile).usrp

    freq_range = usrp.get_freq_range()
    octaves = utils.split_octaves(freq_range)

    print("-----")
    for octave in octaves:
        freqs = Frequencies(octave,
                            profile.overlap,
                            profile.fft_len,
                            profile.delta_f,
                            profile.usrp_sample_rate)

        test = DANLTest(freqs, usrp, profile)
        print("Running DANL on octave {!r}".format(octave))
        test.run()

        octave_str = '-'.join((format_mhz(freqs.start, None),
                              format_mhz(freqs.stop, None) + " MHz"))

        title_txt  = "Displayed Average Noise Level\n"
        title_txt += "For Octave {0} of {1} {2}\n"
        title_txt += "With Sample Rate {3} MS/s, ENBW {4} kHz, gain {5!r} dB"
        plt.suptitle(title_txt.format(octave_str,
                                      profile.usrp_device_str,
                                      profile.usrp_serial,
                                      format_mhz(profile.usrp_sample_rate, None),
                                      profile.enbw / 1e3,
                                      profile.usrp_gain))

        plt.subplots_adjust(top=0.88)
        plt.xlabel("Frequency (MHz)")
        plt.xlim(freqs.start-1e6, freqs.stop+1e6)
        xticks = np.linspace(freqs.start, freqs.stop, 5, endpoint=True)
        plt.xticks(xticks)

        xaxis_formatter = FuncFormatter(format_mhz)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(xaxis_formatter)

        plt.ylabel("Power (dBm)")
        plt.ylim(-140, -90)   # Experiementally good range
        plt.grid(color='0.90', linestyle='-', linewidth=1)

        data = np.array(test.data_sink.data())
        plt.plot(freqs.bin_freqs, data, zorder=99)

        # Ensure test_results dir exists
        test_results_dir = 'test_results'
        try:
            os.makedirs(test_results_dir)
        except OSError:
            if not os.path.isdir(test_results_dir):
                raise

        fig_name = '_'.join((profile.usrp_device_type,
                             profile.usrp_serial,
                             profile.test_type,
                             octave_str,
                             str(int(time.time()))))

        fig_path = os.path.join(test_results_dir, fig_name + '.png')
        print("Saving {}".format(fig_path))
        plt.savefig(fig_path)
        #plt.show()

        plt.close()

        del test


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        help="Filename of test profile",
                        type=utils.filetype)
    parser.add_argument('--no-plot',
                        help="Do not plot power meter readings against " +
                             "scaled USRP readings after test completes",
                        action='store_true')
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print("Caught Ctrl-C, exiting...", file=sys.stderr)
        sys.exit(130)
