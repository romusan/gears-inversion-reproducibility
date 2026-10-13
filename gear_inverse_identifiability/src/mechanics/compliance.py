"""
Tooth compliance and Hertzian contact for spur gear pairs.

Uses a discrete spring model: each potential tooth pair k is represented by a
single contact point whose stiffness depends on the instantaneous position along
the path of contact (roll angles).  This is the standard quasi-static model
used in gear mesh dynamics literature.
"""

import numpy as np
from typing import Dict, Optional, List


class ToothCompliance:
    """
    Analytical tooth compliance based on a variable-section cantilever beam
    fixed at the root section and loaded at the contact point.

    Bending/shear are integrated along the RADIAL tooth direction (x = r -
    r_fixed), with the section thickness taken from the involute
    construction. This is the standard Weber-type model found in the gear
    mesh-stiffness literature. (An earlier revision integrated along the
    involute arc with arm rb*du, which overestimates the bending arm by up
    to ~2x and, worse, silently changed behavior across geometries through
    a negative-thickness guard; V6 caught a 100x amplitude error for the
    Korta & Mundo benchmark because of it.)
    """

    def __init__(self, gear, variant='legacy'):
        if variant not in ('legacy', 'shear-G', 'projected-energy', 'centerline-energy'):
            raise ValueError('Unknown compliance variant')
        self.variant = variant
        self.gear = gear
        self.r_root = gear.rf
        self.r_base = gear.rb
        self.alpha = gear.alpha
        self.m = gear.m
        self.E = gear.E
        self.nu = gear.nu
        self.G = self.E / (2.0 * (1.0 + self.nu))
        self.E_star = self.E / (1.0 - self.nu ** 2)
        # Geometry and material are fixed for the lifetime of this model.
        # Inverse iterations revisit exactly the same roll angles: cache only
        # the geometry-dependent compliance, never contact forces or relief.
        self._flexibility_cache = {}
        self._quadrature = np.polynomial.legendre.leggauss(24)

    def _section_at_radius(self, r: float):
        """Tooth thickness h_t and area at radius r (beam cross-section)."""
        alpha_r = np.arccos(np.clip(self.r_base / r, -1.0, 1.0))
        s_r = self.gear.tooth_thickness_at_radius(r)
        # Physical lower bound: a tooth cannot be thinner than ~0; clamp
        # non-positive involute thickness (pointed-tip artifact) to a small
        # positive value instead of switching to a rigid dummy compliance.
        s_min = 0.2 * self.m
        s_r = max(s_r, s_min)
        return s_r, alpha_r

    def flexibility(self, u: np.ndarray) -> np.ndarray:
        """
        Compliance [mm/N] projected along the flank normal for a contact
        point at roll angle u, including bending, shear and a foundation
        term (compliant embedding of the tooth base).
        """
        u = np.atleast_1d(u)
        c = np.zeros_like(u, dtype=float)
        E = self.E
        b = self.gear.b

        for i, ui in enumerate(u):
            cache_key = float(ui)
            if cache_key in self._flexibility_cache:
                c[i] = self._flexibility_cache[cache_key]
                continue
            r = self.r_base * np.sqrt(1.0 + ui ** 2)
            alpha_r = np.arctan(ui)

            # Beam fixed section: at the root radius (or base circle if the
            # root is undercut below it).
            r_fix = max(self.r_root, self.r_base * 1.0001)
            h = r - r_fix
            if h <= 1e-3 * self.m or not np.isfinite(h):
                c[i] = 1e-6
                self._flexibility_cache[cache_key] = c[i]
                continue

            # Numerical integration along the radial beam direction.
            n_q = 24
            xs = np.linspace(0.0, h, n_q)
            # Gauss-Legendre on [0, h] for smooth integrands
            xi, wi = self._quadrature
            xg = 0.5 * h * (xi + 1.0)
            wg = 0.5 * h * wi

            I_x = np.empty(n_q)
            A_x = np.empty(n_q)
            for k, x in enumerate(xg):
                s_r, _ = self._section_at_radius(r_fix + x)
                I_x[k] = b * s_r ** 3 / 12.0
                A_x[k] = b * s_r

            # Bending: c_bend = ∫ (h-x)^2 / (E I(x)) dx
            # Shear:   c_shr = 1.2 ∫ 1 / (E A(x)) dx
            lever = (h - xg) ** 2
            c_bend = float(np.sum(wg * lever / (E * I_x)))
            shear_modulus = E if self.variant == 'legacy' else self.G
            c_shear = float(1.2 * np.sum(wg / (shear_modulus * A_x)))
            if self.variant == 'centerline-energy':
                # The radial approximation is replaced by the tooth centre-line
                # coordinate y=r*cos(beta), beta=t_arc(r)/(2r). Integrate over
                # y with dy/dr=cos(beta)+u*sin(beta) for the ideal involute.
                # Horizontal thickness is 2*r*sin(beta). A root fillet is still
                # absent: this is an analytical ablation, not full tooth FEM.
                rr=r_fix+xg
                ar=np.arccos(np.clip(self.r_base/rr,-1,1))
                tt=np.array([self._section_at_radius(rv)[0] for rv in rr])
                beta=tt/(2*rr)
                Y=rr*np.cos(beta)
                width=2*rr*np.sin(beta)
                raw_tt=np.array([self.gear.tooth_thickness_at_radius(rv) for rv in rr])
                beta_slope_factor=np.where(raw_tt>=0.2*self.m,np.tan(ar),beta)
                jac_y=np.cos(beta)+beta_slope_factor*np.sin(beta)
                beta_contact=self._section_at_radius(r)[0]/(2*r)
                Xc=r*np.sin(beta_contact);Yc=r*np.cos(beta_contact)
                force_angle=alpha_r-beta_contact
                arm=(Yc-Y)*np.cos(force_angle)-Xc*np.sin(force_angle)
                AA=b*width;II=b*width**3/12
                c_bend=float(np.sum(wg*jac_y*arm**2/(E*II)))
                c_shear=float(1.2*np.cos(force_angle)**2*np.sum(wg*jac_y/(self.G*AA)))
                c_axial=float(np.sin(force_angle)**2*np.sum(wg*jac_y/(E*AA)))
            elif self.variant == 'projected-energy':
                # Radial beam, normal force decomposed into transverse/axial
                # components. The load acts at a flank offset t(r)/2; its
                # axial component contributes an opposing bending moment.
                # Castigliano: c = integral (M/F)^2/EI + (V/F)^2/kGA
                # + (N/F)^2/EA. This still approximates root/foundation geometry.
                t_contact, _ = self._section_at_radius(r)
                arm = (h-xg)*np.cos(alpha_r) - 0.5*t_contact*np.sin(alpha_r)
                c_bend = float(np.sum(wg * arm**2 / (E * I_x)))
                c_shear *= np.cos(alpha_r)**2
                c_axial = float(np.sin(alpha_r)**2 * np.sum(wg/(E*A_x)))
            else:
                c_axial = 0.0

            # Foundation (Weber-type compliant base): the tooth root embeds
            # into a semi-infinite body; standard order-of-magnitude term.
            c_foundation = (1.0 / (E * b)) * np.cos(alpha_r) ** 2

            c[i] = c_bend + c_shear + c_axial + c_foundation
            self._flexibility_cache[cache_key] = c[i]
        return c


