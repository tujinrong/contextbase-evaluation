"""Package each source independently, without original/evaluation specifications or test oracles."""
from pathlib import Path
import argparse,hashlib,json,re,sys,zipfile,os
from output_layout import ensure_directory, regular_destination, staging_file, write_json_latest

ROOT=Path(__file__).resolve().parents[3]
PROFILES=['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']
SKIP={'.tmp','.runtime','spec','spec-eval','build','bin','obj','node_modules','dist','.vs','.git','__pycache__','test-report','tests','Tests','tools'}
OMIT={'.env','appsettings.Local.json','input-manifest.json','spec-inputs.json','spec-mapping.json','test-status.json','SPEC-MAPPING.md','spec-contracts.json','IMPLEMENTATION.md','write_report.py','evidence.py','host_build.py','input_lock.py','generate.mjs','generate_database.mjs'}
BINARY={'.accdb','.accde','.laccdb','.exe','.dll','.pdb','.pyc','.pyo','.o','.so'}
REQUIRED_BUILD_HELPERS={'tools/GeneratedPaths.ps1'}
parser=argparse.ArgumentParser()
parser.add_argument('run_id');parser.add_argument('--profile',choices=PROFILES)
args=parser.parse_args();run=args.run_id
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',run):raise SystemExit('Pass a safe run ID')
selected=[args.profile] if args.profile else PROFILES
report=ROOT/'test-project1'/('srcs/'+args.profile if args.profile else '')/'build/generation'
ensure_directory(report)
manifest=report/'source-packages.json'
packages=[]
def source_files(folder):
    for directory, names, files in os.walk(folder, topdown=True, followlinks=False):
        directory=Path(directory)
        relative=directory.relative_to(folder)
        names[:]=sorted(name for name in names if name not in SKIP or (not relative.parts and name=='tools'))
        if relative.parts and relative.parts[0]=='tools':names[:]=[]
        for name in names:
            child=directory/name
            if child.is_symlink() or getattr(child,'is_junction',lambda:False)():raise RuntimeError('Linked source directory refused: '+str(child))
        for name in sorted(files):
            source=directory/name
            parts=source.relative_to(folder)
            if any(part in SKIP for part in parts.parts) and parts.as_posix() not in REQUIRED_BUILD_HELPERS:continue
            yield source

