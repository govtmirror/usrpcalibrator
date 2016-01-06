from __future__ import division, print_function

import argparse
import math
from pprint import pprint
import sys

import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio

from usrpcalibrator import (controller_cc,
                            bin_statistics_ff,
                            stitch_fft_segments_ff)

from instruments.radio import RadioInterface
from instruments.siggen import SignalGenerator
from instruments.powermeter import PowerMeter
from instruments.switchdriver import SwitchDriver

import utils


def run_test(profile):
    """Runs a P1dB test over USRP frequency range in 100 MHz intervals.

    Steps from -60 to -15 dBm in 1 dB increments. If P1dB not detected by -15
    dBm, -15 dBm is appended to the P1dB array.

    Returns (frequencies, P1dB) tuple of 2 arrays suitable for plotting.
    """
    print("Initializing USRP")
    radio = RadioInterface(profile)
    print("Initializing power meter")
    meter = PowerMeter(profile)
    print("Initializing signal generator")
    siggen = SignalGenerator(profile)
    print("Initializing switch")
    switch = SwitchDriver(profile)

    meter_measurements = []
    radio_measurements = []

    time.sleep(2)
    print("-----\n")

    freq_range_min = radio.usrp.get_freq_range.start()
    freq_range_max = radio.usrp.get_freq_range.stop()

    # Run a test every 100 MHz starting 50 MHz above radio's min freq
    frequencies = np.arange(freq_range_min+50e6, freq_range_max, 100e6)
    # At each fc, step from -60 to at most -16 in 1 dB steps
    amplitudes = np.arange(-60, -15)

    # Adjust for any inline attenuation
    amplitudes = amplitudes + profile.inline_attenuator

    p1db = []

    for fc in frequencies:
        radio.set_frequency(fc)
        meter.set_frequency(fc)
        siggen.set_frequency(fc)

        siggen.rf_on()
        time.sleep(2)

        max_ampl = -15
        for i, ampl in enumerate(amplitudes):
            switch.select_meter()
            time.sleep(2)

            siggen.set_amplitude(ampl)
            time.sleep(2)

            print("Taking power meter measurement... ", end="")
            sys.stdout.flush()
            meter_measurement = meter.take_measurement()
            meter_measurements.append(meter_measurement)
            print("{} dBm".format(meter_measurement))

            switch.select_radio()
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
                fit = np.polyfit(meter_measurements, radio_measurements, 1)
                trendline_fn = np.poly1d(fit)
            elif i > 9:
                if trendline_fn(meter_measurement) - radio_measurement >= 1:
                    # Reached P1dB
                    max_ampl = meter_measurement
                    break

            # Should not trigger this unless profile.inline_attenuator incorrect
            assert meter_measurement + 1 < -15

        p1db.append(max_ampl)
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

    title_txt  = "1 dB Compression Test for {} {}"
    plt.suptitle(title_txt.format(profile.usrp_device_str,
                                  profile.usrp_serial))

    p1db_line, = plt.plot(frequencies,
                          p1db,
                          label="P1dB",
                          zorder=99)
    plt_legend = plt.legend(loc='best')
    plt.grid(color='.90', linestyle='-', linewidth=1)

    plt.xlabel("Frequency")
    plt.ylabel("Power (dBm)")

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
