"""Repeat the original eight phases with P2 and consistent weak pressure hats."""
import json
from run_fe2d import run,OUT
reference=json.loads((OUT/'transition_checks.json').read_text())
phases=sorted([0,.5]+[r['phase_fraction'] for r in reference['records']])
rows=[]
for phase in phases:
    tag=f'f{phase:g}_h0.25_d0.01_b25_r0.4_exactgap_weak_hat_local0.01_P2'
    path=OUT/(tag+'.json')
    if not path.exists():path=OUT/(tag.replace('_exactgap_weak','_exactgap_transition_weak')+'.json')
    if path.exists():
        result=json.loads(path.read_text())
        assert result['element_degree']==2 and result['traction_discretization']=='weak_hat'
    else:
        result=run(phase,.25,.01,25,.4,allow_clipped=True,traction='weak_hat',local_h=.01,degree=2)
    rows.append(result)
    (OUT/'quadratic_eight_partial.json').write_text(json.dumps(rows,indent=2))
approaches=[r['approach_um'] for r in rows]
report=dict(records=rows,sampled_range_um=max(approaches)-min(approaches),
    scope='Eight original phases; quadratic displacements and averaged pressure constraints. Restricted nominal contact windows, approximate tip/root and fixed normals. Not a converged continuous corner-contact cycle.')
(OUT/'quadratic_eight_phases.json').write_text(json.dumps(report,indent=2))
print('Eight quadratic phases complete',report['sampled_range_um'],flush=True)
