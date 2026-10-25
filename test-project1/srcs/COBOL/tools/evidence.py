from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
def compiled_inputs():
 return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['cobol','copy','bridge','tests'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and p.suffix in ['.cob','.cpy','.h','.c']}
def binary_path(name):
 return ROOT/('build/app/windows' if name in ['student.cgi.exe','student-maint.exe'] else '.tmp/host')/name

def binary_hashes():
 return {p.name:hashlib.sha256(binary_path(p.name).read_bytes()).hexdigest() for p in sorted((ROOT/'.tmp/host').glob('*.exe'))}
