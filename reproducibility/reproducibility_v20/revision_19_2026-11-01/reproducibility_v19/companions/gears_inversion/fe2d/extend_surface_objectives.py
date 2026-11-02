"""Checkpointed forward verification, role reversal and actual-relief geometry.
No inverse fits until numerical uncertainty is below a local relief contrast.
"""
import json,traceback
import updated_surface_contact as u


def main():
    plan=[]
    for phase in [.174048546,.5,.825951454]:
        plan += [(phase,.01,.25,'nominal',False),(phase,.02,.35,'nominal',True)]
    for phase in [.174048546,.5]:
        for step,h in [(.02,.35),(.01,.25)]:
            for case in ['addendum','combined']:plan.append((phase,step,h,case,False))
    path=u.OUT/'extended_campaign.json';records=json.loads(path.read_text()) if path.exists() else []
    done={tuple(r['configuration']) for r in records if r.get('result',{}).get('all_load_stages_converged',False)}
    for config in plan:
        if config in done:continue
        phase,step,h,case,reverse=config
        try:
            r=u.run(phase,step,h,case=case,reverse=reverse)
            records.append(dict(configuration=config,result={k:v for k,v in r.items() if k!='history'}))
        except Exception as e:
            traceback.print_exc();records.append(dict(configuration=config,error=repr(e)))
        path.write_text(json.dumps(records,indent=2),encoding='utf-8')


if __name__=='__main__':main()
