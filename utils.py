import argparse
import os

import numpy as np


class DictDotAccessor(object):
    """Allow test profile attributes to be accessed via dot operator"""
    def __init__(self, dct):
        self.__dict__.update(dct)


class FindNearestDict(dict):
    """Return associated value for nearest matching key.

    Raises TypeError if key is not a real number.

    Example usage;
        >>> cals = {100e6: 1.1, 200e6: 1.2, 500e6: 1.5}
        >>> nearest_cal = FindNearestDict(cals)
        >>> nearest_cal[100e6]
        1.1
        >>> nearest_cal[300e6]
        1.2
        >>> nearest_cal[400e6]
        1.5
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._check_keys(self.keys())

    @staticmethod
    def _check_keys(keys):
        if not np.all(np.isreal(keys)):
            raise TypeError("Caught non-real key")

    def __getitem__(self, item):
        """Override __getitem__ to find nearest"""
        self._check_keys(item)
        float_keys = np.array(self.keys(), dtype=float)
        nearest_idx = find_nearest(float_keys, item)
        val = self.get(float_keys[nearest_idx])
        return val

    def __setitem__(self, item, value):
        self._check_keys(item)
        dict.__setitem__(self, item, value)

    def update(self, newdict):
        self._check_keys(newdict.keys())
        dict.update(self, newdict)


def filetype(fname):
    """Return fname if file exists, else raise ArgumentTypeError"""
    if os.path.isfile(fname):
        return fname
    else:
        errmsg = "file {} does not exist".format(fname)
        raise argparse.ArgumentTypeError(errmsg)


def split_octaves(freq_range):
    fstart = freq_range.start()
    fstop = freq_range.stop()
    bands = []
    f = fstart
    while True:
        octv = f * 2
        if (octv + f) >= fstop:
            bands.append((f, fstop))
            break
        else:
            bands.append((f, octv))
            f = octv
    return bands


def dBm_to_volts(values):
    """Takes iterable of dBm and returns numpy array of volts"""
    return np.sqrt(10**(np.array(values) / 10) * 1e-3 * 50)


def volts_to_dBm(values):
    """Takes iterable of volts and returns numpy array of dBm"""
    return 10*np.log10(np.array(values)**2 / (50 * 1e-3))


def find_nearest(array, value):
    """Find the index of the closest matching value in a NumPy array."""
    # http://stackoverflow.com/a/2566508
    return np.abs(array - value).argmin()
