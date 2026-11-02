"""Snapshot-bound compiler declarations, separate from raw syntax observations.

Resolved means a compile-time declaration under the recorded analysis context.
It never confirms an interface implementation, deployment or runtime execution.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile

from . import contracts
from .facts import source_texts


VERSION = 'contextbase-semantic-calls/1'
POLICY = ('Resolved targets are compiler-selected declarations under the recorded '
          'project and metadata inputs. Interface/virtual implementation candidates '
          'are navigation aids, not confirmed runtime targets. Positions are evidence '
          'pointers; they do not constitute delivery or interpretation of original source.')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _implementation():
    from . import semantic_project
    return {p.name: _sha(p) for p in (Path(__file__), Path(semantic_project.__file__))}


class SemanticCallIndex:
    def __init__(self, document, facts, *, cache_hit=False):
        self.document = document
        self.facts = facts
        self.sha256 = contracts.digest(document)
        self.cache_hit = cache_hit

    @classmethod
    def open(cls, facts, store, *, project, dotnet_root=None, package_roots=None, configuration='Release'):
        from .dotnet_host import run_semantic_host, semantic_host_fingerprint
        from .semantic_project import build_project_context
        facts.validate()
        texts = source_texts(facts.source)
        context = build_project_context(texts, project=project, dotnet_root=dotnet_root,
            package_roots=package_roots, configuration=configuration, omitted=facts.source.manifest['omitted'])
        binding = {'schema': VERSION, 'snapshotId': facts.source.snapshot_id,
                   'sourceFactsSha256': facts.sha256, 'rootProject': project,
                   'implementation': _implementation(), 'host': semantic_host_fingerprint(),
                   'context': deepcopy(context['binding'])}
        path = 'semantic-calls/' + contracts.digest(binding) + '.json'
        if store.path(path).exists():
            document = store.get(path)
            if document.get('binding') != binding:
                raise ValueError('Semantic-call cache binding changed')
            result = cls(document, facts, cache_hit=True)
        else:
            response = run_semantic_host(context)
            document = _join(facts, context, response, binding)
            result = cls(document, facts)
            result.validate()
            store.put(path, document)
        result.validate()
        return result

    def assert_current_source(self):
        """Explicit current-tree check; frozen-version queries remain reproducible."""
        from .sources import SourceAccess
        source = self.facts.source
        manifest = source.manifest
        home = Path(__file__).resolve().parents[2] / '.tmp'
        home.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='semantic-current-', dir=home) as directory:
            current = SourceAccess.create(Path(manifest['sourceRoot']), Path(directory) / 'snapshot',
                project_id=manifest['projectId'], allowed_paths=manifest['allowedPaths'],
                excluded_paths=manifest['excludedPaths'])
            if current.snapshot_id != source.snapshot_id:
                raise ValueError('Current source differs from the frozen semantic index; create a new snapshot')

    def validate(self):
        """Recheck frozen source, syntax identities, toolchain and metadata bytes."""
        from .dotnet_host import semantic_host_fingerprint
        self.facts.validate()
        document = self.document
        binding = document.get('binding', {})
        if (document.get('schema') != VERSION or binding.get('schema') != VERSION
                or binding.get('snapshotId') != self.facts.source.snapshot_id
                or binding.get('sourceFactsSha256') != self.facts.sha256
                or binding.get('implementation') != _implementation()
                or binding.get('host') != semantic_host_fingerprint()
                or contracts.digest(document) != self.sha256):
            raise ValueError('Semantic-call source, index or implementation binding changed')
        for reference in binding['context']['references']:
            if _sha(reference['path']) != reference['sha256']:
                raise ValueError('Semantic-call metadata reference changed')
        for package in binding['context'].get('packages', []):
            archive = package.get('archive')
            if archive and _sha(archive['path']) != archive['sha256']:
                raise ValueError('Semantic-call package archive changed')
        projects = {p['id']: p for p in document['projects']}
        seen = set()
        for row in document['results']:
            identity = (row['projectId'], row['callSiteId'])
            if identity in seen or row['projectId'] not in projects:
                raise ValueError('Duplicate or unknown semantic-call context')
            seen.add(identity)
            raw = self.facts.by_id.get(row['callSiteId'])
            if (raw is None or raw['kind'] != 'call' or raw['path'] != row['path']
                    or raw['data']['evidence'] != row['evidence']
                    or row['status'] not in {'resolved', 'candidates', 'unresolved', 'dynamic'}
                    or row['runtimeTargetConfirmed'] is not False):
                raise ValueError('Invalid semantic-call source identity or resolution')
            keys = row['candidateKeys'] + row['implementationCandidateKeys']
            if row['declaredTargetKey'] is not None:
                keys += [row['declaredTargetKey']]
            if any(key not in document['symbols'] for key in keys):
                raise ValueError('Semantic-call declaration is missing')
            if row['status'] == 'resolved':
                if (row['compilerStatus'] != 'resolved' or row['declaredTargetKey'] is None
                        or row['bindingDiagnostics'] or not projects[row['projectId']]['configurationComplete']):
                    raise ValueError('Incomplete semantic-call result cannot claim resolved')
                symbol = document['symbols'][row['declaredTargetKey']]
                if symbol['origin'] == 'source' and not symbol['sourceSymbolIds']:
                    raise ValueError('Resolved source declaration has no exact raw identity')
        for symbol in document['symbols'].values():
            expected = [self.facts.by_id[key] for key in symbol['sourceSymbolIds']]
            if (any(fact['kind'] != 'symbol' for fact in expected)
                    or symbol['evidence'] != [ref for fact in expected for ref in fact['data']['evidence']]):
                raise ValueError('Semantic declaration evidence binding changed')
        for registration in document['registrations']:
            raw = self.facts.by_id.get(registration['callSiteId'])
            if (raw is None or raw['kind'] != 'call' or registration['evidence'] != raw['data']['evidence']
                    or registration['runtimeTargetConfirmed'] is not False
                    or registration['conditional'] is not True
                    or any(k not in document['symbols'] for k in
                           [registration['serviceTypeKey'], *registration['implementationTypeKeys']])):
                raise ValueError('Invalid static registration observation')
        return {'schema': 'contextbase-semantic-calls-validation/1', 'status': 'pass',
                'snapshotId': binding['snapshotId'], 'sourceFactsSha256': self.facts.sha256,
                'indexSha256': self.sha256, 'counts': dict(Counter(r['status'] for r in document['results'])),
                'projects': len(projects), 'unjoinedCompilerCalls': len(document['unjoinedCompilerCalls']),
                'limitations': [POLICY, 'No SQL data flow, runtime trace or business classification is inferred.']}

    def query(self, *, text=None, path=None, caller=None, callee=None, status=None, limit=50, offset=0):
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('Semantic query limit must be between 1 and 1000')
        if type(offset) is not int or offset < 0:
            raise ValueError('Semantic query offset must be a nonnegative integer')
        if path is not None and path not in self.facts.source.paths:
            raise ValueError('Semantic query path is outside the sealed inventory')
        if status is not None and status not in {'resolved', 'candidates', 'unresolved', 'dynamic'}:
            raise ValueError('Unknown semantic resolution status')
        self.validate()
        selected = []
        for row in self.document['results']:
            if path is not None and row['path'] != path:
                continue
            if callee is not None and row['calleeText'] != callee:
                continue
            parent = self.facts.by_id.get(row['callerId'], {}).get('data', {})
            if caller is not None and caller not in {row['callerId'], parent.get('name'), parent.get('qualifiedName')}:
                continue
            if status is not None and row['status'] != status:
                continue
            target = self.document['symbols'].get(row['declaredTargetKey'], {})
            if text is not None and not any(text.casefold() in str(v).casefold() for v in
                    [row['calleeText'], row['path'], parent.get('qualifiedName'), target.get('signature')]):
                continue
            selected.append(row)
        results = []
        service_types = set()
        for row in selected[offset:offset + limit]:
            result = deepcopy(row)
            result['declaredTarget'] = deepcopy(self.document['symbols'].get(result.pop('declaredTargetKey')))
            if result['declaredTarget']:
                service_types.add(result['declaredTarget'].get('containingTypeKey'))
            result['candidates'] = [deepcopy(self.document['symbols'][k]) for k in result.pop('candidateKeys')]
            result['implementationCandidates'] = [deepcopy(self.document['symbols'][k])
                                                  for k in result.pop('implementationCandidateKeys')]
            results.append(result)
        registrations = []
        for observation in self.document['registrations']:
            if observation['serviceTypeKey'] in service_types:
                registration = deepcopy(observation)
                registration['serviceType'] = deepcopy(self.document['symbols'][registration.pop('serviceTypeKey')])
                registration['implementationTypes'] = [deepcopy(self.document['symbols'][key])
                                                        for key in registration.pop('implementationTypeKeys')]
                registrations.append(registration)
        return {'schema': VERSION, 'snapshotId': self.facts.source.snapshot_id,
                'sourceFactsSha256': self.facts.sha256, 'indexSha256': self.sha256,
                'matchBasis': POLICY, 'matchedCount': len(selected), 'returnedCount': len(results),
                'offset': offset, 'nextOffset': offset + len(results) if offset + len(results) < len(selected) else None,
                'truncated': len(results) != len(selected), 'results': results, 'registrationObservations': registrations,
                'projects': [{'id': p['id'], 'configurationComplete': p['configurationComplete'],
                    'sourceFiles': len(p['sourcePaths']),
                    'compilerDiagnosticCounts': dict(Counter(d['severity'] for d in p['compilerDiagnostics']))}
                    for p in self.document['projects']]}


def _join(facts, context, response, binding):
    by_span = defaultdict(list)
    raw_calls = defaultdict(list)
    for fact in facts.by_id.values():
        data = fact['data']
        if fact['kind'] in {'symbol', 'call'} and 'startByte' in data:
            key = (fact['path'], data['startByte'], data['endByte'])
            (by_span if fact['kind'] == 'symbol' else raw_calls)[key].append(fact)
    symbols = {}

    def symbol_key(descriptor):
        if descriptor is None:
            return None
        value = deepcopy(descriptor)
        matches = []
        for declaration in value['declarations']:
            matches.extend(by_span.get((declaration['path'], declaration['startByte'], declaration['endByte']), []))
        # A compiler generated constructor is not the containing type declaration.
        if value.get('kind') in {'method', 'constructor', 'local-function'}:
            matches = [f for f in matches if f['data']['kind'] == value['kind']]
        value['sourceSymbolIds'] = list(dict.fromkeys(f['id'] for f in matches))
        value['evidence'] = [ref for f in matches for ref in f['data']['evidence']]
        if value['origin'] == 'metadata':
            value['metadataReferenceSetSha256'] = contracts.digest(binding['context']['references'])
        key = value['key']
        if key in symbols and symbols[key] != value:
            raise ValueError('Compiler symbol identity is ambiguous across project contexts')
        symbols[key] = value
        return key

    projects, results, unjoined, registrations = [], [], [], []
    contexts = {p['id']: p for p in context['projects']}
    if {p['id'] for p in response['projects']} != set(contexts):
        raise ValueError('Compiler project coverage changed')
    for project in response['projects']:
        setup = contexts[project['id']]
        source_paths = [f['path'] for f in setup['files']]
        projects.append({'id': project['id'], 'sourcePaths': source_paths,
                         'configurationComplete': setup['configurationComplete'],
                         'configurationDiagnostics': deepcopy(setup.get('diagnostics', [])),
                         'compilerDiagnostics': deepcopy(project['diagnostics'])})
        joined = set()
        for observation in project.get('registrations', []):
            key = (observation['path'], observation['startByte'], observation['endByte'])
            matches = raw_calls.get(key, [])
            if len(matches) != 1:
                unjoined.append({'projectId': project['id'], **deepcopy(observation),
                                 'reason': 'Registration has no unique raw call-site span.'})
                continue
            registrations.append({'projectId': project['id'], 'callSiteId': matches[0]['id'],
                'evidence': deepcopy(matches[0]['data']['evidence']),
                'serviceTypeKey': symbol_key(observation['serviceType']),
                'implementationTypeKeys': list(dict.fromkeys(symbol_key(t) for t in observation['implementationTypes'])),
                'factory': observation['factory'], 'registrationMethod': observation['registrationMethod'],
                'conditional': True, 'runtimeTargetConfirmed': False})
        for observed in project['calls']:
            key = (observed['path'], observed['startByte'], observed['endByte'])
            matches = raw_calls.get(key, [])
            if len(matches) != 1:
                unjoined.append({'projectId': project['id'], **deepcopy(observed),
                                 'reason': 'No unique raw call-site span; no name fallback was attempted.'})
                continue
            raw = matches[0]
            joined.add(raw['id'])
            target = symbol_key(observed['declaredTarget'])
            candidates = list(dict.fromkeys(symbol_key(d) for d in observed['candidates']))
            implementations = list(dict.fromkeys(symbol_key(d) for d in observed['implementationCandidates']))
            diagnostics = deepcopy(observed['bindingDiagnostics'])
            status = observed['compilerStatus']
            if status == 'resolved':
                if target and symbols[target]['origin'] == 'source' and not symbols[target]['sourceSymbolIds']:
                    diagnostics.append({'id': 'source-identity-unjoined', 'severity': 'error',
                                        'message': 'No exact raw declaration span for the compiler target.'})
                if diagnostics or not setup['configurationComplete']:
                    status = 'candidates' if target or candidates else 'unresolved'
            data = raw['data']
            results.append({'projectId': project['id'], 'callSiteId': raw['id'], 'path': raw['path'],
                            'callerId': data['callerId'], 'callerContext': data['callerContext'],
                            'calleeText': data['name'], 'evidence': deepcopy(data['evidence']),
                            'status': status, 'compilerStatus': observed['compilerStatus'],
                            'declaredTargetKey': target, 'candidateKeys': candidates,
                            'implementationCandidateKeys': implementations,
                            'dispatchKind': observed['dispatchKind'], 'runtimeTargetConfirmed': False,
                            'candidateReason': observed.get('candidateReason'), 'bindingDiagnostics': diagnostics})
        for rows in raw_calls.values():
            for raw in rows:
                if raw['path'] in source_paths and raw['id'] not in joined:
                    data = raw['data']
                    results.append({'projectId': project['id'], 'callSiteId': raw['id'], 'path': raw['path'],
                                    'callerId': data['callerId'], 'callerContext': data['callerContext'],
                                    'calleeText': data['name'], 'evidence': deepcopy(data['evidence']),
                                    'status': 'unresolved', 'compilerStatus': 'unresolved',
                                    'declaredTargetKey': None, 'candidateKeys': [], 'implementationCandidateKeys': [],
                                    'dispatchKind': 'unknown', 'runtimeTargetConfirmed': False, 'candidateReason': None,
                                    'bindingDiagnostics': [{'id': 'call-site-unjoined', 'severity': 'error',
                                        'message': 'No exact compiler call span; syntax observation retained.'}]})
    return {'schema': VERSION, 'binding': binding, 'projects': projects, 'symbols': symbols,
            'results': results, 'registrations': registrations, 'unjoinedCompilerCalls': unjoined, 'policy': POLICY}
