"""Readable, persistent public IDs; retain opaque IDs as migration aliases.

The ledger is metadata, not an analysis cache. New entries never renumber old
ones; deleted entries reserve their numbers. Paths renamed with identical source
content inherit their prior identity only when that match is unambiguous.
"""
from __future__ import annotations
from copy import deepcopy
import re
from .store import digest


def assign(features: list[dict], ledger: dict | None = None, project: str = '') -> dict:
    ledger = deepcopy(ledger or {'schema': 'contextbase.identities.v1', 'project': project, 'entries': []})
    if ledger.get('project', project) != project:
        raise ValueError('Identity ledger belongs to a different project')
    entries = ledger['entries']
    if len({e['id'] for e in entries}) != len(entries):
        raise ValueError('Duplicate identity ledger IDs')
    used = {e['id'] for e in entries}
    current_paths = {f['path'] for f in features}
    for f in sorted(features, key=lambda f: (f['kind'], f['path'])):
        prefix = 'SCR' if f['kind'] == 'screen' else 'COM'
        previous = next((e for e in entries if e['path'] == f['path']), None)
        if previous is None:
            candidates = [e for e in entries if e['path'] not in current_paths and
                          e.get('kind') == f['kind'] and e.get('source_sha256') == f.get('source_sha256')]
            if len(candidates) == 1:
                previous = candidates[0]
        requested = f.get('id', '')
        opaque = bool(re.fullmatch(r'[FC]-[A-F0-9]{10}', requested))
        if previous:
            public = previous['id']
            if requested and not opaque and requested != public:
                raise ValueError('Explicit ID conflicts with the identity ledger: '+f['path'])
        else:
            if requested and not opaque:
                public = requested
                if public in used:
                    raise ValueError('Duplicate explicit public ID: '+public)
            else:
                values = [int(i.split('-')[1]) for i in used if re.fullmatch(prefix+r'-\d+', i)]
                public = f'{prefix}-{max(values, default=0)+1:03}'
            previous = {'id': public, 'path': f['path'], 'aliases': [], 'previous_paths': []}
            entries.append(previous)
            used.add(public)
        aliases = set(previous.get('aliases', [])) | set(f.get('aliases', []))
        if requested and requested != public:
            aliases.add(requested)
        # The previous generator used these hashes even on a first clean migration.
        legacy = ('F-' if f['kind']=='screen' else 'C-') + digest(f['path'])[:10].upper()
        if legacy != public:
            aliases.add(legacy)
        if previous['path'] != f['path']:
            previous.setdefault('previous_paths', []).append(previous['path'])
        previous.update(path=f['path'], name=f['name'], kind=f['kind'],
                        source_sha256=f.get('source_sha256'), aliases=sorted(aliases), active=True)
        f.update(id=public, aliases=sorted(aliases))
    for e in entries:
        e['active'] = e['path'] in current_paths
    ledger['project'] = project
    ledger['entries'] = sorted(entries, key=lambda e: e['id'])
    return ledger


def resolve(requested: str | None, features: list[dict]) -> str | None:
    if requested is None:
        return None
    matches = [f['id'] for f in features if requested == f['id'] or requested in f.get('aliases', [])]
    if len(matches) != 1:
        raise ValueError('Unknown or ambiguous feature ID: '+requested)
    return matches[0]
