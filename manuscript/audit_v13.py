"""Recalculate new contrasts and check the focused revision's claims."""
import json,sys,platform,re,zipfile,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import mpmath
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_13_2026-10-23';BASE=ROOT/'manuscript'
def main():
    a=json.loads((OUT/'precision_summary.json').read_text());records=[json.loads(x) for x in (OUT/'precision_records.jsonl').read_text().splitlines()]
    assert len(records)==32 and len({(r['mode'],r['phase_fraction']) for r in records})==32
    base=sorted([r for r in records if r['mode']=='baseline'],key=lambda r:r['phase_fraction'])
    for row in a['rows']:
        j=1 if row['depth_um']==10 else 2;rr=sorted([r for r in records if r['mode']==row['mode']],key=lambda r:r['phase_fraction'])
        signal=np.array([r['approach_changes_um'][j] for r in rr]);signal-=signal.mean()
        baseline=np.array([r['approach_changes_um'][j] for r in base]);baseline-=baseline.mean()
        assert abs(1000*np.sqrt(np.mean(signal**2))-row['signal_rms_nm'])<1e-12
        assert abs(1000*np.sqrt(np.mean((signal-baseline)**2))-row['control_change_rms_nm'])<1e-12
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(BASE/'MMT_manuscript_Q1_revision_v13.docx') as z:doc=ET.fromstring(z.read('word/document.xml'))
    paras=[''.join(p.itertext()) for p in doc.findall('.//w:p',ns)];first=[]
    for p in paras:
        if re.match(r'^\[\d+\]',p):continue
        for m in re.finditer(r'\[(\d+(?:,\d+)*)\]',p):
            nums=list(map(int,m[1].split(',')))
            if all(1<=n<=42 for n in nums):
                for n in nums:
                    if n not in first:first.append(n)
    assert first==list(range(1,43)),first
    assert [int(re.match(r'^Figure (\d+) ',p)[1]) for p in paras if re.match(r'^Figure \d+ ',p)]==list(range(1,11))
    assert 'does not establish insufficiency of all possible observations' in '\n'.join(paras)
    assert 'not rigorous bounds' in '\n'.join(paras)
    with zipfile.ZipFile(BASE/'MMT_supplementary_Q1_revision_v13.docx') as z:d=ET.fromstring(z.read('word/document.xml'))
    pp=[''.join(p.itertext()) for p in d.findall('.//w:p',ns)]
    assert [int(re.match(r'^Supplementary Table S(\d+)',p)[1]) for p in pp if p.startswith('Supplementary Table S')]==list(range(1,22))
    largest=max(r['control_change_rms_nm'] for r in a['rows']);smallest=min(r['signal_rms_nm'] for r in a['rows'] if r['mode']=='baseline')
    report=dict(python=sys.version,platform=platform.platform(),mpmath=mpmath.__version__,records=32,phases=8,nominal_h_mm=.35,
        precision='80 decimal digits only for condensed active-contact equations; full FE remains float64',
        independently_recalculated_all_new_RMS=True,largest_control_curve_change_nm=largest,smallest_baseline_signal_nm=smallest,
        largest_same_depth_relative_change_percent=100*max(r['control_change_rms_nm']/next(b['signal_rms_nm'] for b in a['rows'] if b['mode']=='baseline' and b['depth_um']==r['depth_um']) for r in a['rows']),rigorous_total_error_bound=False,
        references_in_order=42,figures_in_order=10,supplementary_tables=21,all_1800_optimizations_repeated=False,
        documents={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in ['MMT_manuscript_Q1_revision_v13.docx','MMT_supplementary_Q1_revision_v13.docx','Highlights_v13.docx']})
    (OUT/'delivery_QA.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    lines=['# Respuesta focalizada al dictamen de v12','',
        'La revisión conserva el argumento y la organización del artículo. Añade únicamente la comprobación numérica de S20 y aclara el alcance de las observaciones retenidas. No se repite la campaña de 1800 inversiones ni se presenta el dictamen simulado como una decisión oficial de MMT.','',
        '## M1 Precisión del contraste nanométrico','',
        'Se repiten las ocho fases de S20 a h=0.35 mm con cuatro variantes: referencia; ordenación alternativa de LU y cuatro correcciones residuales elásticas con pulido del sistema de contacto a 80 dígitos; extensión armónica ponderada con el mismo contorno; e interfaz de 0.01 mm sobre estas mismas fases. El ensamblaje global elástico conserva aritmética float64. LU es un método directo, por lo que cambiar solamente una tolerancia del optimizador de contacto no certificaría la precisión del sistema elástico.','',
        '| Control | Profundidad µm | RMS señal nm | Cambio RMS de curva nm |','|---|---|---|---|']
    for r in a['rows']:lines.append(f"| {r['mode']} | {r['depth_um']:.0f} | {r['signal_rms_nm']:.8g} | {r['control_change_rms_nm']:.8g} |")
    lines+=['',f"Máximo cambio nominal por reensamblaje: {a['max_nominal_reassembly_change_nm']:.6g} nm. Máximo cambio de la repetición respecto a los registros v12: {a['max_baseline_archive_shift_change_nm']:.6g} nm. Los cambios de curva se calculan después de centrar en las mismas ocho fases; no son sólo diferencias entre dos valores RMS.",'',
        'La Tabla S21 informa controles empíricos de estabilidad. No se presenta una cota rigurosa del error total ni una validación metrológica del efecto. La aritmética de 80 dígitos se aplica únicamente al sistema condensado de contacto, no a todo el FE. El nivel de ruido supuesto es 100 nm por muestra; la pequeña variación estructural no acredita detectabilidad ni recuperación de parámetros.','',
        '## M2 Información excluida','',
        'La discusión declara ahora expresamente que la falta de identificación con los datos FE retenidos no demuestra insuficiencia de todas las observaciones posibles. Las fases de transición excluidas pueden aportar información; el modelo analítico lo sugiere, pero no reemplaza el contacto FE que falta resolver.','',
        '## M3 Alcance de la interfaz','',
        'S19 conserva su alcance: 24 fases, elementos P2 y geometría fija; no certifica la inversión P1 de 102 fases. El nuevo control de interfaz S21 utiliza las ocho fases de retirada física y tampoco se convierte en un certificado del ciclo completo. Esta distinción se mantiene en la documentación del paquete.','',
        '## M4 Benchmark y reconstrucción física','',
        'No se añaden afirmaciones de precisión experimental ni de reconstrucción fiable de perfiles manufacturados. La discrepancia externa permanece sin resolver y la contribución sigue condicionada al operador declarado.','',
        '## Paquete de envío','',
        'El kit contiene cuatro archivos de carga: artículo DOCX, suplemento DOCX, Highlights DOCX y ZIP reproducible. CONTENIDO_Y_SHA256.json identifica cada archivo. El ZIP del kit facilita trasladarlos conjuntamente; los cuatro deben seleccionarse individualmente en el sistema editorial según sus categorías. Preparar este kit no constituye un envío a la revista.']
    (OUT/'RESPUESTA_DICTAMEN_v13.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':main()
