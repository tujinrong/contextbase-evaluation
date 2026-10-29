"""Check the selected project's current deliveries; never inspect evaluation inputs."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
sys.dont_write_bytecode=True
from output_layout import write_json_latest
from project_scope import selected_profiles

ROOT=Path(__file__).resolve().parents[4]
parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--profile')
parser.add_argument('--allow-spec-repair',action='append',default=[],help='Exact specification file with a current local-spec-fix.json and matching before/after hashes')
parser.add_argument('--allow-spec-update',action='append',default=[],help='Exact specification file with a user-requested spec-update.json and matching before/after/frozen hashes')
args=parser.parse_args()
if not re.fullmatch(r'(?:sample|test)-project[1-9]\d*',args.project):raise SystemExit('Explicit existing project required')
project=ROOT/args.project
if not project.is_dir():raise SystemExit('Project does not exist')
PROFILES=selected_profiles(ROOT,args.project,args.profile)
findings=[];methods=[];final_files=[]

def redirected(target):
    """Reject linked ancestors before reading a purported final file."""
    lexical=Path(os.path.abspath(target))
    for ancestor in [lexical,*lexical.parents]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():return True
    return str(lexical.resolve()).casefold()!=str(lexical).casefold()

def check_entries(entries):
    for entry in entries:
        if not isinstance(entry,dict) or not isinstance(entry.get('file'),str) or not re.fullmatch(r'[0-9a-f]{64}',str(entry.get('sha256',''))):
            findings.append({'code':'INVALID_MANIFEST_ENTRY'});continue
        file=entry['file'];target=ROOT/file
        if '.tmp' in Path(file).parts or 'spec-eval' in Path(file).parts or not target.resolve().is_relative_to(ROOT) or redirected(target):
            findings.append({'file':file,'code':'EXCLUDED_MANIFEST_ENTRY'});continue
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=entry['sha256']:
            findings.append({'file':file,'code':'HASH_MISMATCH'})

for profile in PROFILES:
    base=project/'srcs'/profile;build=base/'build';generation=build/'generation'
    before=len(findings)
    try:
        inputs=json.loads((generation/'inputs.json').read_text('utf-8'))
        output=json.loads((generation/'outputs.json').read_text('utf-8'))
        structure=json.loads((generation/'structure.json').read_text('utf-8'))
        if not all(isinstance(record,dict) for record in [inputs,output,structure]) or not isinstance(inputs.get('files'),list) or not all(isinstance(output.get(section),list) for section in ['files','artifacts','delivery']):raise ValueError('Malformed current manifest')
    except (OSError,ValueError) as error:
        findings.append({'profile':profile,'code':'MISSING_OR_INVALID_CURRENT_RECORD','detail':str(error)})
        methods.append({'profileId':profile,'status':'FAIL'});continue
    if any(record.get('projectId')!=args.project or record.get('profileId')!=profile for record in [inputs,output,structure]) or not inputs.get('runId') or output.get('runId')!=inputs.get('runId') or structure.get('runId')!=inputs.get('runId') or structure.get('status')!='structure-check-passed' or inputs.get('inspectionOnly') is not False:
        findings.append({'profile':profile,'code':'NONCURRENT_CONTEXT'})
    for entries in [inputs['files'],output['files'],output['artifacts'],output['delivery']]:check_entries(entries)
    permitted={'app','publish','database','test-results','generation','spec-generation','source.zip','input-manifest.json'}
    if profile=='Access':
        permitted.add('seed-manifest.json')
        databases=[entry for entry in output['artifacts'] if isinstance(entry,dict) and isinstance(entry.get('file'),str) and entry.get('kind')=='standalone-access-database']
        if len(databases)!=1:findings.append({'profile':profile,'code':'EXACTLY_ONE_ACCESS_DELIVERY_REQUIRED'})
        for entry in databases:
            artifact=ROOT/entry['file']
            if artifact.parent==build and artifact.suffix.lower()=='.accdb':permitted.add(artifact.name)
            else:findings.append({'file':entry['file'],'code':'ACCESS_DELIVERY_OUTSIDE_FIXED_BUILD'})
    for child in build.iterdir():
        if child.name not in permitted:findings.append({'file':child.relative_to(ROOT).as_posix(),'code':'UNEXPECTED_BUILD_HISTORY_OR_WORK'})
    for directory,names,files in os.walk(base,topdown=True,followlinks=False):
        retained=[]
        for name in names:
            child=Path(directory)/name
            if name in {'.tmp','spec','spec-eval'}:continue
            if child==build:continue
            # The frontend dependency entry is deliberately a link to its own scratch.
            if name=='node_modules' and profile=='Vue_CSharpAPI' and child==base/'frontend/node_modules' and child.resolve()==(base/'.tmp/frontend/node_modules').resolve() and not redirected(base/'.tmp/frontend/node_modules'):continue
            if name in {'build','bin','obj','.vs','test-report','node_modules','dist','__pycache__','.runtime','toolchain','source-isolation','browser-profile'}:
                findings.append({'file':child.relative_to(ROOT).as_posix(),'code':'WORK_OUTSIDE_TMP'});continue
            if redirected(child):findings.append({'file':child.relative_to(ROOT).as_posix(),'code':'LINKED_SOURCE_DIRECTORY'});continue
            retained.append(name)
        names[:]=retained
    coverage={entry['file'] for section in ['artifacts','delivery'] for entry in output[section] if isinstance(entry,dict) and isinstance(entry.get('file'),str)}
    coverage.add((generation/'outputs.json').relative_to(ROOT).as_posix())
    for directory,names,files in os.walk(build,followlinks=False):
        safe=[]
        for name in names:
            child=Path(directory)/name
            if redirected(child):findings.append({'file':child.relative_to(ROOT).as_posix(),'code':'LINKED_FINAL_DIRECTORY'})
            else:safe.append(name)
        names[:]=safe
        for file in files:
            target=Path(directory)/file
            relative=target.relative_to(ROOT).as_posix()
            if redirected(target):findings.append({'file':relative,'code':'LINKED_FINAL_FILE'})
            if relative not in coverage:findings.append({'file':relative,'code':'UNRECORDED_FINAL_FILE'})
            final_files.append(relative)
    probe=f'{args.project}/srcs/{profile}/.tmp/generated-probe.json'
    ignored=subprocess.run(['git','check-ignore','-q','--no-index',probe],cwd=ROOT).returncode==0
    if not ignored:findings.append({'profile':profile,'code':'TMP_NOT_IGNORED'})
    methods.append({'profileId':profile,'runId':inputs.get('runId'),'inputFiles':len(inputs['files']),'sourceFiles':len(output['files']),'artifactFiles':len(output['artifacts']),'status':'PASS' if len(findings)==before else 'FAIL'})

ignored=subprocess.run(['git','-c','core.quotePath=false','check-ignore','--stdin','--no-index'],cwd=ROOT,input='\n'.join(final_files)+'\n',capture_output=True,text=True,encoding='utf-8')
for file in ignored.stdout.splitlines():findings.append({'file':file,'code':'FINAL_RESULT_GIT_IGNORED'})
tracked=subprocess.run(['git','ls-files','-z','--',args.project,'agents/builds/build-agent'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').split('\0')
for file in tracked:
    if '.tmp' in Path(file).parts:findings.append({'file':file,'code':'TMP_TRACKED'})
protected_paths=[f'{args.project}/spec',f'{args.project}/spec-eval',f'{args.project}/QA',f'{args.project}/qa',*[f':(glob){args.project}/srcs/*/{name}/**' for name in ['spec','spec-eval','QA','qa','fixtures']]]
protected_paths.extend(f':(glob){args.project}/srcs/*/**/{pattern}' for pattern in ['*fixture*.json','*Fixture*.json'])
protected_paths.append(f':(glob){args.project}/srcs/Access/tests/**/*.json')
business=subprocess.run(['git','diff','--name-only','-z','HEAD','--',*protected_paths],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
untracked=subprocess.run(['git','ls-files','-z','--others','--exclude-standard','--',f'{args.project}/spec',f'{args.project}/spec-eval',f'{args.project}/QA',f'{args.project}/qa'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
protected_changes=sorted(set(file for file in (business.stdout+untracked.stdout).split('\0') if file))
authorized_repairs=[];authorized_updates=[]
for file in protected_changes:
    if file not in args.allow_spec_repair and file not in args.allow_spec_update:
        findings.append({'file':file,'code':'PROTECTED_INPUT_CHANGED'});continue
    try:
        if file in args.allow_spec_repair and file in args.allow_spec_update:raise ValueError('A change must have exactly one classification')
        relative=Path(file);parts=relative.parts
        if len(parts)<4 or parts[:2]!=(args.project,'spec') or parts[2] not in PROFILES or redirected(ROOT/relative):raise ValueError('Only the exact regular method specification may be repaired')
        base=project/'srcs'/parts[2]
        update=file in args.allow_spec_update
        repair_set=json.loads((base/'build/generation'/('spec-update.json' if update else 'local-spec-fix.json')).read_text('utf-8'))
        matches=[entry for entry in repair_set.get('changes' if update else 'fixes',[repair_set]) if entry.get('file')==file]
        if len(matches)!=1:raise ValueError('Exactly one explicit local repair record required')
        record={**matches[0],'runId':matches[0].get('runId',repair_set.get('runId'))}
        if update:
            if repair_set.get('classification') not in {'user-requested-platform-change','user-requested-ui-change','user-requested-authentication-change'} or not isinstance(repair_set.get('userInstruction'),str) or not repair_set['userInstruction'].strip():raise ValueError('Explicit user-requested platform, UI or authentication change evidence required')
            record.update(classification=repair_set['classification'],userInstruction=repair_set['userInstruction'])
        frozen=json.loads((base/'build/generation/inputs.json').read_text('utf-8'))
        current=(ROOT/relative).read_bytes()
        previous=subprocess.run(['git','show',f'HEAD:{file}'],cwd=ROOT,capture_output=True)
        original=previous.stdout
        before_hashes={hashlib.sha256(data).hexdigest() for data in [original,original.replace(b'\r\n',b'\n'),original.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')]}
        if previous.returncode:
            if not update or record.get('beforeSha256') is not None or record.get('beforeVersion') is not None:raise ValueError('Creation requires explicit null previous version and hash')
            before_matches=True
        else:before_matches=str(record['beforeSha256']).lower() in before_hashes
        current_hash=hashlib.sha256(current).hexdigest()
        if record['file']!=file or record['runId']!=frozen['runId'] or not isinstance(record.get('reason'),str) or not record['reason'].strip() or not before_matches or str(record['afterSha256']).lower()!=current_hash or not any(entry['file']==file and entry['sha256']==current_hash for entry in frozen['files']):raise ValueError('Repair record, HEAD, current source and frozen input disagree')
        (authorized_updates if update else authorized_repairs).append(record)
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as error:
        findings.append({'file':file,'code':'UNVERIFIED_SPEC_REPAIR','detail':str(error)})
for file in set(args.allow_spec_repair)-set(protected_changes):findings.append({'file':file,'code':'UNUSED_SPEC_REPAIR_EXCEPTION'})
for file in set(args.allow_spec_update)-set(protected_changes):findings.append({'file':file,'code':'UNUSED_SPEC_UPDATE_EXCEPTION'})
whitespace=subprocess.run(['git','-c','core.safecrlf=false','diff','--check','--',args.project,'agents/builds/build-agent',f'{args.project}-build-report.md'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
if whitespace.returncode:findings.append({'code':'DIFF_CHECK','detail':whitespace.stdout})
result={'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projectId':args.project,'status':'PASS' if not findings else 'FAIL','methods':methods,'finalFiles':len(final_files),'tmpIgnoredAndUntracked':not any(x['code'] in {'TMP_TRACKED','TMP_NOT_IGNORED'} for x in findings),'protectedInputDiff':protected_changes,'authorizedLocalSpecRepairs':authorized_repairs,'authorizedUserSpecUpdates':authorized_updates,'diffCheck':whitespace.returncode,'findings':findings,'scope':'current frozen input/output/artifact/delivery hashes, complete final coverage, fixed layout, Git inclusion/exclusion, HEAD and untracked protected-input diff with explicit hash-verified local repairs and user-requested platform or UI changes','notChecked':['runtime acceptance','SQL Server integration','IBM i native','formal scoring'],'formalScore':None}
write_json_latest(project/'build/test-results/final-integrity.json',result,project/'.tmp/output-layout')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(1 if findings else 0)
