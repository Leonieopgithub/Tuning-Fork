from scipy.optimize import curve_fit  # - oud 
import time
import pandas as pd
import numpy as np
from rigol_dg1022 import RigolDG

from PIE625 import PIE625
from mitutoyo import Mitutoyo
from SR830 import SR830
import PLL

def calibrateAir(
    ctrlNormal: SR830,
    ctrlShear: SR830,
    freqGen: RigolDG,
    freqNormalRange: list[int | float] = [789.5, 794.5],
    freqShearRange: list[int | float] = [452.6, 457.6],
    delay: int | float = 0.75,
    denseHalfwidth=3.0,
    denseStep=0.1,
    fitMaxFev=5000,
    progress_callback=None,
) -> tuple[list[int | float], list[int | float]]:
    optNormal, optShear = PLL.PLL2x1D(
        ctrlNormal,
        ctrlShear,
        freqGen,
        freqNormalRange,
        freqShearRange,
        delay=delay,
        points=[20, 7],
        iterations=20,
        Kp=1 / (4*np.pi),
        tolerance=(0.1 / 180) * np.pi,
        progress_callback=progress_callback,
    )
    print("STEP 3: PLL2x1D finished")
    print("optNormal =", optNormal)
    print("optShear =", optShear)

    fNormal = optNormal[0]
    # fShear = optShear[0]

    numPts = int(round((2 * denseHalfwidth) / denseStep)) + 1
    freqsDenseNormal = np.linspace(
        fNormal - denseHalfwidth, fNormal + denseHalfwidth, numPts
    )
    ampsDenseNormal = np.empty_like(freqsDenseNormal)
    phasesDenseNormal = np.empty_like(freqsDenseNormal)

    # freqsDenseShear = np.linspace(
    #     fShear - denseHalfwidth, fShear + denseHalfwidth, numPts
    # )
    # ampsDenseShear = np.empty_like(freqsDenseShear)
    # phasesDenseShear = np.empty_like(freqsDenseShear)
    print("STEP 4: starting dense sweep")
    for i, f in enumerate(freqsDenseNormal):
        print(f"STEP 4.{i}: setting frequency to {f:.3f} Hz")
        freqGen.set_frequency(1, f)
        time.sleep(delay)
        A = ctrlNormal.readAmplitude()
        P = ctrlNormal.readPhase()
        print(f"READ: f={f:.3f}, A={A}, P={P}")
        ampsDenseNormal[i] = A
        phasesDenseNormal[i] = P

        if progress_callback is not None:
            progress_callback(
                "dense_sweep",
                i + 1,
                len(freqsDenseNormal),
                f,
                ampsDenseNormal[i],
                phasesDenseNormal[i],
            )
        print(
            f"[CAL] Dense sweep: f={f:.3f} Hz, A={ampsDenseNormal[i]:.6f}, φ={phasesDenseNormal[i]:.2f}"
        )

    print("STEP 5: dense sweep finished")

    # for i, f in enumerate(freqsDenseShear):
    #     freqGen.set_frequency(2, f)
    #     time.sleep(delay)
    #     ampsDenseShear[i] = ctrlShear.readAmplitude()
    #     phasesDenseShear[i] = ctrlShear.readPhase()
    #     print(
    #         f"[CAL] Dense sweep: f={f:.3f} Hz, A={ampsDenseShear[i]:.6f}, φ={phasesDenseShear[i]:.2f}"
    #     )

    # fit Lorentzian
    ω0Normal = 2 * np.pi * fNormal
    C0Normal = np.nanmax(ampsDenseNormal) * ω0Normal
    gamma0Normal = ω0Normal / 10.0

    # ω0Shear = 2 * np.pi * fShear
    # C0Shear = np.nanmax(ampsDenseShear) * ω0Shear
    # gamma0Shear = ω0Shear / 10.0

    def A_model(f, C, gamma_sys, omega0):
        ω = 2 * np.pi * f
        return C / np.sqrt((omega0**2 - ω**2) ** 2 + (gamma_sys * ω) ** 2)
    print("STEP 6: starting curve_fit")
    poptNormal, _ = curve_fit(
        A_model,
        freqsDenseNormal,
        ampsDenseNormal,
        p0=[C0Normal, gamma0Normal, ω0Normal],
        bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
        nan_policy="omit",
        maxfev=fitMaxFev,
    )
    CNormal, gammaNormal, omega0Normal = poptNormal
    f0Normal = omega0Normal / (2 * np.pi)
    print(
        f"[CAL] (Normal) Fit results: C={CNormal:.3e}, γ_sys={gammaNormal:.3e}, f_res={f0Normal:.6f} Hz"
    )

    freqGen.set_frequency(1, round(f0Normal, 6))

    # poptShear, _ = curve_fit(
    #     A_model,
    #     freqsDenseShear,
    #     ampsDenseShear,
    #     p0=[C0Shear, gamma0Shear, ω0Shear],
    #     bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
    #     nan_policy="omit",
    #     maxfev=fitMaxFev,
    # )
    # CShear, gammaShear, omega0Shear = poptShear
    # f0Shear = omega0Shear / (2 * np.pi)
    # print(
    #     f"[CAL] (Shear) Fit results: C={CShear:.3e}, γ_sys={gammaShear:.3e}, f_res={f0Shear:.6f} Hz"
    # )

    # ctrlShear.setFrequency(round(f0Shear, 6))

    return {
        "f0": f0Normal,
        "C": CNormal,
        "gamma": gammaNormal,
        "frequencies": freqsDenseNormal,
        "amplitudes": ampsDenseNormal,
        "phases": phasesDenseNormal,
    }


