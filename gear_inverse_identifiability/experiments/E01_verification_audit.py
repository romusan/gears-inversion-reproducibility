"""Record nonlinear solver residuals and angular convergence with units."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from geometry.involute import InvoluteGear,GearPair
from mechanics.compliance import GearContactModel
from mechanics.transmission_error import TransmissionError
from campaign_provenance import provenance

def main():
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    te=TransmissionError(GearContactModel(pair,linearize_hertz=False))
    torque=100.;force=torque*1e3/pair.g1.rb
    records=[]
    for n in [120,240,480,960]:
        cycle=te.compute_cycle(torque,n)
        residual=max(i['residual_force'] for i in cycle['infos'])
        normalized_comp=max(float(np.max(np.abs(p*w)))/(force*pair.g1.m) for p,w in zip(cycle['forces'],cycle['separations']))
        entry=dict(n_positions=n,rms_mm=float(np.std(cycle['TE_lin_fluct'])),
                   max_force_residual_N=residual,relative_force_residual=residual/force,
                   max_normalized_complementarity=normalized_comp,
                   min_separation_mm=min(float(np.min(w)) for w in cycle['separations']))
        if records:entry['relative_rms_change']=abs(entry['rms_mm']-records[-1]['rms_mm'])/records[-1]['rms_mm']
        records.append(entry);print(entry,flush=True)
    out=Path(__file__).resolve().parents[1]/'results'/'corrections_2026-10-12'/'E01_verification.json'
    out.write_text(json.dumps(dict(provenance=provenance(),torque_Nm=torque,normal_force_N=force,
                                  geometry=[24,48,3,20],microgeometry='none',records=records),indent=2),encoding='utf-8')

if __name__=='__main__':main()
