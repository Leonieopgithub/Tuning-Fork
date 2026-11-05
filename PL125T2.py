"""
Voltcraft PL-125-T2USB Temperature Logger

Controls the two-channel Voltcraft PL-125-T2USB temperature logger.

Main functions:
- Automatically find the device by USB VID/PID.
- Connect to the virtual COM port.
- Request a live temperature reading.
- Read temperature channels T1 and T2.
- Detect whether a sensor is connected.
- Check connection status.
- Close the serial connection safely.

Role in the experiment:
The temperature logger measures the sample temperature during tuning fork
experiments. Temperature is monitored because fluid viscosity depends strongly
on temperature.
"""

import struct
import serial
from serial.tools import list_ports
import time

class PL125T2:

    VID = 0x10C4
    PID = 0xEA60

    BAUDRATE = 9600
    TIMEOUT = 5

    NO_SENSOR = 5000.0

    CMD_START = bytearray(
        [244, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    )

    CMD_STOP = bytearray(
        [245, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    )

    def __init__(self, port=None):

        self.ser = None

        if port is None:
            port = self.find_port()

        if port is None:
            raise ConnectionError(
                "PL-125-T2USB temperature logger could not be found."
            )

        print(f"Using PL-125-T2USB port: {port}")

        self.ser = serial.Serial(
            port=port,
            baudrate=self.BAUDRATE,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=self.TIMEOUT
        )

    def find_port(self):

        for device in list_ports.comports():

            if (
                device.vid == self.VID
                and device.pid == self.PID
            ):
                return device.device

        return None
    def read_temperature(self):

        print("Resetting input buffer...")
        self.ser.reset_input_buffer()

        print("Sending command...")
        self.ser.write(self.CMD_START)

        print("Waiting for response...")

        data = bytearray()
        start_time = time.monotonic()

        while time.monotonic() - start_time < 5:

            waiting = self.ser.in_waiting

            if waiting > 0:
                data.extend(
                    self.ser.read(waiting)
                )

            # We need at least bytes 0-21
            if len(data) >= 22:
                break

            time.sleep(0.05)

        print("Response received:", data)
        print("Number of bytes:", len(data))

        if len(data) < 22:
            print("Not enough data received.")
            return None, None

        return self._parse_response(data)

    def _parse_response(self, data):

        try:
            t1 = struct.unpack_from(
                "<h",
                data,
                18
            )[0] / 10.0

            t2 = struct.unpack_from(
                "<h",
                data,
                20
            )[0] / 10.0

            if abs(t1) >= self.NO_SENSOR:
                t1 = None

            if abs(t2) >= self.NO_SENSOR:
                t2 = None

            return t1, t2

        except struct.error:
            return None, None

    def is_connected(self):

        return (
            self.ser is not None
            and self.ser.is_open
        )

    def close(self):

        if self.ser is not None:

            if self.ser.is_open:

                try:
                    self.ser.write(
                        self.CMD_STOP
                    )
                except Exception:
                    pass

                self.ser.close()

            self.ser = None


        