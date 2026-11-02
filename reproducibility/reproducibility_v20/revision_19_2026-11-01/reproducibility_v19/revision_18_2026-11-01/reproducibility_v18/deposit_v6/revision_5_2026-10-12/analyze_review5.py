import json,csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent.parent;BASE=Path(__file__).resolve().parent
def main():
    fe=json.loads((ROOT/'fe2d/results/separated_convergence.json').read_text());rows=fe['records']
    mc=json.loads((ROOT/'gear_inverse_identifiability/results/q1_review5_2026-10-12/complementary_monte_summary.json').read_text())
    bulk=[];interface=[]
    for phase in [0,.5]:
        select=lambda h,d:next(r for r in rows if r['phase_fraction']==phase and r['mesh_h_mm']==h and r['contact_step_mm']==d)
        a,b=select(.35,.01),select(.25,.01);c=select(.25,.005)
        bulk.append(abs(b['k_incremental_N_um']/a['k_incremental_N_um']-1))
        interface.append(abs(c['k_incremental_N_um']/b['k_incremental_N_um']-1))
        # Body meshes have identical topology counts across pressure steps.
        for d in [.02,.005]:
            t=select(.25,d);assert t['nodes']==b['nodes'] and t['elements']==b['elements']
    assert max(bulk)<.001 and max(interface)<.001
    assert all(r['elastic_residual_relative']<1e-8 and r['force_residual_N']<1e-6 and r['contact_residual_mm']<1e-9 for r in rows)
    assert mc['records']==600 and all(x['n']==100 for x in mc['summary'])
    assert all(x['bootstrap_percentile_95'][0]<=0<=x['bootstrap_percentile_95'][1] for x in mc['summary'])
    fine=[next(x for x in rows if x['phase_fraction']==phase and x['mesh_h_mm']==.25 and x['contact_step_mm']==.005) for phase in [0,.5]]
    result=dict(separated_records=rows,bulk_changes=bulk,interface_changes=interface,
        quadratic_fine_k_N_um=[x['k_incremental_N_um'] for x in fine],quadratic_fine_approach_um=[x['approach_um'] for x in fine],
        quadratic_two_phase_difference_um=fine[0]['approach_um']-fine[1]['approach_um'],
        complementary_mc=mc['summary'],new_fits=600,new_selected_success=sum(x['new_success'] for x in mc['summary']),
        scope='Fixed approximate geometry, interior weak contact, no corner-cycle validation. Observed convergence changes are not exact error bounds.')
    (BASE/'review5_summary.json').write_text(json.dumps(result,indent=2))
    with (BASE/'separated_FE.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['study','phase_fraction','element_degree','mesh_h_mm','contact_step_mm','k_incremental_N_um','approach_um','elastic_residual_relative'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    with (BASE/'complementary_MC.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(mc['summary'][0]));w.writeheader();w.writerows(mc['summary'])
    spectra=json.loads((ROOT/'gear_inverse_identifiability/results/q1_revision_2026-10-12/support_transition.json').read_text())['spectra']
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,sd in zip(axes,[.25,.4]):
        for r in spectra:
            if r['sd_true']==sd:ax.semilogy(range(1,5),r['singular_values'],'o-',label=f"{r['torque_Nm']:.0f} Nm, σ₄={r['singular_values'][-1]:.2g}")
        ax.set_xticks(range(1,5));ax.set_xlabel('Singular value index');ax.set_ylabel('Scaled, whitened singular value');ax.set_title(f'True $s_d$ = {sd}');ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(BASE/'analytic_spectra_v5.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,study in zip(axes,['bulk','interface']):
        for phase in [0,.5]:
            group=[x for x in rows if x['phase_fraction']==phase and (x['study']==study or study=='interface' and x['mesh_h_mm']==.25 and x['contact_step_mm']==.01)]
            group=sorted(group,key=lambda x:x['mesh_h_mm'] if study=='bulk' else x['contact_step_mm'])
            ax.plot([x['mesh_h_mm'] if study=='bulk' else x['contact_step_mm'] for x in group],[x['k_incremental_N_um'] for x in group],'o-',label='One pair' if phase==0 else 'Two pairs')
        ax.set_xlabel('Bulk/root h (mm)' if study=='bulk' else 'Pressure-station step (mm)');ax.set_ylabel('Incremental stiffness (N/µm)');ax.set_title('Quadratic elements and integrated pressure hats');ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(BASE/'separated_convergence.png',dpi=160);plt.close(fig)
    lines=['# Respuesta a la quinta revisión','',
      'Se cerró el control no lineal de fases complementarias y se separaron los controles del cuerpo y de la interfaz FE, con elementos cuadráticos y presión distribuida. Los resultados previos se conservan como diagnósticos de su discretización; la validación física del contacto de esquina sigue abierta.','',
      '## Convergencia FE','',
      'El ajuste de tres valores lineales con orden 0.32 no justificaba una extrapolación certificada. El seguimiento usa elementos de desplazamiento de seis nodos y funciones continuas de presión integradas sobre la traza real del borde. Las holguras se promedian con las mismas funciones. Se fijaron los vértices geométricos del contacto con independencia del paso de presión y la malla local objetivo en 0.01 mm.',
      '','| Fase | Control | h (mm) | Paso presión (mm) | k (N/µm) | Acercamiento (µm) |','|---:|---|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['phase_fraction']} | {r['study']} | {r['mesh_h_mm']} | {r['contact_step_mm']} | {r['k_incremental_N_um']:.5f} | {r['approach_um']:.5f} |")
    lines+=['',f"El último cambio del cuerpo, manteniendo el paso de presión, es {100*bulk[0]:.4f}% y {100*bulk[1]:.4f}%. El cambio de interfaz de 0.01 a 0.005 mm, sobre los mismos recuentos de nodos/elementos y con h fijo, es {100*interface[0]:.4f}% y {100*interface[1]:.4f}%. La prueba de energía bajo deformación constante con elementos cuadráticos dio error relativo 1.82e-14; los casos conservan los controles de equilibrio, energía y rigidez incremental. La restricción de contacto nueva es débil/promediada; no se afirma no penetración puntual exacta a resolución finita.",
      f"Los valores finos son k₁={fine[0]['k_incremental_N_um']:.4f} y k₂={fine[1]['k_incremental_N_um']:.4f} N/µm; los acercamientos son {fine[0]['approach_um']:.4f} y {fine[1]['approach_um']:.4f} µm. La diferencia interior es {result['quadratic_two_phase_difference_um']:.4f} µm. Esta secuencia no respalda el valor 218 N/µm extrapolado de la combinación anterior de malla lineal y cargas nodales. Las variaciones observadas son medidas de estabilidad numérica, no cotas rigurosas del error exacto ni validación del contorno real.",
      '','## Control Monte Carlo','',
      'Se asignan 50 Nm a posiciones pares y 300 Nm a impares de la rejilla canónica de 120 puntos. Cada ciclo tiene 60 observaciones y su propio centrado. El ruido independiente se asigna a la posición angular canónica, para emparejar semillas con la carga única almacenada. Se mantienen escalas, cotas, dos inicios independientes y tolerancias. El motor Lambert W nuevo se cotejó con el iterativo en ambas verdades y ambos inicios.',
      '','| sd | σ (µm) | Convergentes/100 | Mediana 300 | Mediana par | Mediana diferencia pareada | Intervalo bootstrap 95% |','|---:|---:|---:|---:|---:|---:|---|']
    for r in mc['summary']:lines.append(f"| {r['sd_true']} | {r['sigma_um']} | {r['new_success']} | {r['single300_median']:.4g} | {r['complementary_median']:.4g} | {r['median_paired_difference']:.4g} | [{r['bootstrap_percentile_95'][0]:.4g}, {r['bootstrap_percentile_95'][1]:.4g}] |")
    lines+=['',f"Se añadieron 600 reconstrucciones; {result['new_selected_success']} declaran convergencia y los 20 fallos se conservaron. Los seis intervalos incluyen cero. No se demuestra ventaja del par para este reparto complementario en ninguna de las dos verdades. La mediana de diferencias pareadas no es la diferencia de medianas. Los átomos por saturación de cotas producen empates y algunos intervalos terminan exactamente en cero; no se interpreta esto como equivalencia certificada o una prueba de cobertura de parámetros.",
      '','## Inferencia sobre el benchmark','',
      'La concordancia aproximada de los rangos FE y baseline en ocho fases motiva auditar la definición de TE, geometría de punta/borde y configuración unmodified del benchmark. No permite atribuir la brecha solo a la ley de rigidez, pero tampoco identifica su causa: ambos modelos comparten idealizaciones geométricas, las fases FE de borde se recortan y la secuencia lineal original no estaba demostrada como asintótica. El +16.6% queda identificado como comparación de rejilla finita con incertidumbre de discretización; no como error físico certificado.',
      'Un rango discreto puede ser un límite inferior del rango angular del mismo operador; con contactos de esquina omitidos y mallas finitas no certifica un límite del pico a pico físico. El control cuadrático resuelve la estabilidad de las fases interiores, no el ciclo continuo de esquina.',
      '','## Precisión, norma y edición','',
      'Se redondea σ₄ marginal a dos cifras en las tablas de espectros y geometría y en la leyenda de la Figura 6. Se señala su dependencia de la rejilla. El highlight ahora destaca ξ_min como diagnóstico previo.',
      'El rango baseline 14.08–15.07 N/(mm·µm) procede de las 1920 fases, con mínimo 323.8756/23=14.08155. El subconjunto de ocho fases da 14.22–15.07. Los dos rangos son correctos para sus muestreos; se explicita esa diferencia.',
      'ISO 6336-1:2019, 6.4.3 f), páginas impresas 27–28, contiene c′=14 para engranajes rectos dentro de las simplificaciones del método C. La definición y cálculo de rigidez se tratan en la cláusula 9. Se volvió a consultar la transcripción normativa accesible y la ficha oficial; no se afirma disponer de la copia licenciada íntegra.',
      '[Transcripción normativa consultada](https://studylib.net/doc/28005356/iso-6336-1-2019-calculation-of-load-capacity-of-spur-and-...) y [ficha oficial ISO](https://www.iso.org/standard/63819.html).',
      'Las antiguas Tablas 7–10 y 13–14 pasan a S1–S6 del suplemento; S7 contiene los controles separados. El manuscrito principal retiene diez tablas y 40 referencias. Los autores confirmaron los mismos nueve roles CRediT para cada uno. Código y datos: https://github.com/romusan/gears-inversion-reproducibility/tree/manuscript-v5. No se ha asignado DOI.']
    (BASE/'respuesta_revision5.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Review 5 results summarized',result['quadratic_fine_k_N_um'],bulk,interface)
if __name__=='__main__':main()
