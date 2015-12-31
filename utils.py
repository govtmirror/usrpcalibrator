class DictDotAccessor(object):
    """Allow test profile attributes to be accessed via dot operator"""
    def __init__(self, dct):
        self.__dict__.update(dct)


def octaves(freq_range):
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
