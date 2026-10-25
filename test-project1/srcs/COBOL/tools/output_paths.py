"""Method-local current outputs; Git stores history, .tmp stores working files."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.tmp'
RESULTS = ROOT / 'build/test-results'

def result_dir(suite, requested=None):
    target = (Path(requested) / suite if requested else RESULTS / suite).resolve()
    if not any(target.is_relative_to(p.resolve()) for p in (RESULTS, WORK)):
        raise ValueError('Results must stay in this method build/test-results or .tmp')
    target.mkdir(parents=True, exist_ok=True)
    return target

def reset_work(path):
    target = Path(path).resolve()
    if target == WORK.resolve() or not target.is_relative_to(WORK.resolve()):
        raise ValueError('Only a child of this method .tmp may be reset')
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    return target
