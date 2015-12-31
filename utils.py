import numpy as np


class DictDotAccessor(object):
    """Allow test profile attributes to be accessed via dot operator"""
    def __init__(self, dct):
        self.__dict__.update(dct)


def split_octaves(freq_range):
   fstart = freq_range.start()
   fstop = freq_range.stop()
   bands = []
   f = fstart
   while True:
     oct = f * 2
     if (oct + f) >= fstop:
       bands.append((f, fstop))
       break
     else:
       bands.append((f, oct))
       f = oct
   return bands


def dBm_to_volts(values):
    """Takes iterable of dBm and returns numpy array of volts"""
    return np.sqrt(10**(np.array(values) / 10) * 1e-3 * 50)


def volts_to_dBm(values):
    """Takes iterable of volts and returns numpy array of dBm"""
    return 10*np.log10(np.array(values)**2 / (50 * 1e-3))


def find_nearest(array, value):
    """Find the index of the closest matching value in a NumPyarray."""
    #http://stackoverflow.com/a/2566508
    return np.abs(array - value).argmin()
