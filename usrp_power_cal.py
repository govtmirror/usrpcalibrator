#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import os.path
from pprint import pprint
import sys
import time

from matplotlib import pyplot as plt
import numpy as np

from gnuradio import blocks, gr, uhd

from radio import RadioInterface
from powermeter import PowerMeter
from signalgenerator import SignalGenerator
from switchdriver import SwitchDriver


class DictDotAccessor(object):
    """Allow test profile attributes to be accessed via dot operator"""
    def __init__(self, dct):
        self.__dict__.update(dct)


def run_test(profile):
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

        time.sleep(1)

        print("Taking power meter measurement... ", end="")
        sys.stdout.flush()
        meter_measurement = meter.take_measurement()
        meter_measurements.append(meter_measurement)
        print("{} dBm".format(meter_measurement))
        
        print("Switching to USRP")
        switch.select_radio()

        time.sleep(1)

        print("Streaming samples from USRP... ", end="")
        sys.stdout.flush()
        data = radio.acquire_samples()
        idata = np.real(data)
        qdata = np.imag(data)
        meansquared = np.mean(idata**2 + qdata**2)
        rms = np.sqrt(meansquared)
        meanpwr = np.square(rms)/50
        meanpwr_db = 30 + 10*np.log10(meanpwr)
        print("received {} samples with mean power of {} dB".format(len(data), meanpwr_db))
        
        radio_measurement = meanpwr_db
        radio_measurements.append(radio_measurement)

        if i < last_i:
            # Block until time for next measurement
            current_time = time.time()
            test_duration = current_time - start_time
            seconds_to_sleep = profile.time_between_measurements - test_duration
            print("Sleeping {} s until next test...".format(int(seconds_to_sleep)))
            try:
                time.sleep(seconds_to_sleep)
            except IOError:
                msg = "Test took longer ({}) than time_between_measurements ({})"
                print(msg.format(test_duration, profile.time_between_measurements),
                      file=sys.stderr)
                pass

        print("-----\n")
            
    return (meter_measurements, radio_measurements)


def dBm_to_volts(values):
    """Takes iterable of dBm and returns numpy array of volts"""
    return np.sqrt(10**(np.array(values) / 10) * 1e-3 * 50)

    
def volts_to_dBm(values):
    """Takes iterable of volts and returns numpy array of dBm"""
    return 10*np.log10(np.array(values)**2 / (50 * 1e-3))

    
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
    parser.add_argument('--no-plot',
                        help="Do not plot power meter readings against " +
                             "scaled USRP readings after test completes",
                        action='store_true')
    args = parser.parse_args()

    raw_profile = {}
    execfile(args.filename, {}, raw_profile)

    print("Using following profile:")
    pprint(raw_profile)
    print()
    
    profile = DictDotAccessor(raw_profile)
    
    meter_measurements, radio_measurements = run_test(profile)
    scale_factor = compute_scale_factor(meter_measurements, radio_measurements)
    print("\nComputed scale factor: {}\n".format(scale_factor))

    if not args.no_plot:
        print("Plotting...\n")

        radio_measurements_volts = dBm_to_volts(radio_measurements)
        scaled_radio_measurements = radio_measurements_volts * scale_factor
        scaled_radio_measurements_dBm = volts_to_dBm(scaled_radio_measurements)

        title_txt  = "Power Measurements Over Time\n"
        title_txt += "With {} Scale Factor Applied to {} {}"
        plt.suptitle(title_txt.format(scale_factor, profile.usrp_device_str, profile.usrp_serial))
        
        usrp_line, = plt.plot(range(1, profile.nmeasurements+1),
                               scaled_radio_measurements_dBm,
                               'b-',
                               label="USRP")
        meter_line, = plt.plot(range(1, profile.nmeasurements+1),
                              meter_measurements,
                              'g--',
                              label="power meter")
        plt_legend = plt.legend(loc='best')
        plt.grid(color='.90', linestyle='-', linewidth=1)
        
        ymin = np.min((meter_measurements, scaled_radio_measurements_dBm))
        ymax = np.max((meter_measurements, scaled_radio_measurements_dBm))
        yticks = np.linspace(np.floor(ymin), np.ceil(ymax), 11)
        plt.yticks(yticks)
        plt.ylabel("Power (dBm)")
        
        npoints = np.min((profile.nmeasurements, 10))
        xticks = [int(x) for x in
                  np.linspace(1, profile.nmeasurements, npoints, endpoint=True)]
        plt.xticks(xticks)
        xlabel_txt = "Number of measurements at {} second intervals"
        plt.xlabel(xlabel_txt.format(profile.time_between_measurements))
        
        plt.show()

    print("Calibration completed successfully, exiting...")
        
