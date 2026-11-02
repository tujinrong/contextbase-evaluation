"""Snapshot role instructions and explicit Codex settings without copying credentials."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import tomllib

VERSION = 'contextbase-roles/1'
_SETTINGS = ('model', 'model_reasoning_effort', 'model_provider')


def normalize_roles(config=None, base_dir=None):
    config = {} if config is None else config
    if not isinstance(config, dict) or set(config) - {'analysis', 'verification'}:
        raise ValueError('Roles must map analysis and verification operations')
    root = Path(base_dir or Path.cwd()).resolve()
    user_path = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'config.toml'
    inherited = {}
    if user_path.is_file():
        # Never persist complete user configuration (it may include credentials).
        with user_path.open('rb') as stream:
            user_config = tomllib.load(stream)
        inherited = {key: user_config[key] for key in _SETTINGS if key in user_config}
    result = {}
    for operation, filename in (('analysis', 'native_analysis_instructions.md'),
                                ('verification', 'native_verification_instructions.md')):
        entry = config.get(operation, {})
        if not isinstance(entry, dict) or set(entry) - {'id', 'instructions', *_SETTINGS}:
            raise ValueError('Unknown role configuration field')
        path = Path(entry.get('instructions', Path(__file__).with_name(filename)))
        path = (path if path.is_absolute() else root / path).resolve()
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        if not text.strip():
            raise ValueError('Role instructions must be nonempty UTF-8')
        identifier = entry.get('id', operation)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError('Role id must be nonempty')
        spec = {'schema': VERSION, 'id': identifier, 'operation': operation,
                'instructions_path': str(path), 'instructions_text': text,
                'instructions_sha256': hashlib.sha256(raw).hexdigest()}
        sources = {}
        for key in _SETTINGS:
            value = entry.get(key, inherited.get(key))
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError('Role Codex settings must be nonempty strings')
                spec[key] = value
                sources[key] = 'role' if key in entry else 'user-config'
        if spec.get('model_provider', 'openai') != 'openai':
            raise ValueError('Native roles require an explicit supported OpenAI provider; custom provider inheritance is unsupported')
        spec['configuration_sources'] = sources
        result[operation] = spec
    return result


def validate_role(spec, operation=None, *, check_file=True):
    if not isinstance(spec, dict) or spec.get('schema') != VERSION:
        raise ValueError('Unknown role snapshot')
    required = {'schema', 'id', 'operation', 'instructions_path', 'instructions_text', 'instructions_sha256'}
    if not required.issubset(spec) or set(spec) - required - set(_SETTINGS) - {'configuration_sources'}:
        raise ValueError('Invalid role snapshot fields')
    if spec['operation'] not in {'analysis', 'verification'} or (operation and spec['operation'] != operation):
        raise ValueError('Role operation mismatch')
    if any(not isinstance(spec[k], str) or not spec[k].strip() for k in required):
        raise ValueError('Invalid role snapshot values')
    raw = spec['instructions_text'].encode('utf-8')
    if hashlib.sha256(raw).hexdigest() != spec['instructions_sha256']:
        raise ValueError('Role instruction content changed')
    path = Path(spec['instructions_path'])
    if not path.is_absolute() or (check_file and path.read_bytes() != raw):
        raise ValueError('Role instruction file changed')
    for key in _SETTINGS:
        if key in spec and (not isinstance(spec[key], str) or not spec[key].strip()):
            raise ValueError('Invalid role Codex setting')
    return deepcopy(spec)


def validate_roles(mapping, *, check_file=True):
    if not isinstance(mapping, dict) or set(mapping) != {'analysis', 'verification'}:
        raise ValueError('Both author and independent verifier roles are required')
    return {key: validate_role(value, key, check_file=check_file) for key, value in mapping.items()}
