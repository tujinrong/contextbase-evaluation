"""One-shot publication of reviewed specification sources; no application deployment."""
from pathlib import Path
import base64, hashlib, json, lzma, os, shutil, subprocess, sys, tempfile, zipfile

BASE = '5f6a8a3b8b0a40c413295cd6a65fe28cbc9fa7dd'
PAYLOAD_SHA = 'c026c170d8cf6b597e1fbda89209997f02e51220f600fbe712e0aabb640dda27'
WORKFLOW = '.github/workflows/spec-v6-publish.yml'
ROOT = Path.cwd()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def main():
    if git('rev-parse', '--abbrev-ref', 'HEAD').decode().strip() != 'main':
        raise RuntimeError('Publication requires main')
    if git('status', '--porcelain').strip():
        raise RuntimeError('Checkout is not clean')
    subprocess.run(['git', 'diff', '--quiet', BASE, 'HEAD', '--', 'docs', 'spec'], check=True)
    preparatory = git('rev-parse', 'HEAD').decode().strip()
    payload = ''.join((ROOT / f'_spec_v6/source.{i:02}.b64').read_text() for i in range(1, 9))
    packed = base64.b64decode(payload, validate=True)
    if hashlib.sha256(packed).hexdigest() != PAYLOAD_SHA:
        raise RuntimeError('Reviewed source checksum mismatch')
    sources = json.loads(lzma.decompress(packed))
    expected = {'common.py','enhance.py','fields.py','newdocs.py','pipeline.py','render.py','reports.py','restructure.py','screens.py','verify.py'}
    if set(sources) != expected:
        raise RuntimeError('Unexpected source manifest')
    work = Path(tempfile.mkdtemp(prefix='spec-v6-', dir=os.environ.get('RUNNER_TEMP')))
    baseline, tools, output = work/'baseline', work/'tools', work/'output'
    tools.mkdir(); baseline.mkdir()
    old_paths = git('ls-tree', '-rz', '--name-only', BASE, '--', 'docs', 'spec').decode().split('\0')
    old_paths = [p for p in old_paths if p]
    if len(old_paths) != 39 or any(not p.endswith('.md') for p in old_paths):
        raise RuntimeError('Unexpected baseline inventory')
    for name in old_paths:
        target = baseline/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git('show', BASE+':'+name))
    for name, source in sources.items():
        compile(source, name, 'exec')
        (tools/name).write_text(source, encoding='utf-8')
    env = dict(os.environ, SPEC_BASE=str(baseline), SPEC_OUT=str(output), PYTHONPATH=str(tools), PYTHONUTF8='1')
    subprocess.run([sys.executable, str(tools/'pipeline.py')], env=env, check=True)
    result = json.loads((output/'validation_results.json').read_text())
    counts = result['counts']
    if result['status'] != 'PASS' or result['errors'] or counts['markdownFiles'] != 62 or counts['renderedScreens'] != 14 or counts['maximumPerVariant'] != 567:
        raise RuntimeError('Specification checks did not pass')
    files = sorted(p for folder in ('docs','spec') for p in (output/folder).rglob('*') if p.is_file())
    if len(files) != 90 or any(p.suffix not in {'.md','.html','.png'} for p in files):
        raise RuntimeError('Unexpected deliverable inventory')
    new_paths = {p.relative_to(output).as_posix() for p in files}
    for name in old_paths:
        if name not in new_paths:
            (ROOT/name).unlink()
    for source in files:
        destination = ROOT/source.relative_to(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    shutil.rmtree(ROOT/'_spec_v6')
    (ROOT/WORKFLOW).unlink()
    subprocess.run(['git','add','-A','--','docs','spec','_spec_v6',WORKFLOW], check=True)
    subprocess.run(['git','config','user.name','github-actions[bot]'], check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'], check=True)
    subprocess.run(['git','commit','-m','docs: publish round-trip specifications, rendered layouts and scoring baselines'], check=True)
    commit = git('rev-parse','HEAD').decode().strip()
    # Refuse to overwrite a concurrent main update. Push is non-force.
    remote = git('ls-remote','origin','refs/heads/main').decode().split()[0]
    if remote != preparatory:
        raise RuntimeError('Main changed concurrently; publication aborted without pushing')
    subprocess.run(['git','push','origin','HEAD:main'], check=True)
    delivery = Path(os.environ['RUNNER_TEMP'])/'spec-v6-delivery'
    delivery.mkdir(exist_ok=True)
    archive = delivery/'student-management-spec-v6.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for file in files:
            z.write(file, file.relative_to(output).as_posix())
    manifest = {'commit':commit,'baseCommit':BASE,'specVersion':'6.0','validation':result,'files':[]}
    for file in files:
        manifest['files'].append({'path':file.relative_to(output).as_posix(),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    (delivery/'publication.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    for name in ('validation_results.json','render_results.json','score_manifest.json','screen_manifest.json'):
        shutil.copy2(output/name, delivery/name)
    print('PUBLISHED_COMMIT='+commit, flush=True)
    print(json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
