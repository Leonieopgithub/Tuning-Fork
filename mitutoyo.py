"""
Mitutoyo Height Gauge

-> Controls the Mitutoyo height gauge in the set up.

Main functions:
- Connect to the device over serial communication.
- Read the current height using measurement().

The measured height is used to track the physical probe/sample separation.
"""

import serial
from serial.tools import list_ports
from numpy import nan


class Mitutoyo:
    """
    Communication class for the Mitutoyo height gauge.
    """

    # USB identifiers of the Mitutoyo interface
    VID = 0x0FE7
    PID = 0x4001

    def __init__(self, port=None):
    

        self.ser = None

        #Automatically find the correct COM port
        if port is None:
            port = self.find_port()

        if port is None:
            raise ConnectionError(
                "Mitutoyo height gauge could not be found."
            )

        print(f"Using Mitutoyo port: {port}")

        #Open serial connection
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=2
        )

    @classmethod
    def find_port(cls):

        for device in list_ports.comports():

            if (
                device.vid == cls.VID
                and device.pid == cls.PID
            ):
                return device.device

        return None

    def answer(self):

        first_character = self.ser.read().decode(
            errors="ignore"
        )

        answer = ""

        character = ""

        while character != "\r":

            character = self.ser.read().decode(
                errors="ignore"
            )

            if character != "\r":
                answer += character

        if first_character == "9":
            print("Mitutoyo returned an error.")

        return answer

    def measurement(self):
        command = "1\r".encode()

        self.ser.write(command)

        answer = self.answer()

        if answer.startswith("1A"):

            try:
                height = float(
                    answer.replace("1A", "")
                )

            except ValueError:
                height = nan

        else:
            height = nan

        return height

    def info(self):
        """
        Request device information from the Mitutoyo.
        """

        command = "V\r".encode()

        self.ser.write(command)

        return self.answer()

    def is_connected(self):
        """
        Check whether the serial connection is currently open.
        """

        return (
            self.ser is not None
            and self.ser.is_open
        )

    def close(self):
        """
        Close the serial connection safely.
        """

        if self.ser is not None:

            if self.ser.is_open:
                self.ser.close()

            self.ser = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()