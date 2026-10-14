"""Mechanical model I/O gates only. Parser/body/format placement unchanged."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent
O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'delivery_model_v2_62_r05.py';raw=p.read_bytes();pin='3db974859d83fa9d1987b94b310400b27d158ea5b8a851f99c3b297b76d1b6c9';assert hashlib.sha256(raw).hexdigest()==pin
text=raw.decode().replace('\r\n','\n')
text=text.replace("SCHEMA = 'reverse-agent-delivery-model/1'","SCHEMA = 'reverse-agent-delivery-model/1'\nOWN_RUN_ROOTS = (Path(r'D:\\開発\\contextbase-evaluation\\agents\\spec-agent\\.tmp\\20261014-nenkin-high-01'),Path(r'D:\\開発\\contextbase-evaluation\\agents\\spec-agent\\report\\20261014-nenkin-high-01'))",1)
text=text.replace("any(ord(char)<32 for char in value)","any(ord(char)<32 or ord(char)==127 for char in value)",1)
start="def load_bound(binding_path):\n    binding_path = safe_path(binding_path)\n    binding_bytes = binding_path.read_bytes()\n"
replacement="""def render_child(render, name):
    if not isinstance(name,str) or not name or Path(name).name!=name or ':' in name or any(ord(c)<32 or ord(c)==127 for c in name):
        raise ValueError('Render artifact must be one canonical filename')
    child=safe_path(render/name)
    if not child.is_relative_to(render):raise ValueError('Render child escapes pinned directory')
    return child

def load_bound(binding_path, expected_sha256):
    if not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256):raise ValueError('Explicit binding SHA256 required')
    binding_path = safe_path(binding_path)
    if not any(binding_path.is_relative_to(root) for root in OWN_RUN_ROOTS):raise ValueError('Binding outside this owned run')
    binding_bytes = safe_path(binding_path).read_bytes()
    if sha(binding_bytes)!=expected_sha256:raise ValueError('Changed delivery binding')
"""
assert text.count(start)==1;text=text.replace(start,replacement)
old="    renderroot = safe_path(bound['permittedRenderRoot'])\n"
new=old+"    if any(not any(root.is_relative_to(own) for own in OWN_RUN_ROOTS) for root in (mdroot,renderroot)):raise ValueError('Delivery inputs outside this owned run')\n"
assert text.count(old)==1;text=text.replace(old,new)
for old,new in [
 ("raw = md.read_bytes()","raw = safe_path(md).read_bytes()"),
 ("value = (render / filename).read_bytes()","value = render_child(render,filename).read_bytes()"),
 ("content = (render / name).read_bytes()","content = render_child(render,name).read_bytes()"),
 ("html_file = render / pins['canonicalHtmlFilename']","html_file = render_child(render,pins['canonicalHtmlFilename'])"),
 ("sha(html_file.read_bytes())","sha(safe_path(html_file).read_bytes())"),
 ("if html_file.read_bytes() != (render / 'document.html').read_bytes():","if safe_path(html_file).read_bytes() != render_child(render,'document.html').read_bytes():"),
 ("parser.add_argument('--binding',type=Path,required=True); parser.add_argument('--model',type=Path,required=True)","parser.add_argument('--binding',type=Path,required=True); parser.add_argument('--binding-sha256',required=True); parser.add_argument('--model',type=Path,required=True)"),
 ("load_bound(args.binding)","load_bound(args.binding,args.binding_sha256)"),
 ("    output.parent.mkdir(parents=True,exist_ok=True)\n    output.write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')","    safe_path(output.parent).mkdir(parents=True,exist_ok=True)\n    with safe_path(output).open('x',encoding='utf-8') as handle:handle.write(json.dumps(model,ensure_ascii=False,indent=2)+'\\n')"),
 ("output=safe_path(args.model)\n","output=safe_path(args.model)\n")]:
    if old==new:continue
    assert old in text,old;text=text.replace(old,new)
needle="    output=safe_path(args.model)" if "    output=safe_path(args.model)" in text else "    output=safe_path(args.model)"
# The donor spells this assignment with spaces.
assignment="    output=safe_path(args.model)\n" if "    output=safe_path(args.model)\n" in text else "    output = safe_path(args.model)\n"
if assignment not in text:assignment="    output=safe_path(args.model)\n"
assert assignment in text
text=text.replace(assignment,assignment+"    if not any(output.is_relative_to(root) for root in OWN_RUN_ROOTS):raise ValueError('Model output outside this owned run')\n",1)
ast.parse(text)
before={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
after={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
assert changed==['canonical','load_bound','main','render_child'],changed
out=D/'delivery_model_v2_62_r06.py'
with out.open('xb') as h:h.write(text.encode())
assert p.read_bytes()==raw
result={'scope':'MODEL_IO_GUARD_PREPARATION_ONLY','source':{'path':str(p),'sha256':pin},'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'changedFunctionAst':changed,'formatParserAndBodyFunctionsUnchanged':True,'bindingSha256Mandatory':True,'freshExclusiveModelOutput':True,'allRenderChildReadsMetadataGated':True,'actualBusinessReads':0,'actualModelCreated':False,'providerExecuted':0,'actualAuthoring':0,'status':'PREPARED_PENDING_SYNTHETIC_IO_PROBES','limitations':['Metadata checks and exclusive creation do not guarantee absence of filesystem races.','Dependency receipt and actual loaded module pins remain caller requirements.']}
record=O/'model-r06-io-preparation.json'
with record.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'model':str(out),'sha256':result['candidate']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
