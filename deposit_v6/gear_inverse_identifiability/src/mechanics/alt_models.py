"""
Controlled compliance variants M3/M3b for discrepancy sensitivity (E7).
M3 uses a constant global per-pair compliance, derived from mean M2 approach
at 100 Nm. Applying mean(delta_M2)/Fn per pair does not ensure that the
assembled M3 mean approach matches M2, because Hertz contact and load sharing
are retained. This experiment changes both mean and waveform behavior.
M3b scales M2 global compliance around its pitch-point value. Geometry,
contact formulation and Hertz law are shared; these are not independent
higher-fidelity validation models.
"""

import numpy as np
from typing import Optional

from .compliance import GearContactModel, HertzianContact


class ConstantStiffnessContactModel(GearContactModel):
    """
    M3 contact model: constant (position-independent) pair compliance,
    calibrated against a GearContactModel (M2) instance. Geometry,
    modification evaluation, and the Hertzian local contact law are shared
    with M2; only the global (bending/shear/foundation) compliance is
    replaced by a constant.
    """

    def __init__(
        self,
        pair,
        micro1=None,
        micro2=None,
        c_const: Optional[float] = None,
        linearize_hertz: bool = False,
    ):
        super().__init__(pair, micro1=micro1, micro2=micro2,
                         linearize_hertz=linearize_hertz)
        if c_const is None:
            raise ValueError(
                "c_const must be provided; use calibrate_constant_stiffness()."
            )
        self.c_const = float(c_const)

    def get_contact_state(self, phi1, theta1=None, theta2=None):
        state = super().get_contact_state(phi1, theta1=theta1, theta2=theta2)
        n = state["g"].shape[0]
        state["c_lin"] = np.full(n, self.c_const)
        return state


class WaveScaledContactModel(GearContactModel):
    """
    M3b reference model: same position-dependent compliance as M2 but with
    the stiffness-wave amplitude scaled by `beta` around its cycle mean:

        c_b(phi) = c_pitch + beta * (c_M2(phi) - c_pitch)

    beta = 1 recovers M2 exactly; beta = 0 yields a constant global per-pair compliance at c_pitch;
    it is not identical to M3, which uses a different calibration anchor. Intermediate values (e.g. 0.5) produce a *mild* model-
    form error: the model still exhibits a stiffness wave of plausible shape,
    so cross-inversion residuals stay small, but the waveform error biases
    the recovered geometry. This is the subtle-discrepancy regime relevant
    for practical identifiability.
    """

    def __init__(
        self,
        pair,
        c_mean: float,
        beta: float,
        micro1=None,
        micro2=None,
        linearize_hertz: bool = False,
        n_calib: int = 60,
    ):
        super().__init__(pair, micro1=micro1, micro2=micro2,
                         linearize_hertz=linearize_hertz)
        self.beta = float(beta)
        self.c_mean = float(c_mean)

    def get_contact_state(self, phi1, theta1=None, theta2=None):
        state = super().get_contact_state(phi1, theta1=theta1, theta2=theta2)
        state["c_lin"] = (self.c_mean
                          + self.beta * (state["c_lin"] - self.c_mean))
        return state


def calibrate_wave_mean(
    m2_model: GearContactModel,
    n_positions: int = 60,
) -> float:
    """
    Mean per-pair compliance of M2 over one mesh cycle (theta = 0),
    restricted to pairs within one base pitch of the path of contact.
    Used as the center of the wave scaling for WaveScaledContactModel.
    """
    # Center = per-pair compliance AT THE PITCH POINT (s_k = 0), where the
    # main load path sits. Using a mean over entering/exiting pairs would
    # bias the center towards more flexible tip/root sections and inflate
    # the overall deflection (M3b ended up 66% softer than M2).
    st = m2_model.get_contact_state(0.0, theta1=None)
    k0 = int(np.argmin(np.abs(st["s_k"])))
    return float(st["c_lin"][k0])


def calibrate_constant_stiffness(
    m2_model: GearContactModel,
    torque_Nm: float = 100.0,
    n_positions: int = 60,
) -> float:
    """
    Calibrate M3's constant compliance so that the mean elastic deflection
    matches M2 at the given torque, with NO profile modification (theta=0).

    For an unmodified pair, gaps are zero and every potential pair carries
    load, so TE(phi) = F * c_eff(phi) and the mean effective compliance is

        c_const = mean_phi TE(phi) / F .

    Returns c_const [mm/N].
    """
    from .transmission_error import TransmissionError

    pair = m2_model.pair
    F = torque_Nm * 1e3 / pair.g1.rb  # N

    te = TransmissionError(m2_model)
    res = te.compute_cycle(torque_Nm=torque_Nm, n_positions=n_positions,
                           theta1=None)
    c_const = float(np.mean(res["TE_lin"]) / F)
    if not np.isfinite(c_const) or c_const <= 0.0:
        raise RuntimeError(f"Calibration failed: c_const = {c_const}")
    return c_const
