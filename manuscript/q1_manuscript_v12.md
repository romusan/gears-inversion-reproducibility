# Contact support and practical identifiability of spur gear microgeometry from transmission error

Romulo Sandoval Flórez¹; Claudia Patricia Parra Medina²; German Leandro Vargas Fonseca².

¹ Universidad ECCI. ² Grupo GAV, Universidad Militar Nueva Granada.

Corresponding author: Romulo Sandoval Flórez, romulo@ecci.edu.co.

## Abstract

Transmission error constrains gear microgeometry through the part of the flank that carries load. We establish a sufficient condition under which dedendum relief is exactly invisible to a quasistatic contact operator with fixed geometry and compliance, and extend the argument to coupled elastic contact. An implicit contact tangent relates this invariance to parameter sensitivities and to the resolution of a discretized relief field. Nonlinear profiles and noise experiments distinguish exact invariance from weak practical identifiability as relief enters loaded support. For the nominal pair, the median scaled dedendum error decreases from 0.394 to 0.106 when the relief start moves deeper into contact, using 100 realizations, 120 observations, 300 Nm and 0.1 µm Gaussian noise. Equal-budget controls reveal angular-sampling effects and no statistically resolved benefit of the tested two-load allocation. A finite-element contact comparison isolates a dedendum signal of 0.179 µm RMS, close to the analytical 0.197 µm. Nevertheless, an addendum-only inverse attains the same residual as the unrestricted fit, and dedendum profiles remain flat across their tested domains. Interface and angular-mask controls delimit the discretization dependence. A separate eight-phase material-removal control gives approximately 0.4–2.1 nm centred changes outside contact, delimiting exact invariance to fixed compliance. Across twelve external amplitude targets evaluated with four formulations, none meets the adopted 5% research target. These results establish operator-conditioned limits on observability and distinguish contact sensitivity from reliable geometrical recovery.

Keywords: Gear microgeometry; Transmission error; Contact support; Identifiability; Profile likelihood; Inverse problems

## 1 Introduction

Profile modifications influence gear transmission error through normal separation, elastic deformation and load sharing. Their design has been studied through classical profile synthesis, genetic algorithms and response-surface optimization [1,2,3], with standardized descriptions of modification geometry [4] and broader reviews and tolerance-design studies [5,6]. The inverse problem is different: given a measured response, which aspects of the manufactured profile are determined by that response? A small transmission-error residual is insufficient to answer this question because mechanically inactive relief can change the geometry without changing the observable.

Inverse gear analysis has several precedents. Vibration-based methods identify mesh stiffness while accounting for mapping uncertainty [7], tooth-root stresses have been used to estimate meshing transmission error [8], and inverse tooth-contact and double-flank roll-test analyses recover other geometrical quantities [9,10]. Here the unknown is a pinion profile modification and the observable is mean-removed quasistatic transmission error. Spitas et al. prescribe tooth-contact behaviour to synthesize a mating flank [9], whereas Kalligeros et al. infer geometrical deviations from double-flank radial measurements [10]. The present contribution is a pre-inversion observability diagnostic: loaded support defines invariant relief sets, a coupled-contact argument establishes their persistence under fixed elastic coupling, and contact tangents quantify the transition from exact invariance to weak information. It is not a new general framework for inverse gear analysis.

That connection is necessarily conditional on the forward mechanics. Comparisons between analytical and finite-element stiffness models [11], contact-analysis software benchmarks [12] and nonlinear formulations [13] show why response fidelity must be assessed independently. Modified-profile contact studies link relief to load sharing, stiffness and transmission error [14,15]. Sánchez et al. also synthesize relief for prescribed load-sharing or transmission-error functions [14]. Such inverse design does not establish uniqueness when a manufactured relief must be inferred from a measured, centred response. Wide-faced gears [16], mounting deviations [17] and experimental tooth-loading comparisons [18] introduce mechanisms beyond the present profile-only reduction. We therefore distinguish numerical consistency, recovery within a model and agreement with an external mechanical reference.

