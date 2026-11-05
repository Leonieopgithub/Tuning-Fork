"""
Stanford Research Systems SR830 Lock-in Amplifier

Controls the SR830 lock-in amplifier used in the tuning fork setup.

- Automatically find the lock-in amplifier using its serial number.
- Connect to the device over serial communication.
- Read the measured amplitude.
- Read the measured phase.
- Check whether the device is connected.

Role in the experiment:
The lock-in amplifier measures the amplitude and phase of the tuning fork
response relative to the reference signal. These values are used for
resonance detection, PLL control and calibration measurements.
"""

import serial
from serial.tools import list_ports
from numpy import nan

class SR830:

    def __init__(self, serial_number):
        #find serial number & port
        self.serial_number = serial_number
        self.ser = None

        port = self.find_port()

        if port is None:
            raise ConnectionError(
                f"SR830 with serial number {serial_number} could not be found."
            )

        print(f"Using SR830 port: {port}")

        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            timeout=20
        )

        #zowel oude als nieuwe methodes (compatibility tussen oude/nieuwe code)
    def readAmplitude(self):
        return self.read_amplitude()

    def readPhase(self):
        return self.read_phase()
    

    def find_port(self):

        for device in list_ports.comports():

            if device.serial_number == self.serial_number:
                return device.device

        return None

    def _write(self, command):

        send_data = command + "\n\r"

        self.ser.write(send_data.encode())

    def _write_read(self, command):

        self._write(command)

        character = self.ser.read().decode(errors="ignore")
        feedback = character

        while character != "\r":

            character = self.ser.read().decode(errors="ignore")
            feedback += character
            
        return feedback.strip()

    def read_amplitude(self):

        feedback = self._write_read("OUTP? 3")
        try:
            amplitude = float(feedback)
        except ValueError:
            amplitude = nan
        return amplitude

    def setAmplitude(self, voltage):
        self.set_sine_out_amplitude(voltage)

    def set_sine_out_amplitude(self, voltage):
        command = "SLVL " + str(round(voltage, 6))
        self._write(command)

    def read_phase(self):

        feedback = self._write_read("OUTP? 4")
        try:
            phase = float(feedback)

        except ValueError:
            phase = nan

        return phase

    def is_connected(self):

        return (self.ser is not None and self.ser.is_open)

    def close(self):

        if self.ser is not None:

            if self.ser.is_open:
                self.ser.close()

            self.ser = None
    