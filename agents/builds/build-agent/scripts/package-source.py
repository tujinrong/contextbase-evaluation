"""Package each source independently, without original/evaluation specifications or test oracles."""
from pathlib import Path
import argparse,hashlib,json,re,sys,zipfile,os
sys.dont_write_bytecode=True
from output_layout import ensure_directory, regular_destination, staging_file, write_json_latest
from project_scope import selected_profiles, build_instruction, regular_input, production_helpers, is_test_artifact

ROOT=Path(__file__).resolve().parents[4]
SKIP={'.tmp','.runtime','spec','spec-eval','spec-analysis','build','bin','obj','node_modules','dist','.vs','.git','__pycache__','test-report','tests','Tests','tools'}
OMIT={'.env','appsettings.Local.json','input-manifest.json','spec-inputs.json','spec-mapping.json','test-status.json','SPEC-MAPPING.md','spec-contracts.json','IMPLEMENTATION.md','write_report.py','evidence.py','host_build.py','input_lock.py','generate.mjs','generate_database.mjs'}
BINARY={'.accdb','.accde','.laccdb','.exe','.dll','.pdb','.pyc','.pyo','.o','.so'}
parser=argparse.ArgumentParser()
parser.add_argument('run_id');parser.add_argument('--project',required=True);parser.add_argument('--profile')
args=parser.parse_args();run=args.run_id
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',run):raise SystemExit('Pass a safe run ID')
selected=selected_profiles(ROOT,args.project,args.profile)
report=ROOT/args.project/('srcs/'+args.profile if args.profile else '')/'build/generation'
ensure_directory(report)
manifest=report/'source-packages.json'
packages=[]
def source_files(folder, helpers):
    for directory, names, files in os.walk(folder, topdown=True, followlinks=False):
        directory=Path(directory)
        relative=directory.relative_to(folder)
        names[:]=sorted(name for name in names if name not in SKIP or any(helper.startswith((relative/name).as_posix()+'/') for helper in helpers))
        if 'tools' in relative.parts:
            names[:]=[name for name in names if any(helper.startswith((relative/name).as_posix()+'/') for helper in helpers)]
        for name in names:
            child=directory/name
            if child.is_symlink() or getattr(child,'is_junction',lambda:False)():raise RuntimeError('Linked source directory refused: '+str(child))
        for name in sorted(files):
            source=directory/name
            parts=source.relative_to(folder)
            if any(part in SKIP for part in parts.parts) and parts.as_posix() not in helpers:continue
            yield source

