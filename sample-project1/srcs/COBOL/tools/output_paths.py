"""Method-local current outputs; Git stores history, .tmp stores working files."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json
import os
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.tmp'
RESULTS = ROOT / 'build/test-results'

def guard(path, roots=None):
    """Validate lexical ownership before resolving or mutating an output."""
    target = Path(os.path.abspath(path))
    allowed = roots if roots is not None else (ROOT / 'build', WORK)
    if not any(target.is_relative_to(base) for base in allowed):
        raise ValueError('Output must stay in this method build or .tmp')
    for ancestor in (target, *target.parents):
        if ancestor.is_symlink() or getattr(ancestor, 'is_junction', lambda: False)():
            raise ValueError('Linked output path refused: ' + str(ancestor))
    if str(target.resolve()).casefold() != str(target).casefold():
        raise ValueError('Redirected output path refused')
    return target

def ensure_directory(path):
    target = guard(path)
    if target.exists() and not target.is_dir():
        raise ValueError('Regular output directory required')
    target.mkdir(parents=True, exist_ok=True)
    return guard(target)

def write_latest(path, data):
    target = guard(path)
    ensure_directory(target.parent)
    scratch = ensure_directory(WORK / 'output-stage')
    descriptor, temporary = tempfile.mkstemp(prefix='current-', dir=scratch)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data.encode('utf-8') if isinstance(data, str) else data)
    os.replace(temporary, target)

def write_json(path, value):
    write_latest(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def result_dir(suite, requested=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', suite):
        raise ValueError('A simple suite name is required')
    target = guard(Path(requested) / suite if requested else RESULTS / suite, (RESULTS, WORK))
    return ensure_directory(target)

def reset_work(path):
    target = guard(path, (WORK,))
    if target == WORK:
        raise ValueError('Only a child of this method .tmp may be reset')
    if target.exists():
        if not target.is_dir():
            raise ValueError('Regular workspace directory required')
        for directory, names, files in os.walk(target, followlinks=False):
            for name in (*names, *files):
                guard(Path(directory) / name, (WORK,))
        shutil.rmtree(target)
    target.mkdir(parents=True)
    return target
