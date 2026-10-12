"""Optional local portable C test toolchain; no OS installation or PATH mutation."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, urllib.request, hashlib, zipfile
BASE=Path(__file__).resolve().parents[1]/'build/toolchain'
BASE.mkdir(parents=True,exist_ok=True)
def fetch(url,path):
    if not path.exists():
        with urllib.request.urlopen(url,timeout=60) as src,path.open('wb') as dst:
            while block:=src.read(1024*1024):dst.write(block)
    return hashlib.sha256(path.read_bytes()).hexdigest()
index=json.load(urllib.request.urlopen('https://ziglang.org/download/index.json',timeout=60))
zig=index['0.14.1']['x86_64-windows']
assets=[('zig',zig['tarball'],zig['shasum']),('icu','https://github.com/unicode-org/icu/releases/download/release-77-1/icu4c-77_1-Win64-MSVC2022.zip',None)]
def acquire(item):
    name,url,expected=item;target=BASE/(name+'.zip');digest=fetch(url,target)
    if expected and digest!=expected:raise ValueError('Official SHA256 mismatch: '+name)
    destination=BASE/name
    if not destination.exists():
        with zipfile.ZipFile(target) as z:
            for member in z.infolist():
                resolved=(destination/member.filename).resolve()
                if not resolved.is_relative_to(destination.resolve()):raise ValueError('ZIP escapes target')
            z.extractall(destination)
    return dict(asset=name,url=url,sha256=digest,officialExpectedSha256=expected,destination=str(destination))
with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(acquire,assets))
out=BASE/'acquisition.json';out.write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
print(json.dumps(records,indent=2))
