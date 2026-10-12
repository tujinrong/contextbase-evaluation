"""Staged clean rebuild, independent regression gates, then reversible promotion."""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from .registry import configure, resolve_profile, process_env, digest
from .discovery import probe


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    value=obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    path.write_text(value,encoding='utf-8',newline='\n')


def hashes(path: Path) -> dict:
    if not path.exists():return {}
    return {p.relative_to(path).as_posix():digest(p.read_bytes()) for p in sorted(path.rglob('*'))
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix!='.pyc'}


def negative_control_command(module: str) -> list[str]:
    """The reviewed profile owns native tests and the number of selected mutations."""
    if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
        raise ValueError('Invalid native validation module')
    script = ("import importlib,sys; from pathlib import Path; "
              "r=importlib.import_module(sys.argv[1]).mutation_checks(Path.cwd()); "
              "assert type(r.get('total')) is int and r['total'] > 0 "
              "and r.get('detected') == r['total'], r")
    return [sys.executable, '-c', script, module]


def command(root: Path, env: dict, args: list[str], log: str, timeout: int = 300) -> dict:
    start=time.perf_counter()
    print('Stage: '+log, file=sys.stderr, flush=True)
    proc=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    write(root/'report/rebuild/logs'/log,proc.stdout+proc.stderr)
    if proc.returncode:
        raise RuntimeError(f'{log}: exit={proc.returncode}\n'+(proc.stdout+proc.stderr)[-2400:])
    return {'command':args,'seconds':round(time.perf_counter()-start,4),'exit_code':0,'log':log}