Structural and practical identifiability provide complementary descriptions of these limitations [19,20]. Profile likelihood [21], structural analyses [22,23], sensitivity spectra [24] and Fisher-information diagnostics [25] distinguish exact parameter invariance from finite-noise ambiguity. Applied to gear contact, these tools must also accommodate changes in the active contact set. We combine a sufficient invisibility result with an implicit contact tangent, nonlinear profiles, fixed-budget sampling comparisons and noise experiments. Finite-element contact inversions and external amplitude comparisons then delimit the mechanical interpretation of those results.

## 2 Geometry and mechanical model

### 2.1 Profile coordinates

An involute spur pair has tooth numbers z₁ and z₂, module m, reference pressure angle α, face width b and centre distance a [26]. Pair index k identifies a candidate tooth pair, i an angular observation and ℓ an applied load. The line-of-action coordinate is ℓₖ=rᵦ₁φ+k pᵦ, measured from the working pitch point, with nominal contact window [−g_f,g_a]. We describe pinion relief using ξ=clip(u/u_tip,0,1), where u=tan(αᵣ). This coordinate runs from the base circle to the tip; it is not a normalized distance from the start of active profile.

The four parameters θ=(Cₐ,sₐ,C_d,s_d) specify addendum and dedendum depths in millimetres and dimensionless start positions. Positive relief increases normal separation. The wheel is unmodified except in the external benchmark. Unless stated otherwise, the relief exponent is p=2.

EQ: profile (1)

Here [x]₊=max(0,x). At C_d=0, s_d is redundant. For C_d>0, a different source of ambiguity arises if the relief does not intersect loaded contact. We keep these two mechanisms distinct.

### 2.2 Contact and compliance

The elastic constants are E=210000 MPa and ν=0.30 for both gears. Each candidate pair has one effective normal contact, combined tooth compliance cₖ, force pₖ and residual separation wₖ. The approach δ satisfies unilateral contact and the prescribed normal-force budget:

EQ: gaps (2)

EQ: complementarity (3)

EQ: torque equilibrium (4)

The extension outside the nominal contact window in equation (2) is a separation approximation, rather than an exact corner-contact construction. Contact elasticity follows the classical elastic-contact setting [27,28] and its application to gear models [29]. Tooth bending, shear and foundation terms provide the remaining compliance [30,11]. All geometrical sections, contact coordinates and normals remain fixed when relief parameters change.

We retain four compliance formulations to assess the dependence of the results on this approximation. The baseline integrates a radial variable-section beam with 24-point Gauss–Legendre quadrature, thickness floor 0.2m and fixed radius r_fix=max(r_f,1.0001rᵦ). Its tooth compliance is

EQ: baseline compliance (5)

EQ: area and inertia (6)

The baseline shear term uses E rather than the shear modulus and is mechanically inconsistent. It serves as a reference implementation, not as a preferred constitutive law. The shear-G variant replaces that denominator by G=E/[2(1+ν)]. The radial-energy variant also resolves the normal force into transverse and axial components and includes its flank offset in the bending moment. The centre-line variant evaluates the energy along the tooth centre line. In the radial-energy formulation,

EQ: energy compliance (7)

For a beam height below 0.001m the implementation assigns compliance 10⁻⁶ mm/N. This local approximation and the foundation term remain part of the declared operator. None of these formulations reconstructs a manufactured root fillet or the section changes caused by material removal. ISO 6336-1 distinguishes tooth and mesh stiffness [31]; the incremental tangents reported here are diagnostics of the implemented contact problem, rather than complete ISO-method predictions.

The Hertz contribution uses equivalent radius ρₑ and effective modulus E*:

EQ: Hertz contact (8)

The implemented logarithm is clipped when 4ρₑ/a_H<1. With Kₖ=1/(πE*b), its derivative is bounded below by −2Kₖ. The sufficient condition cₖ>2Kₖ makes each complete pair law strictly increasing and the load-controlled solution unique. We check this condition numerically before using the batched operator. It is a property of the declared law and does not validate its high-load extrapolation.

