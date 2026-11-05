from PIE625 import PIE625
from pipython import GCSDevice

device = PIE625()

print(
    "Connected:",
    device.is_connected()
)

voltage = device.get_voltage()

print(
    "Current voltage:",
    voltage
)

device.close()