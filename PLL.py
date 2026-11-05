"""
Phase Lock Loop 

Sweeps through the frequencies, while recording amplitudes and phase
of the returning wave.

At resonance, the amplitude will be greatest and the phase shift at 0.
"""

import numpy as np
import time

from SR830 import SR830
from rigol_dg1022 import RigolDG


def PLL1D(
    ctrl: SR830,
    freqGen: RigolDG,
    freqMin: int | float,
    freqMax: int | float,
    points: int = 11,
    tolerance: int | float = 1e-3,
    iterations: int = 20,
    freqGenChannel: int = 1,
    Kp=1 / np.pi,
    delay: float = 1.0,
    progress_callback=None,
) -> list[float]:
    """
    Find the resonance frequency using a PLL approach via the sfa -> SR830 controller.

    The amplitude sweep uses the measured amplitude (Rm) to pick an
    initial guess.

    The PLL loop reads the phase (Rp) and converts it to radians.
    Resonance is defined as when the phase error is near zero.

    :returns: [fRes, ampRes, phaRes]
    :rtype: list[float]
    """

    # --------------------------------------------------
    # INITIAL AMPLITUDE SWEEP
    # --------------------------------------------------

    freqs = np.linspace(
        freqMin,
        freqMax,
        points,
    )

    amplitudes = np.zeros_like(freqs)

    for i, f in enumerate(freqs):

        freqGen.set_frequency(
            freqGenChannel,
            f,
        )

        time.sleep(delay)

        amp = ctrl.readAmplitude()
        phase = ctrl.readPhase()

        amplitudes[i] = amp

        print(
            f"[INITIAL SWEEP] "
            f"f={f:.3f} Hz | "
            f"A={amp:.9f} V | "
            f"phase={phase:.3f}°"
        )
        
        if progress_callback is not None:
            progress_callback(
                "pll_sweep",
                i + 1,
                len(freqs),
                float(f),
                float(amp),
                None,
            )

    # --------------------------------------------------
    # SELECT INITIAL RESONANCE GUESS
    # --------------------------------------------------

    best_index = np.argmax(amplitudes)

    fRes: float = float(
        freqs[best_index]
    )

    freqGen.set_frequency(
        freqGenChannel,
        fRes,
    )

    time.sleep(delay)

    phaseDeg = ctrl.readPhase()

    # If we are already within tolerance,
    # no PLL adjustment iterations are required.
    if abs(np.deg2rad(phaseDeg)) < tolerance:
        return [
            fRes,
            ctrl.readAmplitude(),
            phaseDeg,
        ]

    # --------------------------------------------------
    # PREPARE PLL ITERATION
    # --------------------------------------------------

    fPrev = fRes
    phasePrev = phaseDeg

    fRes = (
        fRes
        + Kp * np.deg2rad(phaseDeg)
    )

    # --------------------------------------------------
    # PLL ADJUSTMENT LOOP
    # --------------------------------------------------

    for i in range(iterations):

        freqGen.set_frequency(
            freqGenChannel,
            fRes,
        )

        time.sleep(delay)

        phaseDeg = ctrl.readPhase()

        # Send every iteration to the GUI
        if progress_callback is not None:
            progress_callback(
                "pll_adjust",
                i + 1,
                iterations,
                float(fRes),
                None,
                float(phaseDeg),
            )

        print(
            f"Iteration {i:3d}: "
            f"Frequency = {fRes:.6f} Hz, "
            f"Phase = {phaseDeg:.2f} deg"
        )

        # --------------------------------------------------
        # CHECK TOLERANCE
        # --------------------------------------------------

        if abs(np.deg2rad(phaseDeg)) < tolerance:

            if phaseDeg * phasePrev < 0:

                f_interp = (
                    fPrev
                    - phasePrev
                    * (fPrev - fRes)
                    / (phasePrev - phaseDeg)
                )

                return [
                    f_interp,
                    ctrl.readAmplitude(),
                    phaseDeg,
                ]

            else:

                return [
                    fRes,
                    ctrl.readAmplitude(),
                    phaseDeg,
                ]

        # --------------------------------------------------
        # CHECK ZERO CROSSING
        # --------------------------------------------------

        if phasePrev * phaseDeg < 0:

            if i > 1:

                f_interp = (
                    fPrev
                    - phasePrev
                    * (fRes - fPrev)
                    / (phaseDeg - phasePrev)
                )

                return [
                    f_interp,
                    ctrl.readAmplitude(),
                    phaseDeg,
                ]

        # --------------------------------------------------
        # NEXT PLL STEP
        # --------------------------------------------------

        fPrev = fRes
        phasePrev = phaseDeg

        fRes = (
            fRes
            + Kp * np.deg2rad(phaseDeg)
        )

    else:

        opt = [
            fRes,
            ctrl.readAmplitude(),
            phaseDeg,
        ]

    return opt


