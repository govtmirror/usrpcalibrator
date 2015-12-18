from gnuradio import eng_notation

try:
    import visa
except ImportError, visa_import_error:
    msg =  "USRPCalibrator uses PyVisa-py to control test equipment\n\n"
    msg += "$ pip install pyvisa-py"
    print(msg, sys.stderr)


class SwitchDriver(object):
    def __init__(self, profile):
        rm = visa.ResourceManager('@py')
        self.profile = profile

        self.switch = rm.open_resource(profile.powerswitch_visa_connect_str)

    def select_radio(self):
        self.switch.write(self.profile.switchdriver_scpi_select_radio_cmd)

    def select_meter(self):
        self.switch.write(self.profile.switchdriver_scpi_select_meter_cmd)

    def __del__(self):
        self.switch.close()
