"""Run regression tests, two generations and native-language comparison."""
from __future__ import annotations
import hashlib,subprocess,sys
from pathlib import Path
from qualitygen.__main__ import run
from qualitygen.pilot import finalize
from overviewgen.core import save


def fingerprints(root):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'output').iterdir() if p.is_file() and p.suffix in {'.md','.html'}}


def main():
    root=Path.cwd();report=root/'report/quality';report.mkdir(parents=True,exist_ok=True)
    for folder in ['src/specgen/tests','src-dynamic/tkl/overviewgen/tests','src-dynamic/tkl/qualitygen/tests']:
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s',folder,'-v'],capture_output=True,text=True)
        save(report/('tests-'+folder.replace('/','-')+'.log'),result.stdout+result.stderr)
        print(folder,'exit',result.returncode,flush=True)
        if result.returncode:return result.returncode
    cold=run(root,cold=True);before=fingerprints(root);warm=run(root);after=fingerprints(root)
    reproducibility={'status':'equal' if before==after else 'different','changed':[k for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]}
    save(report/'performance.json',{'cold':cold,'warm':warm,'reproducibility':reproducibility,'timing_scope':'generation only; excludes setup, native test, Mermaid, upload and manual review'})
    if cold['automatic_errors'] or warm['automatic_errors'] or cold['conflicts'] or warm['conflicts'] or before!=after:return 1
    from .native_checks import run_native,mutation_checks
    outcome=run_native(root);finalize(root)
    if outcome['failed']:
        save(root/'report/pilot/native-mutations.json',{'status':'not_run_baseline_failed','detected':0,'total':4,'reason':'Negative controls require a passing clean comparison; pre-existing failures must not be counted as detections.'})
        return 1
    mutations=mutation_checks(root)
    print('native cases',outcome['cases'],'failed',outcome['failed'],'negative controls',mutations['detected'],'/',mutations['total'],flush=True)
    return int(outcome['failed']>0 or mutations['detected']!=mutations['total'])

if __name__=='__main__':raise SystemExit(main())
