import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
def compiled_inputs():
 result={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['cobol','copy','bridge','tests'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and p.suffix in ['.cob','.cpy','.h','.c']}
 for p in [ROOT/'build.py',ROOT/'tools/host_build.py']:
  if p.is_file():result[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return result
def binary_path(name):
 return ROOT/('build/app/windows' if name in ['student-text.exe','student-maint.exe'] else '.tmp/host')/name

def binary_hashes():
 paths=[*sorted((ROOT/'.tmp/host').glob('*.exe')),*sorted((ROOT/'build/app/windows').glob('*.exe'))]
 return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
