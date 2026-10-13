"""
Involute spur gear geometry and line-of-action contact potentials.

All calculations are in the transverse plane for straight spur gears.
Coordinates follow standard involute parametrization.
"""

import numpy as np
from typing import Tuple, Optional


class InvoluteGear:
    """
    Standard involute spur gear geometry.
    """

    def __init__(
        self,
        z: int,
        m: float,
        alpha_deg: float,
        b: float,
        x: float = 0.0,
        haP: float = 1.0,
        hfP: float = 1.25,
        rhoFP: float = 0.38,
        E: float = 210e3,  # MPa
        nu: float = 0.30,
        pitch_thickness_mm: Optional[float] = None,
    ):
        self.z = z
        self.m = m
        self.alpha = np.deg2rad(alpha_deg)
        self.b = b
        self.x = x
        self.haP = haP
        self.hfP = hfP
        self.rhoFP = rhoFP
        self.E = E
        self.nu = nu

        # Basic diameters
        self.d = m * z
        self.r = self.d / 2.0
        self.db = self.d * np.cos(self.alpha)          # base diameter
        self.rb = self.db / 2.0
        self.da = self.d + 2.0 * m * (haP + x)          # tip diameter
        self.ra = self.da / 2.0
        self.df = self.d - 2.0 * m * (hfP - x)          # root diameter
        self.rf = self.df / 2.0

        # Pressure angle at tip
        if self.ra > self.rb:
            self.alpha_a = np.arccos(self.rb / self.ra)
        else:
            self.alpha_a = 0.0

        # Roll angle at tip
        self.inv_alpha = np.tan(self.alpha) - self.alpha
        self.inv_alpha_a = np.tan(self.alpha_a) - self.alpha_a if self.alpha_a > 0 else 0.0

        # Circular tooth thickness at pitch radius
        self.s = m * (np.pi / 2.0 + 2.0 * x * np.tan(self.alpha))
        if pitch_thickness_mm is not None:
            if not np.isfinite(pitch_thickness_mm) or not 0 < pitch_thickness_mm < np.pi * m:
                raise ValueError('pitch_thickness_mm must lie between zero and the circular pitch')
            self.s = float(pitch_thickness_mm)

    def tooth_thickness_at_radius(self, r: float) -> float:
        """Circular tooth thickness at arbitrary radius r (r >= rb)."""
        if r < self.rb:
            raise ValueError("Radius below base circle.")
        alpha_r = np.arccos(self.rb / r)
        inv_alpha_r = np.tan(alpha_r) - alpha_r
        return r * (self.s / self.r + 2.0 * (self.inv_alpha - inv_alpha_r))

    def involute_profile(self, u: np.ndarray, flank: str = "right") -> Tuple[np.ndarray, np.ndarray]:
        """
        Parametric involute in Cartesian coordinates.
        u : roll angle (rad), array
        flank : 'right' or 'left'
        Returns (x, y) arrays.
        """
        x = self.rb * (np.cos(u) + u * np.sin(u))
        y = self.rb * (np.sin(u) - u * np.cos(u))
        if flank == "left":
            x = -x
        return x, y

    def get_active_roll_angles(self, n_points: int = 200) -> np.ndarray:
        """
        Roll angles covering the active profile from root to tip.
        For contact analysis we typically need the segment that actually engages.
        Returns u from near-root to tip.
        """
        # Approximate roll angle at root (conservative, slightly above root)
        if self.rf > self.rb:
            alpha_f = np.arccos(np.clip(self.rb / self.rf, -1.0, 1.0))
            inv_alpha_f = np.tan(alpha_f) - alpha_f
            u_min = inv_alpha_f
        else:
            # Undercut case: start near base circle
            u_min = 0.0
        u_max = self.inv_alpha_a
        return np.linspace(max(u_min, 0.0), u_max, n_points)


