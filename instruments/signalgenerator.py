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

    def rf_on(self):
        self.siggen.write(self.profile.siggen_scpi_rf_on_cmd)

    def rf_off(self):
        self.siggen.write(self.profile.siggen_scpi_rf_off_cmd)

    def set_amplitude(self, ampl):
        if ampl - self.profile.inline_attenuator > -15:
            err  = "Requested amplitude > -15 dBm.\n"
            raise ValueError(err.format(ampl))
        cmd = ':POWer ' + eng_notation.num_to_str(ampl) + 'DBM'
        self.siggen.write(cmd)

    def set_frequency(self, freq):
        cmd = ':FREQuency ' + eng_notation.num_to_str(freq) + 'HZ'
        self.siggen.write(cmd)

    def __del__(self):
        # Return siggen to PRESet state
        self.siggen.write(':SYSTem:PRESet')
        self.rf_off()
        self.siggen.close()
