"""Optional frozen semantic evidence for ordinary independent D/R tasks.

This module selects and binds shared compiler data. It never interprets
business behavior, adopts a catalog, or launches another Agent.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import PurePosixPath
import time


VERSION = 'contextbase-semantic-evidence/1'
RUNTIME_VERSION = 'contextbase-semantic-runtime/1'
INITIAL_MAX_GROUPS = 2
INITIAL_MAX_CHARS = 8000
POLICY = '''Host static call bindings are available in this task.
Ordinary syntax query responses include semanticBindings and canonical
declarationFacts for returned calls. The host also supplies a bounded initial
packet for known investigation paths. Use these checked compile-time targets
directly: do not search or reread files merely to rediscover a resolved target.
Read original source to interpret business purpose, conditions, argument values,
SQL and data effects. A resolved declaration is not a confirmed runtime edge.
Keep interface declarations, implementation candidates and conditional DI
registrations separate. Candidates, dynamic and unresolved items remain unknown
unless new evidence answers them. Independent review checks business relevance,
omissions and uncertainty, not a second guess at host compiler bindings.
Query pointers alone are not original-source text delivery. Fact usage may cite
only actual canonical facts delivered in this task, with ordinary source rules.
'''


def normalize_options(options):
    if options is None:
        return None
    if (not isinstance(options, dict) or not {'project'}.issubset(options)
            or set(options) - {'schema', 'project', 'configuration'}
            or options.get('schema', VERSION) != VERSION):
        raise ValueError('Semantic options require a supported schema and explicit project')
    project = options['project']
    if not isinstance(project, str) or not project or '\\' in project or ':' in project:
        raise ValueError('Semantic project must be a canonical relative csproj path')
    path = PurePosixPath(project)
    if (str(path) != project or path.is_absolute() or '..' in path.parts
            or path.suffix.lower() != '.csproj'):
        raise ValueError('Semantic project must be a canonical relative csproj path')
    configuration = options.get('configuration', 'Release')
    if not isinstance(configuration, str) or configuration not in {'Debug', 'Release'}:
        raise ValueError('Semantic configuration must be Debug or Release')
    return {'schema': VERSION, 'project': project, 'configuration': configuration}


def initialize(session, *, create=False):
    """Create once or reopen the exact derived index fixed by this session."""
    options = normalize_options(session.config.get('semanticOptions'))
    if options is None:
        return None
    pointer_path = 'semantic-runtime.json'
    existing = session.store.get(pointer_path) if session.store.path(pointer_path).exists() else None
    if existing is None and not create:
        raise ValueError('Semantic runtime binding is missing; use a fresh initialized workspace')
    cached = getattr(session, '_semantic_runtime_index', None)
    if cached is not None:
        if existing != getattr(session, '_semantic_runtime_pointer', None):
            raise ValueError('Semantic runtime binding changed')
        return cached
    from .facts import FactIndex
    from .semantic_calls import SemanticCallIndex
    started = time.perf_counter()
    raw = FactIndex.open(session.source, session.store)
    index = SemanticCallIndex.open(raw, session.store, project=options['project'],
                                   configuration=options['configuration'])
    binding = {'schema': RUNTIME_VERSION, 'policy': VERSION, 'options': options,
               'snapshotId': session.source.snapshot_id, 'sourceFactsSha256': raw.sha256,
               'semanticIndexSha256': index.sha256}
    if existing is not None:
        if any(existing.get(key) != value for key, value in binding.items()):
            raise ValueError('Semantic runtime inputs or implementation changed; create a new workspace')
        pointer = existing
    else:
        pointer = {**binding, 'preparationSeconds': time.perf_counter() - started,
                   'derivedCacheHit': index.cache_hit}
        session.store.put(pointer_path, pointer)
    session._semantic_runtime_index = index
    session._semantic_runtime_pointer = deepcopy(pointer)
    return index


def fact_index(session, raw):
    """Attach navigation without changing any raw source-fact document or ID."""
    semantic = initialize(session)
    if semantic is not None:
        if semantic.facts.sha256 != raw.sha256 or semantic.facts.source.snapshot_id != raw.source.snapshot_id:
            raise ValueError('Semantic evidence belongs to another source-fact index')
        raw.semantic_index = semantic
    return raw


def task_extensions(session):
    index = initialize(session)
    if index is None:
        return {}
    index.validate()
    return {'semanticPolicy': VERSION, 'semanticIndexSha256': index.sha256}


def capabilities(session):
    index = initialize(session)
    if index is None:
        return None
    pointer = session.store.get('semantic-runtime.json')
    return {'policy': VERSION, 'indexSha256': index.sha256,
            'snapshotId': index.facts.source.snapshot_id, 'sourceFactsSha256': index.facts.sha256,
            'project': pointer['options']['project'], 'configuration': pointer['options']['configuration'],
            'preparationSeconds': pointer['preparationSeconds'],
            'counts': dict(Counter(r['status'] for r in index.document['results'])),
            'projects': [{'id': p['id'], 'sourceFileCount': len(p['sourcePaths']),
                          'configurationComplete': p['configurationComplete']}
                         for p in index.document['projects']],
            'unjoinedCompilerCallCount': len(index.document['unjoinedCompilerCalls']),
            'delivery': 'Bounded initial query packets and ordinary call queries include checked static bindings.',
            'initialNavigation': {'maxCallerGroups': INITIAL_MAX_GROUPS, 'maxChars': INITIAL_MAX_CHARS,
                'meaning': 'Partial source-focused navigation only; oversized items remain available on demand.'},
            'meaning': 'Compiler declaration navigation, not runtime selection or business correctness.',
            'lookup': 'Use ordinary query with kind:call and a path or caller; paginate using nextOffset.'}


def initial_requests(index, task, unit=None, materials=None):
    """Preselect a small ordinary query packet; it grants no authority itself."""
    if task.get('semanticPolicy') != VERSION:
        return []
    semantic = getattr(index, 'semantic_index', None)
    if semantic is None and hasattr(index, 'facts'):
        semantic = index
    if semantic is None or task.get('semanticIndexSha256') != semantic.sha256:
        raise ValueError('Initial semantic delivery requires the task-bound index')
    raw = semantic.facts
    acquired = {p['path'] for p in raw.document['files']}
    call_paths = {r['path'] for r in semantic.document['results']}
    paths = []
    if unit is not None:
        paths.extend(unit.get('paths', []))
        for key in unit.get('recordKeys', []):
            record = (materials or {}).get('records', {}).get(key, {})
            paths.extend(ref['path'] for ref in record.get('evidence', []))
        for key in unit.get('unknownIds', []):
            unknown = (materials or {}).get('unknowns', {}).get(key, {})
            content = unknown.get('content', unknown)
            paths.extend(ref['path'] for ref in content.get('evidence', []))
    else:
        paths.extend(f['path'] for f in raw.by_id.values() if f['kind'] == 'entry')
        if not paths:
            paths.extend(sorted(call_paths))
    selected = []
    for path in paths:
        if path in acquired and path in call_paths and path not in selected:
            selected.append(path)
    path_order = {path: position for position, path in enumerate(selected)}
    symbols = semantic.document['symbols']
    groups = defaultdict(dict)
    for row in semantic.document['results']:
        if row['path'] not in path_order:
            continue
        keys = [row['declaredTargetKey'], *row['candidateKeys'], *row['implementationCandidateKeys']]
        if not any(symbols.get(key, {}).get('sourceSymbolIds') for key in keys):
            continue
        call = raw.by_id[row['callSiteId']]
        identity = (row['path'], call['data']['callerId'])
        groups[identity][call['id']] = row
    entry_callers = {f['data'].get('symbolId') for f in raw.by_id.values() if f['kind'] == 'entry'} - {None}

    def group_rank(item):
        (path, caller), rows = item
        parent = raw.by_id.get(caller, {}).get('data', {})
        return (caller not in entry_callers, -len(rows), path_order[path], parent.get('startByte', 0))

    requests = []
    for (path, caller), group in sorted(groups.items(), key=group_rank)[:INITIAL_MAX_GROUPS]:
        row = min(group.values(), key=lambda r: (
            r['status'] != 'resolved',
            not bool(symbols.get(r['declaredTargetKey'], {}).get('sourceSymbolIds')),
            raw.by_id[r['callSiteId']]['data']['startByte']))
        call = raw.by_id[row['callSiteId']]
        matching = raw.query(kind='call', path=path, caller=caller, callee=call['data']['name'])['facts']
        offset = next(i for i, fact in enumerate(matching) if fact['id'] == call['id'])
        requests.append({'operation': 'query', 'offset': offset, 'limit': 1, 'path': path,
                         'kind': 'call', 'text': None, 'caller': caller,
                         'callee': call['data']['name'], 'route': None})
    return requests


def initial_pairs(access, index, task, unit=None, materials=None):
    """Deliver complete receipts only within the small initial navigation budget."""
    pairs = []
    for request in initial_requests(index, task, unit, materials):
        reply = access.handle(request)
        if reply['status'] != 'ok':
            continue
        candidate = [*pairs, {'request': request, 'reply': reply}]
        size = len(json.dumps(candidate, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':'), allow_nan=False))
        if size <= INITIAL_MAX_CHARS:
            pairs = candidate
    return pairs