### 2.3 Observation and inverse problem

For each load we observe F_ℓ(θ)=δ_ℓ(θ)−mean[δ_ℓ(θ)] at the selected angular positions. Encoder synchronization and angular sampling affect the measured counterpart [32]. The noise experiments add independent errors to the already centred prediction:

EQ: observations (9)

Consequently, an individual noise realization may have a nonzero mean. That component contributes to cost but not to parameter gradients. If measurements were centred after adding noise, their covariance would instead be σ²(I−11ᵀ/N), requiring a projected likelihood. The stated experiments use the independent-error convention throughout.

Bounds are Cₐ∈[0,0.100] mm, sₐ∈[0.30,0.95], C_d∈[0,0.050] mm and s_d∈[0.05,0.50]. We scale parameters by s=(0.05,1,0.01,1), write q=θ/s and solve bounded least squares with a trust-region reflective method [33,34]:

EQ: inverse objective (10)

Bounds are not evidence of observability. Regularization [35,36] or Bayesian priors [37] could select a profile in an unresolved set but would supply information beyond transmission error. Synthetic data generated and inverted with the same operator measure internal recovery, whereas cross-operator data also include mechanical discrepancy [38]. We report parameter errors, full-flank profile errors and response residuals separately.

## 3 Contact support and identifiability

### 3.1 A sufficient invisibility condition

Consider the zero-dedendum solution with addendum relief, contact coordinates and compliance fixed. Suppose every loaded pinion contact satisfies ξ≥s_max. Any nonnegative dedendum depth with s_d≤s_max leaves the gaps of loaded contacts unchanged and can only increase the gaps of unloaded candidates. The original forces and approach therefore satisfy the modified complementarity equations and force equilibrium. Under the monotonicity condition in Section 2.2, uniqueness implies identical approach and identical transmission error.

The statement is sufficient, not necessary. It applies to every phase at which its support hypothesis holds. A finite angular grid verifies only those sampled phases, and a continuous-cycle claim requires a support bound over the whole cycle. Changes in section stiffness, normals or contact coordinates caused by physical material removal lie outside the hypotheses.

Q1_COUPLED_OBSERVATION

### 3.2 Implicit contact tangent

On a fixed active contact set A, differentiating compatibility and force equilibrium gives the approach derivative

EQ: implicit derivative (11)

Subtracting its angular mean gives the prediction Jacobian. This expression is piecewise valid away from contact switches; one-sided or generalized derivatives are needed at a switch. The batched implementation caches geometry but recomputes forces and active sets at every evaluation. Comparisons with the scalar solver and central finite differences verify its response and tangent.

The scaled, whitened Jacobian is J_q=σ⁻¹(∂F/∂θ)diag(s), with information matrix

EQ: information (12)

We use direct singular-value decomposition and rank tolerance 10⁻⁷ relative to the largest singular value. The condition number of the information matrix is the squared Jacobian condition number. Null directions are retained rather than filled by an eigenvalue floor. Local rank measures first-order sensitivity [19,20,22,23,24]; finite-noise precision additionally depends on scale, bounds and nonlinearity [25].

### 3.3 Nonlinear profiles and sampling design

For each fixed parameter value v, the profile objective minimizes the same weighted residual over the remaining coordinates:

EQ: profile likelihood (13)

The nominal Δχ²=3.841 line is a visual diagnostic, not a coverage-certified threshold near a bound or an invariant set [21,25]. The same caution applies more strongly to finite-element cross-operator residuals, which contain deterministic discrepancy. For the null model C_d=0 we also fix the redundant s_d, leaving only the two addendum coordinates free.

D- and E-optimality [39,40,41] are compared at a fixed total of 120 measurements: one load receives 120 angular positions and two loads receive 60 each. Repeating a load controls for replication. Conditional addendum information holds the dedendum fixed and is distinct from information marginalized over unknown dedendum parameters. These are local designs at specified truths; design under uncertain geometry would require a broader treatment [42].

