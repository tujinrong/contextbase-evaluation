"""Exercise actual fixed-output tools in disposable, method-local fixtures."""
from pathlib import Path
import copy, hashlib, io, json, os, shutil, subprocess, sys, tempfile, unittest, zipfile
sys.dont_write_bytecode=True
from output_layout import write_json_latest, ensure_directory

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
WORK=HERE.parent/'.tmp/layout-tests';ensure_directory(WORK)
PROFILES=['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']

class LayoutTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='work-',dir=WORK);self.root=Path(self.temp.name)/'repo'
  tools=self.root/'agents/builds/build-agent/scripts';tools.mkdir(parents=True)
  for name in ['package-source.py','verify-packages.py','output_layout.py','project_scope.py']:
   shutil.copyfile(HERE/name,tools/name)
  for profile in PROFILES:
   base=self.root/'sample-project1/srcs'/profile;base.mkdir(parents=True)
   canonical=self.root/'sample-project1/spec'/profile;canonical.mkdir(parents=True)
   (canonical/'original-spec.md').write_text('canonical original specification must never enter source packages','utf-8')
   (base/'README.md').write_text('source fixture','utf-8');(base/'app.cs').write_text('// version one','utf-8')
   for excluded in ['.tmp','spec','spec-eval','spec-analysis','tests']:
    (base/excluded).mkdir();(base/excluded/'poison.txt').write_text('not an archive input','utf-8')
  (self.root/'sample-project1/spec/README.md').write_text(self.routing('sample-project1',PROFILES),'utf-8')
  self.base=self.root/'sample-project1/srcs/Access'
  (self.base/'profile.json').write_text(json.dumps({'name':'Access','specRoot':'../../spec/Access','inputRoot':'../../spec/Access','productionHelpers':['tools/GeneratedPaths.ps1']}),'utf-8')
  (self.base/'tools').mkdir();(self.base/'tools/GeneratedPaths.ps1').write_text('# required production helper','utf-8');(self.base/'tools/test-oracle.py').write_text('# excluded','utf-8')
  # A self-contained legacy evidence fixture; no application source is read.
  (self.base/'Build-Access.ps1').write_text("""# Production builder fixture before input evidence
function Invoke-FixtureBuild {
        @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../../spec/Access') -Filter '*.md' -Recurse | ForEach-Object {
            [ordered]@{file=$_.FullName;sha256='fixture-only'}
        }) | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'inputs.json') -Encoding UTF8
        [ordered]@{status='Generated';formalScore=$null} | ConvertTo-Json
}
# Production publication fixture remains unchanged
""",'utf-8')
 def tearDown(self):self.temp.cleanup()
 @staticmethod
 def routing(project,profiles):
  return '| 方式ID | specRoot | sourceRoot |\n| --- | --- | --- |\n'+''.join(f'| {p} | {project}/spec/{p}/ | {project}/srcs/{p}/ |\n' for p in profiles)
 def run_tool(self,name,*args,expected=0,project='sample-project1'):
  result=subprocess.run([sys.executable,'-X','utf8',str(self.root/'agents/builds/build-agent/scripts'/name),*args,'--project',project],capture_output=True,text=True,encoding='utf-8')
  self.assertEqual(result.returncode,expected,result.stdout+result.stderr);return result
 def package(self):self.run_tool('package-source.py','current','--profile','Access')
 def manifest(self):return self.base/'build/generation/source-packages.json'
 def verify(self,expected=0):return self.run_tool('verify-packages.py','current','--profile','Access','--hashes-only',expected=expected)
 def result(self):return json.loads((self.base/'build/test-results/source-package-validation.json').read_text('utf-8'))
 def test_repeat_updates_fixed_archive_and_retains_required_helper(self):
  self.package();source=self.base/'build/source.zip';before=hashlib.sha256(source.read_bytes()).hexdigest()
  with zipfile.ZipFile(source) as archive:
   names=archive.namelist();self.assertIn('tools/GeneratedPaths.ps1',names);self.assertNotIn('tools/test-oracle.py',names);self.assertFalse(any(part in {'.tmp','spec','spec-eval','spec-analysis','tests'} for name in names for part in Path(name).parts))
   self.assertNotIn('original-spec.md',names)
   metadata=json.loads(archive.read('profile.json'));self.assertNotIn('specRoot',metadata);self.assertNotIn('inputRoot',metadata)
  (self.base/'app.cs').write_text('// version two','utf-8');self.package();self.assertNotEqual(before,hashlib.sha256(source.read_bytes()).hexdigest())
  self.assertEqual(sorted(p.name for p in (self.base/'build').iterdir()),['generation','source.zip'])
  self.verify();self.assertEqual(self.result()['status'],'PASSED');self.assertTrue((self.base/'.tmp/source-isolation/app.cs').is_file())
 def test_invalid_manifest_never_retains_old_pass(self):
  self.package();self.verify();original=json.loads(self.manifest().read_text('utf-8'))
  variants=[]
  value=copy.deepcopy(original);value['sourceOnly']=False;variants.append(value)
  value=copy.deepcopy(original);value['packages']=[];variants.append(value)
  value=copy.deepcopy(original);value['packages']*=2;variants.append(value)
  value=copy.deepcopy(original);value['packages'][0]['profile']='../spec';variants.append(value)
  value=copy.deepcopy(original);value['packages'][0]['file']='sample-project1/other.zip';variants.append(value)
  for value in variants:
   with self.subTest(value=value):
    self.manifest().write_text(json.dumps(value),'utf-8');self.verify(expected=1);self.assertEqual(self.result()['status'],'FAILED')
 def test_access_source_only_evidence_without_original_specifications(self):
  builder=self.base/'Build-Access.ps1';original=builder.read_bytes();self.package()
  isolated=self.root/'isolated-access';isolated.mkdir()
  with zipfile.ZipFile(self.base/'build/source.zip') as archive:
   packaged=archive.read('Build-Access.ps1').decode('utf-8');archive.extractall(isolated)
  self.assertEqual(builder.read_bytes(),original,'Packaging changed the authoritative builder')
  text=original.decode('utf-8');start=text.index("        @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../../spec/Access')")
  end=text.index("        [ordered]@{status='Generated'",start)
  self.assertEqual(packaged[:start],text[:start],'Build steps before input evidence changed')
  suffix=packaged.index("        [ordered]@{status='Generated'")
  self.assertEqual(packaged[suffix:],text[end:],'Artifact and verification publication changed')
  evidence=packaged[start:suffix].strip();self.assertNotIn('Get-ChildItem',evidence);self.assertNotIn('../../spec',packaged)
  self.assertFalse((isolated/'../../spec/Access').resolve().exists(),'Fixture unexpectedly has original specifications')
  script=isolated/'evidence-only.ps1'
  script.write_text("$ErrorActionPreference='Stop'\n$taskReport=Join-Path $PSScriptRoot 'build/test-results'\nNew-Item -ItemType Directory -Path $taskReport -Force | Out-Null\n"+evidence+'\n','utf-8')
  shell=shutil.which('pwsh') or shutil.which('powershell.exe');self.assertIsNotNone(shell,'PowerShell is required for evidence-only fixture')
  result=subprocess.run([shell,'-NoProfile','-NonInteractive','-File',str(script)],capture_output=True,text=True,encoding='utf-8')
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  record=json.loads((isolated/'build/test-results/inputs.json').read_text('utf-8-sig'))
  self.assertTrue(record['sourceOnly']);self.assertEqual(record['specificationInputs'],'excluded');self.assertIsNone(record['formalScore'])
  entry=next(item for item in json.loads(self.manifest().read_text('utf-8'))['packages'][0]['entries'] if item['file']=='Build-Access.ps1')
  self.assertEqual(entry['sourceSha256'],hashlib.sha256(original).hexdigest());self.assertIn('publication unchanged',entry['transformation'])
 def test_access_source_only_builder_change_requires_review(self):
  builder=self.base/'Build-Access.ps1';builder.write_text(builder.read_text('utf-8').replace("'../../spec/Access'","'unexpected-spec-root'"),'utf-8')
  self.run_tool('package-source.py','current','--profile','Access',expected=1)
  self.assertFalse((self.base/'build/source.zip').exists(),'An unreviewed builder was published')
 def test_two_method_project_and_topic_independent_build_entry(self):
  project='sample-project2';spec=self.root/project/'spec';spec.mkdir(parents=True)
  (spec/'README.md').write_text(self.routing(project,['Access','CSharp_ASPNET']),'utf-8')
  for profile in ['Access','CSharp_ASPNET']:
   folder=self.root/project/'srcs'/profile;folder.mkdir(parents=True)
   (folder/'README.md').write_text('Current project source instructions','utf-8')
   (folder/'application.txt').write_text('production fixture','utf-8')
  access=self.root/project/'srcs/Access';(access/'Build-Access.ps1').write_text('# Standalone builder; no original specification dependency','utf-8')
  web=self.root/project/'srcs/CSharp_ASPNET';code=web/'src/EmployeePortal';code.mkdir(parents=True)
  (web/'CareerPortal.slnx').write_text('<Solution><Project Path="src/EmployeePortal/Portal.csproj" /><Project Path="tools/SeedPortal/SeedPortal.csproj" /></Solution>','utf-8')
  (web/'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>','utf-8')
  (code/'Portal.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>','utf-8')
  (code/'Program.cs').write_text('System.Console.WriteLine(StateStore.Value + Stateful.Value + Latest.Value);','utf-8')
  for name in ('StateStore','Stateful','Latest'):
   (code/(name+'.cs')).write_text('public static class '+name+' { public const int Value = 14; }','utf-8')
  for name in ('TestSuite.cs','Test-Oracle.cs','PortalTests.cs'):
   (code/name).write_text('invalid C# test oracle; must never enter production source ZIP','utf-8')
  setup=web/'tools/SeedPortal';setup.mkdir(parents=True)
  (setup/'SeedPortal.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup><ProjectReference Include="../../src/EmployeePortal/Portal.csproj" /></ItemGroup></Project>','utf-8')
  (setup/'Program.cs').write_text('System.Console.WriteLine(SetupStateStore.Value + SetupLatest.Value);','utf-8')
  (setup/'StateStore.cs').write_text('public static class SetupStateStore { public const int Value = 20; }','utf-8')
  (setup/'Latest.cs').write_text('public static class SetupLatest { public const int Value = 22; }','utf-8')
  (web/'profile.json').write_text(json.dumps({'productionHelpers':['tools/SeedPortal/SeedPortal.csproj','tools/SeedPortal/Program.cs','tools/SeedPortal/StateStore.cs','tools/SeedPortal/Latest.cs']}),'utf-8')
  self.run_tool('package-source.py','current',project=project)
  metadata=json.loads((self.root/project/'build/generation/source-packages.json').read_text('utf-8'))
  self.assertEqual(metadata['projectId'],project);self.assertEqual({p['profile'] for p in metadata['packages']},{'Access','CSharp_ASPNET'})
  with zipfile.ZipFile(web/'build/source.zip') as archive:
   text=archive.read('README.md').decode();self.assertIn('CareerPortal.slnx',text);self.assertNotIn('StudentManagement',text);self.assertNotIn('authentication disabled',text)
   self.assertIn('tools/SeedPortal/Program.cs',archive.namelist())
   for name in ('StateStore.cs','Stateful.cs','Latest.cs'):
    self.assertIn('src/EmployeePortal/'+name,archive.namelist())
   for name in ('TestSuite.cs','Test-Oracle.cs','PortalTests.cs'):
    self.assertNotIn('src/EmployeePortal/'+name,archive.namelist())
   self.assertIn('tools/SeedPortal/StateStore.cs',archive.namelist());self.assertIn('tools/SeedPortal/Latest.cs',archive.namelist())
  self.run_tool('verify-packages.py','current','--hashes-only',project=project)
  self.run_tool('package-source.py','current','--profile','COBOL',project=project,expected=1)
  if shutil.which('dotnet'):
   self.run_tool('verify-packages.py','current',project=project)
   result=json.loads((self.root/project/'build/test-results/source-package-validation.json').read_text('utf-8'))
   self.assertEqual(len(result['runs']),1);self.assertIn('CareerPortal.slnx',result['runs'][0]['command']);self.assertEqual(result['runs'][0]['exitCode'],0)
   self.assertTrue((web/'.tmp/source-isolation/tools/SeedPortal/bin/Release/net10.0/SeedPortal.dll').is_file(),'Packaged production setup did not compile standalone')
 def test_exact_helper_allowlist_rebuild_and_license_resources(self):
  (self.base/'Build-Access.ps1').unlink()
  nested=self.base/'tools/native';nested.mkdir()
  (nested/'producer.py').write_text("from pathlib import Path\ndef rebuild(root):\n output=root/'.tmp/compiled.txt';output.parent.mkdir(exist_ok=True);output.write_text((root/'app.cs').read_text(),encoding='utf-8')\n",'utf-8')
  (self.base/'tools/build.py').write_text("from pathlib import Path\nfrom native.producer import rebuild\nrebuild(Path(__file__).resolve().parents[1])\n",'utf-8')
  helpers=['tools/build.py','tools/native/producer.py']
  (self.base/'profile.json').write_text(json.dumps({'productionHelpers':helpers}),'utf-8')
  license_dir=self.base/'third-party/licenses/example';license_dir.mkdir(parents=True)
  (license_dir/'Example.nuspec').write_text('<package><metadata><license type="expression">MIT</license></metadata></package>','utf-8')
  (license_dir/'LICENSE.txt').write_text('fixture copyright and license','utf-8')
  self.package();self.verify()
  isolated=self.base/'.tmp/source-isolation'
  result=subprocess.run([sys.executable,'-B','-X','utf8','tools/build.py'],cwd=isolated,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertEqual((isolated/'.tmp/compiled.txt').read_text('utf-8'),'// version one')
  with zipfile.ZipFile(self.base/'build/source.zip') as archive:
   names=archive.namelist();self.assertTrue(set(helpers).issubset(names));self.assertNotIn('tools/test-oracle.py',names);self.assertNotIn('tools/GeneratedPaths.ps1',names)
   self.assertIn('third-party/licenses/example/Example.nuspec',names);self.assertIn('third-party/licenses/example/LICENSE.txt',names)
   self.assertIn('tools/build.py',archive.read('README.md').decode())
 def test_production_helpers_reject_scope_escape_and_nonfiles(self):
  self.package();archive=self.base/'build/source.zip';before=hashlib.sha256(archive.read_bytes()).hexdigest()
  (self.base/'tools/TestSuite.bas').write_text('test-only fixture','utf-8')
  for helpers in [['../outside.py'],['tests/poison.txt'],['.tmp/poison.txt'],['spec/poison.txt'],['spec-eval/poison.txt'],['tools/*.py'],['tools\\GeneratedPaths.ps1'],['tools'],['tools/missing.py'],['tools/test-oracle.py'],['tools/TestSuite.bas'],['tools/GeneratedPaths.ps1','tools/generatedpaths.ps1']]:
   with self.subTest(helpers=helpers):
    (self.base/'profile.json').write_text(json.dumps({'productionHelpers':helpers}),'utf-8');self.run_tool('package-source.py','current','--profile','Access',expected=1)
    self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),before,'Unsafe declaration replaced a prior artifact')
  external=self.root/'external';external.mkdir();(external/'builder.py').write_text('# must not be read','utf-8')
  self.junction(external,self.base/'tools/redirected')
  (self.base/'profile.json').write_text(json.dumps({'productionHelpers':['tools/redirected/builder.py']}),'utf-8')
  self.run_tool('package-source.py','current','--profile','Access',expected=1)
 def test_test_name_boundaries_preserve_production_words(self):
  from project_scope import is_test_artifact
  for name in ('StateStore.cs','Latest.cs','Contest.cs','Attestation.cs','tools/StateStore.cs','tools/Latest.ps1','latest:build'):
   with self.subTest(name=name):self.assertFalse(is_test_artifact(name))
  for name in ('TestSuite.bas','Test-Oracle.py','test_oracle.py','PortalTests.cs','Portal.Test.cs','Portal.TestSuite.cs','portal.test','module.test.json','preflight-tests.mjs','test:unit','tests/StateStore.cs'):
   with self.subTest(name=name):self.assertTrue(is_test_artifact(name))
 def test_undeclared_helper_in_archive_is_rejected(self):
  self.package();metadata=json.loads(self.manifest().read_text('utf-8'));pack=metadata['packages'][0];archive=self.base/'build/source.zip';payload=(self.base/'tools/test-oracle.py').read_bytes()
  with zipfile.ZipFile(archive,'a') as target:target.writestr('tools/test-oracle.py',payload)
  pack['entries'].append({'file':'tools/test-oracle.py','sha256':hashlib.sha256(payload).hexdigest(),'sourceSha256':hashlib.sha256(payload).hexdigest()});pack['sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
  self.manifest().write_text(json.dumps(metadata),'utf-8');self.verify(expected=1);self.assertIn('Undeclared production helper',self.result()['error'])
 def test_source_changed_after_packaging_is_rejected(self):
  self.package();(self.base/'app.cs').write_text('// changed after package','utf-8');self.verify(expected=1)
  self.assertIn('Source changed after packaging',self.result()['error'])
 def test_unsafe_archive_member_rejected(self):
  self.package();metadata=json.loads(self.manifest().read_text('utf-8'));source=self.base/'build/source.zip';payload=b'no write outside scratch'
  with zipfile.ZipFile(source,'w') as archive:archive.writestr('../escape.txt',payload)
  metadata['packages'][0].update(sha256=hashlib.sha256(source.read_bytes()).hexdigest(),entries=[{'file':'../escape.txt','sha256':hashlib.sha256(payload).hexdigest()}])
  self.manifest().write_text(json.dumps(metadata),'utf-8');self.verify(expected=1);self.assertFalse((self.base/'.tmp/escape.txt').exists())
 def test_staging_hardlink_does_not_truncate_input(self):
  protected=self.base/'spec/input.json';protected.write_text('protected input','utf-8');scratch=self.base/'.tmp/staging';scratch.mkdir()
  os.link(protected,scratch/'summary.json.pending')
  write_json_latest(self.base/'build/summary.json',{'status':'current'},scratch)
  self.assertEqual(protected.read_text('utf-8'),'protected input')
 def junction(self,target,link):
  result=subprocess.run(['node','-e',"require('fs').symlinkSync(process.argv[1],process.argv[2],'junction')",str(target),str(link)],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_parent_redirect_refused_before_extract_or_write(self):
  self.package();shutil.rmtree(self.base/'.tmp');self.junction(self.base/'spec',self.base/'.tmp')
  with self.assertRaises(RuntimeError):ensure_directory(self.base/'.tmp/source-isolation')
  result=self.verify(expected=1)
  self.assertFalse((self.base/'spec/source-isolation').exists());self.assertTrue((self.base/'spec/poison.txt').is_file())
 def test_node_guard_and_evaluation_exclusion(self):
  script=r"""
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
(async()=>{const base=process.argv[1],tools=process.argv[2];const {writeLatest}=await import(pathToFileURL(path.join(tools,'output-layout.mjs')));const {sourceFiles}=await import(pathToFileURL(path.join(tools,'source-files.mjs')));
const protectedFile=path.join(base,'spec/poison.txt'),scratch=path.join(base,'.tmp/node-stage');fs.mkdirSync(scratch,{recursive:true});fs.linkSync(protectedFile,path.join(scratch,'summary.json.pending'));writeLatest(path.join(base,'build/summary.json'),'current',scratch);if(fs.readFileSync(protectedFile,'utf8')!=='not an archive input')throw Error('Input truncated');
const visible=sourceFiles(base,{excludeSpec:true});if(visible.some(p=>path.relative(base,p).split(path.sep).some(part=>['spec-eval','spec-analysis','.tmp','spec'].includes(part))))throw Error('Excluded input enumerated');
const redirected=path.join(base,'redirected');fs.symlinkSync(path.join(base,'spec'),redirected,'junction');let rejected=false;try{writeLatest(path.join(base,'build/new.json'),'current',redirected);}catch(e){rejected=true;}if(!rejected||fs.existsSync(path.join(base,'spec/new.json.pending')))throw Error('Redirected scratch accepted');console.log('PASS node guard and source exclusion');})().catch(e=>{console.error(e);process.exit(1)});
"""
  result=subprocess.run(['node','-e',script,str(self.base),str(HERE)],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LayoutTests));text=stream.getvalue();print(text,end='')
 final=HERE.parent/'build/tool-tests';scratch=WORK/'result'
 write_json_latest(final/'output-layout-tests.json',{'status':'PASSED' if result.wasSuccessful() else 'FAILED','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'fixed path/package/exclusion/filesystem contracts in disposable fixtures; no business/DB/native acceptance','formalScore':None},scratch)
 from output_layout import write_latest
 write_latest(final/'output-layout-tests.log',text,scratch)
 raise SystemExit(0 if result.wasSuccessful() else 1)