class HertzianContact:
    def __init__(self, E1: float, nu1: float, E2: float, nu2: float, b: float, linearize: bool = False):
        self.E1 = E1
        self.nu1 = nu1
        self.E2 = E2
        self.nu2 = nu2
        self.b = b
        self.E_star = 1.0 / ((1.0 - nu1 ** 2) / E1 + (1.0 - nu2 ** 2) / E2)
        self.linearize = linearize

    def _approach_linear(self, p: np.ndarray, r_eq: np.ndarray) -> np.ndarray:
        """Linearized Hertzian approach for small forces (~1 um / 1000 N typical)."""
        # Typical hertzian stiffness for gear contact: ~ 10^9 N/m per unit length
        # => compliance ~ 1e-9 m^2/N = 1e-6 mm * mm / N... let's calibrate heuristically.
        # For cylindrical contact: c_h = (2/(pi*E_star*L)) * log(...)
        # Approximate with a constant: k_h ≈ E_star * b / (10 * r_eq) in N/mm
        # Actually, simpler: use explicit formula evaluated at a reference load.
        p_ref = 1000.0  # N
        w_ref = self._approach_nonlinear(np.full_like(p, p_ref), r_eq)
        c_h = w_ref / p_ref  # linearized compliance [mm/N]
        return c_h * p

    def _approach_nonlinear(self, p: np.ndarray, r_eq: np.ndarray) -> np.ndarray:
        p = np.atleast_1d(p)
        r_eq = np.atleast_1d(r_eq)
        eps = 1e-12
        p_safe = np.where(p > eps, p, eps)
        pL = p_safe / self.b
        a_h = np.sqrt(4.0 * pL * r_eq / (np.pi * self.E_star))
        w = pL / (np.pi * self.E_star) * (2.0 * np.log(np.clip(4.0 * r_eq / a_h, 1.0, None)) - 1.0)
        w = np.where(p > eps, w, 0.0)
        return w

    def approach(self, p: np.ndarray, r_eq: np.ndarray) -> np.ndarray:
        if self.linearize:
            return self._approach_linear(p, r_eq)
        return self._approach_nonlinear(p, r_eq)

    def stiffness_derivative(self, p: np.ndarray, r_eq: np.ndarray) -> np.ndarray:
        if self.linearize:
            p_ref = 1000.0
            w_ref = self._approach_nonlinear(np.full_like(p, p_ref), r_eq)
            return np.full_like(p, w_ref / p_ref)
        eps = 1e-12
        p_safe = np.where(p > eps, p, eps)
        pL = p_safe / self.b
        a_h = np.sqrt(4.0 * pL * r_eq / (np.pi * self.E_star))
        ratio = 4.0 * r_eq / a_h
        # d[pL(2 log(K/sqrt(pL))-1)]/dpL = 2 log(...)-2.
        # Once the logarithm is clipped, it is constant and the slope is -1.
        dw_dpL = np.where(ratio > 1.0, 2.0 * np.log(np.maximum(ratio, 1.0)) - 2.0, -1.0) / (np.pi * self.E_star)
        return np.where(p > eps, dw_dpL / self.b, 0.0)


