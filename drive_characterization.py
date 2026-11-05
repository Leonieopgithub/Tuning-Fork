import time
import csv
import os
import numpy as np
import matplotlib.pyplot as plt

from SR830 import SR830
from Rigol import Rigol


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

START_FREQUENCY = 796.0
STOP_FREQUENCY = 803.0
STEP = 0.05

DRIVE_AMPLITUDE = 0.035

WAIT_TIME = 0.5
NOISE_SAMPLES = 30

CSV_FILE = "drive_characterization_results2.csv"
print("CSV path:", os.path.abspath(CSV_FILE))
PLOT_FOLDER = "drive_characterization_plots"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def find_zero_crossing(frequencies, phases):
    for i in range(len(phases) - 1):

        if phases[i] == 0:
            return frequencies[i]

        if phases[i] * phases[i + 1] < 0:

            f1 = frequencies[i]
            f2 = frequencies[i + 1]

            p1 = phases[i]
            p2 = phases[i + 1]

            return f1 + (0 - p1) * (f2 - f1) / (p2 - p1)

    return None


def interpolate_crossing(f1, a1, f2, a2, target):
    if a2 == a1:
        return f1

    return f1 + (target - a1) * (f2 - f1) / (a2 - a1)


def calculate_q(frequencies, amplitudes, f0, background=0.0):

    corrected = np.array(amplitudes) - background
    corrected = np.maximum(corrected, 0)

    peak_index = np.argmax(corrected)
    peak_amplitude = corrected[peak_index]

    target = peak_amplitude / np.sqrt(2)

    f_left = None
    f_right = None

    # Left -3 dB crossing
    for i in range(peak_index - 1, -1, -1):

        if corrected[i] <= target <= corrected[i + 1]:

            f_left = interpolate_crossing(
                frequencies[i],
                corrected[i],
                frequencies[i + 1],
                corrected[i + 1],
                target
            )

            break

    # Right -3 dB crossing
    for i in range(peak_index, len(corrected) - 1):

        if corrected[i] >= target >= corrected[i + 1]:

            f_right = interpolate_crossing(
                frequencies[i],
                corrected[i],
                frequencies[i + 1],
                corrected[i + 1],
                target
            )

            break

    if f_left is None or f_right is None:
        return None, None, None, None

    bandwidth = f_right - f_left
    q_factor = f0 / bandwidth

    return f_left, f_right, bandwidth, q_factor


def save_to_csv(result):

    file_exists = os.path.exists(CSV_FILE)

    fieldnames = [
        "drive_amplitude_V",
        "f0_phase_Hz",
        "peak_frequency_Hz",
        "peak_amplitude_V",
        "noise_mean_V",
        "noise_std_V",
        "snr",
        "f_left_3db_Hz",
        "f_right_3db_Hz",
        "bandwidth_Hz",
        "Q_factor",
        "Apeak_per_Vdrive"
    ]

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)


# --------------------------------------------------
# MAIN MEASUREMENT
# --------------------------------------------------

