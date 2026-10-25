"""Fingerprint the exact source/document sets read by the static runner."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
def checked_source_hashes():
 extensions={'.cob','.cpy','.c','.h','.py','.mjs','.json','.sql','.md','.js','.css'}
 paths=[p for folder in ['cobol','copy','bridge','sql','assets','tools','deploy','database']
        for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in extensions and '__pycache__' not in p.parts]
 paths += [ROOT/'README.md',ROOT/'IMPLEMENTATION.md',ROOT/'Makefile',ROOT/'dependencies.lock.json']
 return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
