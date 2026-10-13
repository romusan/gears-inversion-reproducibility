"""Checks for the coupled linear-contact observation, including signed coupling."""
import json
import numpy as np
from run_fe2d import solve_contact,OUT

def exact_small_contact(H,g,F):
    # Exhaustive active sets provide an independent reference on seven unknowns.
    for mask in range(1,1<<len(g)):
        active=np.array([bool(mask&(1<<i)) for i in range(len(g))]);i=np.where(active)[0]
        v=np.linalg.solve(H[np.ix_(i,i)],np.column_stack([np.ones(len(i)),g[i]]))
        delta=(F+v[:,1].sum())/v[:,0].sum();p=np.zeros(len(g));p[i]=delta*v[:,0]-v[:,1]
        w=H@p+g-delta
        if p.min()>=-1e-9 and w.min()>=-1e-9:return dict(p=p,delta=delta,active=active)
    raise AssertionError('No admissible active set')
cases=[]
rng=np.random.default_rng(20261012)
for trial in range(12):
    A=rng.normal(size=(7,7));H=(A.T@A+np.eye(7))*1e-4
    # Three low-gap candidates and four clearly unloaded ones.
    g=np.array([0,.001,.002,1,1.2,1.4,1.6])
    F=10.;r=exact_small_contact(H,g,F)
    changed=g.copy();changed[~r['active']]+=.5+rng.random((~r['active']).sum())
    v=exact_small_contact(H,changed,F)
    p_change=float(np.max(abs(r['p']-v['p'])));delta_change=float(abs(r['delta']-v['delta']))
    assert p_change<1e-7 and delta_change<1e-10
    rr=[exact_small_contact(H,g,f) for f in [5,10,15]]
    assert all(rr[i+1]['delta']>rr[i]['delta'] for i in [0,1])
    cases.append(dict(trial=trial,min_eigenvalue=float(np.linalg.eigvalsh(H).min()),
        signed_off_diagonal=bool(np.any((H-np.diag(np.diag(H)))<0)),max_force_change_N=p_change,max_approach_change_mm=delta_change))
(OUT/'coupled_invisibility_checks.json').write_text(json.dumps(cases,indent=2))
print('12 SPD coupled-contact checks passed')
