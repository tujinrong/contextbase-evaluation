"""Freeze explicitly selected native capabilities and documentation-only Skills."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path, PurePosixPath
import re


VERSION = 'contextbase-capabilities/1'
MAX_BUNDLE_BYTES = 1_048_576
MAX_BUNDLE_FILES = 256
MAX_SKILLS = 16
_DOCUMENT_SUFFIXES = {'.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.csv', '.svg'}
_NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
_SHA256 = re.compile(r'[0-9a-f]{64}\Z')


def _linked(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def _check_links(path):
    if any(_linked(part) for part in (path, *path.parents)):
        raise ValueError('Skill paths must not contain symlinks or junctions')


def _name(raw):
    try:
        lines = raw.decode('utf-8').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError('Skills must use UTF-8 text') from exc
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        raise ValueError('SKILL.md requires YAML frontmatter with a name')
    header = lines[1:lines[1:].index('---') + 1]
    names = [line[5:].strip() for line in header if line.startswith('name:')]
    if len(names) != 1:
        raise ValueError('SKILL.md requires exactly one top-level name')
    name = names[0]
    if len(name) >= 2 and name[0] == name[-1] and name[0] in {'"', "'"}:
        name = name[1:-1]
    if not 1 <= len(name) <= 64 or not _NAME.fullmatch(name):
        raise ValueError('Skill names must contain lowercase letters, numbers and hyphens')
    return name


def _scan_skill(path):
    _check_links(path)
    if path.name != 'SKILL.md' or not path.is_file():
        raise ValueError('Each selected Skill must name an existing SKILL.md')
    path = path.resolve()
    files, size, skill_raw = [], 0, None
    for item in sorted(path.parent.rglob('*'), key=lambda item: item.relative_to(path.parent).as_posix()):
        if _linked(item):
            raise ValueError('Skill bundles must not contain symlinks or junctions')
        if item.is_dir():
            continue
        if not item.is_file() or item.suffix.lower() not in _DOCUMENT_SUFFIXES:
            raise ValueError('Only documentation-only Skill bundles are supported; executable dependencies are unsupported')
        if len(files) >= MAX_BUNDLE_FILES or item.stat().st_size > MAX_BUNDLE_BYTES - size:
            raise ValueError('Selected Skill bundle exceeds its file or byte limit')
        raw = item.read_bytes()
        size += len(raw)
        if size > MAX_BUNDLE_BYTES:
            raise ValueError('Selected Skill bundle exceeds its byte limit')
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('Skill support documents must use UTF-8 text') from exc
        relative = item.relative_to(path.parent).as_posix()
        files.append({'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
        if item == path:
            skill_raw = raw
    return {'name': _name(skill_raw), 'path': str(path), 'files': files}


def normalize_capabilities(config=None, base_dir=None):
    """Resolve a role's opt-in capabilities and pin its complete Skill bundles."""
    config = {} if config is None else config
    if not isinstance(config, dict):
        raise ValueError('Role capabilities must be an object')
    if any(not isinstance(key, str) for key in config):
        raise ValueError('Role capability names must be strings')
    unsupported = set(config) - {'skills', 'web_search', 'subagents'}
    if unsupported:
        raise ValueError('Unsupported role capabilities: ' + ', '.join(sorted(unsupported)))
    selected = config.get('skills', [])
    if not isinstance(selected, list) or len(selected) > MAX_SKILLS:
        raise ValueError('Role skills must be a bounded list of SKILL.md paths')
    root = Path(base_dir or Path.cwd()).resolve()
    skills = []
    for value in selected:
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Role skills require nonempty SKILL.md paths')
        path = Path(value)
        skills.append(_scan_skill(path if path.is_absolute() else root / path))
    snapshot = {'schema': VERSION, 'skills': skills,
                'web_search': config.get('web_search', 'disabled'),
                'subagents': config.get('subagents', False)}
    return validate_capabilities(snapshot, check_files=False)


