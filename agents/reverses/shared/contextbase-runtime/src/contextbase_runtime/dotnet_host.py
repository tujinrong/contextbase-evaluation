"""Run our Roslyn front end without evaluating or building the input project.

Only this package's helper is compiled. Target text is passed over stdin and
never emitted; package analyzers, source generators and MSBuild are not loaded.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def _run(args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                            timeout=180, check=False, **kwargs)
    if result.returncode:
        raise RuntimeError('Trusted semantic helper failed: ' + (result.stderr + result.stdout)[-12000:])
    return result.stdout


def _toolchain():
    executable = shutil.which('dotnet')
    if not executable:
        raise RuntimeError('Static C# binding requires an installed .NET SDK')
    sdks = []
    for line in _run([executable, '--list-sdks']).splitlines():
        match = re.fullmatch(r'([^ ]+) \[(.*)\]', line.strip())
        if match and re.fullmatch(r'\d+(?:\.\d+)+', match[1]):
            sdks.append((tuple(map(int, match[1].split('.'))), Path(match[2]) / match[1]))
    if not sdks:
        raise RuntimeError('No stable .NET SDK available for semantic helper')
    _, sdk = max(sdks)
    config = json.loads((sdk / 'Roslyn/bincore/csc.runtimeconfig.json').read_text('utf-8'))
    return executable, sdk, config['runtimeOptions']


def framework_references(tfm, *, aspnet=False):
    """Explicit trusted framework metadata; no restore or build invocation."""
    _, sdk, _ = _toolchain()
    if not re.fullmatch(r'net\d+\.\d+', tfm):
        raise ValueError('Only explicit netN.N framework metadata is supported')
    root = sdk.parent.parent / 'packs'
    result = []
    for pack in ['Microsoft.NETCore.App.Ref'] + (['Microsoft.AspNetCore.App.Ref'] if aspnet else []):
        available = []
        for candidate in (root / pack).glob('*/ref/' + tfm):
            version = candidate.parents[1].name
            if re.fullmatch(r'\d+(?:\.\d+)+', version):
                available.append((tuple(map(int, version.split('.'))), candidate))
        if not available:
            raise ValueError(f'No installed {pack} metadata for {tfm}')
        result.extend(str(p.resolve()) for p in sorted(max(available)[1].glob('*.dll')))
    return result


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic_host_fingerprint():
    _, sdk, runtime = _toolchain()
    helper = Path(__file__).with_name('dotnet') / 'SemanticCalls.cs'
    compiler = sdk / 'Roslyn/bincore'
    return {'schema': 'contextbase-roslyn-host/1', 'helperSha256': _sha(helper),
            'packageHashHelperSha256': _sha(helper.with_name('NugetContentHash.cs')),
            'nuget': {name: _sha(sdk / name) for name in _NUGET_LIBRARIES},
            'bootstrapSha256': _sha(__file__), 'sdk': sdk.name,
            'runtime': runtime, 'compiler': {name: _sha(compiler / name) for name in
                ['csc.dll', 'Microsoft.CodeAnalysis.dll', 'Microsoft.CodeAnalysis.CSharp.dll']}}


def run_semantic_host(request, *, cache_root=None):
    executable, sdk, runtime = _toolchain()
    fingerprint = semantic_host_fingerprint()
    refs = framework_references(runtime['tfm'])
    fingerprint['bootstrapReferences'] = {str(Path(p).name): _sha(p) for p in refs}
    key = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    root = Path(cache_root) if cache_root is not None else Path(__file__).resolve().parents[2] / '.tmp/semantic-dotnet'
    root.mkdir(parents=True, exist_ok=True)
    destination = root / key
    marker = destination / 'ready.json'
    if not marker.exists():
        temporary = Path(tempfile.mkdtemp(prefix='compile-', dir=root))
        source = Path(__file__).with_name('dotnet') / 'SemanticCalls.cs'
        compiler = sdk / 'Roslyn/bincore'
        args = ['/nologo', '/target:exe', '/langversion:latest', '/nullable:enable',
                '/out:' + str(temporary / 'SemanticCalls.dll')]
        args += ['/reference:' + p for p in refs]
        args += ['/reference:' + str(compiler / name) for name in
                 ['Microsoft.CodeAnalysis.dll', 'Microsoft.CodeAnalysis.CSharp.dll']]
        args.append(str(source))
        # Fixed arguments come only from our helper/toolchain, never the target project.
        _run([executable, str(compiler / 'csc.dll'), *args])
        (temporary / 'SemanticCalls.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': runtime}), 'utf-8')
        for name in ['Microsoft.CodeAnalysis.dll', 'Microsoft.CodeAnalysis.CSharp.dll']:
            shutil.copyfile(compiler / name, temporary / name)
        bundle = {p.name: _sha(p) for p in temporary.iterdir() if p.is_file()}
        (temporary / 'ready.json').write_text(json.dumps({'fingerprint': fingerprint, 'bundle': bundle}, sort_keys=True), 'utf-8')
        try:
            temporary.rename(destination)
        except FileExistsError:
            # A concurrent compiler won; retain its immutable complete tool bundle.
            pass
    sealed = json.loads(marker.read_text('utf-8'))
    if sealed.get('fingerprint') != fingerprint:
        raise ValueError('Trusted helper cache binding changed')
    if any(_sha(destination / name) != digest for name, digest in sealed['bundle'].items()):
        raise ValueError('Trusted helper cache bytes changed')
    payload = _run([executable, str(destination / 'SemanticCalls.dll')],
                   input=json.dumps(request, ensure_ascii=False))
    return json.loads(payload)


_NUGET_LIBRARIES = ('NuGet.Packaging.dll', 'NuGet.Common.dll', 'NuGet.Frameworks.dll',
                    'NuGet.Versioning.dll', 'System.Security.Cryptography.Pkcs.dll')
_PACKAGE_HASHES = {}


def package_content_hashes(paths):
    """NuGet's stable signed/unsigned content hash, without restore or scripts.

    The raw archive is hashed before every reuse. Matching a lockfile content
    hash authenticates neither the lockfile nor a package's signing identity.
    """
    executable, sdk, runtime = _toolchain()
    source = Path(__file__).with_name('dotnet') / 'NugetContentHash.cs'
    references = framework_references(runtime['tfm'])
    fingerprint = {'source': _sha(source), 'sdk': sdk.name,
                   'compiler': _sha(sdk / 'Roslyn/bincore/csc.dll'),
                   'libraries': {name: _sha(sdk / name) for name in _NUGET_LIBRARIES},
                   'references': {str(Path(p).name): _sha(p) for p in references}, 'runtime': runtime}
    key = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    normalized = sorted({str(Path(p).resolve(strict=True)) for p in paths})
    archive_keys = {path: (key, path, _sha(path)) for path in normalized}
    missing = [path for path in normalized if archive_keys[path] not in _PACKAGE_HASHES]
    if missing:
        root = Path(__file__).resolve().parents[2] / '.tmp/semantic-nuget'
        root.mkdir(parents=True, exist_ok=True)
        destination = root / key
        marker = destination / 'ready.json'
        if not marker.exists():
            temporary = Path(tempfile.mkdtemp(prefix='compile-', dir=root))
            args = ['/nologo', '/target:exe', '/langversion:latest', '/nullable:enable',
                    '/out:' + str(temporary / 'NugetContentHash.dll')]
            args += ['/reference:' + p for p in references]
            args += ['/reference:' + str(sdk / name) for name in _NUGET_LIBRARIES]
            _run([executable, str(sdk / 'Roslyn/bincore/csc.dll'), *args, str(source)])
            (temporary / 'NugetContentHash.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': runtime}), 'utf-8')
            for name in _NUGET_LIBRARIES:
                shutil.copyfile(sdk / name, temporary / name)
            bundle = {p.name: _sha(p) for p in temporary.iterdir() if p.is_file()}
            (temporary / 'ready.json').write_text(json.dumps({'fingerprint': fingerprint, 'bundle': bundle}, sort_keys=True), 'utf-8')
            try:
                temporary.rename(destination)
            except FileExistsError:
                pass
        sealed = json.loads(marker.read_text('utf-8'))
        if sealed.get('fingerprint') != fingerprint or any(_sha(destination / n) != h for n, h in sealed['bundle'].items()):
            raise ValueError('Trusted package hash helper cache changed')
        values = json.loads(_run([executable, str(destination / 'NugetContentHash.dll')], input=json.dumps(missing)))
        for path in missing:
            if _sha(path) != archive_keys[path][2]:
                raise ValueError('Package archive changed while computing content hash')
            _PACKAGE_HASHES[archive_keys[path]] = values[path]
    return {path: _PACKAGE_HASHES[archive_keys[path]] for path in normalized}
