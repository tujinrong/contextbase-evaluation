"""Snapshot-bound syntax facts, reusable queries, and evidence validation.

The index proves where syntax was observed. It does not resolve call targets or
prove that a registered-looking endpoint is reachable in a deployed system.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.metadata
from pathlib import Path

from . import contracts
from .paths import material_path
from .sources import decode


VERSION = 'contextbase-source-facts/1'
_USAGE_POLICY = '''Fact IDs, source hashes and line ranges are host-owned.
Calls are syntax observations, not resolved semantic edges. A caller is the
containing declaration; lambda bodies retain their enclosing declared caller.
Entries are registration/declaration candidates, not proof of runtime reachability
or independent business functions. Unsupported files are not evidence of absence.
For every proposed record return factUsage with its recordKey, supporting factIds
and a reason explaining their relevance. Use relevant entry/call facts when they
support the claim; a class declaration alone does not prove an entire workflow.
Return analysis records using only task.recordKinds; catalog summaries belong
to the appropriate catalog kind. Source-fact rows are referenced via factUsage.
Every selected fact ID must overlap at least one evidence range on THAT record,
in the same source file. When selecting a supporting call or entry from another
file, add its exact source path, hash and line range to the record's evidence.
Use evidenceRanges for multi-location entries and structure.files for hashes.
Retain only fact references whose source evidence the record explicitly cites.
Empty factIds are allowed only when the record's evidence has no indexed facts;
explain the unsupported or uncovered material instead. Do not invent identifiers.
Return sourceFactsSha256 exactly as bound by the host task.'''
POLICY = '''Use the complete source-fact tables in structure, together with the
original source and full inventory. Table columns define each row; file indexes
refer to structure.files. ''' + _USAGE_POLICY
EVIDENCE_POLICY = '''Use host evidence requests to query snapshot-bound source
facts and read exact original source. The initial structure contains capability
metadata, not the complete fact rows. All facts and authorized original materials
remain available. Page through relevant results and investigate omissions using
the full inventory, registrations, reverse uses and unsupported materials.
Query evidence pointers are not original-source reads. Cite only source ranges
actually delivered in this task and fact IDs returned by its fact queries.
''' + _USAGE_POLICY
VERIFY_POLICY = '''Independently check the candidate's factUsage against the full
source-fact index, original source and inventory, including omissions outside
the author's chosen fact IDs. Return factUsageCheck with pass/fail/unknown,
reason and original-source evidence. An existing ID or matching file is not
proof that the fact supports the business claim. Preserve syntax/semantic and
registration/reachability distinctions. Return the host's sourceFactsSha256.'''
EVIDENCE_VERIFY_POLICY = '''Independently query the host's complete source-fact
index and read original source, including omissions outside the author's chosen
fact IDs. Query pointers alone do not prove that original source was read.
Return factUsageCheck with pass/fail/unknown, reason and original-source evidence
actually supplied to this verifier task. Preserve syntax/semantic and
registration/reachability distinctions. Return the host's sourceFactsSha256.
The entire candidate and retained verification view remain assigned; evidence
pagination does not narrow the requirements or permit skipping unknowns.'''


def extractor_fingerprint():
    from . import adapters
    versions = {}
    for package in ('tree-sitter', 'tree-sitter-c-sharp', 'tree-sitter-java'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return contracts.digest({'schema': VERSION, 'versions': versions,
        'implementation': {p.name: p.read_text(encoding='utf-8') for p in
            (Path(__file__), Path(adapters.__file__))}})


def source_texts(source):
    """Verify the sealed inventory once, then pin every individual read by hash."""
    source.verify()
    texts = {}
    for entry in source.manifest['files']:
        data = material_path(source.root, 'sources/' + entry['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Source changed during indexed access')
        texts[entry['path']] = decode(data)[0]
    return texts


class FactIndex:
    def __init__(self, document, source):
        self.document = document
        self.source = source
        self.sha256 = contracts.digest(document)
        self.by_id = {item['id']: item for item in document['facts']}

    @classmethod
    def open(cls, source, store, *, parser=None, extractor_sha256=None):
        from .adapters import index_source_isolated
        fingerprint = extractor_sha256 or extractor_fingerprint()
        binding = {'schema': VERSION, 'snapshotId': source.snapshot_id,
                   'extractorSha256': fingerprint}
        path = 'source-facts/' + contracts.digest(binding) + '.json'
        if store.path(path).exists():
            document = store.get(path)
            if any(document.get(key) != value for key, value in binding.items()):
                raise ValueError('Source-fact cache binding changed')
        else:
            texts = source_texts(source)
            files, facts = [], []
            parse = parser or index_source_isolated
            for entry in source.manifest['files']:
                raw = parse(entry['path'], texts[entry['path']], source_sha256=entry['sha256'])
                metadata = {key: deepcopy(value) for key, value in raw.items()
                            if key not in {'symbols', 'calls', 'imports', 'entries'}}
                metadata.update(sourceSha256=entry['sha256'], lines=entry['lines'])
                files.append(metadata)
                for collection, kind in [('symbols', 'symbol'), ('calls', 'call'),
                                         ('imports', 'import'), ('entries', 'entry')]:
                    for observation in raw.get(collection, []):
                        data = deepcopy(observation)
                        identifier = data.pop('id', None) or kind + ':' + contracts.digest(
                            [entry['path'], entry['sha256'], observation])
                        facts.append({'id': identifier, 'kind': kind, 'path': entry['path'], 'data': data})
            document = {**binding, 'files': files, 'facts': facts}
            # Validate before an immutable cache can become visible.
            cls(document, source).validate()
            store.put(path, document)
        result = cls(document, source)
        result.validate()
        return result

    def validate(self):
        self.source.verify()
        if self.document.get('schema') != VERSION or self.document.get('snapshotId') != self.source.snapshot_id:
            raise ValueError('Source-fact index belongs to another snapshot')
        expected = {item['path']: item for item in self.source.manifest['files']}
        files = self.document['files']
        if len(files) != len(expected) or {item['path'] for item in files} != set(expected):
            raise ValueError('Source-fact inventory coverage changed')
        for item in files:
            entry = expected[item['path']]
            if item['sourceSha256'] != entry['sha256'] or item['lines'] != entry['lines']:
                raise ValueError('Source-fact file binding changed')
        if len(self.by_id) != len(self.document['facts']):
            raise ValueError('Duplicate source-fact ID')
        for fact in self.document['facts']:
            if fact['kind'] not in {'symbol', 'call', 'entry', 'import'} or fact['path'] not in expected:
                raise ValueError('Invalid source-fact kind or path')
            data = fact['data']
            if not data.get('evidence'):
                raise ValueError('Source fact requires original-source evidence')
            for evidence in data['evidence']:
                entry = expected[fact['path']]
                if (set(evidence) != {'path', 'startLine', 'endLine', 'sha256'}
                        or evidence['path'] != fact['path'] or evidence['sha256'] != entry['sha256']
                        or type(evidence['startLine']) is not int or type(evidence['endLine']) is not int
                        or not 1 <= evidence['startLine'] <= evidence['endLine'] <= entry['lines']):
                    raise ValueError('Source-fact evidence binding changed')
            if fact['kind'] == 'call':
                if data.get('resolution') != 'unresolved':
                    raise ValueError('Syntax calls cannot claim semantic resolution')
                parent = data.get('callerId')
                if parent is not None:
                    caller = self.by_id.get(parent)
                    if caller is None or caller['kind'] != 'symbol' or caller['path'] != fact['path']:
                        raise ValueError('Source-fact caller does not exist in the file')
                    for evidence in data['evidence']:
                        if not any(ref['startLine'] <= evidence['startLine'] <= evidence['endLine'] <= ref['endLine']
                                   for ref in caller['data']['evidence']):
                            raise ValueError('Call lies outside its declared caller')
            if fact['kind'] == 'entry' and data.get('symbolId') is not None:
                symbol = self.by_id.get(data['symbolId'])
                if symbol is None or symbol['kind'] != 'symbol' or symbol['path'] != fact['path']:
                    raise ValueError('Source-fact entry declaration is missing')
        return {'schema': 'contextbase-source-facts-validation/1', 'status': 'pass',
                'indexSha256': self.sha256, 'snapshotId': self.source.snapshot_id,
                'extractorSha256': self.document['extractorSha256'],
                'files': len(files), 'counts': dict(Counter(item['kind'] for item in self.by_id.values())),
                'checks': ['cache binding and digest', 'complete sealed inventory', 'unique fact IDs',
                           'source hashes and line ranges', 'caller containment', 'entry declarations',
                           'no semantic resolution claims'],
                'limitations': ['Syntax facts do not prove runtime reachability, semantic binding or business boundaries.',
                               'Unsupported/partial files remain visible; zero facts do not establish absence.',
                               'C# entry rules omit inherited routes, MapGroup prefixes and CLI selector interpretation.']}

    def raw_indexes(self):
        result = []
        for file in self.document['files']:
            item = {key: deepcopy(value) for key, value in file.items() if key not in {'sourceSha256', 'lines'}}
            for collection, kind in [('symbols', 'symbol'), ('calls', 'call'), ('imports', 'import'), ('entries', 'entry')]:
                item[collection] = [{**deepcopy(fact['data']), 'id': fact['id']}
                                    for fact in self.document['facts'] if fact['path'] == file['path'] and fact['kind'] == kind]
            result.append(item)
        return result

    def query(self, *, text=None, path=None, kind=None, caller=None, callee=None, route=None, limit=None):
        if kind is not None and kind not in {'symbol', 'call', 'entry', 'import'}:
            raise ValueError('Unknown source-fact kind')
        if limit is not None and (type(limit) is not int or limit <= 0):
            raise ValueError('Query limit must be a positive integer')
        if path is not None and path not in {item['path'] for item in self.document['files']}:
            raise ValueError('Query path is outside the sealed source-fact inventory')
        found = []
        for fact in self.document['facts']:
            data = fact['data']
            if path is not None and fact['path'] != path:
                continue
            if kind is not None and fact['kind'] != kind:
                continue
            if callee is not None and (fact['kind'] != 'call' or data.get('name') != callee):
                continue
            if caller is not None:
                parent = self.by_id.get(data.get('callerId'), {})
                if fact['kind'] != 'call' or caller not in {data.get('callerId'), parent.get('data', {}).get('name'),
                                                           parent.get('data', {}).get('qualifiedName')}:
                    continue
            if route is not None and (fact['kind'] != 'entry' or data.get('route') != route):
                continue
            if text is not None:
                values = [fact['id'], fact['path'], *(str(data.get(key, '')) for key in
                          ('name', 'qualifiedName', 'signature', 'text', 'receiver', 'route'))]
                if not any(text.casefold() in value.casefold() for value in values):
                    continue
            found.append(deepcopy(fact))
        selected = found if limit is None else found[:limit]
        return {'schema': VERSION, 'snapshotId': self.source.snapshot_id, 'indexSha256': self.sha256,
                'matchBasis': 'syntax observations; callee names are not resolved symbol references',
                'matchedCount': len(found), 'returnedCount': len(selected), 'truncated': len(selected) != len(found),
                'files': [deepcopy(item) for item in self.document['files'] if path is None or item['path'] == path],
                'facts': selected}

    def context(self):
        """Lossless evidence projection with compact tables instead of repeated keys."""
        files = self.document['files']
        file_ids = {item['path']: number for number, item in enumerate(files)}
        tables = {
            'symbol': ['id', 'file', 'kind', 'name', 'qualifiedName', 'signature', 'startLine', 'endLine'],
            'call': ['id', 'file', 'callerId', 'callerContext', 'name', 'receiver', 'kind', 'arity', 'startLine', 'endLine'],
            'entry': ['id', 'file', 'kind', 'name', 'symbolId', 'verb', 'route', 'templateStatus', 'handlerShape',
                      'startLine', 'endLine', 'evidenceRanges'],
            'import': ['id', 'file', 'text', 'startLine', 'endLine'],
        }
        result = {'schema': VERSION, 'indexSha256': self.sha256, 'snapshotId': self.source.snapshot_id,
                  'files': deepcopy(files), 'counts': dict(Counter(fact['kind'] for fact in self.document['facts'])),
                  'limitations': self.validate()['limitations']}
        for kind, columns in tables.items():
            rows = []
            for fact in self.document['facts']:
                if fact['kind'] != kind:
                    continue
                values = {**fact['data'], 'id': fact['id'], 'file': file_ids[fact['path']]}
                refs = fact['data']['evidence']
                values.update(startLine=min(ref['startLine'] for ref in refs),
                              endLine=max(ref['endLine'] for ref in refs),
                              evidenceRanges=[[ref['startLine'], ref['endLine']] for ref in refs])
                rows.append([values.get(key) for key in columns])
            result[{'entry': 'entries'}.get(kind, kind + 's')] = {'columns': columns, 'rows': rows}
        return result

    def validate_usage(self, answer, expected_sha256):
        if expected_sha256 != self.sha256 or answer['sourceFactsSha256'] != self.sha256:
            raise ValueError('Source-fact usage belongs to another index or snapshot')
        records = {item['key']: item for item in answer['records']}
        usage = answer['factUsage']
        if len(usage) != len(records) or {item['recordKey'] for item in usage} != set(records):
            raise ValueError('Source-fact usage must account for every proposed record exactly once')
        for item in usage:
            record = records[item['recordKey']]
            available = {fact['id'] for fact in self.document['facts'] if any(
                ref['path'] == evidence['path'] and ref['startLine'] <= evidence['endLine']
                and evidence['startLine'] <= ref['endLine'] for ref in fact['data']['evidence']
                for evidence in record['evidence'])}
            missing = set(item['factIds']) - set(self.by_id)
            if missing:
                raise ValueError('Source-fact identifier does not exist: ' + item['recordKey'])
            disjoint = set(item['factIds']) - available
            if disjoint:
                raise ValueError('Source-fact evidence is not cited by record: ' + item['recordKey'])
            if available and not item['factIds']:
                raise ValueError('Available indexed evidence cannot be bypassed with empty fact usage')


def response_properties(task, verification):
    if not task.get('sourceFactsSha256'):
        return {}
    properties = {'sourceFactsSha256': {'type': 'string', 'const': task['sourceFactsSha256']}}
    if verification:
        properties['factUsageCheck'] = contracts.obj({'status': {'enum': ['pass', 'fail', 'unknown']},
            'reason': contracts.TEXT, 'evidence': contracts.arr(contracts.EVIDENCE)})
    else:
        properties['factUsage'] = contracts.arr(contracts.obj({'recordKey': contracts.TEXT,
            'factIds': contracts.STRINGS, 'reason': contracts.TEXT}))
    return properties
