"""Exercise the production output guard with disposable, same-method junction fixtures."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
B = Path(os.path.abspath(__file__)).parents[1]
SPEC = B.parent.parent / 'spec' / B.name
sys.path.insert(0, str(B))
from build_paths import OutputPaths

paths = OutputPaths(B)
paths.preflight()
workspace = paths.mkdir(B / '.tmp/path-guard')
report = paths.mkdir(B / 'build/test-results')
checks = []
raw = []
links = []

def check(condition, name):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

def junction(link, target):
    assert link.absolute().is_relative_to(workspace) and target.absolute().is_relative_to(workspace)
    paths.output(link)
    paths.regular(target)
    if os.name == 'nt':
        script = workspace / 'junction.ps1'
        paths.write(script, 'param([string]$Link,[string]$Target)\n$ErrorActionPreference="Stop"\nNew-Item -ItemType Junction -Path $Link -Target $Target | Out-Null\n')
        subprocess.run(['powershell', '-NoProfile', '-File', str(script), str(link), str(target)], check=True)
    else:
        link.symlink_to(target, target_is_directory=True)
    links.append(link)

def remove_link(link):
    # Remove the reparse entry itself, never recurse through its target.
    assert link.absolute().is_relative_to(workspace)
    paths.regular(link.parent)
    assert OutputPaths.redirected(link)
    if os.name == 'nt' and not link.is_symlink():
        os.rmdir(link)
    else:
        link.unlink()

def fixture(name):
    root = paths.mkdir(workspace / name)
    paths.output(root,tree=True)
    for child in ['spec', 'qa', 'tools', 'frontend']:
        paths.mkdir(root / child)
    paths.write(root / 'spec/KEEP.txt','fictional specification: must remain unchanged\n')
    paths.write(root / 'qa/KEEP.txt','fictional QA: must remain unchanged\n')
    paths.copyfile(B / 'build_paths.py', root / 'build_paths.py')
    paths.copyfile(B / 'tools/build.py', root / 'tools/build.py')
    paths.copyfile(B / 'tools/build_config.json', root / 'tools/build_config.json')
    if (B / 'frontend/build.py').exists():
        paths.copyfile(B / 'frontend/build.py', root / 'frontend/build.py')
    return root

def inputs(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in ['spec', 'qa'] for p in (root / directory).rglob('*') if p.is_file()}

def rejects(action, name):
    try:
        action()
    except ValueError as error:
        raw.append(name + ': ' + str(error))
        check(True, name)
    else:
        check(False, name)

def reject_helper(root, frontend=False):
    before = inputs(root)
    script = 'frontend/build.py' if frontend else 'tools/build.py'
    arguments = ['publish'] if frontend else ['--skip-tests']
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run([sys.executable, '-X', 'utf8', script, *arguments], cwd=root, env=env,
                            capture_output=True, text=True, encoding='utf8', errors='replace')
    raw.append(script + '\n' + result.stdout + result.stderr)
    check(result.returncode != 0 and ('Redirected' in result.stderr or 'redirect' in result.stderr), root.name + ': actual helper rejected before compiler/npm')
    check(before == inputs(root), root.name + ': fictional specification and QA unchanged')

if not SPEC.is_dir():
    raise SystemExit(f'Canonical specification root missing: {SPEC}')
actual_spec_before = {str(p.relative_to(SPEC)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in SPEC.rglob('*') if p.is_file()}
try:
    normal = fixture('normal')
    guard = OutputPaths(normal)
    guard.write(normal / 'build/normal.txt', 'final\n')
    guard.write(normal / '.tmp/normal.txt', 'temporary\n')
    check((normal / 'build/normal.txt').read_text('utf8') == 'final\n', 'regular final output accepted')
    check((normal / '.tmp/normal.txt').read_text('utf8') == 'temporary\n', 'regular temporary output accepted')
    rejects(lambda: guard.write(normal / 'spec/KEEP.txt', 'must fail'), 'direct specification write rejected')
    rejects(lambda: guard.remove(normal / '.tmp/../qa'), 'lexical parent traversal into QA rejected')

    for name, relative, target in [
        ('temporary-root', '.tmp', 'spec'),
        ('final-app', 'build/app', 'spec'),
        ('final-publish', 'build/publish', 'qa'),
        ('final-report', 'build/test-results', 'spec'),
        ('temporary-build', '.tmp/build', 'spec'),
        ('temporary-runtime', '.tmp/runtime', 'qa'),
        ('nuget-descendant', '.tmp/nuget/packages', 'spec'),
        ('publish-descendant', 'build/publish/nested', 'spec'),
    ]:
        root = fixture(name)
        link = root / relative
        link.parent.mkdir(parents=True, exist_ok=True)
        junction(link, root / target)
        reject_helper(root)
        remove_link(link)
        links.remove(link)

    if (B / 'frontend/build.py').exists():
        for name, relative in [('frontend-work', '.tmp/frontend'), ('frontend-final', 'build/publish'),
                               ('frontend-wrong-link', 'frontend/node_modules'),
                               ('frontend-redirected-target', '.tmp/frontend/node_modules')]:
            root = fixture(name)
            link = root / relative
            link.parent.mkdir(parents=True, exist_ok=True)
            junction(link, root / 'spec')
            reject_helper(root, frontend=True)
            remove_link(link)
            links.remove(link)
        root = fixture('frontend-dedicated-link')
        guard = OutputPaths(root)
        target = guard.mkdir(root / '.tmp/frontend/node_modules')
        link = root / 'frontend/node_modules'
        junction(link, target)
        check(guard.frontend_link() == (link, target), 'exact dedicated frontend dependency link accepted')
        guard.preflight()
        check(True, 'dedicated link does not permit redirects beneath its temporary target')
        remove_link(link)
        links.remove(link)
finally:
    for link in reversed(links):
        remove_link(link)
    actual_spec_after = {str(p.relative_to(SPEC)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in SPEC.rglob('*') if p.is_file()}
    check(actual_spec_before == actual_spec_after, 'actual method specification unchanged')

paths.write(report / 'path-guard.log', '\n'.join(raw) + '\n')
paths.write(report / 'path-guard.json', json.dumps(dict(status='PASSED', checks=len(checks), assertions=checks,
            scope='Production OutputPaths and copied production helper entry points; disposable fictional inputs, no real DB/deployment'), indent=2) + '\n')
print(json.dumps(dict(method=B.name, status='PASSED', checks=len(checks))))
