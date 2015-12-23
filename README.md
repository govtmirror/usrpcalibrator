USRP Calibrator
===============

USRP Calibrator provides power calibration and other test utilities for USRP software defined radio using VISA-compatible test equipment.

Quick Start
-----------

1. Install GNU Radio and UHD (recommend using [PyBombs](https://github.com/pybombs/pybombs))
2. Don't forget to `./pybombs env` and then `source setup_env.sh`
3. `sudo apt-get install python-numpy python-matplotlib python-pip`
4. `sudo pip install pyvisa-py`
5. Setup equipment simliar to the following block diagram
![Block Diagram](img/block_diagram.png)
6. Copy and modify a `test_profile/*.profile` to your needs.
**WARNING:** Notice there is a 30dB attenuator after the signal generator in the block diagram. If you don't have an attenuator make sure to adjust the `siggen_amplitude` and set `siggen_amplitude_check = True` so that USRP Calibrator will refuse to burn out the front end of your USRP!
7. `./usrp_power_cal.py test_profiles/your.profile`
8. The calibration utilty provides a *voltage* scale factor suitable for usage input to, e.g., GNU Radio's `mutliply_const_cc` block.
