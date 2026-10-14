"""Synthetic metadata/FS guard tests only: never imports Artifact or reads actual forms."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime,timezone

BASE=Path(r"D:\開発\contextbase-evaluation\agents\spec-agent")
DEL=BASE/".tmp/20261014-nenkin-high-01/delivery"
AUDIT=BASE/"report/20261014-nenkin-high-01/delivery-audit-r01"
EV=AUDIT/"fs-preflight-synthetic-r01"
HELPER=DEL/"fs_preflight_v2_62_r02.py"
BUILDER=DEL/"build_xlsx_v2_62_r04.mjs"
PY=Path(r"C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
NODE=Path(r"C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={HELPER:"4c03b060269ee36dbbb1b8368fbb6cde9a95a6f7e91849e376c40919b61c567c",
 BUILDER:"e54ec6d0c7d545222ae5599bfa128c403ddd3bf34e3db49b49aa654ec3476fea",
 DEL/"build_xlsx_v2_62_r03.mjs":"de37a7c26746a29b3d3289bae50345e59359688af7614b0b40f58ba739ddb606",
 DEL/"build_xlsx_v2_62_r02.mjs":"b73991d39d017002512672838f4544309233629cd2c26dede6b22c80d6668b6d",
 DEL/"fs_preflight_v2_62_r01.py":"7545f36e3b2336152a0f8e27dc6fecdb05b76b6a09e5df78f051f5d167db68c7",
 DEL/"connect_print_metadata_v2_62_r03.py":"4e16de6949f8cf4175904d5d8523ac842c64c7dea2b782e27ed96403dc388f2c"}
for p,h in pins.items():assert sha(p)==h
spec=importlib.util.spec_from_file_location("fresh_fs_preflight",HELPER)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert not EV.exists();EV.mkdir()
mdroot=EV/"md";renderroot=EV/"render";mdroot.mkdir();renderroot.mkdir()
md=mdroot/"synthetic.md";md.write_bytes(b"SYNTHETIC_BYTE_PIN_ONLY\n")
image=renderroot/"synthetic.png";image.write_bytes(b"SYNTHETIC_NONIMAGE_BYTE_FIXTURE")
renderpins=renderroot/"render-pins.json";renderpins.write_text("{}",encoding="utf-8")
manifest=renderroot/"manifest.json";manifest.write_text("{}",encoding="utf-8")
model=EV/"synthetic-model.json";model.write_text("{}",encoding="utf-8")
binding=EV/"synthetic-binding.json"
binding_data={"schema":"reverse-agent-delivery-binding/1","permittedMarkdownRoot":str(mdroot),"permittedRenderRoot":str(renderroot)}
binding.write_text(json.dumps(binding_data),encoding="utf-8")
descriptor={"path":str(binding),"sha256":sha(binding)}
out=EV/"out";out.mkdir()
owned=out/"owned.bin";owned.write_bytes(b"SYNTHETIC_OWNED_BYTES")
results=[]
def run(name,request=None,action=None,negative=False):
 try:
  value=action() if action else m.check(request)
 except (ValueError,OSError) as error:
  if not negative:raise
  results.append({"name":name,"result":"PASS_REJECTED","reason":str(error)});return
 assert not negative,("unexpected acceptance",name)
 results.append({"name":name,"result":"PASS","scope":value.get("scope") if isinstance(value,dict) else "PURE_CHECK"})
def req(path,role="model",operation="read",**kw):
 result={"schema":m.SCHEMA,"path":str(path),"role":role,"operation":operation,**kw}
 if role in {"markdown","image","render-pins","render-manifest"}:result["binding"]=descriptor
 return result
run("positive_owned_model_read",req(model,expectedSha256=sha(model)))
run("positive_owned_binding_read",req(binding,"binding",expectedSha256=sha(binding)))
for role,p in [("markdown",md),("image",image),("render-pins",renderpins),("render-manifest",manifest)]:
 run("positive_bound_"+role,req(p,role,expectedSha256=sha(p)))
run("positive_fresh_directory",req(EV/"never-created","output","mkdir",outputRoot=str(EV/"never-created"),fresh=True))
run("positive_existing_owned_directory",req(out,"output","mkdir",outputRoot=str(out),fresh=False))
run("positive_fresh_output",req(out/"fresh.bin","output","write-fresh",outputRoot=str(out)))
run("positive_fresh_xlsx_save_metadata_only",req(out/"never-created.xlsx","output","save-fresh",outputRoot=str(out)))
run("positive_owned_update",req(owned,"output","write-owned",outputRoot=str(out),ownedOutput=True,expectedSha256=sha(owned)))
run("positive_postwrite_pin",req(owned,"output","post-write",outputRoot=str(out),ownedOutput=True,expectedSha256=sha(owned)))
run("positive_owned_output_read",req(owned,"output","read",outputRoot=str(out),ownedOutput=True,expectedSha256=sha(owned)))
run("negative_model_outside_owned_run",req(m.WORKSPACE/"outside.json",expectedSha256="0"*64),negative=True)
run("negative_source_path",req(m.OWN_TMP/"input/blocked.json",expectedSha256="0"*64),negative=True)
run("negative_spec_path",req(m.OWN_REPORT/"spec/blocked.json",expectedSha256="0"*64),negative=True)
run("negative_eval_path",req(m.OWN_REPORT/"spec-eval/blocked.json",expectedSha256="0"*64),negative=True)
run("negative_model_wrong_hash",req(model,expectedSha256="0"*64),negative=True)
run("negative_missing_byte_pin",req(model),negative=True)
run("negative_nonstring_hash",req(model,expectedSha256=True),negative=True)
run("negative_bound_input_write",req(md,"markdown","write-fresh"),negative=True)
run("negative_output_escape",req(md,"output","write-fresh",outputRoot=str(out)),negative=True)
run("negative_existing_fresh_output",req(owned,"output","write-fresh",outputRoot=str(out)),negative=True)
run("negative_save_over_existing",req(owned,"output","save-fresh",outputRoot=str(out)),negative=True)
run("negative_unowned_output_read",req(owned,"output","read",outputRoot=str(out),expectedSha256=sha(owned)),negative=True)
run("negative_unowned_output_write",req(owned,"output","write-owned",outputRoot=str(out),expectedSha256=sha(owned)),negative=True)
run("negative_owned_output_drift",req(owned,"output","write-owned",outputRoot=str(out),ownedOutput=True,expectedSha256="0"*64),negative=True)
run("negative_unknown_operation",req(model,operation="launch-provider",expectedSha256=sha(model)),negative=True)
run("negative_unknown_role",req(model,role="business-source",expectedSha256=sha(model)),negative=True)
run("negative_unknown_metadata_expectation",action=lambda:m.metadata(model,expectation="unknown"),negative=True)
run("negative_unknown_metadata_kind",action=lambda:m.metadata(model,kind="executable"),negative=True)
run("negative_directory_as_file",req(mdroot,expectedSha256="0"*64),negative=True)
run("negative_absolute_colon_stream",action=lambda:m.absolute_path(str(model)+":stream"),negative=True)
run("negative_absolute_control",action=lambda:m.absolute_path(str(model)+"\x01"),negative=True)
for name,value in [("colon","a:b.md"),("control","a\x00.md"),("traversal","../a.md"),("backslash",r"a\b.md"),("absolute","/a.md"),("empty_segment","a//b.md")]:
 run("negative_canonical_"+name,action=lambda v=value:m.canonical_relative(v,suffix=".md"),negative=True)
run("positive_canonical_relative",action=lambda:m.canonical_relative("設計/文書.md",suffix=".md"))
pathclass=type(model);original_lstat=pathclass.lstat;original_resolve=pathclass.resolve
def fake_lstat(kind):
 def call(p,*args,**kw):
  st=original_lstat(p,*args,**kw)
  if p==EV:return SimpleNamespace(st_mode=(stat.S_IFLNK|0o777) if kind=="symlink" else st.st_mode,st_file_attributes=(getattr(st,"st_file_attributes",0)|0x400) if kind=="reparse" else getattr(st,"st_file_attributes",0))
  return st
 return call
with patch.object(pathclass,"lstat",fake_lstat("reparse")):
 run("negative_inward_reparse",req(model,expectedSha256=sha(model)),negative=True)
with patch.object(pathclass,"lstat",fake_lstat("symlink")):
 run("negative_symlink_component",req(model,expectedSha256=sha(model)),negative=True)
def fake_resolve(p,*args,**kw):
 return EV/"different.json" if p==model else original_resolve(p,*args,**kw)
with patch.object(pathclass,"resolve",fake_resolve):
 run("negative_changed_resolved_path",req(model,expectedSha256=sha(model)),negative=True)
def alternate_binding(name,values):
 p=EV/(name+".json");p.write_text(json.dumps(values),encoding="utf-8")
 q=req(md,"markdown",expectedSha256=sha(md));q["binding"]={"path":str(p),"sha256":sha(p)}
 return q
bad=copy.deepcopy(binding_data);bad["schema"]="wrong"
run("negative_binding_schema",alternate_binding("bad-schema",bad),negative=True)
bad=copy.deepcopy(binding_data);bad["permittedMarkdownRoot"]=str(m.WORKSPACE);bad["permittedRenderRoot"]=str(m.WORKSPACE)
run("negative_wide_workspace_roots",alternate_binding("wide-roots",bad),negative=True)
bad=copy.deepcopy(binding_data);bad["permittedMarkdownRoot"]=str(m.OWN_REPORT/"spec")
run("negative_protected_bound_root",alternate_binding("protected-root",bad),negative=True)
q=req(md,"markdown",expectedSha256=sha(md));q["binding"]["sha256"]="0"*64
run("negative_binding_byte_drift",q,negative=True)
old=image.read_bytes();old_hash=sha(image)
run("positive_image_before_export_pin",req(image,"image",expectedSha256=old_hash))
image.write_bytes(old+b"_DRIFT")
run("negative_image_postexport_drift",req(image,"image",expectedSha256=old_hash),negative=True)
image.write_bytes(old)
# Evaluate only the pinned static bootstrap; Artifact module is never imported.
text=BUILDER.read_text(encoding="utf-8")
anchor="const BOOTSTRAP_PY=String.raw"+chr(96)
a=text.index(anchor)+len(anchor);b=text.index(chr(96)+";\n",a);bootstrap=text[a:b]
environment={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}
environment.pop("PYTHONPATH",None);environment.pop("PYTHONHOME",None)
def boot(path,expected):
 p=subprocess.run([str(PY),"-I","-B","-c",bootstrap,str(path),expected],input=json.dumps(req(model,expectedSha256=sha(model))),encoding="utf-8",capture_output=True,env=environment,timeout=30,cwd=str(m.OWN_TMP))
 return p
p=boot(HELPER,pins[HELPER]);assert p.returncode==0,p.stderr
assert json.loads(p.stdout)["status"]=="METADATA_AND_PINS_CHECKED"
results.append({"name":"positive_pinned_samebytes_bootstrap","result":"PASS","argvShell":False,"isolatedPython":True})
p=boot(HELPER,"0"*64);assert p.returncode!=0 and "bootstrap helper SHA" in p.stderr
results.append({"name":"negative_bootstrap_helper_sha","result":"PASS_REJECTED"})
p=boot(DEL/"fs_preflight_v2_62_r01.py",pins[DEL/"fs_preflight_v2_62_r01.py"]);assert p.returncode!=0 and "bootstrap helper path" in p.stderr
results.append({"name":"negative_bootstrap_helper_path","result":"PASS_REJECTED"})
def fake_helper_lstat(p,*args,**kwargs):
 st=original_lstat(p,*args,**kwargs)
 if p==HELPER:return SimpleNamespace(st_mode=st.st_mode,st_file_attributes=getattr(st,"st_file_attributes",0)|0x400)
 return st
with patch.object(pathclass,"lstat",fake_helper_lstat),patch.object(sys,"argv",["-c",str(HELPER),pins[HELPER]]):
 run("negative_bootstrap_inward_reparse",action=lambda:exec(compile(bootstrap,"<synthetic-bootstrap>","exec"),{}),negative=True)
nodecheck=subprocess.run([str(NODE),"--check",str(BUILDER)],capture_output=True,text=True,timeout=30)
assert nodecheck.returncode==0,nodecheck.stderr
results.append({"name":"positive_node_syntax_only","result":"PASS","ArtifactImportExecuted":False})
# Isolated canonical function only: no builder module, marker or Artifact import.
a=text.index("const canonicalRelative=value=>{");b=text.index("\n};",a)+3
canonical=text[a:b]
cases=[["設計/文書.md",True],["a:b.md",False],["a\u0000.md",False],["../a.md",False],[r"a\b.md",False],["/a.md",False],["a//b.md",False]]
js="import path from 'node:path';\n"+canonical+"\nconst cases="+json.dumps(cases,ensure_ascii=False)+";for(const [v,ok]of cases){let accepted=true;try{canonicalRelative(v)}catch{accepted=false}if(accepted!==ok)throw Error('canonical mismatch')}console.log(JSON.stringify({caseCount:cases.length,ArtifactImported:false}));"
p=subprocess.run([str(NODE),"--input-type=module","-e",js],capture_output=True,text=True,timeout=30)
assert p.returncode==0,p.stderr
results.append({"name":"positive_isolated_MJS_canonical_7cases","result":"PASS","caseCount":7,"ArtifactImportExecuted":False})
# Runtime metadata bootstrap hashes the public export and package JSON only.
match=re.search(r"const PACKAGE_BOOTSTRAP_PY=(.+);\n",text);assert match
package_bootstrap=json.loads(match.group(1))
p=subprocess.run([str(PY),"-I","-B","-c",package_bootstrap],capture_output=True,text=True,env=environment,timeout=30)
assert p.returncode==0,p.stderr;package_pins=json.loads(p.stdout)
assert package_pins["importExecuted"] is False
results.append({"name":"positive_public_bundled_entry_metadata_only","result":"PASS","ArtifactImportExecuted":False})
# Enumerate explicit actor FS sites; every one is in a guarded wrapper.
fs_lines=[{"line":i,"code":line.strip()} for i,line in enumerate(text.splitlines(),1) if re.search(r"\bfs\.(?:readFile|writeFile|mkdir|lstat|stat)\(",line)]
assert len(fs_lines)==4 or len(fs_lines)==5,fs_lines
assert "await xlsx.save(file)" in text and "preflight(outputRequest(file,'save-fresh'));await xlsx.save(file)" in text
assert "for(const sheet of document.sheets)for(const image of sheet.images)await readPinned" in text
assert "await boundInput(document);\n    const xlsx=await SpreadsheetFile.exportXlsx(workbook);" in text
assert "await boundInput(document); console.log" in text
assert "import { Workbook, SpreadsheetFile } from '@oai/artifact-tool'" not in text
assert "await import(pathToFileURL(ARTIFACT_ENTRY).href)" in text
assert "range.format.borders={top:{style:'thin',color:light}}" in text
assert "delete guardEnv.PYTHONPATH" in text and "['-I','-B','-c'" in text
for p,h in pins.items():assert sha(p)==h
result={"schema":"synthetic-filesystem-preflight-validation/1","createdUtc":datetime.now(timezone.utc).isoformat(),
 "helper":{"path":str(HELPER),"sha256":sha(HELPER)},"builder":{"path":str(BUILDER),"sha256":sha(BUILDER)},
 "tests":results,"allPassed":True,"testCount":len(results),"positiveCount":sum(x["result"]=="PASS" for x in results),
 "negativeCount":sum(x["result"]=="PASS_REJECTED" for x in results),"isolatedMjsCanonicalCaseCount":7,
 "explicitMjsFsSites":fs_lines,"publicPackageMetadataPins":package_pins,"oldImmutablePins":{str(p):h for p,h in pins.items()},
 "actualInputRead":False,"actualArtifactImported":False,"artifactAuthorExecuted":False,"realXlsxCreated":False,
 "markerExecuted":False,"providerExecuted":False,"applicationExecuted":False,"raceFreeGuarantee":False,
 "scope":"SYNTHETIC_CALLER_FS_ACTOR_GUARDS_ONLY"}
target=EV/"result.json"
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"result":str(target),"sha256":sha(target),"testCount":len(results),"positiveCount":result["positiveCount"],"negativeCount":result["negativeCount"],"allPassed":True},ensure_ascii=False))