def regression(root: Path, profile: dict) -> dict:
    expected=json.loads((Path(profile['directory'])/profile['baseline']).read_text(encoding='utf-8'))
    actual={}
    for path in (root/'.specgen-state/quality/outlines').glob('*.json'):
        f=json.loads(path.read_text());subset={k:f.get(k) for k in expected['semantic_keys']}
        raw=json.dumps(subset,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        actual[f['id']]={'sha256':digest(raw),'items':len(f['items']),'events':len(f['events'])}
    different=[key for key in sorted(set(expected['features'])|set(actual)) if expected['features'].get(key)!=actual.get(key)]
    result={'status':'equal' if not different else 'different','reference_revision':expected['revision'],
            'features':len(actual),'items':sum(x['items'] for x in actual.values()),'events':sum(x['events'] for x in actual.values()),
            'changed_features':different,'scope':'Normalized feature facts including items, events, DB usage, rules and source evidence; not a new business approval'}
    write(root/'report/rebuild/semantic-regression.json',result)
    if different:raise RuntimeError('Baseline semantic regression: '+', '.join(different))
    return result


def promote(root: Path, stage: Path, replace_output: bool) -> dict:
    paths=['output','report','pilot','.specgen-state']
    if (stage/'ContextBase').exists():paths.append('ContextBase')
    if (stage/'QA').exists():paths.append('QA')
    if not replace_output and (root/'output').exists():raise ValueError('Use --replace-output for an explicitly authorized clean replacement; use build for MD edits')
    for name in paths:
        if (root/name).is_symlink() or (stage/name).is_symlink():raise ValueError('Refusing generated-root symlink')
    backup=root/'.contextbase-work'/('previous-'+stage.name);backup.mkdir()
    moved=[];installed=[]
    try:
        for name in paths:
            old=root/name;new=stage/name
            if old.exists():old.rename(backup/name);moved.append(name)
            if new.exists():new.rename(old);installed.append(name)
    except Exception:
        for name in reversed(installed):(root/name).rename(stage/name)
        for name in reversed(moved):(backup/name).rename(root/name)
        raise
    return {'replaced':installed,'previous_copy':str(backup.relative_to(root)),
            'previous_file_count':sum(1 for p in backup.rglob('*') if p.is_file()),'history':'Git contains pre-refactor versions; local backup is ignored by Git'}


def rebuild(root: Path, config_file: str='config/project.toml', *, native: bool=False, browser: bool=False,
            replace_output: bool=False, pdf: bool=False, excel: bool=False) -> dict:
    root=root.resolve();cfg=configure(root,config_file);profile=resolve_profile(root,cfg)
    work=root/'.contextbase-work'
    if work.is_symlink():raise ValueError('Workspace must not be a symlink')
    work.mkdir(exist_ok=True);lock=work/'rebuild.lock'
    try:
        with lock.open('x') as stream:stream.write(str(os.getpid()))
    except FileExistsError:raise ValueError('Another rebuild is running; do not delete the lock until confirmed stopped')
    stage=Path(tempfile.mkdtemp(prefix='build-',dir=work));start=time.perf_counter()
    original_input=hashes(root/cfg['input']);source_code={p:hashes(root/p) for p in ['src','src-dynamic']}
    persistent_before={name:hashes(root/name) for name in ['QA','report']}
    identity_before=(root/'ContextBase/identities.json').read_bytes() if (root/'ContextBase/identities.json').exists() else None
    stages=[];result={'status':'running','workspace':str(stage.relative_to(root)),'profile':profile['id'] if profile else 'generic'}
    try:
        # New workspace receives input and implementation only: no output, index or cache.
        for name in ['src','src-dynamic','config','docs','examples']:
            if (root/name).is_dir():shutil.copytree(root/name,stage/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
        shutil.copytree(root/cfg['input'],stage/cfg['input'],symlinks=True)
        # Retain stable public identifiers, not old analysis or generated prose.
        identity=root/'ContextBase/identities.json'
        if identity.exists():
            if identity.is_symlink():raise ValueError('Unsafe identity ledger')
            (stage/'ContextBase').mkdir(exist_ok=True)
            shutil.copy2(identity,stage/'ContextBase/identities.json')
        if (root/'specgen.toml').exists():shutil.copy2(root/'specgen.toml',stage/'specgen.toml')
        # Preserve human QA answers and report history; never reuse output or analysis caches.
        for name in ['QA','report']:
            if (root/name).is_symlink():raise ValueError('Refusing persistent-root symlink')
            if (root/name).is_dir():
                if any(p.is_symlink() for p in (root/name).rglob('*')):raise ValueError('Persistent files cannot contain symlinks')
                shutil.copytree(root/name,stage/name,dirs_exist_ok=True)
        selected=resolve_profile(stage,cfg);env=process_env(stage,selected)
        write(stage/'report/rebuild/system-discovery.json',probe(stage,cfg))
        suites=['src/specgen/tests','src/docsite/tests','src/contextbase/tests']
        if selected:suites += [str(Path(selected['directory']).relative_to(stage)/s) for s in selected['test_suites']]
        for suite in suites:
            stages.append(command(stage,env,[sys.executable,'-m','unittest','discover','-s',suite,'-v'],suite.replace('/','-')+'.log'))
        canonical=bool(selected and selected.get('pipeline')=='canonical')
        if canonical:
            stages.append(command(stage,env,[sys.executable,'-m',selected['generation_module'],'--input',cfg['input'],'--cold'],'target-cold.log',600))
            target_report=stage/'report'/selected['report_directory']/'result.json'
            cold=json.loads(target_report.read_text())
            if cold.get('cache_hits')!=0 or cold.get('parsed_this_run',0)<=0:raise RuntimeError('New target did not start with fresh nonempty analysis')
            first=hashes(stage/'output/md')
            stages.append(command(stage,env,[sys.executable,'-m',selected['generation_module'],'--input',cfg['input']],'target-warm.log',600))
            if first!=hashes(stage/'output/md'):raise RuntimeError('Cold/warm target MD differs')
            validation=json.loads((stage/'report'/selected['report_directory']/'evaluation.json').read_text())
            if validation.get('errors') or not validation.get('input_unchanged'):raise RuntimeError('Target structural validation failed')
            semantics={'status':'new_target_static_review','previous_project_baseline_used':False,'target':selected['id'],'features':cold['features'],'items':cold['items'],'event_bindings':cold['event_bindings'],'cold_warm_equal':True,'full_semantic_equivalence':'not_verified'}
            write(stage/'report/rebuild/semantic-regression.json',semantics)
            write(stage/'report/rebuild/native-status.json',{'status':'not_run','requested':native,'reason':'Native reconstruction is not configured for this target; no earlier project results reused'})
            revision=os.environ.get('GITHUB_SHA') or 'main'
            stages.append(command(stage,env,[sys.executable,'-m','docsite','build','--repository',cfg['repository'],'--revision',revision],'publication-target.log',600))
            stages.append(command(stage,env,[sys.executable,'-m','docsite','check'],'publication-check.log',600))
        elif selected:
            reviewed=json.loads((Path(selected['directory'])/'profile.json').read_text())
            unmatched=[i['path'] for i in reviewed['inventory'] if i['selected'] and
                       (not (stage/i['path']).is_file() or digest((stage/i['path']).read_bytes())!=i['sha256'])]
            if unmatched:raise ValueError('Reviewed dynamic profile is stale; review affected source before using its prose: '+str(unmatched[:10]))
            stages.append(command(stage,env,[sys.executable,'-m',selected['initial_module'],'generate','--input',cfg['input'],'--cold','--label','fresh'],'initial-analysis.log'))
            cold=json.loads((stage/'report/overview/metrics-fresh.json').read_text())
            if cold['cache_hits']!=0 or cold['parsed']==0:raise RuntimeError('Fresh run unexpectedly reused a cache or parsed no sources')
            stages.append(command(stage,env,[sys.executable,'-m',selected['generation_module'],'--input',cfg['input'],'--cold'],'quality-cold.log'))
            first=hashes(stage/'output')
            stages.append(command(stage,env,[sys.executable,'-m',selected['generation_module'],'--input',cfg['input']],'quality-warm.log'))
            if first!=hashes(stage/'output'):raise RuntimeError('Cold/warm generated documents differ')
            semantics=regression(stage,selected)
            if native:
                stages.append(command(stage,env,[sys.executable,'-m',selected['native_module']],'native-pilot.log'))
                stages.append(command(stage,env,negative_control_command(selected['native_module']),'native-negative-controls.log',600))
            else:write(stage/'report/rebuild/native-status.json',{'status':'not_run','reason':'--native was not supplied','old_results_used':False})
            revision=os.environ.get('GITHUB_SHA') or 'main'
            stages.append(command(stage,env,[sys.executable,'-m','docsite.ci','--repository',cfg['repository'],'--revision',revision],'publication.log',600))
        else:
            # P1/P2/P3 are independent processes with sealed JSON handoffs.
            for module, label in [('foundation','phase1-foundation.log'),
                                  ('detail','phase2-detail.log'),
                                  ('specification','phase3-specification.log')]:
                args=[sys.executable,'-m','contextbase.'+module]
                if module in {'foundation','detail'}:args.append('--cold')
                if module=='foundation':args += ['--config',config_file]
                stages.append(command(stage,env,args,label,600))
            stages.append(command(stage,env,[sys.executable,'-m','contextbase.validation'],'two-stage-contracts.log',180))
            semantics={'status':'partial','analysis_phases':2,'generation_programs':4,
                       'foundation':json.loads((stage/'report/foundation/result.json').read_text()),
                       'detail':json.loads((stage/'report/detail/result.json').read_text()),
                       'source_free_P3':json.loads((stage/'report/two-stage/source-free-replay.json').read_text()),
                       'independent_quality':{k:v for k,v in json.loads((stage/'report/quality/validation.json').read_text()).items() if k in {'status','errors','checks_count','independent_source_scan'}},
                       'message':'Two-stage static analysis; business equivalence is not fully verified'}
            write(stage/'report/rebuild/semantic-regression.json',semantics)
            write(stage/'report/generic/evaluation.json',{'status':'superseded_by_two_stage','reports':['report/foundation/result.json','report/detail/result.json']})
            write(stage/'report/rebuild/native-status.json',{'status':'not_run','requested':native,'reason':'No native execution in the two-stage static profile'})
            stages.append(command(stage,env,[sys.executable,'-m','docsite','build','--repository',cfg['repository']],'publication-generic.log',600))
            stages.append(command(stage,env,[sys.executable,'-m','docsite','check'],'publication-check.log'))
        excel_result={'count':0,'status':'not_requested'}
        if excel:
            stages.append(command(stage,env,[sys.executable,'-m','docsite.excel','--repository',cfg['repository']],'publication-excel.log',600))
            excel_result=json.loads((stage/'report/excel/validation.json').read_text(encoding='utf-8'))
            if excel_result.get('status')!='verified' or excel_result.get('errors'):
                raise RuntimeError('Excel validation failed; previous output retained')
        pdf_result={'count':0,'status':'not_requested'}
        if pdf:
            stages.append(command(stage,env,[sys.executable,'-m','docsite.pdf'],'publication-pdf.log',1200))
            pdf_result=json.loads((stage/'report/pdf/validation.json').read_text(encoding='utf-8'))
            if pdf_result.get('status')!='verified' or pdf_result.get('errors'):
                raise RuntimeError('PDF validation failed; published output retained')
        if browser:
            browser_args=[sys.executable,'-m','docsite.browser_check']
            if os.environ.get('DOCSITE_CHROMIUM'):browser_args += ['--executable',os.environ['DOCSITE_CHROMIUM']]
            stages.append(command(stage,env,browser_args,'browser.log',600))
            if selected and not canonical:stages.append(command(stage,env,[sys.executable,'-m','docsite.ci','--summary'],'publication-summary.log'))
        if original_input!=hashes(root/cfg['input']) or original_input!=hashes(stage/cfg['input']):raise RuntimeError('Input changed during rebuild')
        if source_code!={p:hashes(root/p) for p in source_code}:raise RuntimeError('Generator changed during rebuild; restart from scratch')
        for p in (stage/'pilot').rglob('*'):
            if p.is_dir() and p.name in {'bin','obj'}:shutil.rmtree(p)
        result.update(status='verified_static_output' if canonical else 'verified' if selected and native and browser else 'verified_structure_only',
                      clean_workspace=True,prior_cache_files=0,input_unchanged=True,input_files=len(original_input),
                      semantics=semantics,native_executed=native and bool(selected) and not canonical,browser_executed=browser,
                      generated_markdown=len(list((stage/'output/md').rglob('*.md'))),
                      generated_html=len(list((stage/'output/html').rglob('*.html'))),
                      generated_pdf=pdf_result['count'],pdf_status=pdf_result['status'],
                      generated_excel=excel_result['count'],excel_status=excel_result['status'],
                      stages=stages,total_seconds=round(time.perf_counter()-start,4),
                      limitation='New target static scope only; no prior-project accuracy or native-equivalence claim' if canonical else 'Two-stage structural validation; full business behavior, native DB/app execution and all-language precision are not verified')
        write(stage/'report/rebuild/result.json',result)
        text='# 入力からのクリーン再生成\n\n'
        text+=f"実行状態：{result['status']}。既存キャッシュの読込は0件。入力{len(original_input)}ファイルを変更せず、MD {result['generated_markdown']}文書・HTML {result['generated_html']}ページ・Excel {result['generated_excel']}文書を生成。\n\n"
        text+='## 解析範囲と定義の比較\n\n'+json.dumps(semantics,ensure_ascii=False,indent=2)+'\n\n'
        text+='## ソース構造\n\n汎用実行・検出・出版・基礎解析はsrc。対象案件に依存する説明・規則・解析拡張・Pilotとテストはsrc-dynamic。inputは非実行の原本。\n\n'
        text+='## 検証の限界\n\n新しい言語の形式検出と限定抽出は、既存案件と同じ精度を保証しません。Accessバイナリ内部、実画面、実DB、動的連携は別途解析・検証が必要です。\n'
        write(stage/'report/rebuild/再生成結果.md',text)
        if persistent_before!={name:hashes(root/name) for name in persistent_before}:
            raise RuntimeError('QA/report changed during rebuild; preserve the new human edits and retry')
        identity_now=(root/'ContextBase/identities.json').read_bytes() if (root/'ContextBase/identities.json').exists() else None
        if identity_before!=identity_now:raise RuntimeError('Identity ledger changed during rebuild; preserve concurrent edits and retry')
        promotion=promote(root,stage,replace_output)
        result['promotion']=promotion;write(root/'report/rebuild/result.json',result)
        shutil.rmtree(stage)
        return result
    except Exception as exc:
        result.update(status='failed',error=str(exc),stages=stages,previous_output_retained=True,total_seconds=round(time.perf_counter()-start,4))
        write(stage/'report/rebuild/failure.json',result)
        write(root/'report/rebuild/latest-failure.json',result)
        raise
    finally:lock.unlink(missing_ok=True)