def PLL2D(
    ctrlNormal: SR830,
    ctrlShear: SR830,
    freqGen: RigolDG,
    freqNormalRange: list[int | float] = [789.5, 794.5],
    freqShearRange: list[int | float] = [452.6, 457.6],
    delay: int | float = 0.75,
    iterations: int = 3,
    Kp: float = 1 / np.pi,
    tolerance: float = 1e-3,
    points: list[int] = [6, 6],
) -> list[list[float]]:
    """
    Sweeps through the shear frequencies nested in a sweep
    of the normal frequencies.

    Starts a 2D sweep. At worst O(n^2) time complexity.

    :returns:
        [[fNormal, normalAmp, normalPha],
         [fShear, shearAmp, shearPha]]

    :rtype: list[list[float]]
    """

    optNormal: list[float] = [
        freqNormalRange[0],
        0.0,
        180.0,
    ]

    optShear: list[float] = [
        freqShearRange[0],
        0.0,
        180.0,
    ]

    freqsNormal = np.linspace(
        *freqNormalRange,
        num=points[0],
        endpoint=True,
    )

    freqsShear = np.linspace(
        *freqShearRange,
        num=points[1],
        endpoint=True,
    )

    amps = np.zeros(
        shape=(
            points[0],
            points[1],
        )
    )

    for i, fNormal in enumerate(
        freqsNormal.data
    ):

        freqGen.set_frequency(
            1,
            fNormal,
        )

        for j, fShear in enumerate(
            freqsShear.data
        ):

            freqGen.set_frequency(
                2,
                fShear,
            )

            time.sleep(delay)

            amps[i, j] = np.sqrt(
                (ctrlNormal.readAmplitude() ** 2) / 2
                + (ctrlNormal.readAmplitude() ** 2) / 2
            )

    indAmp = np.unravel_index(
        np.argmax(amps),
        amps.shape,
    )

    fResNormal: float = freqsNormal[
        indAmp[0]
    ]

    fResShear: float = freqsShear[
        indAmp[1]
    ]

    print(
        "Initial guess from amplitude sweep:\n"
        f"Normal: {fResNormal:.3f} Hz\n"
        f"Shear: {fResShear:.3f} Hz"
    )

    # --------------------------------------------------
    # NORMAL LOOP
    # --------------------------------------------------

    for i in range(iterations):

        freqGen.set_frequency(
            1,
            fResNormal,
        )

        # --------------------------------------------------
        # SHEAR LOOP
        # --------------------------------------------------

        for j in range(iterations):

            freqGen.set_frequency(
                2,
                fResShear,
            )

            time.sleep(delay)

            phaseDegShear = (
                ctrlShear.readPhase()
            )

            print(
                f"Iteration {j:3d}: "
                f"Frequency = {fResShear:.6f} Hz, "
                f"Phase = {phaseDegShear:.2f} deg"
            )

            if (
                abs(
                    np.deg2rad(
                        phaseDegShear
                    )
                )
                < tolerance
            ):

                print(
                    "(Shear) PLL converged "
                    f"after {j} iterations "
                    f"with frequency "
                    f"{fResShear:.6f} Hz"
                )

                optShear = [
                    fResShear,
                    ctrlShear.readAmplitude(),
                    phaseDegShear,
                ]

                break

            fResShear = (
                fResShear
                + Kp
                * np.deg2rad(
                    phaseDegShear
                )
            )

        else:

            optShear = [
                fResShear,
                ctrlShear.readAmplitude(),
                phaseDegShear,
            ]

            print(
                "(Shear) Maximum iterations "
                "reached without full convergence "
                "in the PLL loop."
            )

        # --------------------------------------------------
        # NORMAL PHASE
        # --------------------------------------------------

        phaseDegNormal = (
            ctrlNormal.readPhase()
        )

        print(
            f"Iteration {i:3d}: "
            f"Frequency = {fResNormal:.6f} Hz, "
            f"Phase = {phaseDegNormal:.2f} deg"
        )

        if (
            abs(
                np.deg2rad(
                    phaseDegNormal
                )
            )
            < tolerance
        ):

            print(
                "(Normal) PLL converged "
                f"after {i} iterations "
                f"with frequency "
                f"{fResNormal:.6f} Hz"
            )

            optNormal = [
                fResNormal,
                ctrlNormal.readAmplitude(),
                phaseDegNormal,
            ]

            break

        fResNormal = (
            fResNormal
            + Kp
            * np.deg2rad(
                phaseDegNormal
            )
        )

    else:

        optNormal = [
            fResNormal,
            ctrlNormal.readAmplitude(),
            phaseDegNormal,
        ]

        print(
            "(Normal) Maximum iterations "
            "reached without full convergence "
            "in the PLL loop."
        )

    return [
        optNormal,
        optShear,
    ]


