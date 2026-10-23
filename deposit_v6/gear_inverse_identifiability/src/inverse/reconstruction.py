"""
Inverse reconstruction of gear microgeometry from transmission error.
"""

import numpy as np
from scipy.optimize import least_squares
from typing import Optional, Tuple, Dict


class InverseReconstructor:
    """
    Constrained least-squares reconstruction of profile modification parameters.
    """

    def __init__(
        self,
        transmission_error_model,
        torque_levels_Nm: np.ndarray,
        theta_bounds: np.ndarray,  # shape (p, 2)
        theta_scale: Optional[np.ndarray] = None,
        n_positions_forward: int = 60,
        observation_sigma_mm=None,
    ):
        """
        Parameters
        ----------
        transmission_error_model : TransmissionError
            Forward model instance.
        torque_levels_Nm : np.ndarray
            Torque levels at which TE was observed.
        theta_bounds : np.ndarray
            Lower and upper bounds for each parameter, shape (p, 2).
        theta_scale : np.ndarray, optional
            Characteristic scale for each parameter (used for conditioning).
        n_positions_forward : int
            Number of angular positions to use in the forward model during inversion.
            Smaller values speed up optimization at the cost of some accuracy.
        """
        self.te_model = transmission_error_model
        self.torques = np.atleast_1d(torque_levels_Nm)
        self.bounds = theta_bounds
        self.p = theta_bounds.shape[0]
        self.n_positions_forward = n_positions_forward
        self.observation_sigma_mm = observation_sigma_mm
        if theta_scale is None:
            self.scale = np.ones(self.p)
        else:
            self.scale = theta_scale
        self.scale = np.asarray(self.scale, dtype=float)
        if self.scale.shape != (self.p,) or np.any(self.scale <= 0) or not np.all(np.isfinite(self.scale)):
            raise ValueError('theta_scale must contain finite positive entries')

    def _stack_observations(self, y_list):
        """Stack observations from multiple torque levels."""
        return np.concatenate(y_list)

    def _predict(self, theta_scaled: np.ndarray) -> np.ndarray:
        """Evaluate forward model at all torque levels."""
        theta = theta_scaled * self.scale
        preds = []
        for T in self.torques:
            res = self.te_model.compute_cycle(
                torque_Nm=T,
                n_positions=self.n_positions_forward,
                theta1=theta,
                theta2=None,
            )
            preds.append(res["TE_lin_fluct"])
        return self._stack_observations(preds)

    def reconstruct(
        self,
        y_obs: np.ndarray,
        theta0: Optional[np.ndarray] = None,
        method: str = "trf",
        ftol: float = 1e-9,
        xtol: float = 1e-12,
        gtol: float = 1e-12,
        max_nfev: int = 2000,
        verbose: int = 0,
        jacobian_scheme: str = '2-point',
    ) -> Dict:
        """
        Solve the inverse problem.

        Parameters
        ----------
        y_obs : np.ndarray
            Stacked observed TE fluctuation curves (same ordering as self.torques).
        theta0 : np.ndarray, optional
            Initial guess. Random within bounds if None.

        Returns
        -------
        result : dict with keys theta, cost, nfev, success, etc.
        """
        # The stacked prediction has one TE sample per angular position and
        # per torque level; observations must match that length exactly.
        n_expected = self.torques.size * self.n_positions_forward
        y_obs = np.asarray(y_obs, dtype=float)
        if y_obs.shape[0] != n_expected:
            raise ValueError(
                f"Observation length {y_obs.shape[0]} does not match stacked "
                f"prediction length {n_expected} "
                f"({self.torques.size} torque level(s) x "
                f"{self.n_positions_forward} positions). Generate observations "
                f"with the same n_positions used by the reconstructor."
            )

        if theta0 is None:
            theta0 = np.random.uniform(
                self.bounds[:, 0] / self.scale,
                self.bounds[:, 1] / self.scale,
            )
        else:
            theta0 = theta0 / self.scale

        lb = self.bounds[:, 0] / self.scale
        ub = self.bounds[:, 1] / self.scale

        def residuals(theta_s):
            return (self._predict(theta_s) - y_obs) / sigma

        sigma = np.ones(n_expected) if self.observation_sigma_mm is None else np.broadcast_to(
            np.asarray(self.observation_sigma_mm, dtype=float), (n_expected,))
        if np.any(sigma <= 0) or not np.all(np.isfinite(sigma)):
            raise ValueError('observation_sigma_mm must be finite and positive')

        def scaled_central_jacobian(q):
            # Absolute 1e-4 steps in q=theta/scale, independently audited in E5.
            # Bound-aware second-order one-sided differences avoid evaluating
            # negative relief or start positions outside the admissible box.
            J = np.zeros((n_expected, self.p))
            base = residuals(q)
            for j in range(self.p):
                h = min(1e-4, (ub[j]-lb[j])/4)
                v = np.zeros(self.p);v[j] = h
                if q[j]-h >= lb[j] and q[j]+h <= ub[j]:
                    J[:,j] = (residuals(q+v)-residuals(q-v))/(2*h)
                elif ub[j]-q[j] >= 2*h:
                    J[:,j] = (-3*base+4*residuals(q+v)-residuals(q+2*v))/(2*h)
                else:
                    J[:,j] = (3*base-4*residuals(q-v)+residuals(q-2*v))/(2*h)
            return J

        if jacobian_scheme not in ('2-point','scaled-central'):
            raise ValueError('jacobian_scheme must be 2-point or scaled-central')

        res = least_squares(
            residuals,
            theta0,
            method=method,
            bounds=(lb, ub),
            jac=scaled_central_jacobian if jacobian_scheme == 'scaled-central' else '2-point',
            ftol=ftol,
            xtol=xtol,
            gtol=gtol,
            max_nfev=max_nfev,
            verbose=verbose,
        )

        theta_est = res.x * self.scale
        cost = res.cost
        nfev = res.nfev

        # Compute predicted TE with estimated parameters
        y_pred = self._predict(res.x)
        rmse = np.sqrt(np.mean((y_pred - y_obs) ** 2))

        return {
            "theta": theta_est,
            "cost": cost,
            "rmse": rmse,
            "nfev": nfev,
            "success": res.success,
            "status": res.status,
            "message": res.message,
            "jac": res.jac,
            "theta0": theta0 * self.scale,
            "jacobian_scheme": jacobian_scheme,
        }

