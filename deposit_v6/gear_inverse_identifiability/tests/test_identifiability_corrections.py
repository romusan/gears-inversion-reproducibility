import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
import pytest
from geometry.microgeometry import TipRelief
from identifiability.fisher_optimal_loads import FisherLoadSelector
from inverse.reconstruction import InverseReconstructor

class ToyTE:
    def compute_cycle(self, torque_Nm, n_positions, theta1, theta2=None):
        phase = 2*np.pi*np.arange(n_positions)/n_positions
        return {'TE_lin_fluct': theta1[0]*np.sin(phase) + theta1[1]*np.cos(phase)}

@pytest.mark.parametrize('power',[1.0,2.0,3.0])
def test_relief_derivatives_against_perturbations(power):
    model=TipRelief(p=power)
    s=np.array([0.02,0.1,0.8,0.9,1.0])
    theta=np.array([0.02,0.75,0.005,0.25])
    numeric=np.zeros((s.size,4))
    for j in range(4):
        dp=np.zeros(4);dp[j]=1e-7
        numeric[:,j]=(model.evaluate(s,theta+dp)-model.evaluate(s,theta-dp))/(2e-7)
    np.testing.assert_allclose(model.jacobian(s,theta),numeric,rtol=1e-6,atol=1e-10)

def test_equal_budget_and_repeated_load_have_equal_information():
    selector=FisherLoadSelector(ToyTE(),[1,1],parameter_scale=[2,3],sigma_mm=0.1)
    np.testing.assert_allclose(selector.fisher_matrix([100],120),selector.fisher_matrix([50,300],120),rtol=1e-10,atol=1e-6)
    np.testing.assert_allclose(selector.fisher_matrix([100,100],120),selector.fisher_matrix([50,300],120),rtol=1e-10,atol=1e-6)
    assert selector.diagnostics([50,300],120)['n_observations']==120

def test_rank_deficient_design_does_not_invent_information():
    selector=FisherLoadSelector(ToyTE(),[1,1,1],parameter_scale=[1,1,1])
    diagnostic=selector.diagnostics([50,300],120)
    assert diagnostic['rank']==2
    assert diagnostic['logdet']==-np.inf
    assert diagnostic['min_eigenvalue']==0
    assert diagnostic['condition_F']==np.inf
    reduced=selector.diagnostics([50,300],120,subspace=np.eye(3)[:,:2])
    assert reduced['rank']==2 and np.isfinite(reduced['logdet'])

def test_coordinate_scaling_invariance_of_scaled_information():
    class UnitTE(ToyTE):
        def compute_cycle(self, torque_Nm, n_positions, theta1, theta2=None):
            return super().compute_cycle(torque_Nm,n_positions,np.array(theta1)/[1000,1])
    a=FisherLoadSelector(ToyTE(),[1,1],parameter_scale=[2,3])
    b=FisherLoadSelector(UnitTE(),[1000,1],parameter_scale=[2000,3])
    np.testing.assert_allclose(a.fisher_matrix([100],120),b.fisher_matrix([100],120),rtol=1e-9,atol=1e-9)

def test_heteroscedastic_weights_change_the_estimator():
    class ConstantTE:
        def compute_cycle(self,torque_Nm,n_positions,theta1,theta2=None):
            return {'TE_lin_fluct':np.full(n_positions,theta1[0])}
    recon=InverseReconstructor(ConstantTE(),[100],np.array([[-10,10]]),n_positions_forward=2,
                               observation_sigma_mm=[1,3])
    result=recon.reconstruct(np.array([0.,2.]),theta0=np.array([1.]))
    assert result['theta'][0]==pytest.approx(0.2,abs=1e-6)

def test_invalid_subspace_and_noise_rejected():
    with pytest.raises(ValueError): FisherLoadSelector(ToyTE(),[1,1],sigma_mm=0)
    with pytest.raises(ValueError): FisherLoadSelector(ToyTE(),[1,1]).diagnostics([100],subspace=np.ones((2,2)))

