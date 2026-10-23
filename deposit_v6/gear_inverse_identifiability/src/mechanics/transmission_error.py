"""
Transmission error computation over a mesh cycle.
"""

import numpy as np
from typing import Dict, Optional
from .contact_solver import ContactSolver


class TransmissionError:
    """
    Computes TE curves for one or multiple torque levels.
    """

    def __init__(self, contact_model):
        self.model = contact_model
        self.pair = contact_model.pair
        self.solver = ContactSolver(contact_model)

    def compute_cycle(
        self,
        torque_Nm: float,
        n_positions: int = 120,
        theta1: np.ndarray = None,
        theta2: np.ndarray = None,
    ) -> Dict:
        """
        Compute TE over one base-pitch cycle.

        Returns dict with arrays phi, TE_lin, TE_ang, and lists of per-position data.
        """
        phi, dphi = self.pair.rotation_for_mesh(n_positions)

        TE_lin = np.zeros(n_positions)
        TE_ang = np.zeros(n_positions)
        delta_vals = np.zeros(n_positions)
        forces = []
        gaps = []
        seps = []
        infos = []
        states = []

        delta_guess = 0.0
        for i, ph in enumerate(phi):
            res = self.solver.solve_position(
                phi1=ph,
                torque_Nm=torque_Nm,
                theta1=theta1,
                theta2=theta2,
                delta_guess=delta_guess,
            )
            delta_guess = res["delta"]  # warm start next position
            TE_lin[i] = res["TE_lin"]
            TE_ang[i] = res["TE_ang"]
            delta_vals[i] = res["delta"]
            forces.append(res["p"])
            gaps.append(res["g"])
            seps.append(res["w"])
            infos.append(res["info"])
            states.append(res["state"])

        # Remove rigid-body mean trend to get fluctuating TE
        TE_lin_fluct = TE_lin - np.mean(TE_lin)
        TE_ang_fluct = TE_ang - np.mean(TE_ang)

        return {
            "phi": phi,
            "dphi": dphi,
            "TE_lin": TE_lin,
            "TE_ang": TE_ang,
            "TE_lin_fluct": TE_lin_fluct,
            "TE_ang_fluct": TE_ang_fluct,
            "delta": delta_vals,
            "forces": forces,
            "gaps": gaps,
            "separations": seps,
            "infos": infos,
            "states": states,
        }

