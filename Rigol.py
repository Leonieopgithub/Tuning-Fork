"""
Rigol Function Generator

Controls the Rigol function generator used to drive the tuning fork.

- Connect to the Rigol function generator.
- Set the waveform of channel 1 and channel 2.
- Set the drive frequency.
- Set the output state on or off.
- Close the connection safely.

Role in the experiment:
The Rigol generates the sinusoidal excitation signal for the tuning fork.
Channel 1 is used for the normal mode and channel 2 for the shear mode.
The drive frequency is adjusted during resonance searches and PLL operation.
"""

from rigol_dg1022 import RigolDG

class Rigol:

    def __init__(self):
        self.device = None

        print("Connecting to Rigol...")
        self.device = RigolDG()
        print("Rigol connected.")

    def set_frequency(self, channel, frequency):
        self.device.set_frequency(
            channel=channel,
            frequency=frequency
        )
    def set_amplitude(self, channel, amplitude):
        self.device.set_amplitude(
            channel=channel,
            amplitude=amplitude
        )
        
    def get_frequency(self, channel):
        return self.device.get_frequency(
            channel=channel
        )

    def set_waveform(self, channel, waveform="SIN"):
        self.device.set_waveform(
            channel,
            waveform
        )

    def set_output(self, channel, state):
        self.device.set_output(
            channel=channel,
            state=state)

    def get_output_state(self, channel):
        return self.device.get_output_state(
            channel=channel)

    def get_amplitude(self, channel):
            return self.device.get_amplitude(
                channel=channel
            )

    def get_waveform(self, channel):
        return self.device.get_waveform(
            channel=channel
        )

    def is_connected(self):
        return self.device is not None

    def close(self):

        if self.device is not None:

            try:
                self.device.set_output(1, False)
                self.device.set_output(2, False)

            except Exception:
                pass

            self.device.close()
            self.device = None