A pre-inversion diagnostic follows from these results. First solve the zero-dedendum contact problem on the intended load and phase grid and compare its loaded-support minimum with the admissible relief starts. A region satisfying the sufficient condition defines an invariant parameter set before optimization. Where support overlaps relief, inspect the scaled tangent and nonlinear profiles rather than equating nonzero rank with usable precision. Finally compare the unrestricted fit with the addendum-only model and report the complete reconstructed profile. Each step concerns the same declared mechanical operator and retained observations; physical interpretation additionally requires an independent fidelity check.

## 4 Numerical results

### 4.1 Forward response and external fidelity

The nominal pair G0 has z₁=24, z₂=48, m=3 mm, α=20° and b=20 mm. Equilibrium and complementarity tests assess solution consistency. Angular convergence is assessed separately for cycle RMS, extrema and sensitivities because contact transitions can dominate the latter two quantities.

The external amplitude reference is Korta and Mundo [1]. The symmetric 57/57 pair has m=2.6 mm, α=20°, b=23 mm, a=150 mm, tip and root diameters 154.50 and 141.70 mm, circular tooth thickness 3.78 mm and tool-radius coefficient 0.555. Explicit diameters and thickness override standard proportions without reconstructing the manufacturing tool setting. Linear relief acts on both gears. The three modified cases use depth and start radius (16.3 µm,74.134 mm), (15.4 µm,74.402 mm) and (13.4 µm,74.190 mm). We map each start radius to sₐ=√[(r_t/rᵦ)²−1]/√[(rₐ/rᵦ)²−1].

The twelve targets comprise four profiles at three torques, using the FE-derived rows of the reference Tables 6–8 rather than its surrogate predictions. Evaluating four formulations gives 48 comparisons with those same twelve targets, not 48 independent validations. The adopted 5% peak-to-peak criterion is a research target and has no status as a journal rule or standardized validation tolerance.

Q1_BENCHMARK

Q1_ANGULAR

### 4.2 Transition into loaded support

We hold Cₐ=0.020 mm, sₐ=0.75 and C_d=0.005 mm and vary s_d from 0.20 to 0.50 in increments of 0.01 at 100 Nm with 240 angular positions. The isolated dedendum signal is the RMS difference from C_d=0 at identical addendum settings. Two fixed starts, (0.030,0.65,0.010,0.35) and (0.015,0.85,0.020,0.45), are independent of the generating truth. Parameter errors use the scales in Section 2.3.

Q1_TRANSITION

### 4.3 Nonlinear uncertainty and noise recovery

We compare s_d=0.25 and 0.40 using the same depths and addendum start, at either 300 Nm or 50/300 Nm and 120 observations. The depth profile uses 41 points from 0 to 50 µm; the start profile uses 46 points from 0.05 to 0.50. Three starts per profile point comprise the unrestricted estimate and the two fixed guesses. Each of twelve Monte Carlo cells contains 100 independent Gaussian realizations at σ=0.1,0.5 or 1.0 µm. Both fixed starts are optimized and the smaller objective is retained, including its convergence status. Seed indices act as common random numbers in paired design comparisons.

The error metrics are the maximum scaled error within each relief block, profile RMS on 1001 full-flank coordinates, fit residual and prediction RMS on a noise-free held-out 200 Nm curve with 240 positions. The latter tests transfer within the same operator. These noise scenarios do not include mechanical discrepancy. To assess optimizer termination, the 65 flagged fits across the main and complementary-phase experiments were refitted from four additional starts with an increased evaluation budget. Per-cell median dedendum errors changed by at most 0.0034. This supports stability of those summaries under the tested search expansion without establishing global minimization.

Q1_PROFILES

Q1_MONTE_CARLO

### 4.4 Load and geometry dependence

Q1_SPECTRA

