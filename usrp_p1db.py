#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import os
from pprint import pprint
import sys
import time

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from instruments.radio import RadioInterface
from instruments.signalgenerator import SignalGenerator

import utils


# Matplotlib.ticker.FuncFormatter compatible Hz to MHz with 0 decimal places.
format_mhz = lambda x, _: "{:.0f}".format(x / float(1e6))


# Ensure test_results dir exists
test_results_dir = 'test_results'
try:
    os.makedirs(test_results_dir)
except OSError:
    if not os.path.isdir(test_results_dir):
        raise


def run_test(profile):
    """Runs a P1dB test over USRP frequency range in 100 MHz intervals.

    Steps from -60 to -15 dBm in 1 dB increments. If P1dB not detected by -15
    dBm, -15 dBm is appended to the P1dB array.

    Returns (frequencies, P1dB) tuple of 2 arrays suitable for plotting.
    """
    print("Initializing USRP")
    radio = RadioInterface(profile)
    print("Initializing signal generator")
    siggen = SignalGenerator(profile)

    radio_measurements = []

    time.sleep(2)
    print("-----\n")

    freq_range_min = radio.usrp.get_freq_range().start()
    freq_range_max = radio.usrp.get_freq_range().stop()

    # Run a test every 100 MHz starting 50 MHz above radio's min freq
    frequencies = np.arange(freq_range_min+50e6, freq_range_max, 200e6)
    # At each fc, step from -60 to at most -16 in 1 dB steps
    amplitudes = np.arange(-60, -15)

    p1db = []

    for fc in frequencies:
        print("Setting USRP to {} MHz".format(fc / 1e6))
        radio.set_frequency(fc)
        print("Setting siggen to {} MHz".format(fc / 1e6))
        siggen.set_frequency(fc)

        print("Signal generator RF ON")
        siggen.rf_on()
        time.sleep(2)

        max_ampl = -15
        for i, ampl in enumerate(amplitudes):
            adjusted_ampl = ampl + profile.inline_attenuator
            siggen_str = "Setting siggen amplitude to {} dBm ({} dBm before attenuation)"
            print(siggen_str.format(ampl, adjusted_ampl))
            siggen.set_amplitude(adjusted_ampl)
            time.sleep(2)

            print("Streaming samples from USRP... ", end="")
            sys.stdout.flush()
            data = np.array(radio.acquire_samples())
            scaled_data = data * profile.scale_factor
            idata = np.real(scaled_data)
            qdata = np.imag(scaled_data)
            meansquared = np.mean(idata**2 + qdata**2)
            rms = np.sqrt(meansquared)
            meanpwr = np.square(rms)/50
            meanpwr_dbm = 30 + 10*np.log10(meanpwr)
            rx_msg = "received {} samples with mean power of {} dBm"
            print(rx_msg.format(len(data), meanpwr_dbm))

            radio_measurement = meanpwr_dbm
            radio_measurements.append(radio_measurement)

            if i == 9:
                # After 10 measurements, determine a line of best fit.
                # x-axis is the power meter measurements, y-axis is radio
                assert len(amplitudes[:i+1]) == len(radio_measurements)
                fit = np.polyfit(amplitudes[:i+1], radio_measurements, 1)
                trendline_fn = np.poly1d(fit)
            elif i > 9:
                expected = trendline_fn(ampl)
                print("Expected measurement value: {} dBm".format(expected))
                actual = radio_measurement
                print("Actual measurement value: {} dBm".format(actual))
                error = abs(expected - actual)
                print("Error: {} dBm".format(error))
                if error >= 1:
                    # Reached P1dB
                    max_ampl = ampl
                    print("Detected P1dB {} dBm at {} MHz".format(ampl, fc/1e6))
                    break

            assert ampl + 1 < -15

        fc_str = format_mhz(fc, None) + " MHz"

        plt.plot(amplitudes[:i+1],
                 [trendline_fn(a) for a in amplitudes[:i+1]],
                 'k--',
                 label="Expected measurement")
        plt.plot(amplitudes[:i+1], amplitudes[:i+1], label="Power at USRP RF-in")
        plt.plot(amplitudes[:i+1], radio_measurements, label="Actual measurement")
        plt.legend(loc='best')
        plt.xlabel("Power at USRP RF-in (dBm)")
        plt.ylabel("USRP measurement (dBm)")

        plt.grid(color='.90', linestyle='-', linewidth=1)

        title_txt  = "1 dB Compression Test at {}\n"
        title_txt += "With {} Scale Factor Applied to {} {}\n"
        title_txt += "And Gain Setting of {!r} dB"
        plt.suptitle(title_txt.format(fc_str,
                                      profile.scale_factor,
                                      profile.usrp_device_str,
                                      profile.usrp_serial,
                                      profile.usrp_gain))
        plt.subplots_adjust(top=0.88)

        fig_name = '_'.join((profile.usrp_device_type,
                             profile.usrp_serial,
                             profile.test_type,
                             fc_str,
                             str(int(time.time()))))

        fig_path = os.path.join(test_results_dir, fig_name + '.png')
        print("Saving {}".format(fig_path))
        plt.savefig(fig_path)
        plt.close()

        print("Clearing radio measurements")
        radio_measurements = []

        p1db.append(max_ampl)
        print("Signal Generator RF OFF")
        siggen.rf_off()
        time.sleep(2)

    # sanity check
    assert len(frequencies) == len(p1db)

    return (frequencies, p1db)


def main(args):
    raw_profile = {}
    execfile(args.filename, {}, raw_profile)

    print("Using following profile:")
    pprint(raw_profile)
    print()

    profile = utils.DictDotAccessor(raw_profile)

    frequencies, p1db = run_test(profile)

    print("Plotting...\n")

    title_txt  = "1 dB Compression Test\n"
    title_txt += "With {} Scale Factor Applied to {} {}\n"
    title_txt += "And Gain Setting of {!r} dB"
    plt.suptitle(title_txt.format(profile.scale_factor,
                                  profile.usrp_device_str,
                                  profile.usrp_serial,
                                  profile.usrp_gain))

    plt.subplots_adjust(top=0.88)

    p1db_line, = plt.plot(frequencies,
                          p1db,
                          label="P1dB",
                          zorder=99)
    plt_legend = plt.legend(loc='best')
    plt.grid(color='.90', linestyle='-', linewidth=1)

    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Power at USRP RF-in (dBm)")

    xaxis_formatter = FuncFormatter(format_mhz)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(xaxis_formatter)

    fig_name = '_'.join((profile.usrp_device_type,
                         profile.usrp_serial,
                         profile.test_type,
                         str(int(time.time()))))

    fig_path = os.path.join(test_results_dir, fig_name + '.png')
    print("Saving {}".format(fig_path))
    plt.savefig(fig_path)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        help="Filename of test profile",
                        type=utils.filetype)
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print("Caught Ctrl-C, exiting...", file=sys.stderr)
        sys.exit(130)