def _relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or PurePosixPath(value).is_absolute() or value != PurePosixPath(value).as_posix()
            or any(part in {'.', '..'} for part in PurePosixPath(value).parts)):
        raise ValueError('Invalid Skill support document path')
    return value


def validate_capabilities(snapshot, *, check_files=True):
    """Check a frozen policy; historic export checks can omit live file access."""
    if (not isinstance(snapshot, dict)
            or set(snapshot) != {'schema', 'skills', 'web_search', 'subagents'}
            or snapshot.get('schema') != VERSION):
        raise ValueError('Invalid role capability snapshot')
    if snapshot['web_search'] not in ('disabled', 'cached', 'live'):
        raise ValueError('web_search must be disabled, cached or live')
    if type(snapshot['subagents']) is not bool:
        raise ValueError('subagents must be a boolean')
    skills = snapshot['skills']
    if not isinstance(skills, list) or len(skills) > MAX_SKILLS:
        raise ValueError('Invalid selected Skill list')
    paths, names, total, count = set(), set(), 0, 0
    for skill in skills:
        if not isinstance(skill, dict) or set(skill) != {'name', 'path', 'files'}:
            raise ValueError('Invalid selected Skill snapshot')
        name, path = skill['name'], skill['path']
        if not isinstance(name, str) or not 1 <= len(name) <= 64 or not _NAME.fullmatch(name):
            raise ValueError('Invalid selected Skill name')
        if not isinstance(path, str) or not Path(path).is_absolute() or Path(path).name != 'SKILL.md':
            raise ValueError('Selected Skill path must be an absolute SKILL.md path')
        identity = os.path.normcase(os.path.normpath(path))
        if identity in paths or name in names:
            raise ValueError('Duplicate selected Skill path or name')
        paths.add(identity)
        names.add(name)
        files = skill['files']
        if not isinstance(files, list) or not files:
            raise ValueError('Selected Skill requires its support document manifest')
        relative_paths = []
        for entry in files:
            if not isinstance(entry, dict) or set(entry) != {'path', 'sha256', 'bytes'}:
                raise ValueError('Invalid Skill support document manifest')
            relative = _relative(entry['path'])
            if PurePosixPath(relative).suffix.lower() not in _DOCUMENT_SUFFIXES:
                raise ValueError('Only documentation-only Skill bundles are supported')
            if (not isinstance(entry['sha256'], str) or not _SHA256.fullmatch(entry['sha256'])
                    or type(entry['bytes']) is not int or entry['bytes'] < 0):
                raise ValueError('Invalid Skill support document fingerprint')
            relative_paths.append(relative)
            total += entry['bytes']
            count += 1
        if (relative_paths != sorted(set(relative_paths)) or 'SKILL.md' not in relative_paths
                or total > MAX_BUNDLE_BYTES or count > MAX_BUNDLE_FILES):
            raise ValueError('Invalid or oversized Skill support document manifest')
        if check_files and _scan_skill(Path(path)) != skill:
            raise ValueError('Selected Skill bundle changed')
    return deepcopy(snapshot)


def stage_skills(snapshot, directory):
    """Copy verified Skill documents into a caller-owned private directory."""
    policy = validate_capabilities(snapshot)
    if not policy['skills']:
        return []
    directory = Path(directory).absolute()
    _check_links(directory)
    contents = []
    for skill in policy['skills']:
        target = directory / skill['name']
        if target.exists():
            raise ValueError('Selected Skill staging destination already exists')
        rows = []
        for entry in skill['files']:
            raw = (Path(skill['path']).parent / entry['path']).read_bytes()
            if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError('Selected Skill bundle changed during staging')
            rows.append((entry['path'], raw))
        contents.append((target, rows))
    directory.mkdir(parents=True, exist_ok=True)
    result = []
    for target, rows in contents:
        target.mkdir()
        for relative, raw in rows:
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                stream.write(raw)
        result.append(target / 'SKILL.md')
    return result
