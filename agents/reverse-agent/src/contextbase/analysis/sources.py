"""Scoped, sealed source access. Input programs and configuration are never run."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path, PurePosixPath

from contextbase.ai.capsule import (
    EXCLUDED_DIRECTORIES, TEXT_SUFFIXES, decode, material_path, safe_path,
    sha256, write_json,
)

SCHEMA = 'contextbase-source-snapshot/1'
SEAL_SCHEMA = 'contextbase-source-seal/1'
PRIVATE_NAMES = frozenset({'agents.md', 'agent.md', 'claude.md', 'skill.md',
                           'prompt.md', '.env', 'appsettings.local.json'})


def source_lines(text: str) -> list[str]:
    """Keep original delimiters; count LF rows like the Tree-sitter adapter.

    Unicode separators within a literal must not shift all later evidence rows.
    """
    parts = text.split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def _canonical(value: str, *, root: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError('A canonical relative source path is required')
    path = PurePosixPath(value)
    if (str(path) != value or path.is_absolute() or '..' in path.parts or
            '\\' in value or ':' in value or (value == '.' and not root) or
            any(part.endswith((' ', '.')) for part in path.parts)):
        raise ValueError('Invalid source path: ' + value)
    return value


def _scope(values: list[str]) -> list[str]:
    if not isinstance(values, list):
        raise ValueError('Source scope must be a list')
    result = [_canonical(value, root=True) for value in values]
    if len({value.casefold() for value in result}) != len(result):
        raise ValueError('Duplicate or ambiguous source scope')
    return sorted(result)


def _inside(path: str, prefixes: list[str]) -> bool:
    path = path.casefold()
    return any(prefix == '.' or path == prefix.casefold() or
               path.startswith(prefix.casefold() + '/') for prefix in prefixes)


def _needed(path: str, prefixes: list[str]) -> bool:
    """A selected file/subtree or an ancestor needed to reach it."""
    return _inside(path, prefixes) or any(
        prefix.casefold().startswith(path.casefold() + '/') for prefix in prefixes)


def _forbidden(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if any(part.casefold() in EXCLUDED_DIRECTORIES for part in parts):
        return 'excluded-directory'
    name = parts[-1].casefold()
    if name in PRIVATE_NAMES or name.startswith('.env.'):
        return 'instructions-or-local-secret'
    return None


def _json(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate snapshot JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Non-finite snapshot JSON number')
    result = json.loads(path.read_text(encoding='utf-8'),
                        object_pairs_hook=unique, parse_constant=invalid)
    if not isinstance(result, dict):
        raise ValueError('Snapshot JSON object required')
    return result


def _walk_error(error: OSError) -> None:
    raise ValueError('Source/snapshot directory cannot be enumerated: ' + str(error.filename)) from error


class SourceAccess:
    """Every public read revalidates the sealed inventory and raw file bytes."""

    def __init__(self, root: Path, snapshot_id: str):
        self.root = root
        self._snapshot_id = snapshot_id

    @classmethod
    def create(cls, source_root: Path, destination: Path, *, project_id: str,
               allowed_paths: list[str], excluded_paths: list[str]) -> SourceAccess:
        source = safe_path(source_root)
        destination = safe_path(destination)
        if not source.is_dir() or any(
                part.casefold() in EXCLUDED_DIRECTORIES for part in source.parts):
            raise ValueError('An authorized source directory is required')
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError('Project identity is required')
        allowed, excluded = _scope(allowed_paths), _scope(excluded_paths)
        if not allowed:
            raise ValueError('An explicit nonempty source scope is required')
        if (destination == source or source in destination.parents or
                destination in source.parents):
            raise ValueError('Source and snapshot must not overlap')
        if destination.exists():
            raise ValueError('Snapshot destination must be fresh')
        files, omitted, selected = [], [], []
        seen = set()
        # Prune scope and excluded directories before inspecting material contents.
        for base, directories, names in os.walk(source, followlinks=False, onerror=_walk_error):
            for name in sorted(directories + names):
                relative = (Path(base) / name).relative_to(source).as_posix()
                is_directory = name in directories
                reason = (_forbidden(relative) or
                          ('excluded-path' if _inside(relative, excluded) else None) or
                          ('outside-allowed-paths' if not _needed(relative, allowed) else None))
                if reason:
                    omitted.append({'path': relative, 'reason': reason})
                    if is_directory:
                        directories.remove(name)
                    continue
                _canonical(relative)
                identity = relative.casefold()
                if identity in seen:
                    raise ValueError('Ambiguous source path case: ' + relative)
                seen.add(identity)
                item = safe_path(source / relative)
                if is_directory:
                    continue
                if not _inside(relative, allowed):
                    omitted.append({'path': relative, 'reason': 'outside-allowed-paths'})
                    continue
                if not item.is_file():
                    raise ValueError('Regular source file required: ' + relative)
                if item.suffix.casefold() not in TEXT_SUFFIXES:
                    omitted.append({'path': relative, 'reason': 'unsupported-text-material'})
                    continue
                data = item.read_bytes()
                try:
                    text, encoding = decode(data)
                except (ValueError, UnicodeError) as exc:
                    omitted.append({'path': relative, 'reason': 'unsupported-encoding-or-binary',
                                    'diagnostic': str(exc)})
                    continue
                files.append({'path': relative, 'sha256': sha256(data),
                              'encoding': encoding, 'lines': len(source_lines(text)),
                              'bytes': len(data)})
                selected.append((item, relative, data))
            directories.sort()
        if not files:
            raise ValueError('No supported source material in authorized scope')
        destination.mkdir(parents=True)
        for item, relative, data in selected:
            if item.read_bytes() != data:
                raise ValueError('Source changed during snapshot: ' + relative)
            target = material_path(destination, 'sources/' + relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(data)
        manifest = {'schema': SCHEMA, 'projectId': project_id,
                    'sourceRoot': str(source), 'allowedPaths': allowed,
                    'excludedPaths': excluded, 'mode': 'source-only',
                    'files': sorted(files, key=lambda entry: entry['path']),
                    'omitted': sorted(omitted, key=lambda entry: entry['path'])}
        for item, relative, data in selected:
            if safe_path(item).read_bytes() != data:
                raise ValueError('Source changed before snapshot seal: ' + relative)
        write_json(destination / 'manifest.json', manifest)
        write_json(destination / 'seal.json', {
            'schema': SEAL_SCHEMA,
            'manifestSha256': sha256((destination / 'manifest.json').read_bytes()),
        })
        return cls.open(destination)

    @classmethod
    def open(cls, destination: Path) -> SourceAccess:
        root = safe_path(destination)
        try:
            digest = sha256(material_path(root, 'manifest.json').read_bytes())
        except OSError as exc:
            raise ValueError('A sealed source snapshot is required') from exc
        instance = cls(root, digest)
        instance.verify()
        return instance

    @property
    def snapshot_id(self) -> str:
        self.verify()
        return self._snapshot_id

    @property
    def manifest(self) -> dict:
        self.verify()
        return copy.deepcopy(_json(material_path(self.root, 'manifest.json')))

    @property
    def paths(self) -> list[str]:
        return [entry['path'] for entry in self.manifest['files']]

    def verify(self) -> None:
        try:
            self._verify()
        except (OSError, KeyError, TypeError, UnicodeError) as exc:
            raise ValueError('Invalid or incomplete source snapshot') from exc

    def _verify(self) -> None:
        root = safe_path(self.root)
        manifest_path = material_path(root, 'manifest.json')
        seal = _json(material_path(root, 'seal.json'))
        digest = sha256(manifest_path.read_bytes())
        if (seal.get('schema') != SEAL_SCHEMA or
                seal.get('manifestSha256') != digest or digest != self._snapshot_id):
            raise ValueError('Snapshot manifest differs from its seal or pinned identity')
        manifest = _json(manifest_path)
        if (manifest.get('schema') != SCHEMA or manifest.get('mode') != 'source-only' or
                not isinstance(manifest.get('projectId'), str) or not manifest['projectId'].strip()):
            raise ValueError('Unsupported snapshot contract')
        allowed, excluded = _scope(manifest['allowedPaths']), _scope(manifest['excludedPaths'])
        entries = manifest['files']
        if not allowed or not isinstance(entries, list) or not entries:
            raise ValueError('Snapshot requires explicit scope and nonempty source inventory')
        expected, seen, order = {'manifest.json', 'seal.json'}, set(), []
        for entry in entries:
            relative = _canonical(entry['path'])
            if (_forbidden(relative) or not _inside(relative, allowed) or
                    _inside(relative, excluded) or relative.casefold() in seen):
                raise ValueError('Invalid or ambiguous snapshot source scope')
            seen.add(relative.casefold())
            order.append(relative)
            data = material_path(root, 'sources/' + relative).read_bytes()
            text, encoding = decode(data)
            if (entry['sha256'] != sha256(data) or entry['encoding'] != encoding or
                    type(entry['bytes']) is not int or entry['bytes'] != len(data) or
                    type(entry['lines']) is not int or entry['lines'] != len(source_lines(text))):
                raise ValueError('Snapshot source metadata differs from raw bytes')
            expected.add('sources/' + relative)
        if order != sorted(order):
            raise ValueError('Noncanonical snapshot inventory order')
        actual = set()
        expected_directories = {parent.as_posix() for name in expected
                                for parent in PurePosixPath(name).parents
                                if parent.as_posix() != '.'}
        for base, directories, names in os.walk(root, followlinks=False, onerror=_walk_error):
            for name in directories + names:
                item = safe_path(Path(base) / name)
                if name in names:
                    actual.add(item.relative_to(root).as_posix())
                elif item.relative_to(root).as_posix() not in expected_directories:
                    raise ValueError('Unlisted snapshot directory')
        if actual != expected:
            raise ValueError('Unlisted or missing snapshot material')

    def _range(self, path: str, start_line: int, end_line: int | None, *, allow_empty=False):
        self.verify()
        path = _canonical(path)
        manifest = _json(material_path(self.root, 'manifest.json'))
        entry = next((entry for entry in manifest['files'] if entry['path'] == path), None)
        if entry is None:
            raise ValueError('Source path is outside the sealed inventory')
        whole_empty_file = (allow_empty and end_line is None and entry['lines'] == 0
                            and type(start_line) is int and start_line == 1)
        end_line = entry['lines'] if end_line is None else end_line
        if not whole_empty_file and (type(start_line) is not int or type(end_line) is not int or
                start_line < 1 or end_line < start_line or end_line > entry['lines']):
            raise ValueError('Evidence requires a nonempty exact source line range')
        data = material_path(self.root, 'sources/' + path).read_bytes()
        if sha256(data) != entry['sha256']:
            raise ValueError('Source changed during access')
        return entry, data, end_line

    def read(self, path: str, start_line: int = 1, end_line: int | None = None) -> str:
        _, data, end_line = self._range(path, start_line, end_line, allow_empty=True)
        return ''.join(source_lines(decode(data)[0])[start_line - 1:end_line])

    def evidence(self, path: str, start_line: int = 1, end_line: int | None = None) -> dict:
        entry, _, end_line = self._range(path, start_line, end_line)
        return {'path': path, 'startLine': start_line, 'endLine': end_line,
                'sha256': entry['sha256']}

    def verify_evidence(self, ref: dict) -> None:
        if not isinstance(ref, dict) or set(ref) != {'path', 'startLine', 'endLine', 'sha256'}:
            raise ValueError('Exact source evidence fields required')
        expected = self.evidence(ref['path'], ref['startLine'], ref['endLine'])
        if ref != expected:
            raise ValueError('Evidence hash differs from sealed source bytes')
