"""Independent code-only delta and in-memory synthetic ZIP checks. No CLI/XLSX/provider."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import zipfile

D = Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery")
O = Path(__file__).parent
PINS = {
    1: "6ee87012a2697aea4e8db8b1e5722f761a9470703e5af5adbbeb73b3ff26f307",
    2: "8f92a7e763f376119255e8a628db05c0b0483132b95ebb5f01ea4b0d96ed76e4",
    3: "4e16de6949f8cf4175904d5d8523ac842c64c7dea2b782e27ed96403dc388f2c",
}
checks = []
def check(name, expected, observed):
    ok = observed == expected
    checks.append({"name": name, "expected": expected, "observed": observed, "pass": ok})
    if not ok: raise AssertionError(name)
def accepted(fn):
    try: fn(); return True
    except ValueError: return False
def sha(raw): return hashlib.sha256(raw).hexdigest()
raws = {}
modules = {}
for rev, pin in PINS.items():
    path = D / f"connect_print_metadata_v2_62_r{rev:02}.py"
    raw = path.read_bytes(); check(f"r{rev} exact SHA", pin, sha(raw)); raws[rev] = raw
    name = f"print_meta_independent_r{rev}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)  # stdlib declarations only; __main__ is false
    modules[rev] = module
def changed_nodes(a, b):
    def nodes(raw):
        return {getattr(n, "name", f"statement-{i}"): ast.dump(n, include_attributes=False)
                for i,n in enumerate(ast.parse(raw).body)}
    aa,bb = nodes(a),nodes(b)
    return sorted(k for k in aa.keys() | bb.keys() if aa.get(k) != bb.get(k))
check("r01->r02 only specified functions changed",
      ["main", "patch_workbook", "safe_run_path", "zip_index"], changed_nodes(raws[1], raws[2]))
check("r02->r03 only general LIST and own filename changed",
      ["main", "sheet_settings"], changed_nodes(raws[2], raws[3]))

class FakePath:
    """Synthetic Windows metadata, no filesystem node is created or followed."""
    def __init__(self, *, root=False, reparse=False, existing=True):
        self.root=root; self.reparse=reparse; self.existing=existing; self.parents=()
    def absolute(self): return self
    def resolve(self): return self
    def is_relative_to(self, other): return True
    def is_symlink(self): return False
    def lstat(self): return types.SimpleNamespace(st_file_attributes=0x400 if self.reparse else 0)
    def exists(self): return self.existing
    def is_file(self): return True
def path_case(module, *, child_reparse=False, parent_reparse=False, existing=True):
    root=FakePath(root=True)
    path=FakePath(reparse=child_reparse,existing=existing)
    parent=FakePath(reparse=parent_reparse)
    path.parents=(parent,root)
    old=(module.Path,module.os,module.RUN_DELIVERY)
    module.Path=lambda value:value
    module.os=types.SimpleNamespace(path=types.SimpleNamespace(abspath=lambda value:value))
    module.RUN_DELIVERY=root
    try: return accepted(lambda:module.safe_run_path(path,exists=existing))
    finally: module.Path,module.os,module.RUN_DELIVERY=old
check("old inward reparse negative is reproduced",True,path_case(modules[1],child_reparse=True))
for rev in (2,3):
    check(f"r{rev} ordinary read accepted",True,path_case(modules[rev]))
    check(f"r{rev} fresh ordinary output accepted",True,path_case(modules[rev],existing=False))
    check(f"r{rev} inward child reparse refused",False,path_case(modules[rev],child_reparse=True))
    check(f"r{rev} ancestor reparse refused",False,path_case(modules[rev],parent_reparse=True))

m=modules[3]
def item(**kw):
    base={"ordinal":0,"name":"synthetic","kind":"list","lastRow":8,"columns":3,"headerRow":1}
    base.update(kw); return base
for cols, end in [(1,"A"),(3,"C"),(9,"I"),(10,"J"),(16384,"XFD")]:
    check(f"general LIST {cols} exact extent",(f"A1:{end}8",1,0),m.sheet_settings(item(columns=cols)))
check("item LIST ten exact",("A1:J8",1,0),m.sheet_settings(item(columns=10,itemList=True)))
for desc, data in [
    ("item nine",item(columns=9,itemList=True)),("columns bool",item(columns=True)),
    ("columns float",item(columns=10.0)),("columns zero",item(columns=0)),
    ("columns overbound",item(columns=16385)),("itemList string",item(itemList="true")),
    ("header bool",item(headerRow=True)),("header float",item(headerRow=1.0)),
    ("header two",item(headerRow=2))]:
    check(desc+" refused",False,accepted(lambda data=data:m.sheet_settings(data)))
check("TABLE nine unchanged",("A1:I8",4,0),m.sheet_settings(item(kind="table",columns=9,headerRow=4)))
check("TABLE ten refused",False,accepted(lambda:m.sheet_settings(item(kind="table",columns=10,headerRow=4))))

def archive(payload):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as z:
        for name,data in payload.items(): z.writestr(name,data)
    return stream.getvalue()
external=archive({"_rels/.rels":f'<Relationships xmlns="{m.P}"><Relationship Id="r" Type="test" Target="https://invalid.example" TargetMode=" ExTeRnAl "/></Relationships>'.encode()})
check("old whitespace external negative reproduced",True,accepted(lambda:modules[1].zip_index(external)))
for rev in (2,3):check(f"r{rev} whitespace external refused",False,accepted(lambda rev=rev:modules[rev].zip_index(external)))
macro=f'<workbook xmlns="{m.S}"><sheets/><definedNames><definedName name="_XLNM.AUTO_OPEN">1</definedName></definedNames></workbook>'.encode()
check("old case macro negative reproduced",True,accepted(lambda:modules[1].patch_workbook(macro,[item(columns=10)])))
for rev in (2,3):check(f"r{rev} case macro refused",False,accepted(lambda rev=rev:modules[rev].patch_workbook(macro,[item(columns=10)])))

payload={
 "xl/workbook.xml":f'<workbook xmlns="{m.S}" xmlns:r="{m.R}"><sheets><sheet name="synthetic" sheetId="1" r:id="r1"/></sheets><definedNames><definedName name="retained" hidden="1">synthetic!$C$2</definedName></definedNames></workbook>'.encode(),
 "xl/_rels/workbook.xml.rels":f'<Relationships xmlns="{m.P}"><Relationship Id="r1" Type="{m.R}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'.encode(),
 "xl/worksheets/sheet1.xml":f'<worksheet xmlns="{m.S}"><cols><col min="1" max="3" width="12" customWidth="1"/></cols><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>001</t></is></c><c r="B1" t="inlineStr"><is><t>令和01年</t></is></c><c r="C1" t="inlineStr"><is><t>=literal</t></is></c></row></sheetData><mergeCells count="1"><mergeCell ref="A3:C3"/></mergeCells></worksheet>'.encode(),
 "xl/styles.xml":b'<synthetic>literal styles exact</synthetic>',
 "xl/media/image1.png":b'not-a-real-image: do-not-render',
}
raw=archive(payload)
output,receipt=m.connect_bytes(raw,{"schema":m.SCHEMA,"scope":"PRINT_METADATA_ONLY","sheets":[item()]})
_,after,_,_=m.zip_index(output)
check("member identities exact",sorted(payload),sorted(after))
for name in payload:
    if name not in {"xl/workbook.xml","xl/worksheets/sheet1.xml"}:
        check(name+" payload exact",payload[name],after[name])
old_sheet=payload["xl/worksheets/sheet1.xml"]
new_sheet=after["xl/worksheets/sheet1.xml"]
for key in ("cols","sheetData","mergeCells"):
    import re
    expr=("<"+key+r"\b[^>]*>.*?</"+key+">").encode()
    check(key+" byte exact",re.search(expr,old_sheet).group(),re.search(expr,new_sheet).group())
check("retained nonprint defined name exact",True,b'<definedName name="retained" hidden="1">synthetic!$C$2</definedName>' in after["xl/workbook.xml"])
check("source synthetic bytes unchanged",sha(raw),sha(raw))
check("receipt scope", "PRINT_METADATA_ONLY", receipt["scope"])
for rev in PINS:
    check(f"r{rev} code unchanged after synthetic probes",PINS[rev],sha((D/f"connect_print_metadata_v2_62_r{rev:02}.py").read_bytes()))

def jsonable(value):
    if isinstance(value,bytes):return {"length":len(value),"sha256":sha(value)}
    if isinstance(value,tuple):return list(value)
    return value
result={"schema":"independent-print-metadata-delta/1","status":"PASS_CODE_AND_SYNTHETIC_SCOPE_ONLY",
 "inputs":[{"path":str(D/f'connect_print_metadata_v2_62_r{r:02}.py'),"sha256":s} for r,s in PINS.items()],
 "checks":checks,"count":len(checks),"passCount":sum(c["pass"] for c in checks),
 "providers":0,"productionBusinessReads":0,"actualXlsxReads":0,"actualAuthoring":0,"cliExecuted":False,
 "limitations":["Synthetic ZIP only; not a generated or adopted workbook.","Read-time gates do not provide a race-free filesystem guarantee.","Caller must bind actual author receipt and real sheet extents; ownedFreshArtifact alone is a declaration.","No assessment of additional attributes on selected existing print definedName elements.","Old r01 HOLD and self-test records remain immutable."]}
out=O/"print-metadata-independent-code-review-r03.json"
with out.open("x",encoding="utf-8") as h:json.dump(result,h,ensure_ascii=False,indent=2,default=jsonable);h.write("\n")
print(json.dumps({"path":str(out),"sha256":sha(out.read_bytes()),"checks":len(checks),"status":result["status"]}))