def main():

    frequencies = np.arange(
        START_FREQUENCY,
        STOP_FREQUENCY + STEP,
        STEP
    )

    amplitudes = []
    phases = []

    normal_lockin = SR830("A9JSTXTQA")
    rigol = Rigol()

    os.makedirs(
        PLOT_FOLDER,
        exist_ok=True
    )

    try:

        # Set drive
        normal_lockin.set_sine_out_amplitude(
            DRIVE_AMPLITUDE
        )

        # Rigol
        rigol.set_waveform(1, "SIN")
        rigol.set_output(1, True)

        print(
            f"Starting sweep at "
            f"{DRIVE_AMPLITUDE:.3f} V drive"
        )

        # ------------------------------------------
        # SWEEP
        # ------------------------------------------

        for frequency in frequencies:

            rigol.set_frequency(
                1,
                frequency
            )

            time.sleep(WAIT_TIME)

            amplitude = normal_lockin.read_amplitude()
            phase = normal_lockin.read_phase()

            amplitudes.append(amplitude)
            phases.append(phase)

            print(
                f"{frequency:.3f} Hz | "
                f"A = {amplitude:.6f} V | "
                f"phase = {phase:.2f}°"
            )

        frequencies = np.array(frequencies)
        amplitudes = np.array(amplitudes)
        phases = np.array(phases)

        # ------------------------------------------
        # PEAK
        # ------------------------------------------

        peak_index = np.argmax(amplitudes)

        peak_amplitude = amplitudes[peak_index]
        peak_frequency = frequencies[peak_index]

        # ------------------------------------------
        # PHASE ZERO CROSSING
        # ------------------------------------------

        f0_phase = find_zero_crossing(
            frequencies,
            phases
        )

        # ------------------------------------------
        # NOISE
        # ------------------------------------------

        normal_lockin.set_sine_out_amplitude(0.0)

        noise_samples = []

        print("\nMeasuring noise...")

        for _ in range(NOISE_SAMPLES):

            time.sleep(0.1)

            noise_samples.append(
                normal_lockin.read_amplitude()
            )

        noise_mean = np.mean(noise_samples)
        noise_std = np.std(noise_samples)

        snr = (
            peak_amplitude - noise_mean
        ) / noise_std

        # ------------------------------------------
        # Q
        # ------------------------------------------

        f_left, f_right, bandwidth, q_factor = (
            calculate_q(
                frequencies,
                amplitudes,
                f0_phase,
                background=noise_mean
            )
        )

        apeak_per_vdrive = (
            peak_amplitude
            / DRIVE_AMPLITUDE
        )

        # ------------------------------------------
        # PRINT RESULTS
        # ------------------------------------------

        print("\n--- RESULTS ---")
        print(
            f"Drive amplitude: "
            f"{DRIVE_AMPLITUDE:.3f} V"
        )
        print(
            f"Peak amplitude: "
            f"{peak_amplitude:.6f} V"
        )
        print(
            f"Peak frequency: "
            f"{peak_frequency:.3f} Hz"
        )
        print(
            f"f0 phase: "
            f"{f0_phase:.3f} Hz"
        )
        print(
            f"Noise mean: "
            f"{noise_mean:.9f} V"
)
        print(f"Noise std: " f"{noise_std:.9f} V")
        print(f"SNR: " f"{snr:.1f}")
        print(f"Q: " f"{q_factor:.1f}")
        print(f"Apeak / Vdrive: " f"{apeak_per_vdrive:.3f}")

        # ------------------------------------------
        # SAVE CSV
        # ------------------------------------------

        result = {
            "drive_amplitude_V": DRIVE_AMPLITUDE,
            "f0_phase_Hz": f0_phase,
            "peak_frequency_Hz": peak_frequency,
            "peak_amplitude_V": peak_amplitude,
            "noise_mean_V": noise_mean,
            "noise_std_V": noise_std,
            "snr": snr,
            "f_left_3db_Hz": f_left,
            "f_right_3db_Hz": f_right,
            "bandwidth_Hz": bandwidth,
            "Q_factor": q_factor,
            "Apeak_per_Vdrive": apeak_per_vdrive
        }

        save_to_csv(result)

        # ------------------------------------------
        # PLOTS
        # ------------------------------------------

        filename_base = (
            f"drive_{DRIVE_AMPLITUDE:.3f}V"
            .replace(".", "p")
        )

        # Amplitude
        plt.figure()

        plt.plot(
            frequencies,
            amplitudes,
            marker="."
        )

        plt.axvline(
            f0_phase,
            linestyle="--",
            label=f"f0 = {f0_phase:.3f} Hz"
        )

        if f_left is not None:
            plt.axvline(
                f_left,
                linestyle=":"
            )

        if f_right is not None:
            plt.axvline(
                f_right,
                linestyle=":"
            )

        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Amplitude (V)")
        plt.ylim(0, 0.6)
        plt.title(
            f"Amplitude response - "
            f"{DRIVE_AMPLITUDE:.3f} V drive"
        )

        plt.grid(True)
        plt.legend()

        plt.savefig(
            os.path.join(
                PLOT_FOLDER,
                filename_base + "_amplitude.png"
            ),
            dpi=300,
            bbox_inches="tight"
        )

        # Phase
        plt.figure()

        plt.plot(
            frequencies,
            phases,
            marker="."
        )

        plt.axhline(
            0,
            linestyle="--"
        )

        plt.axvline(
            f0_phase,
            linestyle="--",
            label=f"f0 = {f0_phase:.3f} Hz"
        )

        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Phase (degrees)")
        plt.title(
            f"Phase response - "
            f"{DRIVE_AMPLITUDE:.3f} V drive"
        )

        plt.grid(True)
        plt.legend()

        plt.savefig(
            os.path.join(
                PLOT_FOLDER,
                filename_base + "_phase.png"
            ),
            dpi=300,
            bbox_inches="tight"
        )

        plt.show()

    finally:

        normal_lockin.set_sine_out_amplitude(0.0)

        rigol.set_output(
            1,
            False
        )


if __name__ == "__main__":
    main()