def PLL2x1D(
    ctrlNormal: SR830,
    ctrlShear: SR830,
    freqGen: RigolDG,
    freqNormalRange: list[int | float] = [795.0, 797.0],
    freqShearRange: list[int | float] = [459.0, 465.0],
    points: list[int] = [6, 6],
    tolerance: float = 1e-3,
    Kp: float = 1 / np.pi,
    iterations: int = 3,
    delay: int | float = 0.75,
    progress_callback=None,
) -> list[list[float]]:
    """
    Sweeps through normal frequencies and shear frequencies
    sequentially.

    Starts 2 separate 1D sweeps instead of the full 2D sweep.

    :returns:
        [[fNormal, normalAmp, normalPha],
         [fShear, shearAmp, shearPha]]

    :rtype: list[list[float]]
    """

    # --------------------------------------------------
    # NORMAL MODE
    # --------------------------------------------------

    optNormal = PLL1D(
        ctrlNormal,
        freqGen,
        freqNormalRange[0],
        freqNormalRange[1],
        points[0],
        freqGenChannel=1,
        tolerance=tolerance,
        iterations=iterations,
        Kp=Kp,
        delay=delay,
        progress_callback=progress_callback,
    )

    # --------------------------------------------------
    # SHEAR MODE
    # --------------------------------------------------
    #
    # Currently intentionally disabled in the local setup.
    #
    # optShear = PLL1D(
    #     ctrlShear,
    #     freqGen,
    #     freqShearRange[0],
    #     freqShearRange[1],
    #     points[1],
    #     freqGenChannel=2,
    #     tolerance=tolerance,
    #     iterations=iterations,
    #     Kp=Kp,
    #     delay=delay,
    #     progress_callback=progress_callback,
    # )

    optShear = [
        1,
        1,
        1,
    ]

    return [
        optNormal,
        optShear,
    ]


if __name__ == "__main__":

    ctrlNormal = SR830(
        SN=""
    )

    freqGen = RigolDG()

    freqGen.set_waveform(
        1,
        "SIN",
    )

    freqGen.set_waveform(
        2,
        "SIN",
    )

    freqGen.set_output(
        1,
        True,
    )

    freqGen.set_output(
        2,
        True,
    )

    resonance = PLL1D(
        ctrlNormal,
        freqGen,
        789.5,
        794.5,
    )

    print(
        "Final estimated resonance frequency: "
        f"{resonance[0]:.6f} Hz"
    )

    ctrlNormal.ser.close()