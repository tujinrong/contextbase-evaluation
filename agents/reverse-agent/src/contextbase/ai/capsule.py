"""Lossless source-only snapshots. No semantic inference or prose assembly."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone

EXCLUDED_DIRECTORIES = frozenset({
    '.git', '.vs', '.venv', '__pycache__', 'bin', 'obj', 'build', 'dist',
    'node_modules', 'spec', 'spec-eval', 'spec-analysis', 'test-report',
    'report', 'output', 'qa', 'metadata', 'agent-input', 'tests', 'test',
})
TEXT_SUFFIXES = frozenset({
    '.cs', '.vb', '.xaml', '.cshtml', '.razor', '.vue', '.ts', '.js', '.jsx',
    '.tsx', '.java', '.jsp', '.jspx', '.ftl', '.html', '.htm', '.css', '.scss',
    '.sql', '.json', '.xml', '.config', '.toml', '.yaml', '.yml', '.properties',
    '.csproj', '.vbproj', '.sln', '.props', '.targets', '.bas', '.cls', '.frm',
    '.c', '.h', '.cpp', '.hpp', '.cob', '.cbl', '.cpy', '.rpg', '.rpgle',
    '.sqlrpgle', '.dds', '.cl', '.clle', '.bnd', '.py', '.rb', '.go', '.rs',
    '.php', '.sh', '.ps1', '.bat', '.cmd', '.resx', '.txt',
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


def material_root(value: Path) -> Path:
    """An explicit source/design root never authorizes evaluator-only input."""
    value = safe_path(value)
    if any(part.casefold() == 'spec-eval' for part in value.parts):
        raise ValueError('Evaluator-only material is forbidden in a source/design capsule')
    if not value.is_dir():
        raise ValueError('Regular source/design directory required')
    return value


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


def create(source: Path, destination: Path, *, project_id: str,
           excluded_directories=EXCLUDED_DIRECTORIES,
           authorized_reference_directories: tuple[Path, ...] = ()) -> dict:
    source = material_root(source)
    destination = safe_path(destination)
    authorized_reference_directories = tuple(material_root(path) for path in authorized_reference_directories)
    if not source.is_dir() or source.is_symlink():
        raise ValueError('Regular source directory required')
    if destination == source or source in destination.parents:
        raise ValueError('Snapshot must be outside its source tree')
    if destination.exists():
        raise ValueError('Snapshot must be fresh; immutable artifacts cannot be overwritten')
    excluded = {name.casefold() for name in excluded_directories}
    destination.mkdir(parents=True)
    files, omitted = [], []
    for base, directories, names in os.walk(source, followlinks=False):
        directories.sort()
        for name in directories[:]:
            item = safe_path(Path(base) / name)
            if item.is_symlink():
                raise ValueError(f'Linked source directory refused: {item.relative_to(source)}')
            if name.casefold() in excluded:
                omitted.append({'path': item.relative_to(source).as_posix(), 'reason': 'excluded-directory'})
                directories.remove(name)
        for name in sorted(names):
            item = safe_path(Path(base) / name)
            relative = item.relative_to(source).as_posix()
            if item.is_symlink():
                raise ValueError(f'Linked source file refused: {relative}')
            if name.casefold() in {'agents.md', 'agent.md', '.env', 'appsettings.local.json'}:
                omitted.append({'path': relative, 'reason': 'instructions-or-local-secret'})
                continue
            if item.suffix.casefold() not in TEXT_SUFFIXES:
                omitted.append({'path': relative, 'reason': 'not-supported-text-material'})
                continue
            data = item.read_bytes()
            try:
                text, encoding = decode(data)
            except ValueError as exc:
                omitted.append({'path': relative, 'reason': str(exc)})
                continue
            original = destination / 'sources' / relative
            original.parent.mkdir(parents=True, exist_ok=True)
            with original.open('xb') as handle:
                handle.write(data)
            # Number every line without shortening literals, large methods, or SQL.
            numbered = destination / 'indexed' / (relative + '.txt')
            numbered.parent.mkdir(parents=True, exist_ok=True)
            lines = text.splitlines(keepends=True)
            with numbered.open('x', encoding='utf-8', newline='') as handle:
                handle.write(''.join(f'{i:06d} | {line}' for i, line in enumerate(lines, 1)))
            files.append({'path': relative, 'bytes': len(data), 'sha256': sha256(data),
                          'encoding': encoding, 'lines': len(lines),
                          'indexed': 'indexed/' + relative + '.txt'})
    if not files:
        raise ValueError('No source material found; extraction cannot report success')
    references = []
    for directory in authorized_reference_directories:
        originals = []
        for base, directories, names in os.walk(directory, followlinks=False):
            directories.sort()
            for name in directories:
                material_root(Path(base) / name)
            for name in sorted(names):
                original = safe_path(Path(base) / name)
                if original.suffix.casefold() == '.md':
                    originals.append(original)
        for original in originals:
            data = original.read_bytes()
            text, encoding = decode(data)
            relative = 'reference-designs/' + directory.name + '/' + original.relative_to(directory).as_posix()
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(data)
            references.append({'path': relative, 'bytes': len(data), 'sha256': sha256(data),
                               'encoding': encoding, 'lines': len(text.splitlines()),
                               'basis': 'user-authorized-training-reference',
                               'originalPath': str(original)})
    # Recheck source bytes before declaring this complete snapshot. The source
    # tree itself is never written by the extractor.
    for entry in files:
        if sha256(safe_path(source / entry['path']).read_bytes()) != entry['sha256']:
            raise ValueError('Original source changed during snapshot: ' + entry['path'])
    for entry in references:
        if sha256(safe_path(Path(entry['originalPath'])).read_bytes()) != entry['sha256']:
            raise ValueError('Training reference changed during snapshot: ' + entry['path'])
    manifest = {'schema': 'reverse-ai-source-capsule/2', 'projectId': project_id,
                'createdAt': datetime.now(timezone.utc).isoformat(), 'sourceRoot': str(source),
                'files': files, 'omitted': omitted, 'sourceBytesModified': False,
                'referenceSpecificationIncluded': bool(references),
                'trainingReferenceAuthorizedByUser': bool(authorized_reference_directories),
                'referenceFiles': references,
                'mode': 'training-assisted' if references else 'source-only',
                'semanticAnalysisPerformedByPython': False}
    write_json(destination / 'manifest.json', manifest)
    write_json(destination / 'seal.json', {
        'schema': 'reverse-ai-capsule-seal/1',
        'manifestSha256': sha256((destination / 'manifest.json').read_bytes()),
    })
    return manifest


def _load_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate artifact JSON member')
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('Non-finite artifact JSON number')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=nonfinite)


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


def _check_entry(entry: dict, data: bytes) -> tuple[str, list[str]]:
    text, encoding = decode(data)
    lines = text.splitlines(keepends=True)
    if (entry.get('sha256') != sha256(data) or
            type(entry.get('bytes')) is not int or entry['bytes'] != len(data) or
            type(entry.get('lines')) is not int or entry['lines'] != len(lines) or
            entry.get('encoding') != encoding):
        raise ValueError('Capsule material metadata differs from raw bytes: ' + str(entry.get('path')))
    return text, lines


def reference_mode(manifest: dict) -> str:
    mode = manifest.get('mode')
    if (mode is None and manifest.get('schema') == 'reverse-ai-source-capsule/1' and
            manifest.get('referenceSpecificationIncluded') is False and
            not manifest.get('referenceFiles', [])):
        return 'source-only'
    return mode


def verify(directory: Path) -> dict:
    directory = safe_path(directory)
    manifest_file = material_path(directory, 'manifest.json')
    manifest = _load_json(manifest_file)
    if manifest.get('schema') not in {'reverse-ai-source-capsule/1', 'reverse-ai-source-capsule/2'}:
        raise ValueError('Unsupported capsule schema')
    seal_file = material_path(directory, 'seal.json')
    if seal_file.exists():
        seal = _load_json(seal_file)
        if (seal.get('schema') != 'reverse-ai-capsule-seal/1' or
                seal.get('manifestSha256') != sha256(manifest_file.read_bytes())):
            raise ValueError('Capsule manifest differs from its seal')
    elif manifest['schema'] != 'reverse-ai-source-capsule/1':
        raise ValueError('A new capsule requires its immutable manifest seal')
    if not isinstance(manifest.get('files'), list) or not manifest['files']:
        raise ValueError('Capsule requires nonempty source material')
    reference_files = manifest.get('referenceFiles', [])
    if not isinstance(reference_files, list):
        raise ValueError('Reference material list required')
    mode = reference_mode(manifest)
    if mode == 'training-assisted':
        if not (reference_files and manifest.get('trainingReferenceAuthorizedByUser') is True and
                manifest.get('referenceSpecificationIncluded') is True):
            raise ValueError('Training references require consistent explicit authorization')
    elif mode != 'source-only' or reference_files or manifest.get('referenceSpecificationIncluded') is not False:
        raise ValueError('Source-only capsule cannot contain reference designs')
    seen = set()
    for entry in manifest['files']:
        key = entry['path'].casefold()
        if key in seen:
            raise ValueError('Duplicate capsule source identity')
        seen.add(key)
        original = material_path(directory, 'sources/' + entry['path'])
        data = original.read_bytes()
        _, lines = _check_entry(entry, data)
        expected = ''.join(f'{i:06d} | {line}' for i, line in enumerate(lines, 1)).encode('utf-8')
        expected_path = 'indexed/' + entry['path'] + '.txt'
        if entry.get('indexed') != expected_path:
            raise ValueError('Noncanonical indexed source path')
        indexed = material_path(directory, expected_path)
        if indexed.read_bytes() != expected:
            raise ValueError('Indexed text differs from sealed raw source: ' + entry['path'])
    for entry in reference_files:
        if not manifest.get('trainingReferenceAuthorizedByUser'):
            raise ValueError('Reference design supplied without explicit training authorization')
        if not entry['path'].startswith('reference-designs/'):
            raise ValueError('Invalid reference manifest path')
        key = entry['path'].casefold()
        if key in seen:
            raise ValueError('Duplicate capsule reference identity')
        seen.add(key)
        target = material_path(directory, entry['path'])
        _check_entry(entry, target.read_bytes())
    expected_files = {
        'sources': {'sources/' + entry['path'] for entry in manifest['files']},
        'indexed': {entry['indexed'] for entry in manifest['files']},
        'reference-designs': {entry['path'] for entry in reference_files},
    }
    for folder, expected in expected_files.items():
        material_root = safe_path(directory / folder)
        actual = set()
        if material_root.exists():
            for base, dirs, names in os.walk(material_root, followlinks=False):
                for name in dirs:
                    safe_path(Path(base) / name)
                for name in names:
                    item = safe_path(Path(base) / name)
                    actual.add(item.relative_to(directory).as_posix())
        if actual != expected:
            raise ValueError('Unlisted or missing capsule material in ' + folder)
    return manifest


def verification_state(directory: Path) -> dict:
    directory = safe_path(directory)
    manifest = verify(directory)
    return {'manifestSha256': sha256((directory / 'manifest.json').read_bytes()),
            'capsuleSchema': manifest['schema'], 'mode': reference_mode(manifest),
            'modeDerivation': 'legacy-v1-explicit-no-references' if 'mode' not in manifest else 'explicit-manifest-mode',
            'scope': 'sealed-manifest-and-raw-material' if (directory / 'seal.json').exists()
                     else 'legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest'}
