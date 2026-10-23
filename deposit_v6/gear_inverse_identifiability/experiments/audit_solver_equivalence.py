"""Quantify response changes from correcting the Newton derivative only."""
import sys,json,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from geometry.involute import InvoluteGear,GearPair
from geometry.microgeometry import TipRelief
from mechanics.compliance import GearContactModel
from mechanics.transmission_error import TransmissionError
from campaign_provenance import provenance

ROOT=Path(__file__).resolve().parents[1]
BACKUP=ROOT.parent/'correcciones_2026-10-12'/'respaldo'
OUT=ROOT/'results'/'corrections_2026-10-12'

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,BACKUP/file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def main():
    old_comp=load('mechanics.compliance_before_hertz','compliance_before_hertz_jacobian.py')
    old_solver=load('mechanics.solver_before_hertz','contact_solver_before_hertz_jacobian.py')
    pair=GearPair(InvoluteGear(24,3,20,20),InvoluteGear(48,3,20,20))
    old=TransmissionError(old_comp.GearContactModel(pair,micro1=TipRelief(2),linearize_hertz=False))
    old.solver=old_solver.ContactSolver(old.model)
    new=TransmissionError(GearContactModel(pair,micro1=TipRelief(2),linearize_hertz=False))
    rows=[]
    for theta in [[.02,.75,.005,.25],[.1,.3,.05,.5],[0,.95,0,.05]]:
        for torque in [50,100,200,300]:
            a=old.compute_cycle(torque,60,np.array(theta))
            b=new.compute_cycle(torque,60,np.array(theta))
            diff=float(np.max(np.abs(a['TE_lin_fluct']-b['TE_lin_fluct'])))
            row=dict(theta=theta,torque_Nm=torque,n_positions=60,max_response_change_mm=diff)
            rows.append(row);print(row,flush=True)
    worst=max(r['max_response_change_mm'] for r in rows)
    (OUT/'solver_equivalence.json').write_text(json.dumps(dict(provenance=provenance(),comparisons=rows,
        max_response_change_mm=worst,within_1e_minus_10_mm=worst<1e-10,
        limitation='Finite sampled comparisons; historical optimization trajectories are not rerun or recertified.'),indent=2),encoding='utf-8')
    if worst>=1e-10:raise RuntimeError('Derivative correction changes response above audit tolerance')

if __name__=='__main__':main()
