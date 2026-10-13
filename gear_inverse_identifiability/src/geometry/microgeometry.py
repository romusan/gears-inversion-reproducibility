"""
Profile modification parametrization for gear tooth microgeometry.
"""

import numpy as np
from typing import Tuple


class TipRelief:
    """
    Tip relief modification for one flank.

    Parameter vector (4 components, p fixed to 2):
        theta = [Ca, sa, Cd, sd]

    Modification function h(s) with s in [0, 1] along active profile:
        h(s) = Ca * [ (s - sa) / (1 - sa) ]_+^p  (addendum/top relief)
             + Cd * [ (sd - s) / sd ]_+^p        (dedendum/root relief)

    where [x]_+ = max(0, x).
    """

    def __init__(self, p: float = 2.0):
        self.p = p

    def evaluate(self, s: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """
        Evaluate modification at dimensionless profile coordinates s.

        Parameters
        ----------
        s : np.ndarray, shape (n,)
            Dimensionless coordinate along active profile, typically 0 at root side, 1 at tip side.
        theta : np.ndarray, shape (4,)
            [Ca, sa, Cd, sd] with sa in (0,1), sd in (0,1).

        Returns
        -------
        h : np.ndarray
            Modification amount (same units as Ca, Cd), positive means material removal.
        """
        Ca, sa, Cd, sd = theta
        h = np.zeros_like(s, dtype=float)

        # Addendum relief (tip side)
        mask_a = s > sa
        if np.any(mask_a):
            h[mask_a] += Ca * ((s[mask_a] - sa) / (1.0 - sa)) ** self.p

        # Dedendum relief (root side)
        mask_d = s < sd
        if np.any(mask_d):
            h[mask_d] += Cd * ((sd - s[mask_d]) / sd) ** self.p

        return h

    def jacobian(self, s: np.ndarray, theta: np.ndarray) -> np.ndarray:
        """
        Jacobian dh/dtheta, shape (n, 4).
        """
        Ca, sa, Cd, sd = theta
        n = s.size
        J = np.zeros((n, 4), dtype=float)

        mask_a = s > sa
        if np.any(mask_a):
            t = (s[mask_a] - sa) / (1.0 - sa)
            J[mask_a, 0] = t ** self.p
            # Both numerator and denominator depend on sa.
            J[mask_a, 1] = (Ca * self.p * t ** (self.p - 1)
                           * (s[mask_a] - 1.0) / (1.0 - sa) ** 2)

        mask_d = s < sd
        if np.any(mask_d):
            t = (sd - s[mask_d]) / sd
            J[mask_d, 2] = t ** self.p
            if self.p == 2.0:
                J[mask_d, 3] = Cd * 2.0 * t * (s[mask_d] / sd ** 2)
            else:
                J[mask_d, 3] = Cd * self.p * t ** (self.p - 1) * (s[mask_d] / sd ** 2)

        return J


def map_roll_to_modification_domain(
    u: np.ndarray,
    u_tip: float,
    u_root: float,
) -> np.ndarray:
    """
    Map involute roll angle u to dimensionless s in [0,1].
    s = 0 corresponds to active profile start (root side),
    s = 1 corresponds to active profile end (tip side).

    Parameters
    ----------
    u : np.ndarray
        Roll angles (involute parameter).
    u_tip : float
        Roll angle at tip.
    u_root : float
        Roll angle at active profile start (near root).

    Returns
    -------
    s : np.ndarray
        Dimensionless coordinate.
    """
    s = (u - u_root) / (u_tip - u_root)
    return np.clip(s, 0.0, 1.0)

