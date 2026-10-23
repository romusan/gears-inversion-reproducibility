import json,csv,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'fe2d'))
from run_fe2d import solve_contact

def main():
    fe=json.loads((ROOT/'fe2d/results/quadratic_eight_phases.json').read_text())
    offsets=json.loads((OUT/'angular_offset_control.json').read_text())
    old=[json.loads(s) for s in (ROOT/'gear_inverse_identifiability/results/q1_revision_2026-10-12/monte_carlo_records.jsonl').read_text().splitlines()]
    new=[json.loads(s) for s in (ROOT/'gear_inverse_identifiability/results/q1_review5_2026-10-12/complementary_monte_records.jsonl').read_text().splitlines()]
    summary=[]
    for sd in [.25,.4]:
        for sigma in [.1,.5,1]:
            a={r['seed']:r['dedendum_scaled_error'] for r in old if r['sd_true']==sd and r['sigma_um']==sigma and r['design']=='single300'}
            b={r['seed']:r['dedendum_scaled_error'] for r in new if r['sd_true']==sd and r['sigma_um']==sigma}
            assert len(a)==len(b)==100
            delta=np.array([b[i]-a[i] for i in range(100)])
            summary.append(dict(sd=sd,sigma_um=sigma,pair_better_percent=int(np.sum(delta<0)),
                pair_worse_percent=int(np.sum(delta>0)),exact_ties=int(np.sum(delta==0)),
                improved_beyond_1e_8=int(np.sum(delta< -1e-8)),worse_beyond_1e_8=int(np.sum(delta>1e-8)),ties_within_1e_8=int(np.sum(abs(delta)<=1e-8))))
    rows=fe['records'];checks=[]
    for r in rows:
        tag=f"f{r['phase_fraction']:g}_h0.25_d0.01_b25_r0.4_exactgap"
        if r['restricted_nominal_window']:tag+='_transition'
        tag+='_weak_hat_local0.01_P2'
        f=ROOT/'fe2d/results'/(tag+'_contact.npz')
        stored=np.load(f);H=stored['H_mm_N'];gap=stored['gap_mm'];force=r['normal_force_N'];pressures=stored['p_N']
        symmetry=float(np.max(abs(H-H.T)));mineig=float(np.linalg.eigvalsh(H).min())
        assert mineig>0 and symmetry<1e-12
        assert r['force_residual_N']<1e-6 and r['elastic_residual_relative']<1e-8 and r['contact_residual_mm']<1e-9
        perturbations=[]
        for eps in [.001,.0003,.0001,.00003,.00001]:
            low=solve_contact(H,gap,force*(1-eps),pressures);high=solve_contact(H,gap,force*(1+eps),pressures)
            k=2*eps*force/(1000*(high['delta']-low['delta']))
            err=float(abs(k/r['k_incremental_N_um']-1))
            perturbations.append(dict(relative_force_step=eps,k_fd_N_um=k,relative_difference=err,active_sets_match=bool(np.array_equal(low['active'],high['active']))))
            if err<1e-7:break
        assert min(t['relative_difference'] for t in perturbations)<1e-7
        checks.append(dict(phase=r['phase_fraction'],minimum_eigenvalue_mm_N=mineig,symmetry_residual_mm_N=symmetry,torque_relative_error=r['torque_relative_error'],tangent_perturbations=perturbations))
    result=dict(quadratic=fe,monte_carlo_seed_comparisons=summary,angular=offsets,FE_checks=checks,
        original_linear_range_um=12.278,baseline_matched_range_um=11.662,
        quadratic_reference_difference_percent=100*(fe['sampled_range_um']/10.527-1),
        maximum_torque_error_percent=100*max(r['torque_relative_error'] for r in rows),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'fe2d/run_fe2d.py',ROOT/'fe2d/quadratic_eight_phases.py',ROOT/'gear_inverse_identifiability/experiments/Q1_review6_angular.py']})
    (OUT/'review6_summary.json').write_text(json.dumps(result,indent=2))
    with (OUT/'quadratic_eight_FE.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['phase_fraction','nominal_pairs','approach_um','k_incremental_N_um','tooth_edge_loaded','torque_relative_error','elastic_residual_relative'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    b=offsets['results'][-2];q=offsets['results'][-1]
    lines=['# Respuesta a la revisión de la v5','',
        f"Se repitieron las ocho fases con desplazamientos cuadráticos y presión distribuida débil. El rango muestreado es {fe['sampled_range_um']:.6f} µm, frente al rango lineal original 12.278 µm y al baseline en esas fases, 11.662 µm. La comparación con 10.527 µm es {result['quadratic_reference_difference_percent']:+.3f}% y continúa siendo de ocho fases y de un operador con contactos de esquina omitidos; no se convierte en p-p físico certificado.",
        f"Las ocho matrices condensadas son definidas positivas. Se verificaron simetría, equilibrio elástico y de fuerza, contacto promediado y tangente por perturbación independiente. La desviación máxima del momento resultante respecto al torque nominal es {result['maximum_torque_error_percent']:.6f}%; se conserva como diagnóstico de la normal fija, sin recalibrar rigidez ni cargas.",
        '', '## Semillas, empates y bootstrap','',
        '| sd | σ µm | Par mejora % | Par empeora % | Empates exactos | Empates con tolerancia 1e-8 |','|---:|---:|---:|---:|---:|---:|']
    for r in summary:lines.append(f"| {r['sd']} | {r['sigma_um']} | {r['pair_better_percent']} | {r['pair_worse_percent']} | {r['exact_ties']} | {r['ties_within_1e_8']} |")
    lines+=['','Las fracciones usan las 100 semillas por celda, incluidos los fallos. La comparación estricta puede contar diferencias del optimizador casi nulas; la tolerancia se muestra separadamente y está expresada en el error máximo de parámetros normalizado. No se equipara un extremo bootstrap en cero con equivalencia o cobertura de parámetros.',
        '', '## Muestreo cada 0.21 grados','',
        f"El periodo es 360/57={offsets['period_deg']:.9f}°. Se recorre todo el intervalo de desfase [0,0.21°), conservando los 30 o 31 puntos que caen en el ciclo fijo. El baseline da un rango de p-p de {b['min_pp_um']:.6f} a {b['max_pp_um']:.6f} µm. Las representaciones de 3840, 7680 y 15360 nodos dan prácticamente el mismo intervalo. Este control no permite explicar 10.527 µm solo por el muestreo angular del baseline.",
        f"El interpolante lineal periódico de las ocho fases FE cuadráticas da {q['min_pp_um']:.6f}–{q['max_pp_um']:.6f} µm. Es un diagnóstico del interpolante, no un barrido FE directo. Ocho fases no resuelven una rampa de 0.02°; por ello sigue pendiente un ciclo FE angular denso, con contacto de esquina y convergencia propia, para decidir el efecto de muestreo físico.",
        'El cálculo divide todos los desfases en intervalos cuyos límites son nudos desplazados y el cambio del número de muestras. Dentro de cada intervalo el rango de líneas afines es convexo; su máximo está en un extremo y el mínimo se obtiene por búsqueda ternaria de 70 pasos. No se selecciona un desfase para ajustar el benchmark.',
        '', '## Interfaz, contribuciones, datos y norma','',
        'La interfaz de S7 es no monótona. El texto describe estabilidad observada y excluye una certificación de convergencia asintótica o error exacto.',
        'Los nueve roles CRediT comunes proceden de la respuesta expresa de los autores en esta conversación; no se deducen de las afiliaciones. No se han enviado mensajes a coautores ni se afirma una confirmación independiente por correo.',
        'El repositorio GitHub es público (HTTP 200 sin autenticación) y se creó el tag anotado manuscript-v5 sobre e33ca4edb7eb09a7dd34c890d4bd7e6d988c4d99. La revisión nueva se deposita por separado como manuscript-v6. No se ha asignado DOI ni se presenta GitHub como un depósito Zenodo.',
        'La vista previa normativa accesible confirma que 6.4.3 trata el método C del factor dinámico y que la cláusula 9 trata rigidez. No expone el cuerpo de 6.4.3 f). La copia completa indexada no pudo recuperarse. Se retira del manuscrito la afirmación numérica c′=14 asociada a esa cláusula; no se presenta la transcripción de terceros como verificación definitiva.',
        '[Vista previa de ISO 6336-1:2019](https://cdn.standards.iteh.ai/sist-preview/iso/iso-6336-1-2019/31cd8c848a1146a9926fec6fc8290727/iso-6336-1-2019.pdf).']
    (OUT/'respuesta_revision6.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Validated eight FE phases, range',fe['sampled_range_um'],'seed fractions',[r['pair_better_percent'] for r in summary])

if __name__=='__main__':main()
