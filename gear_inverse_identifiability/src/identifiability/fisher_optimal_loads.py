"""Scaled, noise-whitened sensitivities and fixed-budget local design.
No eigenvalue floor is used to create information in null directions.
"""
from itertools import combinations
import numpy as np

class FisherLoadSelector:
    def __init__(self, transmission_error_model, theta0, n_positions=60,
                 parameter_scale=None, sigma_mm=1.0, h_rel=1e-4, rank_rtol=1e-7):
        self.te_model = transmission_error_model
        self.theta0 = np.asarray(theta0, dtype=float).copy()
        self.n_positions = int(n_positions)
        self.p = self.theta0.size
        self.scale = np.ones(self.p) if parameter_scale is None else np.asarray(parameter_scale, dtype=float)
        if self.scale.shape != (self.p,) or np.any(self.scale <= 0) or not np.all(np.isfinite(self.scale)):
            raise ValueError('parameter_scale must contain p finite positive entries')
        if not np.isfinite(sigma_mm) or sigma_mm <= 0:
            raise ValueError('sigma_mm must be finite and positive')
        if self.n_positions < 2 or h_rel <= 0 or rank_rtol <= 0:
            raise ValueError('invalid sampling or differentiation tolerance')
        self.sigma_mm, self.h_rel, self.rank_rtol = float(sigma_mm), float(h_rel), float(rank_rtol)
        self._cache = {}

    def _compute_jacobian(self, torque_Nm, h_rel=None, n_positions=None):
        """Central differences in q=theta/scale; contact is re-solved.
        Returns d(TE/sigma)/dq. No fixed-active-set derivative is claimed.
        """
        h = self.h_rel if h_rel is None else float(h_rel)
        n = self.n_positions if n_positions is None else int(n_positions)
        key = (float(torque_Nm), h, n)
        if key in self._cache:
            return self._cache[key].copy()
        J = np.zeros((n, self.p))
        for j in range(self.p):
            hj = h * self.scale[j]
            tp, tm = self.theta0.copy(), self.theta0.copy()
            tp[j] += hj
            tm[j] -= hj
            yp = self.te_model.compute_cycle(torque_Nm=torque_Nm, n_positions=n,
                                             theta1=tp, theta2=None)['TE_lin_fluct']
            ym = self.te_model.compute_cycle(torque_Nm=torque_Nm, n_positions=n,
                                             theta1=tm, theta2=None)['TE_lin_fluct']
            J[:, j] = (yp - ym) / (2 * h * self.sigma_mm)
        self._cache[key] = J.copy()
        return J

    def stacked_jacobian(self, torque_levels, total_observations=None):
        torques = np.atleast_1d(torque_levels).astype(float)
        if not torques.size or not np.all(np.isfinite(torques)) or np.any(torques <= 0):
            raise ValueError('positive torque levels required')
        if total_observations is None:
            counts = [self.n_positions] * torques.size
        else:
            budget = int(total_observations)
            if budget != total_observations or budget < 2 * torques.size:
                raise ValueError('budget must allow at least two samples per load')
            counts = [budget // torques.size + (k < budget % torques.size) for k in range(torques.size)]
        return np.vstack([self._compute_jacobian(t, n_positions=n) for t, n in zip(torques, counts)])

    def _basis(self, subspace):
        B = np.asarray(subspace, dtype=float)
        if B.ndim != 2 or B.shape[0] != self.p or not B.shape[1] or not np.allclose(B.T @ B, np.eye(B.shape[1]), atol=1e-10):
            raise ValueError('subspace must be an orthonormal common basis in scaled coordinates')
        return B

    def fisher_matrix(self, torque_levels, total_observations=None, subspace=None):
        J = self.stacked_jacobian(torque_levels, total_observations)
        if subspace is not None:
            J = J @ self._basis(subspace)
        return J.T @ J

    def diagnostics(self, torque_levels, total_observations=None, subspace=None):
        J = self.stacked_jacobian(torque_levels, total_observations)
        if subspace is not None:
            J = J @ self._basis(subspace)
        s = np.linalg.svd(J, compute_uv=False)
        tol = self.rank_rtol * s[0] if s.size else 0.0
        rank = int(np.count_nonzero(s > tol))
        full = rank == J.shape[1]
        return dict(F=J.T @ J, eigs=np.sort(s ** 2), singular_values=s, rank=rank,
                    rank_tolerance=tol, dimension=J.shape[1], n_observations=J.shape[0],
                    logdet=float(2 * np.sum(np.log(s))) if full else -np.inf,
                    min_eigenvalue=float(s[-1] ** 2) if full else 0.0,
                    condition_J=float(s[0]/s[-1]) if full else np.inf,
                    condition_F=float((s[0]/s[-1])**2) if full else np.inf)

    def evaluate_combinations(self, candidate_torques, max_loads=4, criterion='D',
                              total_observations=None, subspace=None):
        if criterion not in ('D', 'E'):
            raise ValueError('criterion must be D or E')
        results = []
        for r in range(1, min(max_loads, len(candidate_torques)) + 1):
            for combo in combinations(candidate_torques, r):
                out = self.diagnostics(combo, total_observations, subspace)
                out.update(torques=np.array(combo), score=out['logdet'] if criterion == 'D' else out['min_eigenvalue'])
                results.append(out)
        return sorted(results, key=lambda x: x['score'], reverse=True)