At fixed budget, the conditional addendum log-determinant is 26.3587 for 300 Nm and 25.9955 for 200/300 Nm. Replication at 100/100 Nm is nearly equivalent to one 100 Nm cycle. These scores concern a specified block and phase grid. Allocating half the observations to 50 Nm reduces addendum information; whether it benefits the dedendum must be assessed from its spectrum and nonlinear recovery rather than from an addendum score.

Q1_GEOMETRIES

Controlled compliance cross-inversions use the same geometry and Hertz law. One replaces the baseline by a constant derived from mean approach divided by force; another scales its variation about the pitch point. Their nonlinear load sharing prevents interpretation as pure stiffness-wave perturbations. They diagnose sensitivity to an operator change rather than furnish an independent mechanical validation. A separate gain-bias experiment likewise illustrates this distinction: at 5% unmodelled gain error, dedendum depth shifts reach 0.045 mm and start shifts reach 0.14, while addendum changes remain below 0.0024 mm and 0.012. Weak relief coordinates can absorb measurement-chain error.

### 4.5 Cross-operator contact tests

The finite-element generator uses two-dimensional plane-strain elasticity, fixed normals and frictionless unilateral contact. Relief enters as an added gap on a nominal contour; the compliance matrix is shared by the unmodified, addendum-only and combined-relief cases. This changes the elastic discretization relative to the beam operator but retains fixed sections. The tests therefore assess sensitivity and inversion across two contact operators under a shared geometrical assumption. A separate contour-modification experiment below changes the elastic domain itself. Its limited phase set and geometry differ from the gap-only inverse experiment; the two tests answer distinct questions.

Q1_CROSS_INVERSE

Q1_DISCRETIZATION_V12

### 4.6 Resolution of a discretized relief field

Q1_RESOLUTION

## 5 Discussion

Loaded support explains why a precise transmission-error fit can coexist with an uncertain profile. Outside that support, nonnegative gap relief satisfying the sufficient condition is exactly invariant. Near its boundary, nonzero sensitivity may be too weak to resolve depth and start in noise. The nominal s_d=0.25 experiment belongs to this second regime: rank four does not prevent its profile objectives from reaching invariant subsets. Deeper penetration improves local conditioning and nonlinear recovery, but contact overlap alone is not a sufficient identifiability test.

Sampling and load must be considered together. Changing a 120-position cycle into two 60-position cycles changes both the torque allocation and the angular grid. Common-grid, interleaved and complementary-phase controls separate these effects for the tested designs. Their bootstrap intervals do not resolve an advantage of the selected two-load allocation. This neither establishes equivalence nor implies that maximum torque is universally optimal; a load that exposes a previously unloaded relief region may have a different value.

The cross-operator experiments distinguish detecting a relief effect from reconstructing its geometry. Their isolated 24/24 dedendum signal is close to the analytical prediction. That agreement concerns an RMS response difference, not agreement of complete waveforms, stiffness fields or inverse parameters. Restricted fits and profile objectives test whether an addendum-only model explains the data and whether depth and start can compensate for each other. Bulk refinement stabilizes the isolated signal but leaves substantial changes in the inverse residual, so mesh-independent inverse recovery is not established. Interpretation remains conditional on the phase mask, parameter bounds, numerical mesh and assumed 0.1 µm objective scale. In particular, deterministic discrepancy prevents a nominal likelihood threshold from certifying physical confidence intervals.

The external benchmark supplies a separate fidelity constraint. All four formulations systematically overpredict the twelve reference amplitudes. Correcting the shear modulus is necessary for constitutive consistency even though it worsens this comparison; closer amplitude agreement cannot validate an incorrect shear law. Projected forces and centre-line geometry reduce part of the increase but leave substantial disagreement. Root transitions, hub support, body coupling, three-dimensional effects, contact normals and engagement geometry remain possible contributors. The available amplitude targets cannot isolate their effects or determine a waveform-discrepancy covariance.

