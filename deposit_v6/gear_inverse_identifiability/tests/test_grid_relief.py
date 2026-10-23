"""Tests for the non-parametric GridRelief and the grid-Jacobian path."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from geometry.microgeometry import TipRelief, GridRelief
from geometry.involute import InvoluteGear, GearPair
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator


def test_grid_relief_interpolation_and_jacobian():
    g = GridRelief(n_nodes=11)
    theta = np.linspace(0.0, 0.02, 11)
    s = np.linspace(0.0, 1.0, 51)
    h = g.evaluate(s, theta)
    assert np.allclose(h, np.interp(s, g.grid, theta))
    J = g.jacobian(s, theta)
    assert J.shape == (51, 11)
    # Row sums of hat functions are one where the value is not clamped.
    assert np.allclose(J.sum(axis=1), 1.0)
    # Finite-difference check on an interior point.
    s0 = np.array([0.37])
    j0 = g.jacobian(s0, theta)[0]
    eps = 1e-8
    h0 = g.evaluate(s0, theta)[0]
    fd = np.array([(g.evaluate(s0, theta + eps * e)[0] - h0) / eps
                   for e in np.eye(11)])
    assert np.allclose(fd, j0, atol=1e-8)
    # Outside the grid the interpolant is clamped to the end value, so the
    # sensitivity is concentrated on the boundary node.
    out = g.jacobian(np.array([-0.1, 1.2]), theta)
    assert out[0, 0] == 1.0 and np.all(out[0, 1:] == 0.0)
    assert out[1, -1] == 1.0 and np.all(out[1, :-1] == 0.0)
    with pytest.raises(ValueError):
        g.evaluate(np.array([0.5]), np.zeros(5))


def test_operator_grid_jacobian_matches_finite_differences():
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    grid = GridRelief(n_nodes=15)
    model = GearContactModel(pair, micro1=grid, compliance_variant='projected-energy')
    op = BatchedGapOperator(model, 300.0, 40)
    rng = np.random.default_rng(7)
    h = 0.004 * rng.random(15) ** 2
    r = op.evaluate(h, jacobian=True)
    J = r['jacobian']
    assert J.shape == (40, 15)
    # Finite-difference check on three columns.
    for col in [0, 7, 14]:
        eps = 1e-7
        h2 = h.copy(); h2[col] += eps
        r2 = op.evaluate(h2)
        fd = (r2['prediction'] - r['prediction']) / eps
        assert np.allclose(J[:, col], fd, rtol=1e-5, atol=1e-5)


def test_grid_truth_reproduces_tip_relief_forward():
    pair = GearPair(InvoluteGear(24, 3, 20, 20), InvoluteGear(48, 3, 20, 20))
    theta = np.array([0.02, 0.75, 0.005, 0.40])
    grid = GridRelief(n_nodes=81)
    h_truth = TipRelief().evaluate(grid.grid, theta)
    m_tip = GearContactModel(pair, micro1=TipRelief(), compliance_variant='projected-energy')
    m_grid = GearContactModel(pair, micro1=grid, compliance_variant='projected-energy')
    op_tip = BatchedGapOperator(m_tip, 300.0, 60)
    op_grid = BatchedGapOperator(m_grid, 300.0, 60)
    r_tip = op_tip.evaluate(theta)
    r_grid = op_grid.evaluate(h_truth)
    # Piecewise-linear vs quadratic relief: expect a small but nonzero
    # forward difference; far below the noise floor of 0.1 um.
    diff_mm = np.max(np.abs(r_tip['prediction'] - r_grid['prediction']))
    assert diff_mm * 1000 < 0.05
