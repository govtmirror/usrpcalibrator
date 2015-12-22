from gnuradio import eng_notation

try:
    import visa
except ImportError, visa_import_error:
    msg =  "USRPCalibrator uses PyVisa-py to control test equipment\n\n"
    msg += "$ pip install pyvisa-py"
    print(msg, sys.stderr)


class PowerMeter(object):
    def __init__(self, profile):
        rm = visa.ResourceManager('@py')
        self.profile = profile

        self.meter = rm.open_resource(profile.powermeter_visa_connect_str)

        # Set meter to remote operating mode
        self.meter.write('SYSTem:REMote')

        # TODO: handle errors
        self.idn = self.meter.query('*IDN?').strip()

        # Set units dBm
        self.meter.write('UNIT1:POWer DBM')

        # Set data format to ASCII
        self.meter.write('FORMat ASCii')

        # Set number data byte order to "normal"
        self.meter.write('FORMat:BORDer NORMal')

        # Set measurement rate to double (40 readings/second)
        self.meter.write('SENSe:MRATe DOUBle')

    def take_measurement(self):
        response = self.meter.query(self.profile.powermeter_scpi_measure_cmd)
        return eng_notation.str_to_num(response)

    def __del__(self):
        self.meter.close()
