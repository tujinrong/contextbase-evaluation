"""Validate current source-only archives; isolated work stays in each method .tmp."""
from pathlib import Path, PurePosixPath
import argparse, datetime, hashlib, json, os, re, shutil, stat, subprocess, sys, zipfile
sys.dont_write_bytecode=True
from output_layout import ensure_directory, regular_destination, write_json_latest, write_latest
from project_scope import selected_profiles, dotnet_entry, regular_input, production_helpers, is_test_artifact

ROOT=Path(__file__).resolve().parents[4]
parser=argparse.ArgumentParser();parser.add_argument('run_id');parser.add_argument('--project',required=True);parser.add_argument('--profile');parser.add_argument('--hashes-only',action='store_true')
args=parser.parse_args();run=args.run_id
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',run):raise SystemExit('Safe package run ID required')
selected=selected_profiles(ROOT,args.project,args.profile)
base=ROOT/args.project/('srcs/'+args.profile if args.profile else '')
prefix=base/'build/test-results/source-package-validation';scratch=base/'.tmp/source-package'
results=[];prepared=[];logs=[];error=None
write_json_latest(prefix.with_suffix('.json'),{'runId':run,'status':'RUNNING','formalScore':None},scratch)

def invoke(profile,cwd,command):
    result=subprocess.run(command,cwd=cwd,capture_output=True,timeout=240)
    output=(result.stdout+result.stderr).decode('utf-8','replace')
    logs.append('['+profile+'] '+subprocess.list2cmdline(command)+'\n'+output)
    results.append({'profile':profile,'cwd':cwd.relative_to(ROOT).as_posix(),'command':command,'exitCode':result.returncode,'passed':result.returncode==0})
    print(f'{profile}: {command[0]} exit={result.returncode}',flush=True)
    if result.returncode:raise RuntimeError('Standalone source build failed')

try:
    manifest=json.loads((base/'build/generation/source-packages.json').read_text(encoding='utf-8'))
    packages=manifest.get('packages')
    if manifest.get('projectId')!=args.project or manifest.get('runId')!=run or manifest.get('sourceOnly') is not True or not isinstance(packages,list):raise RuntimeError('Current project/source-only package metadata required')
    names=[pack.get('profile') for pack in packages]
    if len(names)!=len(selected) or len(set(names))!=len(names) or set(names)!=set(selected):raise RuntimeError('Exactly the selected nonempty profile set is required')
    for pack in packages:
        profile=pack['profile'];owner=ROOT/args.project/'srcs'/profile
        helpers=production_helpers(owner)
        if pack['file']!=f'{args.project}/srcs/{profile}/build/source.zip':raise RuntimeError('Package outside current delivery path')
        source=ROOT/pack['file'];regular_destination(source)
        if hashlib.sha256(source.read_bytes()).hexdigest()!=pack['sha256']:raise RuntimeError('Archive hash mismatch')
        entries=pack['entries'];expected={entry['file']:entry for entry in entries}
        if not entries or len(entries)!=len(expected):raise RuntimeError('Nonempty unique package entries required')
        if not helpers.issubset(expected):raise RuntimeError('Declared production helper is missing from archive metadata')
        destination=owner/'.tmp/source-isolation'
        ensure_directory(owner/'.tmp')
        if destination.is_symlink() or str(destination.resolve()).casefold()!=str(destination.absolute()).casefold():raise RuntimeError('Redirected extraction destination refused')
        if destination.exists():shutil.rmtree(destination)
        ensure_directory(destination)
        with zipfile.ZipFile(source) as archive:
            members=archive.infolist();member_names=[item.filename for item in members]
            if set(member_names)!=set(expected) or len(members)!=len(expected) or len({name.casefold() for name in member_names})!=len(members):raise RuntimeError('Archive members do not match unique manifest entries')
            for member in members:
                name=PurePosixPath(member.filename)
                if name.is_absolute() or '..' in name.parts or ':' in member.filename or '\\' in member.filename or str(name)!=member.filename or member.is_dir() or stat.S_IFMT(member.external_attr>>16)==stat.S_IFLNK:raise RuntimeError('Unsafe archive path/type')
                if any(part in {'.tmp','spec','spec-eval','spec-analysis','tests','Tests','test-report','build','bin','obj','node_modules'} for part in name.parts):raise RuntimeError('Excluded input in source-only archive')
                if 'tools' in name.parts and member.filename not in helpers:raise RuntimeError('Undeclared production helper in source-only archive')
                if is_test_artifact(member.filename):raise RuntimeError('Test artifact in source-only archive')
                original=owner.joinpath(*name.parts);regular_input(original)
                if hashlib.sha256(original.read_bytes()).hexdigest()!=expected[member.filename].get('sourceSha256'):raise RuntimeError('Source changed after packaging')
                data=archive.read(member)
                if hashlib.sha256(data).hexdigest()!=expected[member.filename]['sha256']:raise RuntimeError('Member hash mismatch')
                target=destination.joinpath(*name.parts);ensure_directory(target.parent)
                with target.open('xb') as stream:stream.write(data)
                if os.name!='nt':target.chmod((member.external_attr>>16)&0o777)
        prepared.append({'profile':profile,'destination':destination.relative_to(ROOT).as_posix(),'archiveSha256':pack['sha256'],'members':len(expected),'memberHashesVerified':True})
    print(f'PREPARED {len(prepared)} independent source-only archives',flush=True)
    for profile in ([] if args.hashes_only else selected):
        cwd=ROOT/args.project/'srcs'/profile/'.tmp/source-isolation'
        solution=dotnet_entry(cwd)
        if solution:invoke(profile,cwd,['dotnet','build',solution,'-c','Release','--nologo','-p:RestoreLockedMode=true'])
        elif profile in ['CSharp_WPF','VB.NET_WinForms','CSharp_ASPNET','Vue_CSharpAPI']:raise RuntimeError('No unambiguous .NET build entry in the source-only archive')
        if (cwd/'database/native/Build-Native.ps1').is_file():
            shell=shutil.which('pwsh') or shutil.which('powershell')
            if not shell:raise RuntimeError('PowerShell is required for native resource build')
            invoke(profile,cwd,[shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File','database/native/Build-Native.ps1'])
        if (cwd/'frontend/build.py').is_file():
            invoke(profile,cwd/'frontend',[sys.executable,'-X','utf8','build.py'])
except Exception as failure:
    error=str(failure)
    print(error,file=sys.stderr)
finally:
    record={'projectId':args.project,'runId':run,'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FAILED' if error else 'PASSED','error':error,'prepared':prepared,'runs':results,'scope':'archive/source/member hashes and separate extraction only' if args.hashes_only else 'archive/source/member hashes, separate extraction and available standalone builds','notExecuted':['All standalone builds' if args.hashes_only else 'IBM i compile/runtime, Linux COBOL deployment, Access source rebuild','SQL Server integration','Formal acceptance/scoring'],'formalScore':None}
    write_latest(prefix.with_suffix('.raw.log'),'\n'.join(logs)+('\nERROR '+error if error else ''),scratch)
    write_json_latest(prefix.with_suffix('.json'),record,scratch)
    for profile in selected:
        own=ROOT/args.project/'srcs'/profile
        write_json_latest(own/'build/test-results/source-package-validation.json',{**record,'prepared':[item for item in prepared if item['profile']==profile],'runs':[item for item in results if item['profile']==profile]},own/'.tmp/source-package')
raise SystemExit(1 if error else 0)
