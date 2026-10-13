import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel,ToothCompliance
from mechanics.transmission_error import TransmissionError
from mechanics.batched_operator import BatchedGapOperator

@pytest.mark.parametrize('variant',['legacy','shear-G','projected-energy','centerline-energy'])
@pytest.mark.parametrize('theta,torque',[(np.array([.02,.75,.005,.25]),100),
                                      (np.array([.04,.6,.012,.4]),300)])
def test_batched_contact_matches_original(variant,theta,torque):
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    model=GearContactModel(pair,TipRelief(),compliance_variant=variant)
    ref=TransmissionError(model).compute_cycle(torque,60,theta1=theta)
    fast=BatchedGapOperator(model,torque,60).evaluate(theta,jacobian=True)
    np.testing.assert_allclose(fast['prediction'],ref['TE_lin_fluct'],atol=3e-12,rtol=0)
    assert fast['force_residual_N']<2e-8
    assert np.min(fast['separations'])>-3e-12
    assert np.max(np.abs(fast['forces']*fast['separations']))<2e-8

def test_implicit_contact_tangent():
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    op=BatchedGapOperator(GearContactModel(pair,TipRelief()),100,120)
    theta=np.array([.02,.75,.005,.4]);scale=np.array([.05,1,.01,1])
    J=op.evaluate(theta,jacobian=True)['jacobian']*scale
    for j in range(4):
        v=np.zeros(4);v[j]=scale[j]*1e-5
        fd=(op.evaluate(theta+v)['prediction']-op.evaluate(theta-v)['prediction'])/2e-5
        np.testing.assert_allclose(J[:,j],fd,atol=2e-9,rtol=3e-4)

@pytest.mark.parametrize('theta', [np.array([.02,.75,.005,.25]),np.array([.04,.6,.012,.4])])
def test_lambert_force_inverse_matches_iterative(theta):
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    model=GearContactModel(pair,TipRelief())
    a=BatchedGapOperator(model,300,120,'iterative').evaluate(theta,jacobian=True)
    b=BatchedGapOperator(model,300,120,'lambert').evaluate(theta,jacobian=True)
    np.testing.assert_allclose(a['prediction'],b['prediction'],atol=3e-12,rtol=0)
    np.testing.assert_allclose(a['jacobian'],b['jacobian'],atol=3e-9,rtol=3e-5)

def test_shear_modulus_change_has_predicted_compliance_increment():
    g=InvoluteGear(24,3,20,20)
    legacy=ToothCompliance(g);corrected=ToothCompliance(g,'shear-G')
    u=np.array([.5]);r=g.rb*np.sqrt(1+u[0]**2);fix=max(g.rf,g.rb*1.0001);h=r-fix
    x,w=legacy._quadrature;x=.5*h*(x+1);w=.5*h*w
    A=np.array([g.b*legacy._section_at_radius(fix+t)[0] for t in x])
    increment=1.2*np.sum(w/A)*(1/corrected.G-1/g.E)
    np.testing.assert_allclose(corrected.flexibility(u)-legacy.flexibility(u),increment,rtol=1e-12)

def test_arbitrary_phase_samples_match_scalar_contact():
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    model=GearContactModel(pair,TipRelief());theta=np.array([.02,.75,.005,.4])
    phi=np.array([.017,.041,.153])
    result=BatchedGapOperator(model,100,phi_positions=phi).evaluate(theta)
    solver=TransmissionError(model).solver
    original=[solver.solve_position(p,100,theta1=theta)['delta'] for p in phi]
    np.testing.assert_allclose(result['delta'],original,atol=3e-12,rtol=0)