for profile in selected:
    folder=ROOT/'test-project1/srcs'/profile
    final=folder/'build/source.zip'
    scratch=folder/'.tmp/source-package'
    regular_destination(final)
    filename=staging_file(scratch,'source.zip')
    entries=[]
    with zipfile.ZipFile(filename,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for source in source_files(folder):
            relative=source.relative_to(folder)
            helper=relative.as_posix() in REQUIRED_BUILD_HELPERS
            if (any(p in SKIP for p in relative.parts) and not helper) or source.name in OMIT:continue
            if source.is_symlink():raise RuntimeError('Symlinks not allowed: '+str(source))
            if not source.is_file() or source.suffix.lower() in BINARY:continue
            if re.search(r'test',source.name,re.I) or source.name.startswith('static_check'):continue
            data=source.read_bytes();original_hash=hashlib.sha256(data).hexdigest();transformation=None
            if relative.as_posix()=='README.md':
                command={'VB.NET_WinForms':'dotnet publish StudentManagement.WinForms.vbproj -c Release -o build/app -p:RestoreLockedMode=true','CSharp_WPF':'dotnet publish StudentManagement.Wpf.csproj -c Release -o build/app -p:RestoreLockedMode=true','CSharp_ASPNET':'dotnet publish StudentManagement.Web.csproj -c Release -o build/publish -p:RestoreLockedMode=true','Vue_CSharpAPI':'python -X utf8 frontend/build.py publish','COBOL':'Linux: make all (GnuCOBOL, C11, ICU, OpenSSL, unixODBC, pkg-config)','AS400_RPG':'IBM i: follow docs/deployment.md and compile cl/BUILD.clle','Access':'Windows Access: ./Build-Access.ps1 -SingleFile -CreateBackend -Compile'}[profile]
                data=('# '+profile+' source material\n\nThis archive is independent. Original specifications, evaluation criteria, test expectations and input evidence are excluded.\n\nBuild: '+command+'\n\nRequired external SDKs, runtimes and configured database are supplied by the execution environment. Generated program and database sources are included; original-spec regeneration is outside this source-only input. Database/deployment instructions are local to this archive.\n').encode()
                transformation='source-input readme replaces generation readme'
            elif relative.as_posix()=='Makefile' and profile=='COBOL':
                text=data.decode('utf-8')
                text=text.replace('.PHONY: all inputs generated dependencies probes check clean','.PHONY: all dependencies clean').replace('all: inputs dependencies','all: dependencies')
                text=re.sub(r'^inputs:.*?(?=^dependencies:)', '', text, flags=re.M|re.S)
                text=re.sub(r'^\.tmp/linux/date-probe:.*?(?=^clean:)', '', text, flags=re.M|re.S)
                data=text.encode();transformation='build generated production sources without specification lock or excluded probes'
            elif relative.as_posix()=='database/native/Build-Native.ps1' and profile=='CSharp_WPF':
                text=data.decode('utf-8')
                text=re.sub(r"^& python -X utf8 .*'generate_messages\.py'\).*\r?\nif \(\$LASTEXITCODE -ne 0\).*Native message generation failed.*\r?\n",'',text,flags=re.M)
                data=text.encode();transformation='use included production message catalog without original-spec regeneration'
            elif relative.as_posix()=='database/native/README.md':
                data=('# Local native database deployment\n\nBuild the local SQLCLR assembly and SQL resources with ./database/native/Build-Native.ps1. Generated SQL is updated in build/database/native; intermediate files stay in .tmp. Apply database/001_schema.sql, database/002_seed.sql, then build/database/native/000_sqlclr.sql, build/database/native/010_student_api.sql and build/database/native/020_master_api.sql in order to a separately approved empty SQL Server 2022 database. The DBA explicitly enables CLR and approves the exact assembly hash. Keep CLR strict security enabled. Configure the application database identity and its local roles. Application writes use the local stored procedures. See INTERFACE.md for the local call contract.\n').encode()
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
                metadata=json.loads(data);metadata['scripts']={k:v for k,v in metadata['scripts'].items() if not re.search(r'test',k,re.I)}
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
            if profile=='COBOL' and (relative.as_posix()=='Makefile' or source.suffix in {'.cgi','.sh'}):
                data=data.replace(b'\r\n',b'\n');transformation=(transformation+'; ' if transformation else '')+'portable Linux line endings'
            name=relative.as_posix();mode=0o100755 if name=='deploy/student.cgi' or source.suffix=='.sh' else 0o100644
            member=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0));member.create_system=3;member.external_attr=mode<<16;member.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(member,data)
            entries.append({'file':name,'sourceSha256':original_hash,'sha256':hashlib.sha256(data).hexdigest(),'unixMode':oct(mode),**({'transformation':transformation} if transformation else {})})
    # The only inputs to the archive are from this selected package.
    with zipfile.ZipFile(filename) as z:
        for item in z.infolist():
            if '..' in Path(item.filename).parts or (any(x in SKIP for x in Path(item.filename).parts) and item.filename not in REQUIRED_BUILD_HELPERS):raise RuntimeError('Forbidden archive member')
            if Path(item.filename).name in OMIT or re.search(r'test',Path(item.filename).name,re.I):raise RuntimeError('Forbidden test or evidence member')
        if not entries:raise RuntimeError('Empty package')
    os.replace(filename,final)
    packages.append({'profile':profile,'file':final.relative_to(ROOT).as_posix(),'bytes':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'entries':entries})
record={'runId':run,'sourceOnly':True,'historyPolicy':'git-only; latest fixed paths','excluded':sorted(SKIP|OMIT),'packages':packages}
scratch=ROOT/'test-project1'/('srcs/'+args.profile if args.profile else '')/'.tmp/source-package'
write_json_latest(manifest,record,scratch)
# A profile's package record is also usable by its scoped manifest.
for pack in packages:
 local=ROOT/'test-project1/srcs'/pack['profile']/'build/generation/source-packages.json'
 if local!=manifest:write_json_latest(local,{**record,'packages':[pack]},ROOT/'test-project1/srcs'/pack['profile']/'.tmp/source-package')
print(json.dumps({'profiles':len(packages),'files':sum(len(p['entries']) for p in packages),'manifest':manifest.relative_to(ROOT).as_posix()}))
