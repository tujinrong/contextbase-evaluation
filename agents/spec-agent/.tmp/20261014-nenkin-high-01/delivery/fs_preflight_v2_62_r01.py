"""Public filesystem preflight only. No Artifact/provider/application/business code.
Does NOT make check/use atomic or certify author ownership. Caller must retain input
bindings and control the FS actor; runtime/package-internal operations are outside scope.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from datetime import datetime, timezone

SCHEMA="fs-preflight-v2-62/1"
WORKSPACE=Path(r"D:\開発\contextbase-evaluation")
OWN_TMP=WORKSPACE/"agents/spec-agent/.tmp/20261014-nenkin-high-01"
OWN_REPORT=WORKSPACE/"agents/spec-agent/report/20261014-nenkin-high-01"
OWN_ROOTS=(OWN_TMP,OWN_REPORT)
FORBIDDEN={"input","rawinput","raw-input","raw","source","src","spec","spec-eval","evaluator-only","source-pilot"}
MAX_FILE=256_000_000

def require(ok,message):
    if not ok:raise ValueError("HOLD: "+message)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def json_unique(raw):
    def pairs(items):
        result={}
        for k,v in items:
            require(k not in result,"duplicate JSON key");result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:require(False,"nonfinite JSON"))

def expected_hash(value):
    require(isinstance(value,str) and re.fullmatch(r"[0-9a-fA-F]{64}",value) is not None,"explicit SHA256 required")
    return value.lower()

def canonical_relative(value, *, suffix=None):
    require(isinstance(value,str) and bool(value),"canonical relative path required")
    require(not any(ord(c)<32 or ord(c)==127 for c in value) and ":" not in value and "\\" not in value,"canonical relative colon/control/backslash")
    require(not value.startswith("/") and ".." not in value and all(p not in {"",".",".."} for p in value.split("/")),"canonical path traversal/empty segments")
    if suffix:require(value.endswith(suffix),"canonical suffix mismatch")
    return value

def absolute_path(value):
    require(isinstance(value,(str,Path)),"path must be text")
    value=str(value)
    require(value and not any(ord(c)<32 or ord(c)==127 for c in value),"path control/empty")
    p=Path(value)
    require(p.is_absolute(),"explicit absolute path required")
    # Drive colon is permitted; stream/URI/segment colons are not.
    require(all(":" not in part for part in p.parts[1:]),"path alternate stream/colon")
    require(all(part not in {".",".."} for part in p.parts[1:]),"path lexical descent")
    absolute=Path(os.path.abspath(value))
    require(absolute==p,"noncanonical absolute path")
    return absolute

def is_within(path,roots):
    return any(path.is_relative_to(root) for root in roots)

def reject_protected(path):
    components=path.parts[1:]
    folders=components[:-1] if path.suffix else components
    require(not any(p.casefold() in FORBIDDEN or p.casefold().startswith(("rawinput-","raw-input-","source-snapshot")) for p in folders),"protected input/source/spec/evaluation path")

def metadata(path, *, expectation="any", kind=None):
    """lstat every component including volume ancestors before any data read."""
    for node in (path,*path.parents):
        try:st=node.lstat()
        except FileNotFoundError:continue
        require(not stat.S_ISLNK(st.st_mode),"symlink component")
        require(not (getattr(st,"st_file_attributes",0)&0x400),"reparse component")
    require(path.resolve(strict=False)==path,"resolved path differs from explicit path")
    try:st=path.lstat()
    except FileNotFoundError:st=None
    if expectation=="existing":require(st is not None,"missing existing path")
    elif expectation=="fresh":require(st is None,"fresh path already exists")
    if st is not None and kind=="file":require(stat.S_ISREG(st.st_mode),"not an ordinary file")
    if st is not None and kind=="directory":require(stat.S_ISDIR(st.st_mode),"not an ordinary directory")
    return st

def owned_path(value, *, expectation="existing", kind="file"):
    p=absolute_path(value)
    require(is_within(p,OWN_ROOTS),"not below this run owned tmp/report roots")
    reject_protected(p);metadata(p,expectation=expectation,kind=kind)
    return p

def read_pinned(path,expected):
    expected=expected_hash(expected)
    st=metadata(path,expectation="existing",kind="file")
    require(st.st_size<=MAX_FILE,"file size exceeds bounded read")
    raw=path.read_bytes()
    require(sha(raw)==expected,"file SHA mismatch")
    metadata(path,expectation="existing",kind="file")
    return raw

def input_roots(binding_descriptor):
    require(isinstance(binding_descriptor,dict),"pinned binding descriptor required")
    file=owned_path(binding_descriptor.get("path"),expectation="existing",kind="file")
    require(file.suffix.casefold()==".json","binding JSON extension required")
    raw=read_pinned(file,binding_descriptor.get("sha256"))
    binding=json_unique(raw.decode("utf-8"))
    roots=[]
    for field in ("permittedMarkdownRoot","permittedRenderRoot"):
        require(field in binding,"missing bound permitted root")
        root=absolute_path(binding[field])
        require(root.is_relative_to(WORKSPACE),"bound permitted root outside workspace")
        reject_protected(root);metadata(root,expectation="existing",kind="directory")
        roots.append(root)
    return binding,roots,sha(raw)

def check(request):
    require(isinstance(request,dict) and request.get("schema")==SCHEMA,"explicit FS preflight schema required")
    role=request.get("role");operation=request.get("operation")
    require(role in {"model","binding","markdown","image","render-pins","render-manifest","output"},"unknown filesystem role")
    require(operation in {"read","mkdir","write-fresh","write-owned","save-fresh","post-write"},"unknown filesystem operation")
    path=absolute_path(request.get("path"));reject_protected(path)
    binding_sha=None
    if role in {"model","binding"}:
        require(operation=="read" and is_within(path,OWN_ROOTS),"model/binding read limited to owned new run")
        require(path.suffix.casefold()==".json","model/binding JSON required")
    elif role=="output":
        root=owned_path(request.get("outputRoot"),expectation="any",kind="directory")
        require(path.is_relative_to(root),"output escapes declared fresh output root")
        require(operation!="read" or request.get("ownedOutput") is True,"output reads require caller ownership")
    else:
        require(operation=="read","bound inputs are read-only")
        _,roots,binding_sha=input_roots(request.get("binding"))
        root=roots[0] if role=="markdown" else roots[1]
        require(path.is_relative_to(root),"input outside exact bound permitted root")
        if role=="markdown":require(path.suffix.casefold()==".md","Markdown extension required")
        elif role=="image":require(path.suffix.casefold()==".png","PNG extension required")
        elif role=="render-pins":require(path.name=="render-pins.json","render-pins exact filename")
        elif role=="render-manifest":require(path.name=="manifest.json","render manifest exact filename")
    actual_hash=None
    if operation=="read":
        require(request.get("expectedSha256") is not None,"read requires byte pin")
        read_pinned(path,request["expectedSha256"]);actual_hash=expected_hash(request["expectedSha256"])
    elif operation=="mkdir":
        metadata(path,expectation="fresh" if request.get("fresh") is True else "any",kind="directory")
    elif operation in {"write-fresh","save-fresh"}:
        metadata(path,expectation="fresh",kind="file")
    elif operation=="write-owned":
        require(request.get("ownedOutput") is True,"write-owned needs caller ownership")
        read_pinned(path,request.get("expectedSha256"));actual_hash=expected_hash(request["expectedSha256"])
    elif operation=="post-write":
        require(request.get("ownedOutput") is True,"post-write needs caller ownership")
        st=metadata(path,expectation="existing",kind="file")
        require(st.st_size<=MAX_FILE,"post-write size exceeds bound")
        raw=path.read_bytes();actual_hash=sha(raw)
        if request.get("expectedSha256") is not None:
            require(actual_hash==expected_hash(request["expectedSha256"]),"post-write SHA mismatch")
        metadata(path,expectation="existing",kind="file")
    return {"schema":"fs-preflight-result/1","path":str(path),"role":role,"operation":operation,
            "sha256":actual_hash,"bindingSha256":binding_sha,"status":"METADATA_AND_PINS_CHECKED",
            "createdUtc":datetime.now(timezone.utc).isoformat(),"raceFreeGuarantee":False,
            "callerOwnershipVerified":False,"businessContentEvaluated":False,
            "scope":"CALLER_FS_ACTOR_METADATA_AND_BYTE_BINDINGS_ONLY"}

def main():
    raw=sys.stdin.buffer.read(1_048_577)
    require(len(raw)<=1_048_576,"FS request exceeds bound")
    result=check(json_unique(raw.decode("utf-8")))
    print(json.dumps(result,ensure_ascii=False,separators=(",",":")))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)