class GearPair:
    """
    Pair of involute spur gears with contact geometry along the line of action.
    """

    def __init__(
        self,
        gear1: InvoluteGear,
        gear2: InvoluteGear,
        center_distance: Optional[float] = None,
    ):
        self.g1 = gear1
        self.g2 = gear2

        if center_distance is None:
            center_distance = (gear1.r + gear2.r)
        self.a = center_distance

        # Working pressure angle (transverse)
        cos_alpha_w = (gear1.r + gear2.r) * np.cos(gear1.alpha) / self.a
        cos_alpha_w = np.clip(cos_alpha_w, -1.0, 1.0)
        self.alpha_w = np.arccos(cos_alpha_w)

        # Working pitch radii
        self.rw1 = self.a / (1.0 + gear2.z / gear1.z)
        self.rw2 = self.a - self.rw1

        # Contact ratio (approximate, transverse)
        # Using tip diameters
        ra1 = gear1.ra
        ra2 = gear2.ra
        rb1 = gear1.rb
        rb2 = gear2.rb

        # Length of path of contact
        # Tangent length from working pitch point to tip
        self.T1T2 = (
            np.sqrt(ra1**2 - rb1**2)
            + np.sqrt(ra2**2 - rb2**2)
            - self.a * np.sin(self.alpha_w)
        )
        self.eps_alpha = self.T1T2 / (np.pi * gear1.m * np.cos(gear1.alpha))

        # Base pitch
        self.pb = np.pi * gear1.m * np.cos(gear1.alpha)

    def line_of_action_points(self, n_points: int = 200) -> np.ndarray:
        """
        Coordinates along the line of action in the fixed frame.
        Returns s : distance along line of action from the first contact point
        (near gear1 root / gear2 tip) to the last contact point.
        """
        # We parametrize by distance along line of action from approach point A
        # to recess point E.
        self.s_loa = np.linspace(0.0, self.T1T2, n_points)
        return self.s_loa

    def contact_points_on_gears(self, s: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        For points along line of action (distance s from approach point),
        return the roll angles u1, u2 and radii r1, r2 on each gear.
        """
        # Line of action angle in fixed frame: horizontal if we align centers on x-axis
        # For simplicity, we define local coordinates.
        # Approach point A is where gear2 tip touches gear1 flank near root.
        # From geometry: distance from pitch point to A along LOA = sqrt(ra2^2 - rb2^2) - a*sin(alpha_w)
        # Actually, simpler: from T1 (tangent point on gear1 base circle) measure along LOA.

        # Let's define: s=0 at the first point of contact (gear1 near root, gear2 tip)
        # s increases toward gear1 tip, gear2 root.

        # Distance from gear1 center to LOA = rb1
        # Gear1 roll angle increases as we move along LOA

        # Tangent point on gear1 base circle to LOA
        # For external gears, line of action is tangent to both base circles.
        # Let's work in the frame where centers are on x-axis, gear1 at (0,0), gear2 at (a,0).
        # LOA goes up-right from gear1 with angle = alpha_w above horizontal (for right flank contact).

        # Distance along LOA from tangent point T1 to contact point at radius r1:
        # s_T1_to_r1 = sqrt(r1^2 - rb1^2)
        # At approach point A: r1 is close to root, r2 = ra2
        # sqrt(ra2^2 - rb2^2) = distance from T2 to tip contact point
        # Total T1T2 = sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(alpha_w)
        # Wait, standard formula:
        # T1T2 = (sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2)) - a*sin(alpha_w)

        # Let's define s from the approach point A (first contact).
        # At A: distance from T1 to A along LOA = T1A = sqrt(ra2^2 - rb2^2) - a*sin(alpha_w)
        #        (because T2A = sqrt(ra2^2 - rb2^2), and T1T2 = T1A + AT2... careful with signs)

        # Simpler: for a point at distance s from A along LOA toward E:
        # Distance from T1 = T1A + s
        # But T1A = sqrt(ra2^2 - rb2^2) - a*sin(alpha_w)
        # Actually, for external gears:
        # T1 is the tangent point on gear1, T2 on gear2.
        # T1T2 = length of common tangent.
        # Approach point A is where gear2 tip meets gear1: measured from T1, distance = T1A
        # Recess point E is where gear1 tip meets gear2: measured from T1, distance = T1E
        # T1A = sqrt(ra2^2 - rb2^2) - (T1T2 - sqrt(ra1^2 - rb1^2)) ... no.

        # Standard: T1A = sqrt(ra2^2 - rb2^2) - a*sin(alpha_w) ??? Let's verify.
        # Actually, from geometry:
        # T1T2 = a * sin(alpha_w)  (distance between tangent points along common normal)
        # No, that's wrong. T1T2 = distance between tangent points = a*sin(alpha_w) only if alpha_w is working pressure angle.
        # Yes! For external gears, the length of the common tangent between base circles is a*sin(alpha_w).
        # But the path of contact length is:
        # g_alpha = 0.5*(sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(alpha_w))
        # Wait, the total path of contact AE = sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(alpha_w)
        # This equals T1E + T2A - T1T2? Let's not overcomplicate.

        # What matters: for a point at distance s along path of contact from A:
        # radius on gear1: r1(s) = sqrt(rb1^2 + (T1A + s)^2)
        # radius on gear2: r2(s) = sqrt(rb2^2 + (T2E + (AE - s))^2) ... messy.

        # Alternative: use the fact that roll angle u = tan(alpha_r) - alpha_r = inv(alpha_r)
        # and the arc length on base circle = rb * u.
        # The distance along LOA from base tangent point to point at radius r is sqrt(r^2 - rb^2).

        # Let's define T1 as origin on LOA for gear1 measurements.
        # Contact starts at A where s_A = sqrt(ra2^2 - rb2^2) - a*sin(alpha_w) ???

        # Let me use a cleaner approach:
        # For each contact point along LOA, the radii can be computed from the geometry
        # of the tangent line. In the coordinate system where LOA is the x-axis:
        # Gear1 center at (0, rb1), gear2 center at (a*sin(alpha_w), -rb2) ??? No.

        # Let's use the parametric approach:
        # For a contact point, the normal passes through the pitch point (working).
        # The distance along LOA from the pitch point P to the contact point:
        # For gear1, toward root: negative direction, toward tip: positive.

        # I'll use the standard formula for radius as function of position along path of contact.
        # Define s from the pitch point P, positive toward recess (gear1 tip).
        # Then for gear1: sqrt(r1^2 - rb1^2) = s + some_offset
        # For gear2: sqrt(r2^2 - rb2^2) = (a*sin(alpha_w) - s) + some_offset

        # OK, let me just compute numerically using the known approach/recess geometry.
        # Approach point A: r2 = ra2, so dist from T2 to A = sqrt(ra2^2 - rb2^2)
        # Since T1T2 = a*sin(alpha_w) (length of common tangent), dist from T1 to A = a*sin(alpha_w) - sqrt(ra2^2 - rb2^2)
        # But this could be negative if the approach point is before T1. Actually for external gears,
        # approach point A is always between T1 and T2? No, for standard gears A is between T1 and T2.
        # Actually T1 and T2 are the tangent points. The path of contact is the segment of the common tangent
        # between the two tip circles. So A and E are on the segment T1T2.
        # Distance T1A = sqrt(ra2^2 - rb2^2) - (a*sin(alpha_w) - sqrt(ra1^2 - rb1^2))? No.

        # Let me use the known relation:
        # T1A = sqrt(ra2^2 - rb2^2) - a*sin(alpha_w) only works if ra2 is very large.
        # Standard formula from Dudley/ISO:
        # Approach length g_f = 0.5 * (sqrt(ra2^2 - rb2^2) - a*sin(alpha_w) + sqrt(ra1^2 - rb1^2))
        # No wait, that's the approach segment.
        # Correct: total path AE = g_alpha = sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(alpha_w)
        # Approach segment PA (from pitch point to approach) = sqrt(ra2^2 - rb2^2) - rw2*sin(alpha_w)
        # Recess segment PE = sqrt(ra1^2 - rb1^2) - rw1*sin(alpha_w)
        # Where rw*sin(alpha_w) = rb*tan(alpha_w) ??? Let's check: rw*cos(alpha_w) = rb, so rw*sin(alpha_w) = rb*tan(alpha_w).
        # And sqrt(ra^2 - rb^2) = rb*tan(alpha_a).
        # So approach = rb2*(tan(alpha_a2) - tan(alpha_w)), recess = rb1*(tan(alpha_a1) - tan(alpha_w)).

        # Great, that's clean!
        alpha_a1 = np.arccos(np.clip(self.g1.rb / self.g1.ra, -1.0, 1.0)) if self.g1.ra > self.g1.rb else 0.0
        alpha_a2 = np.arccos(np.clip(self.g2.rb / self.g2.ra, -1.0, 1.0)) if self.g2.ra > self.g2.rb else 0.0

        g_f = self.g2.rb * (np.tan(alpha_a2) - np.tan(self.alpha_w))  # approach (from P to A, gear2 side)
        g_a = self.g1.rb * (np.tan(alpha_a1) - np.tan(self.alpha_w))  # recess (from P to E, gear1 side)

        # Now define s from pitch point P: negative toward approach (A), positive toward recess (E)
        # At position s:
        # For gear1: sqrt(r1^2 - rb1^2) = rb1*tan(alpha_w) + s  (because at s=0, r1=rw1)
        # Check: rb1*tan(alpha_w) = rw1*sin(alpha_w) = sqrt(rw1^2 - rb1^2). Yes!
        # So r1(s) = sqrt(rb1^2 + (rb1*tan(alpha_w) + s)**2)
        # Similarly for gear2: the point is at distance |s| from P but on the other side.
        # Actually, for gear2, the direction is opposite: as s increases (toward E), we move toward gear2 root.
        # At s=0 (pitch point): r2 = rw2.
        # For gear2: sqrt(r2^2 - rb2^2) = rb2*tan(alpha_w) - s  (because at s=g_f <0, r2=ra2)
        # Check at s = -g_f (approach point A): rb2*tan(alpha_w) - (-g_f) = rb2*tan(alpha_w) + g_f = rb2*tan(alpha_a2) = sqrt(ra2^2 - rb2^2). Yes!

        # However, the user's model uses a fixed set of potential contact points on the line of action
        # for each meshing position. The standard way is:
        # For a given pinion rotation angle phi1, the contact point moves along LOA.
        # The base pitch corresponds to rotation: pb = rb1 * (2*pi/z1) * cos(alpha)? No.
        # Base pitch pb = pi*m*cos(alpha). Rotation for one base pitch: delta_phi1 = pb / rb1.

        # For the contact model, we need the separation at each potential contact point
        # for each angular position. This is a standard "slice model" or "potential contact model".

        # Let's define N potential contact points along the line of action, spanning at least
        # one base pitch more than the path of contact to capture double tooth contact.
        pass  # will implement below in the contact model module

    def get_contact_grid(self, n_points: int = 200, overshoot: float = 1.0) -> dict:
        """
        Build a grid of potential contact points along the line of action.
        Returns dict with radii, roll angles, and path coordinates.
        """
        alpha_a1 = np.arccos(np.clip(self.g1.rb / self.g1.ra, -1.0, 1.0)) if self.g1.ra > self.g1.rb else 0.0
        alpha_a2 = np.arccos(np.clip(self.g2.rb / self.g2.ra, -1.0, 1.0)) if self.g2.ra > self.g2.rb else 0.0

        g_f = self.g2.rb * (np.tan(alpha_a2) - np.tan(self.alpha_w))
        g_a = self.g1.rb * (np.tan(alpha_a1) - np.tan(self.alpha_w))

        # Extend by one base pitch on each side for numerical stability during roll
        s_min = -g_f - overshoot * self.pb
        s_max = g_a + overshoot * self.pb

        s = np.linspace(s_min, s_max, n_points)

        # Radii on each gear
        r1 = np.sqrt(self.g1.rb**2 + (self.g1.rb * np.tan(self.alpha_w) + s)**2)
        r2 = np.sqrt(self.g2.rb**2 + (self.g2.rb * np.tan(self.alpha_w) - s)**2)

        # Roll angles (involute parameter u)
        u1 = np.sqrt((r1 / self.g1.rb)**2 - 1.0)  # since u = tan(alpha_r) = sqrt((r/rb)^2 - 1)
        u2 = np.sqrt((r2 / self.g2.rb)**2 - 1.0)

        # Pressure angles at those radii
        alpha_r1 = np.arctan(u1)
        alpha_r2 = np.arctan(u2)

        return {
            "s": s,
            "r1": r1,
            "r2": r2,
            "u1": u1,
            "u2": u2,
            "alpha_r1": alpha_r1,
            "alpha_r2": alpha_r2,
            "s_min": s_min,
            "s_max": s_max,
            "g_f": g_f,
            "g_a": g_a,
        }

    def rotation_for_mesh(self, n_positions: int = 120) -> Tuple[np.ndarray, float]:
        """
        Return an array of pinion rotation angles covering one base pitch (double mesh cycle).
        """
        dphi1 = self.pb / self.g1.rb  # rotation for one base pitch
        phi = np.linspace(0.0, dphi1, n_positions)
        return phi, dphi1