Absolute parameter accuracy would require a geometrically faithful reference or measured dataset with known modifications, compatible boundary conditions, calibrated measurement scale and resolved angular waveforms. A physically modified FE contour must also update elastic stiffness and contact geometry. The modified-contour control tests the elastic consequence of removal while keeping the candidate contact geometry unchanged by construction. It is a controlled test of a theorem hypothesis, not a validation of a complete manufactured profile, contact transitions or inverse reconstruction. The results define what follows from the declared operator and identify which additional information physical reconstruction requires.

The non-parametric analysis adds an observation-level limitation. Mean removal annihilates a uniform gap shift even where contact is loaded. Nodal resolution and uncertainties must therefore be interpreted in the resolved subspace after fixing this additive gauge. Zero columns depend on the support of the interpolation basis, while the sufficient invisibility result concerns actual contact coordinates. Neither a damped resolution diagonal nor a first-order null vector establishes global recovery of an arbitrary finite-amplitude profile.

## 6 Conclusions

For a fixed-geometry quasistatic gap operator, nonnegative relief outside loaded contact support can be exactly invisible to transmission error. The result extends to symmetric positive-definite coupled compliance and gives a mechanical explanation for invariant parameter sets. An implicit contact tangent connects that explanation with local rank and with the null space of a discretized relief field.

Nonlinear profiles and noise experiments distinguish this exact invariance from practical non-identifiability near the support boundary. In the nominal low-noise experiment, moving the dedendum start from 0.25 to 0.40 reduces median scaled error from 0.394 to 0.106. Local Fisher predictions are useful in the deeper regime but fail near invariant sets. Fixed-budget controls establish that angular sampling must be assessed alongside torque allocation.

Finite-element gap tests yield an isolated dedendum response of 0.179 µm RMS against an analytical 0.197 µm. However, the addendum-only inverse attains the same residual, the fitted dedendum block has zero local sensitivity and both dedendum profile objectives remain flat over the tested domains. This cross-operator test does not identify dedendum presence or geometry. The three-level bulk study stabilizes the isolated signal but does not establish convergence of inverse recovery. Physically modifying unloaded relief and reassembling stiffness gives approximately 0.4–2.1 nm centred differences in an eight-phase P2 control. Exact invariance therefore remains conditional on fixed compliance; the small physical effect does not validate profile inversion. None of the four analytical formulations meets the 5% external amplitude target across the twelve reference cases. The defensible outcome is an operator-conditioned account of observability and uncertainty, with physical profile reconstruction remaining contingent on independent mechanical and experimental validation.

## Appendix A Continuum contact and discretization controls

Q1_FE_APPENDIX

## Declarations

Declaration of competing interest. The authors declare that they have no competing financial interests or personal relationships that could have influenced the work reported in this article.

Declaration of generative AI use. During preparation of this work, Kimi (Moonshot AI) and ChatGPT with Codex (OpenAI) were used to assist with code inspection, numerical analysis and manuscript drafting. The authors are responsible for reviewing and verifying the assisted content and for the scientific accuracy and integrity of the submitted article.

CRediT authorship contribution statement. Romulo Sandoval Flórez: Conceptualization, Methodology, Software, Formal analysis, Investigation, Writing – original draft, Writing – review & editing, Visualization, Supervision. Claudia Patricia Parra Medina: Conceptualization, Methodology, Software, Formal analysis, Investigation, Writing – original draft, Writing – review & editing, Visualization, Supervision. German Leandro Vargas Fonseca: Conceptualization, Methodology, Software, Formal analysis, Investigation, Writing – original draft, Writing – review & editing, Visualization, Supervision.

Data availability. The baseline source code and numerical records are available at https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v10. The accompanying MMT_reproducibility_v12.zip package contains the final article, supplementary tables, scripts, new numerical records, bibliographic verification and a SHA-256 manifest. The manuscript-v10 tag identifies only the historical baseline; the current additional evidence requires the version-12 package. The versioned package is deposited at https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v12 with its numerical records and SHA-256 manifest. The historical v10 calculations are preserved separately; no DOI is assigned.

Funding. This research received no funding from any entity.

## References

REFERENCES_40
