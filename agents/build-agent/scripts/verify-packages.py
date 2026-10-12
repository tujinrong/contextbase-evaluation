"""Verify and build delivered source archives in separate package-local scratch trees."""
from pathlib import Path, PurePosixPath
import datetime, hashlib, json, re, shutil, subprocess, sys, zipfile

ROOT=Path(__file__).resolve().parents[3]
run=sys.argv[1] if len(sys.argv)==2 else ''
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',run):raise SystemExit('Fresh package run ID required')
manifest=json.loads((ROOT/f'test-project1/report/{run}-source-packages.json').read_text(encoding='utf-8'))
prefix=ROOT/f'test-project1/test-report/{run}-source-package-validation'
if any(prefix.with_suffix(ext).exists() for ext in ['.json','.raw.log']):raise SystemExit('Old package validation must be preserved')
for pack in manifest['packages']:
    if (ROOT/f"test-project1/srcs/{pack['profile']}/build/source-isolation-{run}").exists():raise SystemExit('Fresh standalone extraction required')
results=[];prepared=[];logs=[]
def invoke(profile,cwd,command):
    p=subprocess.run(command,cwd=cwd,capture_output=True,timeout=240)
    output=(p.stdout+p.stderr).decode('utf-8','replace')
    logs.append('['+profile+'] '+subprocess.list2cmdline(command)+'\n'+output)
    results.append({'profile':profile,'cwd':cwd.relative_to(ROOT).as_posix(),'command':command,'exitCode':p.returncode,'passed':p.returncode==0})
    print(f'{profile}: {command[0]} exit={p.returncode}',flush=True)
    if p.returncode:raise RuntimeError('Standalone source build failed')
try:
    for pack in manifest['packages']:
        source=ROOT/pack['file'];destination=ROOT/f"test-project1/srcs/{pack['profile']}/build/source-isolation-{run}"
        if hashlib.sha256(source.read_bytes()).hexdigest()!=pack['sha256']:raise RuntimeError('Archive hash mismatch')
        expected={x['file']:x for x in pack['entries']}
        with zipfile.ZipFile(source) as archive:
            if set(archive.namelist())!=set(expected):raise RuntimeError('Archive members do not match manifest')
            for member in archive.infolist():
                name=PurePosixPath(member.filename)
                if name.is_absolute() or '..' in name.parts or ':' in member.filename:raise RuntimeError('Unsafe archive path')
                data=archive.read(member)
                if hashlib.sha256(data).hexdigest()!=expected[member.filename]['sha256']:raise RuntimeError('Member hash mismatch')
            destination.mkdir(parents=True)
            archive.extractall(destination)
        prepared.append({'profile':pack['profile'],'destination':destination.relative_to(ROOT).as_posix(),'archiveSha256':pack['sha256'],'members':len(expected),'memberHashesVerified':True})
    print('PREPARED 7 independent source-only archives',flush=True)
    for profile in ['CSharp_WPF','VB.NET_WinForms','CSharp_ASPNET','Vue_CSharpAPI']:
        cwd=ROOT/f'test-project1/srcs/{profile}/build/source-isolation-{run}'
        solution='StudentManagement.WinForms.slnx' if profile=='VB.NET_WinForms' else 'StudentManagement.slnx'
        invoke(profile,cwd,['dotnet','build',solution,'-c','Release','--nologo','-p:RestoreLockedMode=true'])
        if profile in ['CSharp_WPF','VB.NET_WinForms']:
            shell=shutil.which('pwsh') or shutil.which('powershell')
            if not shell:raise RuntimeError('PowerShell is required to build native deployment resources')
            invoke(profile,cwd,[shell,'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File','database/native/Build-Native.ps1'])
        if profile=='Vue_CSharpAPI':
            npm=shutil.which('npm.cmd') or shutil.which('npm')
            invoke(profile,cwd/'frontend',[npm,'ci'])
            invoke(profile,cwd/'frontend',[npm,'run','build'])
finally:
    prefix.with_suffix('.raw.log').write_text('\n'.join(logs),encoding='utf-8')
    prefix.with_suffix('.json').write_text(json.dumps({'runId':run,'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASSED' if len(results)==8 and all(x['passed'] for x in results) else 'FAILED_OR_INCOMPLETE','prepared':prepared,'runs':results,'scope':'archive member hashes, separate extraction, four standalone .NET solution builds, two local native deployment resource builds and Vue npm install/build','notExecuted':['SQL Server deployment/integration','IBM i compile/runtime','Linux COBOL deployment','Access source rebuild (separate record)']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