def calibrateDistance(
    ctrlNormal: SR830,
    z_stage: PIE625,
    height_dev: Mitutoyo,
    start_V=10.0,
    max_V=110.0,
    step_V=1.0,
    amp_fraction=0.05,
    delay=0.5,
):
    """


    Make sure to put the normal mode on resonance with a fitting amplitude.
    """

    print(f"\n[DIST] Moving Z-stage to {start_V} V for probe touch...")
    z_stage.absolute_voltage(start_V)
    time.sleep(1)
    input("Adjust probe to surface and back off, then press Enter.")

    A0 = ctrlNormal.readAmplitude()

    print(f"[DIST] Baseline A0 = {A0:.6f}")

    threshold = amp_fraction * A0
    maxPoints = int((max_V - start_V) / step_V) + 1
    amplitudes, heights = maxPoints * [0.0], maxPoints * [0.0]
    voltages = np.linspace(start_V, max_V, maxPoints, endpoint=True)

    for i, voltage in enumerate(voltages):
        z_stage.absolute_voltage(voltage)
        time.sleep(delay)

        A = ctrlNormal.readAmplitude()
        h = height_dev.measurement()

        print(f"[DIST] Approach V={voltage:.1f} → A={A:.6f}, h={h:.3f}")

        amplitudes[i] = A
        heights[i] = h

        if np.isfinite(A) and A < threshold:
            print(
                f"[DIST] Threshold reached at V={voltage:.1f} V; contact established."
            )

            voltages = voltages[: i + 1]
            amplitudes = amplitudes[: i + 1]
            heights = heights[: i + 1]
            break

    input("Zero the height gauge at contact point, then press Enter.")

    print("[DIST] Retracting from contact back to start...")
    amplitudesRetract, heightsRetract = len(voltages) * [0.0], len(voltages) * [0.0]
    voltagesRetract = np.flip(
        np.linspace(start_V, voltages[-1], len(voltages), endpoint=True)
    )

    for i, voltage in enumerate(voltagesRetract):
        z_stage.absolute_voltage(voltage)
        time.sleep(delay)
        A = ctrlNormal.readAmplitude()
        h = height_dev.measurement()
        print(f"[DIST] Retract V={voltage:.1f} → A={A:.6f}, h={h:.3f}")
        amplitudesRetract[i] = A
        heightsRetract[i] = h

    voltages = np.concatenate((voltages, voltagesRetract))
    amplitudes = np.concatenate((amplitudes, amplitudesRetract))
    heights = np.concatenate((heights, heightsRetract))

    df = pd.DataFrame(
        {"z_voltage": voltages, "amplitude": amplitudes, "height_mm": heights}
    )

    return df

