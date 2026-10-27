"""Versioned, bounded, local-only stores shared by the separated programs."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

VERSION = 'two-phase-1.0'


def digest(value: bytes | str | Any) -> str:
    if not isinstance(value, (str, bytes)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def safe(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    p = Path(os.path.abspath(root / relative))
    if not p.is_relative_to(root):
        raise ValueError(f'Path outside allowed root: {relative}')
    for part in (p, *p.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f'Symlink prohibited: {relative}')
    if not p.resolve().is_relative_to(root):
        raise ValueError(f'Path outside allowed root: {relative}')
    return p


def read(path: Path) -> Any:
    if path.stat().st_size > 32_000_000:
        raise ValueError('JSON file exceeds 32MB')
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    # Large generated graphs remain lossless JSON; omit indentation before reaching
    # the bounded reader's limit. Do not truncate fields or raise the safety limit.
    if not isinstance(value,str) and len(text.encode('utf-8'))>8_000_000:
        text=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
    if not isinstance(value,str) and len(text.encode('utf-8'))>32_000_000:
        raise ValueError('Generated JSON exceeds 32MB; split the data before publication')
    if path.is_file() and path.read_text(encoding='utf-8') == text:
        return
    tmp = path.with_name(path.name + f'.tmp-{os.getpid()}')
    try:
        tmp.write_text(text, encoding='utf-8', newline='\n')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def tree_hashes(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    if root.is_symlink():
        raise ValueError('Symlink root')
    result = {}
    for p in sorted(root.rglob('*')):
        safe(root, p)
        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
            result[p.relative_to(root).as_posix()] = digest(p.read_bytes())
    return result


def engine_hash(root: Path, *directories: str) -> str:
    values = {}
    for folder in directories:
        for name, value in tree_hashes(safe(root, folder)).items():
            if name.endswith(('.py', '.json', '.toml', '.md', '.dot')):
                values[folder + '/' + name] = value
    return digest({'version': VERSION, 'files': values})


def seal(directory: Path, identity: dict) -> dict:
    manifest = {**identity, 'files': {k: v for k, v in tree_hashes(directory).items() if k != 'manifest.json'}}
    manifest['generation'] = digest(manifest)
    write(directory / 'manifest.json', manifest)
    return manifest


def verify(directory: Path) -> dict:
    safe(directory.parent, directory)
    manifest = read(safe(directory, 'manifest.json'))
    content = {k: v for k, v in manifest.items() if k != 'generation'}
    if digest(content) != manifest.get('generation'):
        raise ValueError('Generation manifest mismatch')
    actual = {k: v for k, v in tree_hashes(directory).items() if k != 'manifest.json'}
    if actual != manifest['files']:
        raise ValueError('Stored files changed; rerun the producing phase')
    return manifest


@contextmanager
def locked(root: Path, name: str):
    work = safe(root, '.contextbase-work')
    work.mkdir(exist_ok=True)
    path = work / (name + '.lock')
    try:
        stream = path.open('x', encoding='utf-8')
    except FileExistsError as exc:
        raise ValueError(f'Another {name} operation is running') from exc
    with stream:
        stream.write(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


@contextmanager
def staged(root: Path, relative: str):
    """Publish a complete directory or retain the previous one on failure."""
    target = safe(root, relative)
    work = safe(root, '.contextbase-work')
    work.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='phase-', dir=work))
    backup = work / ('previous-' + stage.name)
    try:
        yield stage
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.rename(backup)
        try:
            stage.rename(target)
        except Exception:
            if backup.exists():
                backup.rename(target)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def fact(value: Any, evidence: list[dict], basis: str = 'source', qa_id: str | None = None) -> dict:
    return {'value': value, 'basis': basis, 'evidence': evidence,
            'review': 'static_extraction' if basis == 'source' else 'requires_review', 'qa_id': qa_id}


def cli(run, description: str, argv=None) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--feature')
    parser.add_argument('--cold', action='store_true')
    parser.add_argument('--config', default='config/project.toml')
    args = parser.parse_args(argv)
    try:
        result = run(args.root.resolve(), feature=args.feature, cold=args.cold, config_file=args.config)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, description + ': ' + str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result.get('errors')))
