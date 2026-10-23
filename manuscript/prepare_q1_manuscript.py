"""Prepare an evidence-based next revision, preserving the earlier draft."""
import json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent

def main():
    old=(BASE/'revised_manuscript.md').read_text(encoding='utf-8')
    intro=old.split('## 1 Introduction\n\n')[1].split('\n\n## 2 Gear')[0]
    intro=intro.replace("Shi and Cheng discuss limitations in inferring individual deviations from a pair's TE [39].",
                         'Recent vibration-based inverse work identifies mesh stiffness and corrects mapping uncertainty [39]; its unknown and observable differ from profile reconstruction using quasi-static TE.')
    intro=intro.replace('and an audited load-information comparison with a fixed observation count.',
                         'a transition map from invisible to active dedendum relief; profile likelihood; and load comparisons with a fixed observation count.')
    intro=intro.replace('Global uniqueness, a statistically resolved noise threshold and experimental reconstruction accuracy are not claimed.',
                         'The numerical experiments characterize a specified observation operator; the external comparison separately tests its mechanical fidelity.')
    intro=re.sub(r'The contributions are:.*',
        'The contribution is a contact-support account of exact invisible relief sets and the weak transition as relief enters the loaded flank. An implicit contact tangent connects this mechanism with local information; nonlinear profiles and noise experiments test when that local account predicts recovery. Equal-budget load comparisons, initialization and bound diagnostics, and geometrical contact-support tests delimit what can be inferred from a response fit. Mechanical fidelity is assessed separately against finite-element peak-to-peak targets.',intro)
    text='''# Contact support and practical identifiability of spur gear microgeometry from transmission error

Romulo Sandoval Flórez¹; Claudia Patricia Parra Medina²; German Leandro Vargas Fonseca².

¹ Universidad ECCI. ² Grupo GAV, Universidad Militar Nueva Granada.

Corresponding author: Romulo Sandoval Flórez, romulo@ecci.edu.co.

## Abstract

Transmission-error fitting can conceal uncertainty in gear profile reconstruction when relief penetrates only marginally into the loaded flank. A quasi-static contact model with four profile parameters establishes a sufficient support condition for exact relief invisibility. Implicit sensitivities, nonlinear profiles and a dedendum-start sweep separate invariant parameter sets from a weak transition with nonzero sensitivity. The dedendum-induced RMS response is zero for sampled starts from 0.20 to 0.23, 0.00057 micrometre at 0.25 and 0.079 micrometre at 0.40. With 120 observations at 300 Nm and noise of 0.1 micrometre, 100 realizations give median scaled dedendum errors of 0.394 and 0.106 for the latter two starts. At 0.25, profiles are nearly flat over the entire tested domains because optimization can approach exactly invisible sets. At 0.40, the weakest-direction Fisher median of 0.1059 agrees with the projected Monte Carlo median of 0.1075. Equal-budget comparison with 50/300 Nm shows no demonstrable two-load advantage. All 48 mechanical benchmark comparisons have positive peak-to-peak error; replacing the shear denominator by G alone increases relative discrepancies to 38.6–105.5%. These results connect relief observability with contact support while retaining forward-model fidelity as a limit on physical reconstruction.

Keywords: Gear microgeometry; Transmission error; Contact support; Identifiability; Profile likelihood; Inverse problems

Highlights

- Relief visibility depends on penetration into the loaded part of the flank
- Contact support supplies a sufficient condition for exact relief invisibility
- Implicit contact sensitivities support nonlinear uncertainty diagnostics
- Noise comparisons use 100 realizations and a fixed observation budget
- Mechanical ablations expose persistent external response discrepancies

## 1 Introduction

INTRO

## 2 Geometry and mechanical model

### 2.1 Profile coordinates

An involute spur pair has tooth numbers z₁ and z₂, module m, reference pressure angle α, width b and centre distance a [2]. Pair index k denotes a potential tooth pair, sample index i denotes angular position and load index ℓ denotes torque. The line-of-action coordinate of pair k is ℓₖ=r_b1 φ+k p_b, measured from the working pitch point. Its nominal contact window is [−g_f,g_a]. The relief coordinate is ξ=clip(u/u_tip,0,1), with u=tan(αᵣ); it runs from the base circle to the tip rather than from the start of active profile. Reported start positions therefore depend on this coordinate convention.

The pinion relief is θ=(C_a,s_a,C_d,s_d), with depths in millimetres and dimensionless start positions. Positive relief increases normal separation. The wheel is unmodified except in the external comparison. Quadratic relief uses p=2; the benchmark uses p=1 on both gears.

EQ: profile (1)

Here [x]₊=max(0,x). Zero C_d makes s_d exactly redundant. With C_d>0, relief may still be invisible when its support is unloaded. This distinction is central to the experiments below.

### 2.2 Contact and compliance

Both gears have E=210000 MPa and ν=0.30. Each potential pair has one effective normal contact, pair compliance cₖ=c₁ₖ+c₂ₖ, force pₖ and residual separation wₖ. The contact problem is

EQ: gaps (2)

EQ: complementarity (3)

EQ: torque equilibrium (4)

The extension of the nominal contact window in equation (2) approximates corner separation. The local contact reduction follows elastic-contact theory [3,35] and the role of contact elasticity in gear models [12]. Bending, shear and foundation assumptions also influence load sharing [8,13]. The baseline radial beam uses 24-point Gauss–Legendre integration, a thickness floor 0.2m and root constraint r_fix=max(r_f,1.0001r_b). At negligible beam height its compliance is 10⁻⁶ mm/N. Its implemented law is retained as a baseline for reproducible comparisons:

EQ: baseline compliance (5)

EQ: area and inertia (6)

The baseline shear denominator E is mechanically incomplete. Three analytical ablations test it: replacing E by G; adding force projection, axial compression and the offset bending arm; and using centre-line coordinates and horizontal section thickness. In the radial energy variant, M(x)/P=(H−x)cos(αᵣ)−t_contact sin(αᵣ)/2 and

EQ: energy compliance (11)

The centre-line variant uses β(r)=t_arc(r)/(2r), y=r cosβ, x_contact=r_contact sinβ_contact and normal-force angle αᵣ−β_contact. Its integration includes dy/dr=cosβ+tan(αᵣ)sinβ. These variants share the simple foundation term and do not generate a tool fillet or resolve body coupling. They are ablations of the beam approximation, not implementations of the complete ISO method [40] or independent finite-element models. No compliance factor is fitted to the external targets.

The local Hertz approximation uses E*⁻¹=(1−ν₁²)/E₁+(1−ν₂²)/E₂ and ρₑ=ρ₁ρ₂/(ρ₁+ρ₂):

EQ: Hertz approach (7)

The logarithm is clipped at a ratio of one. Its derivative is [2log(4ρₑ/a_H)−2]/(πE*b) on the unclipped branch, and −1/(πE*b) on the clipped branch. The unclipped slope tends to −2/(πE*b) at the clipping boundary. The complete pair approach cₖp+w_H(p) is strictly increasing whenever cₖ>2/(πE*b); this condition is satisfied by every valid pair in the stated geometries and is checked by the operator.

### 2.3 Observation and inverse objective

The observable F_ℓi(θ) is rigid-body approach with its cycle mean removed. Independent noise is added after centring, with no second centring of observations. Thus a realized noise mean contributes to residual cost but does not alter parameter gradients. Encoder synchronization and angular sampling matter when applying this observable to measured data [20].

EQ: observations (8)

A separately centred noisy observation would have covariance σ²(I−11ᵀ/N); that pipeline requires projection onto the centred subspace. The present independent-noise experiment uses the stated uncentred noise model. Nominal parameter bounds are C_a∈[0,0.100] mm, s_a∈[0.30,0.95], C_d∈[0,0.050] mm and s_d∈[0.05,0.50]. The scale vector is s=(0.05,1,0.01,1), with q=θ/s. Bound-constrained TRF least squares is implemented with SciPy [34,38]:

EQ: inverse objective (9)

No Tikhonov penalty is applied. Regularization [30,31] and Bayesian inversion [32] provide possible extensions, but bounds alone do not make an unobserved relief identifiable. Synthetic observations generated and inverted with the same operator constitute an inverse crime: they measure internal recovery and noise sensitivity, not physical reconstruction accuracy. The external comparison tests the forward response separately. Controlled compliance cross-inversions are also reported as model perturbations [33].

## 3 Contact support and sensitivities

### 3.1 A sufficient invisibility condition

Take the zero-dedendum solution at fixed contact coordinates, addendum relief and compliance. If every loaded contact satisfies ξ≥s_max, then any C_d≥0 with s_d≤s_max contributes zero relief at all loaded points and only increases gaps at unloaded points. The original forces and approach satisfy the modified contact equations and torque equilibrium. Under the certified monotonicity condition above, each force pₖ(δ) is continuous and nondecreasing, and their sum is strictly increasing wherever it is positive. Positive applied force therefore selects a unique approach and unique pair forces. The modified TE is identical.

This is a sufficient statement for the declared gap operator. A continuous-cycle result requires the support condition at every phase; finite-grid verification establishes only its sampled counterpart. Changes in physical section stiffness due to removed material lie outside its hypotheses. The result does not apply automatically to the nominal s_d=0.25, where loaded points extend below that coordinate.

### 3.2 Implicit contact tangent

For a fixed active set A, differentiate the loaded-pair compatibility equations and torque equilibrium. The approach derivative is

EQ: implicit derivative (12)

The prediction Jacobian is this derivative with its angular mean removed. Contact forces and active sets are solved again at every evaluation; the geometry cache stores neither. The derivative is piecewise valid away from contact switches, where one-sided or generalized derivatives may be needed. Comparisons against central finite differences and the original scalar contact solver verify the implementation. Vectorized safeguarded Newton steps solve all angular positions together, with per-pair force brackets bounded by total applied force.

The scaled whitened Jacobian J_q=σ⁻¹(∂F/∂θ)diag(s) gives information matrix

EQ: information (10)

We use direct SVD and rank tolerance 10⁻⁷ relative to the largest singular value. Local identification [22], structural identifiability [23], comparisons of structural methods [6,24], and weak sensitivity spectra [25] motivate separating rank from practical precision. A Fisher condition number refers to κ(𝓘_q)=κ(J_q)², not κ(J_q). No eigenvalue floor fills a null direction.

### 3.3 Profile likelihood and fixed sampling budget

For each selected parameter value v, we minimize the same noise-weighted objective over the remaining coordinates:

EQ: profile likelihood (13)

Profiles [5,26] test nonlinear ambiguity rather than relying only on local covariance. Three starts are used per profile point: the unrestricted estimate and two fixed guesses. The horizontal Δχ²=3.841 reference is a nominal Wilks diagnostic; bounds and weak directions may invalidate its coverage interpretation.

D- and E-optimality [4,27,28] are evaluated at a fixed total of 120 samples. Single loads receive 120 positions; paired loads receive 60 each. A repeated 100/100 Nm design controls for replication. Conditional addendum information uses a common basis (e₁,e₂), holding dedendum fixed. It differs from marginal information when dedendum is unknown. Bayesian design [29] could account for uncertain true relief; the present design comparisons are local diagnostics at specified truths.

## 4 Numerical experiments

### 4.1 Mechanical fidelity and angular sampling

The nominal pair has z₁=24, z₂=48, m=3 mm, α=20° and b=20 mm. Torque-equilibrium and complementarity checks establish numerical consistency. Angular RMS convergence is distinct from peak-to-peak and derivative convergence; contact-transition peaks require their own refinement study.

The external reference is Korta and Mundo [1]. Its university-hosted author manuscript specifies z₁=z₂=57, m=2.6 mm, α=20°, b=23 mm, a=150 mm, tip/root diameters 154.50/141.70 mm, circular thickness 3.78 mm and tool-radius coefficient 0.555. The working pressure angle and contact ratio are calculated from those dimensions. Stored profile shift is zero; the explicit tip diameter and thickness override the standard tooth dimensions and do not reconstruct a manufacturing tool setting.

The three modified cases are defined by (depth µm, start radius mm): Sol1=(16.3,74.134), Sol2=(15.4,74.402), Sol3=(13.4,74.190). Linear roll-distance relief on both gears is mapped by s_a=√[(r_t/r_b)²−1]/√[(r_a/r_b)²−1]. Translation of the roll-distance origin preserves the physical start radius and normalized ramp. The FE-based targets are from Tables 6–8 of Korta and Mundo's deposited author version [1], excluding surrogate predictions. We adopt a 5% peak-to-peak research target; this threshold is neither a journal acceptance rule nor an ISO validation tolerance.

Q1_BENCHMARK

Q1_ANGULAR

### 4.2 Transition from invisible to active dedendum

We hold C_a=0.020 mm, s_a=0.75 and C_d=0.005 mm, and sweep s_d from 0.20 to 0.50 in steps of 0.01 at 100 Nm with 240 positions. The dedendum signal is the RMS difference against C_d=0 at the same addendum settings. Two starting guesses, (0.030,0.65,0.010,0.35) and (0.015,0.85,0.020,0.45), are fixed independently of truth. Recovery errors are normalized by the declared scales. This experiment tests whether the original marginal-support truth represents the whole domain.

Q1_TRANSITION

### 4.3 Nonlinear uncertainty and noise recovery

Profiles and Monte Carlo experiments compare one 300 Nm load with the pair 50/300 Nm, both at 120 observations. Truths use s_d=0.25 and 0.40 with the same depths and addendum start. Profiles use σ=0.1 µm and seed 20261012. The uniform profile grids have 46 start values from 0.05 to 0.50 (step 0.01) and 41 depth values from 0 to 50 µm (step 1.25 µm). Each Monte Carlo cell has 100 independent Gaussian realizations at σ=0.1,0.5 or 1.0 µm. Both fixed starts are fitted; the smaller objective is selected, and convergence status is retained. Designs share seed indices as common random numbers for paired comparison, while realizations remain independent across seeds.

Metrics separate addendum and dedendum scaled maximum error, full-flank profile RMS on 1001 coordinates, fit residual and prediction RMS on a held-out 200 Nm, 240-position curve. The retained-load test uses noise-free synthetic truth and measures transfer inside the same model class. Simulation σ values are instrument-noise scenarios, not estimates of the external model discrepancy.

Q1_PROFILES

Q1_MONTE_CARLO

### 4.4 Load spectra and other geometries

Q1_SPECTRA

The fixed-budget conditional addendum score increases with torque: the single 300 Nm value is 26.3587, exceeding the 200/300 Nm pair value 25.9955. Replication at 100/100 Nm is nearly equal to a single 100 Nm cycle. This monotone ranking mainly rewards the highest torque within the tested range. The 50/300 Nm pair spends half its budget at a lower-sensitivity load; it therefore tests that specific allocation, rather than all possible two-load designs. Full spectra and nonlinear recovery determine whether the weak dedendum direction benefits.

Q1_GEOMETRIES

Controlled M3/M3b cross-inversions share geometry and Hertz contact with the baseline. M3 assigns a constant derived from mean baseline approach divided by total force; M3b scales the baseline compliance variation around its pitch-point value. Because load sharing remains nonlinear, they do not isolate a pure stiffness-wave change or constitute independent fidelity validation. Addendum and dedendum errors are therefore reported separately in the supplementary records instead of interpreting their overall maximum as uniformly poor recovery.

## 5 Discussion and limitations

The transition map connects relief visibility to loaded support. At the marginal nonzero-relief truth, numerical rank four and a nonzero noiseless signal coexist with nearly flat finite-noise profile objectives. Profiling can move through structurally invisible subsets (C_d=0 or unloaded dedendum support), so the experiment does not resolve the dedendum coordinates across their tested domains. This is practical non-identifiability with access to exact invariant parameter sets; a flat noisy profile alone does not establish structural non-identifiability at the nominal nonzero-sensitivity truth. Deeper penetration changes the result: local Fisher and Monte Carlo agree at low noise, while bounded and nonlinear behaviour becomes material as noise increases.

Mechanical fidelity limits the scope of this inverse result. Baseline discrepancy is systematic across the external peak-to-peak targets. Physically motivated compliance changes do not eliminate it, so retaining a baseline because it agrees better cannot be interpreted as validating its incorrect shear law. Root fillet, gear-body coupling, exact corner contact, relief-induced section changes and boundary conditions require independent evidence. Peak-to-peak error alone does not determine waveform residual covariance and cannot simply be substituted for σ. An independently generated contact/TE dataset with known geometry, load sharing and sufficient angular resolution is needed before physical parameter-recovery claims.

The present scope is quasistatic, ideal involute spur gears with profile-only gaps and a nominal section. It omits lead variation, mounting error, shafts, housing, lubrication and dynamics. Profile thresholds have no demonstrated coverage near degeneracy, and fixed multistart search does not prove global optimization. Statistical summaries include failed optimizations rather than removing them.

## 6 Conclusions

Loaded contact support controls whether a dedendum modification can influence transmission error in the fixed-compliance gap model. Exact invisible sets coexist with weak but nonzero sensitivities when relief only marginally enters the loaded region. The dedendum-start sweep demonstrates this transition and prevents extrapolating the original nominal ambiguity to every relief configuration.

An implicit contact tangent, nonlinear profiles and equal-budget noise experiments provide a reproducible way to separate response fitting from profile recovery. Parameter-block errors and retained-load predictions are more informative than a single maximum relative error. Load ranking must be interpreted jointly with the weak sensitivity direction and the observation budget.

The external comparison limits physical reconstruction. Correcting the shear denominator alone worsens the systematic peak-to-peak discrepancy; force projections and centre-line geometry reduce part of that increase but do not establish benchmark agreement. Local angular refinement is consistent with narrow continuous contact transitions; external waveform and stiffness data are required to determine whether their shape and plateau levels reproduce the mechanical response.

## Declarations

Declaration of competing interest. The authors declare that they have no competing financial interests or personal relationships that could have influenced the work reported in this article.

Declaration of generative AI use. During preparation of this work, the authors used AI tools to assist with code inspection, numerical analysis and manuscript drafting. The authors reviewed the content and take full responsibility for the scientific accuracy and integrity of the article.

Author contributions. Romulo Sandoval Flórez, Claudia Patricia Parra Medina and German Leandro Vargas Fonseca reviewed the manuscript and take responsibility for its content. Individual CRediT role allocation remains to be supplied.

Data availability. Source code, experiment settings, numerical records and figure-generation scripts are prepared for deposit. Public repository URL and persistent identifier: to be supplied.

Funding. This research received no funding from any entity.

## References

REFERENCES_40
'''.replace('INTRO',intro)
    # Clean inline symbols without changing numeric arrays or DOI strings.
    replacements={'r_b1':'rᵦ₁','p_b':'pᵦ','g_f':'g_f','g_a':'g_a','u_tip':'u_tip',
                  'C_a':'Cₐ','C_d':'C_d','s_a':'sₐ','s_d':'s_d','r_fix':'r_fix',
                  'r_f':'r_f','r_b':'rᵦ','r_t':'r_t','r_a':'rₐ','J_q':'J_q','𝓘_q':'𝓘_q'}
    # Keep basic subscripts legible in prose; display equations are native OMML.
    for a,b in replacements.items():text=text.replace(a,b)
    numbering={11:7,7:8,8:9,9:10,12:11,10:12}
    text=re.sub(r'(EQ: [^\n]*?)\((\d+)\)',lambda m:m[1]+'('+str(numbering.get(int(m[2]),int(m[2])))+')',text)
    refs=json.loads((ROOT/'referencias_40_seleccionadas.json').read_text(encoding='utf-8'))
    refs[38]=dict(title=['Inverse modeling with physical constraints and uncertainty correction for mesh stiffness identification in gear crack fault'],
                 author=[dict(given=g,family=f) for g,f in [('Bo','Zhang'),('Wei','Teng'),('Dikang','Peng'),('ShaoFeng','Han'),('Yibing','Liu')]],
                 **{'container-title':['Mechanical Systems and Signal Processing']},year=2026,volume='250',page='114142',
                 DOI='10.1016/j.ymssp.2026.114142',url='https://www.sciencedirect.com/science/article/pii/S0888327026002992')
    for i in [8,16]:refs[i]['title']=[refs[i]['title'][0].capitalize()]
    for ref in refs:
        for author in ref.get('author',[]):
            if author.get('family','').isupper():author['family']=author['family'].title()
    refs[20]['title']=[re.sub(r'^419\s*','',refs[20]['title'][0]).capitalize()]
    refs[35]['title']=[refs[35]['title'][0].replace('trasnsmission','transmission')]
    order=[]
    for match in re.finditer(r'\[([0-9, ]+)\]',text):
        nums=[int(n) for n in match[1].replace(' ','').split(',')]
        if 0 in nums:continue
        for n in nums:
            if n not in order:order.append(n)
    assert set(order)==set(range(1,41)),set(range(1,41))-set(order)
    mapping={old:i+1 for i,old in enumerate(order)}
    def relabel(match):
        nums=[int(n) for n in match[1].replace(' ','').split(',')]
        if 0 in nums:return match[0]
        return '['+','.join(str(mapping[n]) for n in nums)+']'
    text=re.sub(r'\[([0-9, ]+)\]',relabel,text)
    (BASE/'q1_manuscript.md').write_text(text,encoding='utf-8')
    (ROOT/'referencias_40_q1.json').write_text(json.dumps([refs[n-1] for n in order],ensure_ascii=False,indent=2),encoding='utf-8')
    (BASE/'q1_reference_mapping.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    print('Prepared manuscript and 40 references in order of first appearance')

if __name__=='__main__':main()
