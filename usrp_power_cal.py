#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import os.path
from pprint import pprint
import sys
import time

import numpy as np

from gnuradio import blocks, gr, uhd

from radio import RadioInterface
from powermeter import PowerMeter
from signalgenerator import SignalGenerator
from switchdriver import SwitchDriver


def run_test(profile):
    radio = RadioInterface(profile)
    meter = PowerMeter(profile)
    siggen = SignalGenerator(profile)
    switch = SwitchDriver(profile)

    meter_measurements = []
    radio_measurements = []


    for _ in range(profile.nmeasurements):
        start_time = time.time()

        switch.select_meter()

        time.sleep(2)

        meter_measurement = self.meter.take_measurement()
        meter_measurements.append(meter_measurement)

        switch.select_radio()

        time.sleep(2)

        data = radio.acquire_samples()
        i = np.real(data)
        q = np.real(data)
        meansquared = np.mean(i**2 + q**2)
        rms = np.sqrt(meansquared)
        meanpwr = np.square(rms)/50
        meanpwr_dbm = 30 + 10*np.log10(meanpwr)

        radio_measurement = mean_pwr_dbm
        radio_measurements.append(radio_measurement)

        # Block until time for next measurement
        current_time = time.time()
        test_duration = current_time - start_time
        try:
            time.sleep(profile.time_between_measurements - test_duration)
        except IOError:
            msg = "Test took longer ({}) than time_between_measurements ({})"
            print(msg.format(test_duration, profile.time_between_measurements),
                  file=sys.stderr)
            pass

    return (meter_measurements, radio_measurements)


def dBm_to_volts(values):
    np.sqrt(10**(values / 10) * 1e-3 * 50)


def volts_to_dBm(values):
    10*np.log10(values**2 / (50 * 1e-3))


def compute_scale_factor(meter_measurements, radio_measurements):
    # Convert power meter measurements from dBm to volts
    meter_measurements_volts = dBm_to_volts(meter_measurements)
    meter_mean_voltage = np.mean(meter_measurements_volts)

    # Convert radio measurements from dBm to volts
    radio_measurements_volts = dBm_to_volts(radio_measurements)
    radio_mean_voltage = np.mean(radio_measurements_volts)

    return meter_mean_voltage / radio_mean_voltage


if __name__ == '__main__':
    def filetype(fname):
        """Return fname if file exists, or raise ArgumentTypeError"""
        if os.path.isfile(fname):
            return fname
        else:
            errmsg = "file {} does not exist".format(fname)
            raise argparse.ArgumentTypeError(errmsg)

    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                        help="Filename of test profile",
                        type=filetype)
    parser.add_argument('--plot',
                        help="Plot power meter readings against scaled USRP " +
                             "readings after test completes",
                        action='store_true')
    args = parser.parse_args()

    profile = {}
    execfile(args.filename, {}, profile)

    print("Using following profile:")
    pprint(profile)

    meter_measurements, radio_measurements = run_test()
    scale_factor = compute_scale_factor(meter_measurements, radio_measurements)
    print("\n\nComputed scale factor: {}\n\n".format(scale_factor))

    if args.plot:
        from matplotlib import pyplot as plt

        radio_measurements_volts = dBm_to_volts(radio_measurements)
        scaled_radio_measurements = radio_measurements_volts * scale_factor
        scaled_radio_measurements_dBm = volts_to_dBm(scaled_radio_measurements)

        meter_line, = plt.plot(meter_measurements,
                 profile.nmeasurements,
                 'b-',
                 label="USRP")
        usrp_line, = plt.plot(scaled_radio_measurements_dBm,
                 profile.nmeasurements,
                 'g-',
                 label="power meter")
        plt_legend = plt.legend()
        plt.show()
