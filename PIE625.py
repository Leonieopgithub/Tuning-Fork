"""
PI E-625 Piezo Controller

Controls the PI E-625 piezo controller used in the tuning fork setup.

Main functions:
- Connect to the PI E-625 controller over USB.
- Set an absolute piezo voltage.
- Apply a relative voltage change.
- Read the current piezo voltage.
- Check whether the controller is connected.
- Close the connection safely.

Role in the experiment:
The PI E-625 controls the vertical piezo position used to change the
probe/sample separation during calibration and approach measurements.
"""

from pipython import GCSDevice

class PIE625:

    def __init__(self, serial_number="121019479"):

        self.serial_number = serial_number
        self.device = None
        self.target = "A"

        print("Connecting to PI E-625...")

        self.device = GCSDevice("E-625")
        self.device.ConnectUSB(serial_number)

        print("PI E-625 connected.")

    def set_absolute_voltage(self, voltage):

        self.device.SVO(
            self.target,
            False
        )

        self.device.SVA(
            self.target,
            voltage
        )

    def set_relative_voltage(self, voltage):

        self.device.SVO(
            self.target,
            False
        )

        self.device.SVR(
            self.target,
            voltage
        )

    def get_voltage(self):

        voltage = self.device.qVOL(
            self.target
        )

        return voltage[self.target]

    def is_connected(self):

        return self.device is not None

    def close(self):

        if self.device is not None:

            self.device._cleanup()

            self.device = None