class GearContactModel:
    """
    Assembles geometric separations and mechanical compliances for a gear pair.
    Uses a discrete multi-pair contact model.
    """

    def __init__(self, pair, micro1=None, micro2=None, linearize_hertz: bool = False,
                 compliance_variant='legacy'):
        self.pair = pair
        self.micro1 = micro1
        self.micro2 = micro2
        self.compliance_variant = compliance_variant
        self.comp1 = ToothCompliance(pair.g1, variant=compliance_variant)
        self.comp2 = ToothCompliance(pair.g2, variant=compliance_variant)
        self.hertz = HertzianContact(
            pair.g1.E, pair.g1.nu, pair.g2.E, pair.g2.nu, pair.g1.b,
            linearize=linearize_hertz,
        )

    def get_contact_state(
        self,
        phi1: float,
        theta1: Optional[np.ndarray] = None,
        theta2: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Build the contact state for all potentially active tooth pairs at rotation phi1.

        Returns dict with arrays:
            k: tooth-pair indices
            s_k: position along LOA for each pair [mm]
            u1_k, u2_k: roll angles on each gear
            g_k: geometric gap [mm] (modification only for ideal involute)
            c_lin_k: linear compliance [mm/N]
            r_eq_k: equivalent radius [mm]
        """
        pb = self.pair.pb
        s_contact = self.pair.g1.rb * phi1

        # Determine range of k values that can be in contact
        # Path of contact: [s_A, s_E] relative to current s_contact
        # s_A = -g_f, s_E = g_a (from GearPair)
        g_f = self.pair.g2.rb * (
            np.tan(np.arccos(np.clip(self.pair.g2.rb / self.pair.g2.ra, -1.0, 1.0)))
            - np.tan(self.pair.alpha_w)
        )
        g_a = self.pair.g1.rb * (
            np.tan(np.arccos(np.clip(self.pair.g1.rb / self.pair.g1.ra, -1.0, 1.0)))
            - np.tan(self.pair.alpha_w)
        )

        # Active pairs: those whose theoretical contact point s_k = s_contact + k*pb
        # lies within [s_A - pb/2, s_E + pb/2] (generous margin)
        k_min = int(np.floor((-g_f - s_contact - 0.5 * pb) / pb))
        k_max = int(np.ceil((g_a - s_contact + 0.5 * pb) / pb))
        k = np.arange(k_min, k_max + 1)

        s_k = s_contact + k * pb

        # Roll angles for each contact point
        # s_k position -> distance from pitch point along LOA
        # For gear1: sqrt(r1^2 - rb1^2) = rb1*tan(alpha_w) + (s_k - 0)
        # since s is measured from pitch point in our grid convention
        dist1 = self.pair.g1.rb * np.tan(self.pair.alpha_w) + s_k
        dist2 = self.pair.g2.rb * np.tan(self.pair.alpha_w) - s_k

        r1 = np.sqrt(self.pair.g1.rb ** 2 + dist1 ** 2)
        r2 = np.sqrt(self.pair.g2.rb ** 2 + dist2 ** 2)
        u1 = dist1 / self.pair.g1.rb  # because u = tan(alpha_r) = dist/rb
        u2 = dist2 / self.pair.g2.rb

        # Clamp to valid profile range
        u1 = np.clip(u1, 0.0, np.sqrt((self.pair.g1.ra / self.pair.g1.rb) ** 2 - 1.0))
        u2 = np.clip(u2, 0.0, np.sqrt((self.pair.g2.ra / self.pair.g2.rb) ** 2 - 1.0))

        # Geometric gap: pairs OUTSIDE the path of contact have a positive
        # corner separation that grows linearly beyond the approach/roll-off
        # points (standard TCA simplification). Setting g = 0 for every
        # potential pair (as an earlier revision did) makes ALL pairs carry
        # load regardless of position, inflating the contact ratio and
        # flattening the stiffness wave — this is what V6 caught.
        g_k = np.maximum(0.0, np.maximum(s_k - g_a, -g_f - s_k))

        if self.micro1 is not None and theta1 is not None:
            from geometry.microgeometry import map_roll_to_modification_domain
            u_tip1 = np.sqrt((self.pair.g1.ra / self.pair.g1.rb) ** 2 - 1.0)
            s1 = map_roll_to_modification_domain(u1, u_tip1, 0.0)
            g_k = g_k + self.micro1.evaluate(s1, theta1)

        if self.micro2 is not None and theta2 is not None:
            from geometry.microgeometry import map_roll_to_modification_domain
            u_tip2 = np.sqrt((self.pair.g2.ra / self.pair.g2.rb) ** 2 - 1.0)
            s2 = map_roll_to_modification_domain(u2, u_tip2, 0.0)
            g_k = g_k + self.micro2.evaluate(s2, theta2)

        # Mechanical compliances at these roll angles
        c1 = self.comp1.flexibility(u1)
        c2 = self.comp2.flexibility(u2)
        c_lin = c1 + c2

        rho1 = self.pair.g1.rb * u1
        rho2 = self.pair.g2.rb * u2
        r_eq = (rho1 * rho2) / (rho1 + rho2 + 1e-12)
        r_eq = np.clip(r_eq, 1e-6, None)

        return {
            "k": k,
            "s_k": s_k,
            "u1": u1,
            "u2": u2,
            "g": g_k,
            "c_lin": c_lin,
            "r_eq": r_eq,
        }

