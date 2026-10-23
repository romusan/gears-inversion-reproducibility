"""Fase 3.3: reproduccion del benchmark externo Korta & Mundo (2017).

Reutiliza la geometria y los objetivos FE corregidos del experimento V06
(Tables 6-8 del preprint, 12 objetivos). Compara las formulaciones de
compliance 'legacy' (historica) y 'projected-energy' (adoptada Fase 2).

Salida: results/independent_validation/03_benchmark_reproduction.json
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'gear_inverse_identifiability'
sys.path.insert(0, str(PROJ / 'src'))
sys.path.insert(0, str(PROJ / 'experiments'))

from V06_korta_mundo_reproduction import (build_pair, REFERENCE_PP, SOLUTIONS,
                                          rt_to_sa, TORQUES)
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.batched_operator import BatchedGapOperator

N = 120
pair = build_pair()
micro = TipRelief(p=1.0)

cases = {'unmodified': None}
for name, sol in SOLUTIONS.items():
    d_mm = sol['d_um'] * 1e-3
    sa = rt_to_sa(sol['rt_mm'], pair.g1)
    cases[name] = np.array([d_mm, sa, 0.0, 0.5])

rows = []
for variant in ['legacy', 'projected-energy']:
    model = GearContactModel(pair, micro1=micro, micro2=micro,
                             compliance_variant=variant)
    for cname, theta in cases.items():
        for T in TORQUES:
            op = BatchedGapOperator(model, T, N)
            if theta is None:
                pred = op.evaluate(None)['prediction']
            else:
                pred = op.evaluate(theta, theta)['prediction']
            pp = float((pred.max() - pred.min()) * 1000)
            ref = REFERENCE_PP[(cname, T)]
            rows.append(dict(variant=variant, case=cname, torque_Nm=T,
                             model_pp_um=pp, reference_fe_pp_um=ref,
                             signed_error_um=pp - ref,
                             relative_error_percent=100 * (pp - ref) / ref,
                             passes_5_percent=abs(100 * (pp - ref) / ref) < 5))

out = ROOT / 'results' / 'independent_validation'
out.mkdir(parents=True, exist_ok=True)
(out / '03_benchmark_reproduction.json').write_text(json.dumps(rows, indent=1))

for variant in ['legacy', 'projected-energy']:
    rs = [r for r in rows if r['variant'] == variant]
    errs = [abs(r['relative_error_percent']) for r in rs]
    print(variant, 'min/max/mean |e_r| %%: %.2f %.2f %.2f  pass5: %d/12  all_over: %s'
          % (min(errs), max(errs), sum(errs) / len(errs),
             sum(r['passes_5_percent'] for r in rs),
             all(r['signed_error_um'] > 0 for r in rs)))
for r in rows:
    if r['variant'] == 'projected-energy':
        print('  PE', r['case'], int(r['torque_Nm']), '%.3f vs %.3f  %+.1f%%' %
              (r['model_pp_um'], r['reference_fe_pp_um'], r['relative_error_percent']))
