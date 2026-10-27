"""User-supplied document routing, without business facts or prose templates."""
from __future__ import annotations

import json
from pathlib import Path

from . import capsule, schemas


TEXT = {'type': 'string', 'minLength': 1}
SCHEMA = schemas.obj({
    'schema': {'type': 'string', 'const': 'reverse-ai-document-contract/1'},
    'projectId': TEXT,
    'documents': {'type': 'array', 'minItems': 1, 'items': schemas.obj({
        'id': TEXT, 'kind': TEXT, 'path': TEXT,
        'sourcePaths': {'type': 'array', 'minItems': 1, 'uniqueItems': True, 'items': TEXT},
    })},
})
FILENAME = 'document-contract.json'


def validate(value: dict, manifest: dict | None = None) -> None:
    """Validate identities and raw source entry points; never infer their meaning."""
    from jsonschema import Draft202012Validator, ValidationError
    from .workflow import relative_path
    try:
        Draft202012Validator(SCHEMA).validate(value)
    except ValidationError as exc:
        raise ValueError('Invalid document contract schema') from exc
    if manifest is not None and value['projectId'] != manifest['projectId']:
        raise ValueError('Document contract project differs from the source capsule')
    identities, paths = set(), set()
    sources = {entry['path'] for entry in manifest['files']} if manifest is not None else None
    for document in value['documents']:
        for field in ('id', 'kind'):
            text = document[field]
            if text != text.strip() or not text.strip() or any(ord(char) < 32 for char in text):
                raise ValueError('Nonempty canonical document contract identity/kind required')
        path = relative_path(document['path'])
        identity = document['id'].casefold()
        if identity in identities or path.casefold() in paths:
            raise ValueError('Duplicate document contract identity or output path')
        identities.add(identity); paths.add(path.casefold())
        # sourcePaths are entry points, not a dependency-search ceiling.
        if sources is not None and not set(document['sourcePaths']) <= sources:
            raise ValueError('Document contract requires canonical raw source entry paths')


def load(path: Path, manifest: dict) -> tuple[dict, bytes]:
    path = capsule.safe_path(path)
    original = path.read_bytes()
    value = capsule._load_json(path)
    if path.read_bytes() != original:
        raise ValueError('Document contract changed while being read')
    validate(value, manifest)
    return value, original


def match(plan: dict, contract: dict, manifest: dict) -> None:
    """Require the exact requested document set while allowing discovered dependencies."""
    from .workflow import _materials
    validate(contract, manifest)
    documents = {document['id']: document for document in plan['documents']}
    requested = {document['id']: document for document in contract['documents']}
    if set(documents) != set(requested):
        missing = sorted(set(requested) - set(documents))
        extra = sorted(set(documents) - set(requested))
        raise ValueError(f'Document contract coverage mismatch; missing={missing}, unexpected={extra}')
    materials = _materials(manifest)
    for identity, expected in requested.items():
        actual = documents[identity]
        if actual['path'] != expected['path'] or actual['kind'] != expected['kind']:
            raise ValueError('Document contract path/kind mismatch: ' + identity)
        origins = {materials[path]['original'] for path in actual['sourcePaths']
                   if materials[path]['kind'] == 'source'}
        if not set(expected['sourcePaths']) <= origins:
            raise ValueError('Document contract source entries are missing from the AI plan: ' + identity)


def prompt(value: dict) -> str:
    return ('\nユーザー指定の文書対応契約（業務の正解値や本文ではありません）:\n'
            + json.dumps(value, ensure_ascii=False, indent=2)
            + '\n契約の全ID、kind、相対pathを変更せず、それぞれ一度だけ計画してください。'
              '契約外の文書、分析報告、共通索引を追加しません。'
              'sourcePathsは必須の原ソース探索開始点であり、関連する依存先の追加と追跡は許可します。'
              '題名とresponsibilitiesは原ソースから判断し、名前から業務の期待値を創作しません。'
              '補足の共通契約や解析制限は関係するfacts・coverageNotes・unresolvedへ保持し、'
              '契約外の文書へ説明を委ねません。')


def bound(plan_file: Path, handoff: dict, manifest: dict | None = None) -> dict | None:
    """Revalidate the pinned copy before every later AI phase."""
    path = capsule.safe_path(plan_file.parent / FILENAME)
    pin = handoff.get('documentContract')
    if pin is None:
        if path.exists():
            raise ValueError('Document contract is present without its plan handoff pin')
        return None
    if (not isinstance(pin, dict) or set(pin) != {'schema', 'file', 'sha256'} or
            pin['schema'] != 'reverse-ai-document-contract/1' or pin['file'] != FILENAME or
            pin['sha256'] != capsule.sha256(path.read_bytes())):
        raise ValueError('Document contract differs from its plan handoff')
    value = capsule._load_json(path)
    validate(value, manifest)
    return value
