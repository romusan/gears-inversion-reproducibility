"""Retrieve every reference's registration metadata from its primary registry.

Network records are cached verbatim. This verifies bibliographic identity;
abstract/claim support is assessed separately in the editorial audit.
"""
import json,urllib.request,urllib.parse,concurrent.futures,datetime,re,unicodedata,time
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
OUT=ROOT/'revision_12_2026-10-23';CACHE=OUT/'reference_sources'
CACHE.mkdir(parents=True,exist_ok=True)
refs=json.loads((ROOT/'referencias_42_q1.json').read_text(encoding='utf-8'))
def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).lower())
def fetch(item):
    i,ref=item;doi=ref.get('DOI');path=CACHE/f'ref_{i:02}.json'
    if not doi:return {'old_number':i,'url':ref.get('url'),'status':'standard_requires_primary_page'}
    url='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='')
    try:
        if path.exists():data=json.loads(path.read_text(encoding='utf-8'))
        else:
            req=urllib.request.Request(url,headers={'User-Agent':'GearMicrogeometryReferenceAudit/1.0','Accept':'application/json'})
            time.sleep(2.2)
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req,timeout=40) as response:data=json.load(response)
                    break
                except urllib.error.HTTPError as e:
                    if e.code!=429 or attempt==3:raise
                    time.sleep(max(float(e.headers.get('Retry-After','10')),10*(attempt+1)))
            path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
        m=data['message'];title=m.get('title',[''])[0]
        fields=['title','author','container-title','volume','issue','page','article-number','published','published-print','published-online','issued','type','publisher','URL','DOI','abstract','link','relation','update-to']
        oldtitle=ref.get('title',[''])[0]
        return dict(old_number=i,status='verified_registry',source_url=url,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    title_matches=norm(title)==norm(oldtitle),old_title=oldtitle,metadata={k:m[k] for k in fields if k in m})
    except Exception as e:return dict(old_number=i,status='fetch_failed',source_url=url,error=repr(e))
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:rows=list(pool.map(fetch,enumerate(refs,1)))
    (OUT/'bibliography_registry_audit.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    for r in rows:
        m=r.get('metadata',{});print(r['old_number'],r['status'],r.get('title_matches'),m.get('published'),m.get('page'),m.get('article-number'),flush=True)