for profile in selected:
    folder=ROOT/args.project/'srcs'/profile
    if not folder.is_dir() or folder.is_symlink() or str(folder.resolve()).casefold()!=str(folder.absolute()).casefold():raise RuntimeError('Regular selected source root required')
    helpers=production_helpers(folder)
    state_file=folder/'build/generation/regeneration.json'
    state=json.loads(state_file.read_text('utf-8')) if state_file.is_file() else None
    if state and (state.get('runId')!=run or state.get('profileId')!=profile):raise RuntimeError('Generation status belongs to another run/profile')
    generation_status=state.get('status','NOT_RECORDED') if state else 'NOT_RECORDED'
    final=folder/'build/source.zip'
    scratch=folder/'.tmp/source-package'
    regular_destination(final)
    filename=staging_file(scratch,'source.zip')
    entries=[]
    with zipfile.ZipFile(filename,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for source in source_files(folder, helpers):
            relative=source.relative_to(folder)
            helper=relative.as_posix() in helpers
            if (any(p in SKIP for p in relative.parts) and not helper) or source.name in OMIT:continue
            if source.is_symlink():raise RuntimeError('Symlinks not allowed: '+str(source))
            if not source.is_file() or source.suffix.lower() in BINARY:continue
            if is_test_artifact(relative) or source.name.startswith('static_check'):continue
            data=source.read_bytes();original_hash=hashlib.sha256(data).hexdigest();transformation=None
            if relative.as_posix()=='README.md':
                command=build_instruction(folder)
                data=('# '+profile+' source material\n\nThis archive is independent. Original specifications, evaluation criteria, test expectations and input evidence are excluded.\n\nGeneration status: '+generation_status+'. Packaging and hash verification do not establish feature completion or runtime acceptance. Consult the accompanying generation record for incomplete scope.\n\nBuild: '+command+'\n\nRequired external SDKs, runtimes and configured database are supplied by the execution environment. Generated program and database sources are included; original-spec regeneration is outside this source-only input. Database/deployment instructions are local to this archive.\n').encode()
                transformation='source-input readme replaces generation readme'
            elif relative.as_posix()=='Makefile' and profile=='COBOL' and not (folder/'build.py').is_file():
                text=data.decode('utf-8')
                text=text.replace('.PHONY: all inputs generated dependencies probes check clean','.PHONY: all dependencies clean').replace('all: inputs dependencies','all: dependencies')
                text=re.sub(r'^inputs:.*?(?=^dependencies:)', '', text, flags=re.M|re.S)
                text=re.sub(r'^\.tmp/linux/date-probe:.*?(?=^clean:)', '', text, flags=re.M|re.S)
                data=text.encode();transformation='build generated production sources without specification lock or excluded probes'
            elif relative.as_posix()=='database/native/Build-Native.ps1' and profile=='CSharp_WPF':
                text=data.decode('utf-8')
                text=re.sub(r"^& python -X utf8 .*'generate_messages\.py'\).*\r?\nif \(\$LASTEXITCODE -ne 0\).*Native message generation failed.*\r?\n",'',text,flags=re.M)
                data=text.encode();transformation='use included production message catalog without original-spec regeneration'
            elif relative.as_posix()=='Build-Access.ps1' and profile=='Access':
                text=data.decode('utf-8')
                # Retain the builder and publication steps. A source-only rebuild has no original specifications to hash.
                pattern=(r"(?m)^(?P<indent>[ \t]*)@\(Get-ChildItem -LiteralPath \(Join-Path \$PSScriptRoot '\.\./\.\./spec/Access'\)[^\r\n]*\r?\n"
                         r"[^\r\n]*\r?\n[ \t]*\}\) \| ConvertTo-Json -Depth 5 \| Set-Content -LiteralPath \(Join-Path \$taskReport 'inputs.json'\) -Encoding UTF8\r?$")
                replacement="[ordered]@{sourceOnly=$true;inputKind='generated-source';specificationInputs='excluded';reason='Original specifications are not included in this source-only package.';formalScore=$null} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'inputs.json') -Encoding UTF8"
                text,count=re.subn(pattern,lambda match:match['indent']+replacement,text)
                unknown_evidence=re.search(r"(?m)@\(Get-ChildItem[^\r\n]*\r?\n[^\r\n]*\r?\n[ \t]*\}\) \| ConvertTo-Json[^\r\n]*'inputs.json'",text)
                if count>1 or (not count and unknown_evidence) or re.search(r'(?:\.\./)+spec[/\\]',text):raise RuntimeError('Unreviewed Access specification-evidence dependency; source-only builder transformation requires review.')
                if count:
                    data=text.encode();transformation='original specification hashes are explicitly unavailable in source-only build evidence; builder and artifact publication unchanged'
            elif relative.as_posix()=='database/native/README.md':
                data=('# Local native database deployment\n\nUse the included native build entry point and INTERFACE.md for the local call contract. Apply only the schema/deployment resources belonging to this source tree to an explicitly approved isolated application database. Keep the existing database security settings and configured application identity; no database, authentication mode or product name is inferred by packaging. Original-spec regeneration and test results are excluded.\n').encode()
                transformation='production deployment instructions exclude specification links and test results'
            elif relative.as_posix()=='database/README.md':
                data=('# Local database deployment\n\nThis directory contains the database resources for this project. Use the supplied schema and seed only in a separately approved empty application database. Existing databases require an independently reviewed migration. Configure the local application identity, database driver, encryption and certificate verification in the execution environment. For SQLCLR resources, follow native/README.md if that directory is present. Original-spec regeneration is excluded from this source-only package.\n').encode()
                transformation='production deployment instructions exclude original-spec regeneration inputs'
            elif relative.as_posix() in {'profile.json','rpg-project.json'}:
                metadata=json.loads(data)
                for key in ['specRoot','inputRoot','specVersion','testRunner','hostTest','databaseGenerator','sourceOnlyExcluded']:metadata.pop(key,None)
                data=(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n').encode()
                transformation='runtime project metadata excludes original input and test references'
            elif relative.as_posix()=='frontend/package.json':
                metadata=json.loads(data);metadata['scripts']={k:v for k,v in metadata['scripts'].items() if not is_test_artifact(k)}
                data=(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n').encode();transformation='only production npm commands are retained'
            elif relative.as_posix()=='deploy/README.md' and profile=='COBOL':
                data=data.decode('utf-8').replace(' / `make check`','').encode();transformation='document production build without excluded probes'
            elif source.suffix.lower()=='.slnx':
                lines=[]
                for line in data.decode('utf-8').splitlines():
                    project_path=re.search(r'<Project[^>]*Path="([^"]+)"',line)
                    if project_path and any(part.lower()=='tests' for part in project_path.group(1).replace('\\','/').split('/')):continue
                    lines.append(line)
                data=('\n'.join(lines)+'\n').encode()
                transformation='test projects removed from source-only solution'
            if profile=='COBOL' and not (folder/'build.py').is_file() and (relative.as_posix()=='Makefile' or source.suffix in {'.cgi','.sh'}):
                data=data.replace(b'\r\n',b'\n');transformation=(transformation+'; ' if transformation else '')+'portable Linux line endings'
            name=relative.as_posix();mode=0o100755 if source.suffix in {'.cgi','.sh'} else 0o100644
            member=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0));member.create_system=3;member.external_attr=mode<<16;member.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(member,data)
            entries.append({'file':name,'sourceSha256':original_hash,'sha256':hashlib.sha256(data).hexdigest(),'unixMode':oct(mode),**({'transformation':transformation} if transformation else {})})
    # The only inputs to the archive are from this selected package.
    with zipfile.ZipFile(filename) as z:
        for item in z.infolist():
            if '..' in Path(item.filename).parts or (any(x in SKIP for x in Path(item.filename).parts) and item.filename not in helpers):raise RuntimeError('Forbidden archive member')
            if Path(item.filename).name in OMIT or is_test_artifact(item.filename):raise RuntimeError('Forbidden test or evidence member')
        if not entries:raise RuntimeError('Empty package')
        if not helpers.issubset({entry['file'] for entry in entries}):raise RuntimeError('Declared production helper was not packaged')
    os.replace(filename,final)
    packages.append({'profile':profile,'generationStatus':generation_status,'file':final.relative_to(ROOT).as_posix(),'bytes':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'entries':entries})
record={'projectId':args.project,'runId':run,'sourceOnly':True,'historyPolicy':'git-only; latest fixed paths','excluded':sorted(SKIP|OMIT),'packages':packages}
scratch=ROOT/args.project/('srcs/'+args.profile if args.profile else '')/'.tmp/source-package'
write_json_latest(manifest,record,scratch)
# A profile's package record is also usable by its scoped manifest.
for pack in packages:
 local=ROOT/args.project/'srcs'/pack['profile']/'build/generation/source-packages.json'
 if local!=manifest:write_json_latest(local,{**record,'packages':[pack]},ROOT/args.project/'srcs'/pack['profile']/'.tmp/source-package')
print(json.dumps({'profiles':len(packages),'files':sum(len(p['entries']) for p in packages),'manifest':manifest.relative_to(ROOT).as_posix()}))