def test_compliance_cache_preserves_cold_results():
    from geometry.involute import InvoluteGear
    from mechanics.compliance import ToothCompliance
    model=ToothCompliance(InvoluteGear(z=24,m=3,alpha_deg=20,b=20))
    rolls=np.array([0.0,0.1,0.3,0.5])
    cold=model.flexibility(rolls)
    warm=model.flexibility(rolls)
    model._flexibility_cache.clear()
    fresh=model.flexibility(rolls)
    np.testing.assert_array_equal(cold,warm)
    np.testing.assert_array_equal(cold,fresh)

def test_benchmark_tooth_thickness_does_not_change_nominal_defaults():
    from geometry.involute import InvoluteGear
    default=InvoluteGear(z=57,m=2.6,alpha_deg=20,b=23)
    specified=InvoluteGear(z=57,m=2.6,alpha_deg=20,b=23,pitch_thickness_mm=3.78)
    assert default.tooth_thickness_at_radius(default.r)==pytest.approx(np.pi*2.6/2)
    assert specified.tooth_thickness_at_radius(specified.r)==pytest.approx(3.78)
    assert default.rb==specified.rb and default.ra==specified.ra
    with pytest.raises(ValueError):InvoluteGear(z=57,m=2.6,alpha_deg=20,b=23,pitch_thickness_mm=-1)

def test_inactive_relief_preserves_contact_solution():
    from geometry.involute import InvoluteGear,GearPair
    from mechanics.compliance import GearContactModel
    from mechanics.transmission_error import TransmissionError
    pair=GearPair(InvoluteGear(z=24,m=3,alpha_deg=20,b=20),InvoluteGear(z=48,m=3,alpha_deg=20,b=20))
    te=TransmissionError(GearContactModel(pair,micro1=TipRelief(p=2),linearize_hertz=False))
    for torque in [100,300]:
        base=te.compute_cycle(torque,60,np.array([.020,.75,0,.15]))
        u_tip=np.sqrt((pair.g1.ra/pair.g1.rb)**2-1)
        for state,force in zip(base['states'],base['forces']):
            xi=state['u1']/u_tip
            assert np.all(xi[np.asarray(force)>1e-6]>=.15)
        changed=te.compute_cycle(torque,60,np.array([.020,.75,.04,.15]))
        np.testing.assert_allclose(base['TE_lin_fluct'],changed['TE_lin_fluct'],atol=1e-11,rtol=0)

def test_hertz_compliance_derivative_including_clipped_branch():
    from mechanics.compliance import HertzianContact
    h=HertzianContact(210e3,.3,210e3,.3,20)
    forces=np.array([100,300,1000.])
    radii=np.array([2.,10.,1e-6])
    step=forces*1e-5
    derivative=(h.approach(forces+step,radii)-h.approach(forces-step,radii))/(2*step)
    np.testing.assert_allclose(h.stiffness_derivative(forces,radii),derivative,rtol=1e-8,atol=1e-14)

def test_vectorized_point_solver_matches_scalar_root():
    from geometry.involute import InvoluteGear,GearPair
    from mechanics.compliance import GearContactModel
    from mechanics.contact_solver import ContactSolver
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    solver=ContactSolver(GearContactModel(pair,linearize_hertz=False))
    gaps=np.array([0.,.005,.007]);compliance=np.array([1e-6,3e-6,2e-6]);radius=np.array([2.,10.,1e-6])
    _,vector=solver._forces_for_delta(gaps,compliance,radius,.02)
    scalar=np.array([solver._solve_point_force(g,c,r,.02) for g,c,r in zip(gaps,compliance,radius)])
    np.testing.assert_allclose(vector,scalar,rtol=1e-10,atol=1e-8)

def test_scaled_central_reconstruction_respects_physical_bounds():
    class BoundedTE(ToyTE):
        def compute_cycle(self,torque_Nm,n_positions,theta1,theta2=None):
            assert np.all(np.asarray(theta1)>=0) and np.all(np.asarray(theta1)<=1)
            return super().compute_cycle(torque_Nm,n_positions,theta1,theta2)
    obs=ToyTE().compute_cycle(100,20,np.array([-.2,.8]))['TE_lin_fluct']
    recon=InverseReconstructor(BoundedTE(),[100],np.array([[0.,1.],[0.,1.]]),n_positions_forward=20)
    result=recon.reconstruct(obs,theta0=np.array([0.,.4]),jacobian_scheme='scaled-central')
    np.testing.assert_allclose(result['theta'],[0,.8],atol=1e-7)
    assert result['success']
