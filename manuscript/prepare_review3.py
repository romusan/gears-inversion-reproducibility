"""Apply third-review prose corrections after preparing the referenced source."""
from pathlib import Path
from prepare_q1_manuscript import main as prepare
BASE=Path(__file__).resolve().parent

def main():
    prepare()
    p=BASE/'q1_manuscript.md'; t=p.read_text(encoding='utf-8')
    start=t.index('Transmission-error fitting'); end=t.index('\n\nKeywords:',start)
    t=t[:start]+'''Transmission-error fitting can conceal uncertainty in gear profile reconstruction when relief enters only marginally into the loaded flank. A quasi-static model with four profile parameters establishes a sufficient contact-support condition for exact relief invisibility. Implicit sensitivities, nonlinear profiles and noise experiments distinguish these invariant sets from a weak transition with nonzero sensitivity. For the nominal geometry, marginal and deeper dedendum starts of 0.25 and 0.40 give median scaled reconstruction errors of 0.394 and 0.106 under 100 realizations with 120 observations at 300 Nm and 0.1 micrometre noise. Fisher predictions agree with Monte Carlo in the deeper regime but fail near invisible sets. This contrast is geometry dependent: other tooth pairs have clearly visible dedendum relief at the same start of 0.25. Comparing the minimum loaded flank coordinate with the expected relief-start range therefore provides a diagnostic before inversion, complemented by angular-grid refinement and singular values. Common-grid and interleaved-phase controls expose sampling confounding in marginal-support load comparisons; no two-load advantage is demonstrated by the deeper-support experiment. All 48 external mechanical comparisons overpredict peak-to-peak transmission error, and correcting the shear denominator alone worsens agreement. Contact support thus explains internal observability, while independent stiffness and waveform evidence remains necessary for physical reconstruction.''' +t[end:]
    t=t.replace('retained-load','held-out')
    t=t.replace('This monotone ranking mainly rewards the highest torque within the tested range.',
      'This ranks the addendum block on the original grids; it is not a complete profile-recovery criterion.')
    t=t.replace('a lower-sensitivity load', 'a load with lower addendum sensitivity')
    t=t.replace('The dedendum-start sweep demonstrates this transition and prevents extrapolating the original nominal ambiguity to every relief configuration.',
      'The marginal regime is geometry dependent. Before inversion, comparing the minimum loaded coordinate ξ_min with the expected range of s_d identifies whether the relief reaches contact support. G1 and G3 have substantial dedendum sensitivity at s_d=0.25, whereas G0 is marginal and G2 is invisible in the sampled test. This support diagnostic must be checked against angular refinement and the singular spectrum; support overlap alone does not establish parameter identifiability.')
    t=t.replace('Parameter-block errors and held-out predictions are more informative than a single maximum relative error. Load ranking must be interpreted jointly with the weak sensitivity direction and the observation budget.',
      'At s_d=0.40, local information and nonlinear recovery agree at low noise, and the tested 50/300 Nm allocation shows no demonstrated recovery advantage. At s_d=0.25, changing from 120 to 60 phase positions confounds the original load comparison. Shared-grid and interleaved-phase controls separate this effect locally, but a nonlinear recovery comparison on those controlled designs remains necessary. A universal recommendation to use only maximum torque does not follow.')
    t=t.replace('Statistical summaries include failed optimizations rather than removing them.',
      'Statistical summaries include failed optimizations rather than removing them. The pre-inversion support diagnostic uses the nominal contact solution over the anticipated geometry and loading range; it is conditional on the accuracy of that forward model. The sufficient invisibility criterion refers to a zero-dedendum solution, while the tables also report support at the nonzero-relief truth. Adequate angular resolution is particularly important near the engagement boundary.')
    p.write_text(t,encoding='utf-8')

if __name__=='__main__':main()
