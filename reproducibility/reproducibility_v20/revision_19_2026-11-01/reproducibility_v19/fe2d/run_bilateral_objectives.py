"""Staged selected-phase verification after unilateral penetration was detected."""
import json,traceback
import updated_surface_contact as u


def main():
    plan=[]
    for phase in [.174048546,.5,.825951454]:
        for step,h in [(.04,.5),(.02,.35),(.01,.25)]:
            plan.append((phase,step,h,'nominal',False,1e-8))
    plan += [(.174048546,.04,.5,'nominal',False,1e-10),(.174048546,.04,.5,'nominal',True,1e-8)]
    for phase in [.174048546,.5]:
        for step,h in [(.02,.35),(.01,.25)]:
            for case in ['addendum','combined']:plan.append((phase,step,h,case,False,1e-8))
    path=u.OUT/'bilateral_campaign.json';records=json.loads(path.read_text()) if path.exists() else []
    done={tuple(r['configuration']) for r in records if r.get('result',{}).get('all_load_stages_converged',False)}
    for config in plan:
        if config in done:continue
        phase,step,h,case,reverse,regularization=config
        # Reuse already-completed control; retain its source hash and history.
        tag=f'f{phase:.9f}_s{step:g}_h{h:g}'+('' if case=='nominal' else '_'+case)+('_reverse' if reverse else '')+f'_patch2_twopass_reg{regularization:g}'
        existing=u.OUT/(tag+'.json')
        try:
            r=json.loads(existing.read_text()) if existing.exists() else u.run(phase,step,h,case=case,reverse=reverse,two_pass=True,regularization=regularization,maxiter=100)
            records.append(dict(configuration=config,result={k:v for k,v in r.items() if k!='history'}))
        except Exception as e:
            traceback.print_exc();records.append(dict(configuration=config,error=repr(e)))
        path.write_text(json.dumps(records,indent=2),encoding='utf-8')


if __name__=='__main__':
    import argparse
    from pathlib import Path
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    if args.out is not None:u.OUT=args.out.resolve();u.OUT.mkdir(parents=True,exist_ok=True)
    main()
