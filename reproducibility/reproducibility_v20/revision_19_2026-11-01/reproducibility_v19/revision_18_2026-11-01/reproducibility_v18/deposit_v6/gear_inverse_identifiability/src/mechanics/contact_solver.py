"""
Quasi-static contact solver for spur gear mesh.

Uses a diagonal compliance model with Hertzian nonlinearity.
For a given pinion rotation and applied torque, solves for:
- contact forces p_k at each active tooth pair k
- rigid-body approach delta
- transmission error (loaded)
"""

import numpy as np
from scipy.optimize import brentq
from typing import Dict, Tuple


class ContactSolver:
    """
    Solves the contact problem for one angular position.
    """

    def __init__(self, contact_model):
        self.model = contact_model
        self.pair = contact_model.pair

    def _solve_point_force(
        self,
        gap0: float,
        c_lin: float,
        r_eq: float,
        delta: float,
    ) -> float:
        """
        For a single contact point with gap0 (without approach),
        solve for p >= 0 such that w = gap0 - delta + c_lin*p + w_hertz(p) >= 0
        and p*w = 0.

        Returns p (0 if no contact, positive if contact).
        """
        g_eff = gap0 - delta
        if g_eff >= 0:
            return 0.0

        # If Hertzian contact is linearized, explicit solution
        if getattr(self.model.hertz, "linearize", False):
            p_ref = 1000.0
            w_ref = self.model.hertz._approach_nonlinear(np.array([p_ref]), np.array([r_eq]))[0]
            c_h = w_ref / p_ref if p_ref > 0 else 1e-12
            p = -g_eff / (c_lin + c_h)
            return max(p, 0.0)

        hertz = self.model.hertz

        def residual(p):
            if p <= 0:
                return g_eff
            w_h = hertz.approach(np.array([p]), np.array([r_eq]))[0]
            return c_lin * p + w_h + g_eff

        p_low = 0.0
        p_high = 1.0
        for _ in range(60):
            if residual(p_high) > 0:
                break
            p_high *= 2.0
            if p_high > 1e12:
                raise RuntimeError("Cannot bracket root in contact solver.")
        else:
            raise RuntimeError("Bracket expansion failed.")

        p_sol = brentq(residual, p_low, p_high, xtol=1e-14, maxiter=100)
        return max(p_sol, 0.0)

    def _forces_for_delta(
        self,
        g: np.ndarray,
        c_lin: np.ndarray,
        r_eq: np.ndarray,
        delta: float,
    ) -> Tuple[float, np.ndarray]:
        """
        Vectorized (pure-Python loop, optimal for small N) computation of the
        contact force at every pair for a given rigid-body approach delta.

        Returns (S, p) with S = sum of forces and p the per-pair force array.
        Equivalent to _solve_point_force evaluated pair-by-pair, but ~100x
        faster: the nonlinear per-pair equation is solved by bisection in
        log(p) space (monotone residual) instead of bracket expansion + brentq.
        """
        hertz = self.model.hertz
        n = g.size
        p = np.zeros(n)
        g_eff = g - delta

        if getattr(hertz, "linearize", False):
            p_ref = 1000.0
            c_h = hertz._approach_nonlinear(np.full(n, p_ref), r_eq) / p_ref
            denom = c_lin + c_h
            mask = g_eff < 0.0
            p[mask] = -g_eff[mask] / denom[mask]
            return float(np.sum(p)), p

        # Nonlinear Hertzian contact: per pair solve
        #   f(p) = c_lin*p + w_h(p, r_eq) + g_eff = 0,  p > 0
        # f is strictly increasing in p (compliance > 0), so bisection in
        # log-space is robust. 50 iterations give ~1e-13 relative accuracy
        # over a [1e-11, 1e8] N bracket.
        log_lo = -25.328436022934504  # ln(1e-11)
        log_range = 41.44653167389282  # ln(1e18) - ln(1e-11)
        E_star = hertz.E_star
        b = hertz.b
        inv_b = 1.0 / b
        pi_E = np.pi * E_star

        ge_l = g_eff.tolist()
        cl_l = c_lin.tolist()
        r_l = r_eq.tolist()
        p_l = [0.0] * n

        for i in range(n):
            ge = ge_l[i]
            if ge >= 0.0:
                continue
            cl = cl_l[i]
            r = r_l[i]

            # Upper bracket: p0 ignoring Hertzian term, then double in log space
            # until the residual is positive (typically 1-3 doublings).
            p_hi = -ge / cl
            if p_hi <= 0.0:
                p_hi = 1.0
            f_hi = cl * p_hi + 1.0  # placeholder to enter loop
            x_hi = np.log(p_hi)
            for _ in range(200):
                pL = p_hi * inv_b
                a_h = np.sqrt(4.0 * pL * r / pi_E)
                ratio = 4.0 * r / a_h
                if ratio < 1.0:
                    ratio = 1.0
                w = pL / pi_E * (2.0 * np.log(ratio) - 1.0)
                f_hi = cl * p_hi + w + ge
                if f_hi > 0.0:
                    break
                x_hi += 0.6931471805599453  # ln 2
                p_hi = np.exp(x_hi)
            else:
                raise RuntimeError("Bracket expansion failed in vectorized solver.")

            # Bisection in log space
            x_lo = log_lo
            x_hi = np.log(p_hi)
            for _ in range(50):
                x_mid = 0.5 * (x_lo + x_hi)
                pm = np.exp(x_mid)
                pL = pm * inv_b
                a_h = np.sqrt(4.0 * pL * r / pi_E)
                ratio = 4.0 * r / a_h
                if ratio < 1.0:
                    ratio = 1.0
                w = pL / pi_E * (2.0 * np.log(ratio) - 1.0)
                if cl * pm + w + ge > 0.0:
                    x_hi = x_mid
                else:
                    x_lo = x_mid

            # One Newton polish step using the analytical stiffness derivative
            pm = np.exp(0.5 * (x_lo + x_hi))
            pL = pm * inv_b
            a_h = np.sqrt(4.0 * pL * r / pi_E)
            ratio = max(4.0 * r / a_h, 1.0)
            w = pL / pi_E * (2.0 * np.log(ratio) - 1.0)
            dw_dpL = (2.0 * np.log(ratio) - 2.0 if ratio > 1.0 else -1.0) / pi_E
            dw_dp = dw_dpL * inv_b
            f = cl * pm + w + ge
            pm = max(pm - f / (cl + dw_dp), 0.0)

            p_l[i] = pm

        p = np.array(p_l)
        return float(np.sum(p)), p

    def solve_for_delta(
        self,
        g: np.ndarray,
        c_lin: np.ndarray,
        r_eq: np.ndarray,
        F_target: float,
        delta_guess: float = 0.0,
    ) -> Tuple[np.ndarray, float, Dict]:
        """
        Find delta such that sum of contact forces equals F_target.

        Uses safeguarded Newton on delta (warm-started at delta_guess) with the
        analytical derivative dS/ddelta = sum 1/(c_lin + dw_h/dp), falling back
        to brentq if Newton fails to converge.
        """
        hertz = self.model.hertz

        def total_force(delta):
            return self._forces_for_delta(g, c_lin, r_eq, delta)

        delta = float(delta_guess)

        # Initial bracket around the guess (gaps bound the physically
        # meaningful delta range).
        g_abs_max = max(10.0 * float(np.max(np.abs(g))), 1.0)
        delta_low = delta - g_abs_max
        delta_high = delta + g_abs_max

        S_low, _ = total_force(delta_low)
        S_high, _ = total_force(delta_high)

        for _ in range(40):
            if S_low > F_target:
                delta_low -= 10.0 * abs(delta_low) - 1.0
                S_low, _ = total_force(delta_low)
                continue
            if S_high < F_target:
                delta_high += 10.0 * abs(delta_high) + 1.0
                S_high, _ = total_force(delta_high)
                continue
            break
        else:
            raise RuntimeError("Could not bracket delta for force equilibrium.")

        # Warm-started safeguarded Newton
        converged = False
        S, p = total_force(delta)
        for _ in range(40):
            if abs(S - F_target) <= 1e-9:
                converged = True
                break
            # dS/ddelta = sum over active pairs of dp/ddelta
            # with dp/ddelta = 1 / (c_lin + dw_h/dp)  (implicit function theorem)
            mask = p > 1e-12
            if not np.any(mask):
                # No pair in contact; move delta into contact range
                delta = 0.5 * (delta_low + delta_high)
                S, p = total_force(delta)
                continue
            hprime = hertz.stiffness_derivative(p[mask], r_eq[mask])
            dS = float(np.sum(1.0 / (c_lin[mask] + hprime)))
            if not np.isfinite(dS) or dS <= 0.0:
                break
            step = (S - F_target) / dS
            delta_new = delta - step
            # Safeguard: keep within bracket
            if not (delta_low < delta_new < delta_high):
                delta_new = 0.5 * (delta + 0.5 * (delta_low + delta_high))
            if abs(delta_new - delta) < 1e-12:
                delta = delta_new
                S, p = total_force(delta)
                converged = abs(S - F_target) <= 1e-8
                break
            delta = delta_new
            S, p = total_force(delta)
            if S_low > F_target and delta < delta_low:
                break
            if S > F_target:
                delta_high = delta
            else:
                delta_low = delta

        if not converged:
            def residual_delta(d):
                S_d, _ = total_force(d)
                return S_d - F_target

            try:
                delta = brentq(residual_delta, delta_low, delta_high, xtol=1e-12, maxiter=200)
            except ValueError as e:
                raise RuntimeError(f"Delta root finding failed: {e}")
            S, p = total_force(delta)

        info = {
            "residual_force": abs(S - F_target),
            "n_contact": np.count_nonzero(p > 1e-12),
            "delta": delta,
        }
        return p, delta, info

    def solve_position(
        self,
        phi1: float,
        torque_Nm: float,
        theta1: np.ndarray = None,
        theta2: np.ndarray = None,
        delta_guess: float = 0.0,
    ) -> Dict:
        """
        Solve contact for a single angular position.

        Returns dict with keys:
            p, delta, g, w, TE_lin, TE_ang, info
        """
        state = self.model.get_contact_state(phi1, theta1=theta1, theta2=theta2)
        g = state["g"]
        c_lin = state["c_lin"]
        r_eq = state["r_eq"]

        F_target = torque_Nm * 1e3 / self.pair.g1.rb  # N

        p, delta, info = self.solve_for_delta(
            g, c_lin, r_eq, F_target, delta_guess=delta_guess
        )

        w_h = self.model.hertz.approach(p, r_eq)
        w = g - delta + c_lin * p + w_h

        TE_lin = delta  # [mm]
        TE_ang = delta / self.pair.g1.rb  # [rad]

        return {
            "p": p,
            "delta": delta,
            "g": g,
            "w": w,
            "TE_lin": TE_lin,
            "TE_ang": TE_ang,
            "info": info,
            "F_target": F_target,
            "state": state,
        }

