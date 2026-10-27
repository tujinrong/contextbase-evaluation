from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
from .core import collect,digest,save,load
from .refine import preflight,refine
from .dblineage import enrich
from .contexts import apply as apply_contexts
from .delivery import publish
from .review import run_review


def compact_state(root):
    """Compact whitespace only; preserve cache integrity and all evidence values."""
    base=root/'.specgen-state/overview';size_before=size_after=0
    for path in sorted(base.rglob('*.json')):
        if path.is_symlink():raise ValueError('symlink state rejected')
        raw=path.read_bytes();obj=json.loads(raw)
        text=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
        size_before+=len(raw);size_after+=len(text.encode())
        if 'outlines' not in path.parts:save(path,text)
    return {'state_serialized_bytes_before':size_before,'state_compact_bytes_estimate':size_after}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Read-only source analysis and flat overview specifications')
    parser.add_argument('command',choices=['generate']);parser.add_argument('--root',default='.')
    parser.add_argument('--input',default='input');parser.add_argument('--cold',action='store_true')
    parser.add_argument('--label',default='current')
    parser.add_argument('--strict',action='store_true',help='Fail when business implementation readiness is not approved')
    parser.add_argument('--verify-reproducibility',action='store_true')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if not args.label.replace('-','').replace('_','').isalnum():parser.error('invalid label')
    lock=root/'.specgen-state/overview.lock';lock.parent.mkdir(exist_ok=True)
    try:
        with lock.open('x',encoding='utf-8') as f:f.write('running\n')
    except FileExistsError:raise SystemExit('Another run or stale lock exists: '+str(lock))
    start=time.perf_counter()
    try:
        plan=preflight(root,args.input);data=collect(root,args.input,args.cold)
        before=time.perf_counter();refine(root,data);enrich(data);apply_contexts(root,data)
        for feature in data['features']:
            feature['layout_rows']=[{k:item[k] for k in ['order','name','role','line']} for item in feature['items']]
        resolution_seconds=round(time.perf_counter()-before,6)
        for r in data['records'].values():
            for m in r.get('methods',[]):
                key=r['path']+'#'+m['name']+'@'+str(m['line'])
                if key in data['methods']:m.update(data['methods'][key])
        expected=load(root/'.specgen-state/overview/published-fingerprints.json',{})
        before=time.perf_counter();result=publish(root,data);result['publication_seconds']=round(time.perf_counter()-before,6)
        before=time.perf_counter();review=run_review(root,data);result['review_seconds']=round(time.perf_counter()-before,6)
        fingerprints={p.name:digest(p.read_bytes()) for p in (root/'output').glob('*.md')}
        comparison={'status':'not_requested','changed':[]}
        if args.verify_reproducibility:
            comparison={'status':'equal' if fingerprints==expected else 'different','changed':sorted(k for k in set(expected)|set(fingerprints) if expected.get(k)!=fingerprints.get(k))}
        save(root/'.specgen-state/overview/published-fingerprints.json',fingerprints)
        result.update(data['stats']);result.update(compact_state(root));result.update({'label':args.label,'reference_resolution_seconds':resolution_seconds,'adapter_families':plan['adapter_families'],'input_snapshot':data['system']['snapshot_id'],'total_seconds':round(time.perf_counter()-start,6),'evaluation_status':review['status'],'automatic_errors':review['automatic_errors'],'review_findings':review['review_findings'],'reproducibility':comparison})
        report=root/'report/overview';save(report/('metrics-'+args.label+'.json'),result);save(report/'実行結果.json',result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if result['conflicts'] or result['errors'] or review['automatic_errors'] or comparison['status']=='different':return 1
        if args.strict and review['status']!='approved':return 1
        return 0
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':raise SystemExit(main())
