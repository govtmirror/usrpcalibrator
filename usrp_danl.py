#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import math

import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio

import gnuradio.fft
import gnuradio.blocks
from gnuradio import gr
from gnuradio import uhd

from usrpcalibrator import (controller_cc,
                            bin_statistics_ff,
                            stitch_fft_segments_ff)

import utils


# CONSTS
SCALE_FACTOR = 1      # As computed by usrp_power_cal (match gain, srate)
GAIN = 15
SAMPLE_RATE = 10e6    # 10 MS/s
FFT_LEN = 2**12       # 4096
DELTA_F = SAMPLE_RATE / FFT_LEN
FLATTOP_WIN = np.array(gnuradio.fft.window.flattop(FFT_LEN))
ENBW = SAMPLE_RATE * sum(FLATTOP_WIN**2) / sum(FLATTOP_WIN)**2
NENBW = ENBW / DELTA_F
RBW = NENBW * DELTA_F # RBW == ENBW for discrete systems
OVERLAP = .1          # Oversample to allow dropping outer 10% of bins
NAVERAGES = 100       # Number of DFTs to average at each center frequency
LO_OFFSET = SAMPLE_RATE / 2
NSKIP_USRP_INIT = int(SAMPLE_RATE)  # Samples to drop after USRP init (skip_initial)
NSKIP_USRP_TUNE = int(SAMPLE_RATE)  # Samples to drop after each tune (tune_delay)


class DANLTest(gr.top_block):
    def __init__(self, freqs, usrp):
        gr.top_block.__init__(self)

        self.freqs = freqs
        self.usrp = usrp

        nsamples_each_cfreq = FFT_LEN * NAVERAGES
        self.ctrl = controller_cc(self.usrp,
                                  freqs.center_freqs,
                                  LO_OFFSET,
                                  NSKIP_USRP_INIT,
                                  NSKIP_USRP_TUNE,
                                  nsamples_each_cfreq)

        self.ctrl.set_exit_after_complete()

        stream_to_fft_vec = gnuradio.blocks.stream_to_vector(gr.sizeof_gr_complex,
                                                             FFT_LEN)
        fft_vec_to_stream = gnuradio.blocks.vector_to_stream(gr.sizeof_float,
                                                             FFT_LEN)

        scale = gnuradio.blocks.multiply_const_cc(SCALE_FACTOR, FFT_LEN)

        forward = True
        shift = True
        fft = gnuradio.fft.fft_vcc(FFT_LEN, forward, FLATTOP_WIN, shift)

        c2mag_sq = gnuradio.blocks.complex_to_mag_squared(FFT_LEN)

        impedance = 50 # ohms
        power = gnuradio.blocks.multiply_const_ff(impedance, FFT_LEN)

        W2dBm = gnuradio.blocks.nlog10_ff(10.0, FFT_LEN, 30)

        stats = bin_statistics_ff(FFT_LEN, NAVERAGES)

        stitch_vlen = int(freqs.nsegments * FFT_LEN)
        stream_to_stitch_vec = gnuradio.blocks.stream_to_vector(gr.sizeof_float,
                                                                stitch_vlen)
        stitch = stitch_fft_segments_ff(FFT_LEN,
                                        freqs.nsegments,
                                        OVERLAP,
                                        freqs.nvalid_bins)

        data_vlen = int(freqs.nsegments * freqs.nvalid_bins)
        self.data_sink = gnuradio.blocks.vector_sink_f(data_vlen)

        self.connect(self.usrp, self.ctrl)
        self.connect(self.ctrl, stream_to_fft_vec)
        self.connect(stream_to_fft_vec, scale)
        self.connect(scale, fft)
        self.connect(fft, c2mag_sq)
        self.connect(c2mag_sq, stats)
        self.connect(stats, power)
        self.connect(power, W2dBm)
        self.connect(W2dBm, fft_vec_to_stream)
        self.connect(fft_vec_to_stream, stream_to_stitch_vec, stitch)
        self.connect(stitch, self.data_sink)



class Frequencies(object):
    def __init__(self, octave):
        """Takes a (start, stop) tuple and produces EVERYTHING you need to know"""
        self.start, self.stop = octave
        self.span = self.stop - self.start
        self.nvalid_bins = int((FFT_LEN - (FFT_LEN * OVERLAP))) // 2 * 2

        usable_bw = SAMPLE_RATE * (1 - OVERLAP)
        self.step = int(round(usable_bw / DELTA_F) * DELTA_F)

        self.center_freqs = self.cache_center_freqs()
        self.nsegments = len(self.center_freqs)

        self.bin_freqs = self.cache_bin_freqs()

        self.bin_start = int(FFT_LEN * (OVERLAP / 2))
        self.bin_stop = int(FFT_LEN - self.bin_start)
        self.max_plotted_bin = utils.find_nearest(self.bin_freqs, self.stop) + 1
        self.bin_offset = (self.bin_stop - self.bin_start) / 2

    def cache_center_freqs(self):
        min_fc = self.start + (self.step / 2)
        tmp_nsegments = math.floor(self.span / self.step)
        max_fc = min_fc + (tmp_nsegments * self.step)
        return np.arange(min_fc, max_fc + 1, self.step)

    def cache_bin_freqs(self):
        max_fc = self.center_freqs[-1]
        max_bin_freq = max_fc + (self.step / 2)
        return np.arange(self.start, max_bin_freq, DELTA_F)


if __name__ == '__main__':
    def valid_serial(serial):
        """Return device_addr_t if serial valid, else raise ArgumentTypeError"""
        serial_str = "serial={}".format(serial)
        found_devices = uhd.find_devices(uhd.device_addr_t(serial_str))
        if found_devices:
            return found_devices[0]
        else:
            errmsg = "No devices found matching serial {}".format(serial)
            raise argparse.ArgumentTypeError(errmsg)

    parser = argparse.ArgumentParser()
    parser.add_argument('serial',
                        help="Serial number of a connected USRP",
                        type=valid_serial)
    args = parser.parse_args()

    stream_args = uhd.stream_args('fc32')
    usrp = uhd.usrp_source(args.serial, stream_args)
    usrp.set_samp_rate(SAMPLE_RATE)
    usrp_gain = usrp.get_gain()

    freq_range = usrp.get_freq_range()
    octaves = utils.split_octaves(freq_range)

    for octave in octaves:
        freqs = Frequencies(octave)
        test = DANLTest(freqs, usrp)
        print("Running DANL on octave {!r}".format(octave))
        test.run()

        data = np.array(test.data_sink.data())
        plt.plot(freqs.bin_freqs, data)
        plt.show()

        del test
