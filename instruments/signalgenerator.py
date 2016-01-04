from gnuradio import eng_notation

try:
    import visa
except ImportError, visa_import_error:
    msg =  "USRPCalibrator uses PyVisa-py to control test equipment\n\n"
    msg += "$ pip install pyvisa-py"
    print(msg, sys.stderr)


class SignalGenerator(object):
    def __init__(self, profile):
        rm = visa.ResourceManager('@py')
        self.profile = profile

        self.siggen = rm.open_resource(profile.siggen_visa_connect_str)

        # Preset siggen
        self.siggen.write(':SYSTem:PRESet')

        # TODO: handle errors
        self.idn = self.siggen.query('*IDN?', delay=5).strip()

        # Disable modulation
        self.siggen.write(':OUTPut:MODulation:STATe OFF')

        # Set frequency
        freq = eng_notation.num_to_str(profile.siggen_center_freq)
        freq_cmd = ':FREQuency ' + freq + 'HZ'
        self.siggen.write(freq_cmd)

        ampl = profile.siggen_amplitude
        if profile.siggen_amplitude_check and ampl > -15:
            err =  "\n\nThe test profile specifies a signal generator amplitude of "
            err += "{} which may damage your USRP.\nMost USRP frontends have a "
            err += "maximum input power of -15dBm.\n"
            err += "If you've taken steps to protect your frontend, add the "
            err += "following line in your test profile:\n\n"
            err += "siggen_amplitude_check = False\n"
            raise ValueError(err.format(ampl))

        pow_cmd = ':POWer ' + eng_notation.num_to_str(ampl) + 'DBM'
        self.siggen.write(pow_cmd)

    def rf_on(self):
        self.siggen.write(self.profile.siggen_scpi_rf_on_cmd)

    def rf_off(self):
        self.siggen.write(self.profile.siggen_scpi_rf_off_cmd)

    def __del__(self):
        # Return siggen to PRESet state
        self.siggen.write(':SYSTem:PRESet')
        self.rf_off()
        self.siggen.close()
