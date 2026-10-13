"""Complete missing legacy tasks with explicit provenance on new records.

Historical records are preserved and labelled unversioned in the manifest.
They are not retrospectively certified by hashes of the current code.
"""
import json,shutil,concurrent.futures,argparse
from pathlib import Path
from campaign_provenance import provenance

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'corrections_2026-10-12'
FIELDS={'E04':('mode','case','sigma_um','gamma','seed'),
        'E07':('gen','inv','case','sigma_um','seed'),
        'E08':('geom','mod','case')}

def execute(name,task):
    if name=='E04':from E04_noise_bias import run_one
    elif name=='E07':from E07_model_discrepancy import run_one
    else:from E08_generalization import run_one
    return run_one(task)

def main(workers,jacobian_scheme='2-point'):
    import E04_noise_bias as e4
    import E07_model_discrepancy as e7
    import E08_generalization as e8
    OUT.mkdir(parents=True,exist_ok=True)
    stamp=provenance()
    pending=[];manifest={'provenance':stamp,'historical_unversioned':{},'expected':{}}
    for name,mod in [('E04',e4),('E07',e7),('E08',e8)]:
        path=ROOT/'results'/f'{name}_records.jsonl'
        backup=OUT/(name+'_records_before_campaign.jsonl')
        if not backup.exists():shutil.copy2(path,backup)
        rows=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
        fields=FIELDS[name]
        done={tuple(r[k] for k in fields) for r in rows}
        manifest['historical_unversioned'][name]=sum('provenance' not in r for r in rows)
        tasks=mod.task_list();manifest['expected'][name]=len(tasks)
        for t in tasks:
            if tuple(t[k] for k in fields) not in done:
                if name in ('E04','E07'):t['jacobian_scheme']=jacobian_scheme
                pending.append((name,t))
    (OUT/'completion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Missing tasks:',len(pending),flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(execute,name,t):(name,t) for name,t in pending}
        for f in concurrent.futures.as_completed(futures):
            name,t=futures[f]
            try:
                row=f.result();row['provenance']=stamp
                row['task_definition']=t
                with (ROOT/'results'/f'{name}_records.jsonl').open('a',encoding='utf-8') as out:
                    out.write(json.dumps(row)+'\n')
                print(name,t,'success',row['success'],'RMSE',row['fit_rmse_mm'],flush=True)
            except Exception as e:
                with (OUT/'completion_errors.jsonl').open('a',encoding='utf-8') as out:
                    out.write(json.dumps(dict(experiment=name,task=t,error=str(e)))+'\n')
                print('ERROR',name,t,str(e),flush=True)
    status={}
    for name in FIELDS:
        rows=[json.loads(l) for l in (ROOT/'results'/f'{name}_records.jsonl').read_text().splitlines() if l.strip()]
        status[name]=dict(records=len(rows),expected=manifest['expected'][name],success=sum(r['success'] for r in rows))
    (OUT/'completion_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print('Complete',status,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--jacobian-scheme',choices=['2-point','scaled-central'],default='2-point')
    args=parser.parse_args();main(args.workers,args.jacobian_scheme)
