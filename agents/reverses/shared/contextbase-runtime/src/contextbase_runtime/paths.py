"""Shared lossless text and path primitives; input programs are never run."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath

EXCLUDED_DIRECTORIES = frozenset({
    '.git', '.vs', '.venv', '__pycache__', 'bin', 'obj', 'build', 'dist',
    'node_modules', 'spec', 'spec-eval', 'spec-analysis', 'spec-reverse', 'test-report',
    'report', 'output', 'qa', 'metadata', 'agent-input', 'tests', 'test',
})


TEXT_SUFFIXES = frozenset({
    '.cs', '.vb', '.xaml', '.cshtml', '.razor', '.vue', '.ts', '.js', '.mjs', '.jsx',
    '.tsx', '.java', '.jsp', '.jspx', '.ftl', '.html', '.htm', '.css', '.scss',
    '.sql', '.json', '.xml', '.config', '.toml', '.yaml', '.yml', '.properties',
    '.csproj', '.vbproj', '.sln', '.slnx', '.props', '.targets', '.bas', '.cls', '.frm',
    '.c', '.h', '.cpp', '.hpp', '.cob', '.cbl', '.cpy', '.rpg', '.rpgle',
    '.sqlrpgle', '.dds', '.cl', '.clle', '.bnd', '.py', '.rb', '.go', '.rs',
    '.php', '.sh', '.ps1', '.bat', '.cmd', '.resx', '.txt', '.md',
})


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(value: Path) -> Path:
    value = Path(os.path.abspath(value))
    for item in (value, *value.parents):
        if item.is_symlink():
            raise ValueError('Linked snapshot/input path refused')
        if item.exists() and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse point in snapshot/input path refused')
    return value.resolve()


def write_json(path: Path, value) -> None:
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def decode(data: bytes) -> tuple[str, str]:
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16'), 'utf-16'
    if b'\x00' in data:
        raise ValueError('Binary content is not a text source')
    for encoding in ('utf-8-sig', 'cp932', 'cp936'):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise ValueError('Encoding must be explicitly resolved; no lossy decoding')


def material_path(directory: Path, relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError('Material path must be a string')
    path = PurePosixPath(relative)
    if (not relative or str(path) != relative or path.is_absolute() or
            '..' in path.parts or '\\' in relative or ':' in relative):
        raise ValueError('Invalid capsule material path')
    target = safe_path(directory / relative)
    if directory not in target.parents:
        raise ValueError('Material escapes capsule')
    return target
