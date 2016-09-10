#!/usr/bin/env python

from __future__ import division, print_function

import argparse
from pprint import pprint
import sys
import time

from matplotlib import pyplot as plt
import numpy as np

from instruments.radio import RadioInterface
from instruments.powermeter import PowerMeter
from instruments.signalgenerator import SignalGenerator
from instruments.switchdriver import SwitchDriver
import utils


def run_test(profile):
    print("Initializing USRP")
    radio = RadioInterface(profile)
    print("Initializing power meter")
    meter = PowerMeter(profile)
    print("Initializing signal generator")
    siggen = SignalGenerator(profile)
    siggen.set_frequency(profile.siggen_center_freq)
    siggen.set_amplitude(profile.siggen_amplitude)
    print("Initializing switch")
    switch = SwitchDriver(profile)

    meter_measurements = []
    radio_measurements = []

    time.sleep(2)

    print("Signal generator RF ON")
    siggen.rf_on()

    time.sleep(2)
    print("-----\n")

    last_i = profile.nmeasurements - 1
    for i in range(profile.nmeasurements):
        start_time = time.time()

        print("Starting test {} at {}".format(i+1, int(start_time)))

        print("Switching to power meter")
        switch.select_meter()

        time.sleep(2)

        print("Taking power meter measurement... ", end="")
        sys.stdout.flush()
        meter_measurement = meter.take_measurement()
        meter_measurements.append(meter_measurement)
        print("{} dBm".format(meter_measurement))

        print("Switching to USRP")
        switch.select_radio()

        time.sleep(2)

        print("Streaming samples from USRP... ", end="")
        sys.stdout.flush()
        data = radio.acquire_samples()
        idata = np.real(data)
        qdata = np.imag(data)
        meansquared = np.mean(idata**2 + qdata**2)
        rms = np.sqrt(meansquared)
        meanpwr = np.square(rms)/50
        meanpwr_db = 30 + 10*np.log10(meanpwr)
        rx_msg = "received {} samples with mean power of {} dB"
        print(rx_msg.format(len(data), meanpwr_db))

        radio_measurement = meanpwr_db
        radio_measurements.append(radio_measurement)

        if i < last_i:
            # Block until time for next measurement
            current_time = time.time()
            actual_test_duration = current_time - start_time
            desired_test_duration = profile.time_between_measurements
            seconds_to_sleep = desired_test_duration - actual_test_duration
            print("Sleeping {} s...".format(int(seconds_to_sleep)))
            try:
                time.sleep(seconds_to_sleep)
            except IOError:
                # Test took longer than desired_test_duration
                pass

        print("-----\n")

    return (meter_measurements, radio_measurements)


def compute_scale_factor(meter_measurements, radio_measurements):
    # Convert power meter measurements from dBm to volts
    meter_measurements_volts = utils.dBm_to_volts(meter_measurements)
    meter_mean_voltage = np.mean(meter_measurements_volts)

    # Convert radio measurements from dBm to volts
    radio_measurements_volts = utils.dBm_to_volts(radio_measurements)
    radio_mean_voltage = np.mean(radio_measurements_volts)

    return meter_mean_voltage / radio_mean_voltage


def main(args):
    raw_profile = {}
    execfile(args.filename, {}, raw_profile)

    print("Using following profile:")
    pprint(raw_profile)
    print()

    profile = utils.DictDotAccessor(raw_profile)

    meter_measurements, radio_measurements = run_test(profile)

    scale_factor = compute_scale_factor(meter_measurements, radio_measurements)
    print("\nComputed scale factor: {}\n".format(scale_factor))

    if not args.no_plot:
        print("Plotting...\n")

        radio_measurements_volts = utils.dBm_to_volts(radio_measurements)
        scaled_radio_measurements = radio_measurements_volts * scale_factor
        scaled_radio_measurements_dBm = utils.volts_to_dBm(scaled_radio_measurements)

        title_txt  = "Power Measurements Over Time\n"
        title_txt += "With {} Scale Factor Applied to {} {}\n"
        title_txt += "And Gain Setting of {!r} dB"
        plt.suptitle(title_txt.format(scale_factor,
                                      profile.usrp_device_str,
                                      profile.usrp_serial,
                                      profile.usrp_gain))

        usrp_line, = plt.plot(range(1, profile.nmeasurements+1),
                               scaled_radio_measurements_dBm,
                               'b-',
                               label="USRP",
                              zorder=99)
        meter_line, = plt.plot(range(1, profile.nmeasurements+1),
                               meter_measurements,
                               'g--',
                               label="power meter",
                               zorder=99)
        plt_legend = plt.legend(loc='best')
        plt.grid(color='.90', linestyle='-', linewidth=1)

        ymin = np.min((meter_measurements, scaled_radio_measurements_dBm))
        ymax = np.max((meter_measurements, scaled_radio_measurements_dBm))
        yticks = np.linspace(np.floor(ymin), np.ceil(ymax), 11)
        plt.yticks(yticks)
        plt.ylabel("Power (dBm)")

        npoints = np.min((profile.nmeasurements, 10))
        xticks = [int(x) for x in np.linspace(1, profile.nmeasurements,
                                              npoints,
                                              endpoint=True)]
        plt.xticks(xticks)
        xlabel_txt = "Number of measurements at {} second intervals"
        plt.xlabel(xlabel_txt.format(profile.time_between_measurements))

        plt.subplots_adjust(top=0.88)
        plt.show()

    print("Calibration completed successfully, exiting...")


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
