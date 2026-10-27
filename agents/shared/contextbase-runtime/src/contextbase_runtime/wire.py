"""Task-local compact transport, exactly expanded before domain validation."""
from __future__ import annotations

from copy import deepcopy
from . import contracts


VERSION = 'contextbase-wire/1'
POLICY = '''Transport encoding for this task: use the supplied response schema.
Evidence is {file,startLine,endLine}; file is the ref shown in inventory.files.
The host restores the exact bound path and source hash. Fact IDs in structure
are task-local short references; copy those references into factUsage.factIds.
The host restores canonical fact IDs without changing business statements.
Return wireSha256 exactly as task.wireSha256. References from another task are
invalid. All ordinary evidence, uncertainty and adoption rules still apply.
Keep statements, rationale, alternatives and unknown reasons at catalog depth:
one concise explanation each. Leave internal conditions, branches, exceptions,
state transitions and detailed call differences to relationship/behavior.
Preserve every required record, uncertainty and contrary interpretation.'''


def bind(task, index):
    prefix = task['id'][:10]
    binding = {'schema': VERSION, 'taskId': task['id'], 'contextId': task['contextId'],
        'snapshotId': task['snapshotId'], 'indexSha256': index.sha256,
        'candidate': task['candidate'], 'viewSha256': task['viewSha256'],
        'files': {f'p{prefix}_{n}': {'path': item['path'], 'sha256': item['sourceSha256']}
                  for n, item in enumerate(index.document['files'])},
        'facts': {f"{item['kind']}:{prefix}_{n}": item['id']
                  for n, item in enumerate(index.document['facts'])}}
    return {'wireBinding': binding, 'wireSha256': contracts.digest(binding)}


class CompactWire:
    def __init__(self, task):
        self.task = task
        self.binding = task['wireBinding']
        if (self.binding.get('schema') != VERSION or contracts.digest(self.binding) != task['wireSha256']
                or self.binding.get('taskId') != task['id']):
            raise ValueError('Compact transport binding changed')
        for key in ('contextId', 'snapshotId', 'candidate', 'viewSha256'):
            if self.binding.get(key) != task.get(key):
                raise ValueError('Compact transport belongs to another task, snapshot or candidate')
        if self.binding['indexSha256'] != task.get('sourceFactsSha256'):
            raise ValueError('Compact transport index binding changed')
        self.files = self.binding['files']
        self.facts = self.binding['facts']
        self.file_refs = {(value['path'], value['sha256']): key for key, value in self.files.items()}
        self.path_refs = {value['path']: key for key, value in self.files.items()}
        self.fact_refs = {value: key for key, value in self.facts.items()}
        if len(self.file_refs) != len(self.files) or len(self.fact_refs) != len(self.facts):
            raise ValueError('Duplicate compact transport reference')

    def _evidence(self, evidence, encode):
        if encode:
            if set(evidence) != {'path', 'sha256', 'startLine', 'endLine'}:
                raise ValueError('Canonical evidence fields required for encoding')
            alias = self.file_refs.get((evidence['path'], evidence['sha256']))
            if alias is None:
                raise ValueError('Evidence is outside the bound transport files')
            return {'file': alias, 'startLine': evidence['startLine'], 'endLine': evidence['endLine']}
        if set(evidence) != {'file', 'startLine', 'endLine'} or evidence['file'] not in self.files:
            raise ValueError('Unknown compact source reference or evidence fields')
        return {**self.files[evidence['file']], 'startLine': evidence['startLine'], 'endLine': evidence['endLine']}

    def _walk(self, value, encode):
        if isinstance(value, list):
            return [self._walk(item, encode) for item in value]
        if not isinstance(value, dict):
            return deepcopy(value)
        result = {}
        for key, item in value.items():
            if key == 'evidence' and isinstance(item, list):
                result[key] = [self._evidence(ref, encode) for ref in item]
            elif key == 'factIds' and isinstance(item, list):
                lookup = self.fact_refs if encode else self.facts
                try:
                    result[key] = [lookup[ref] for ref in item]
                except (KeyError, TypeError) as exc:
                    raise ValueError('Unknown or stale compact fact reference') from exc
            else:
                result[key] = self._walk(item, encode)
        return result

    def encode_response(self, canonical):
        result = self._walk(canonical, True)
        result['wireSha256'] = self.task['wireSha256']
        return result

    def decode_response(self, raw):
        if not isinstance(raw, dict) or raw.get('wireSha256') != self.task['wireSha256']:
            raise ValueError('Compact response belongs to another transport binding')
        return self._walk({key: value for key, value in raw.items() if key != 'wireSha256'}, False)

    def schema(self, canonical_schema):
        def project(value):
            if isinstance(value, list):
                return [project(item) for item in value]
            if not isinstance(value, dict):
                return value
            if (value.get('type') == 'object' and
                    set(value.get('properties', {})) == {'path', 'sha256', 'startLine', 'endLine'}):
                return contracts.obj({'file': {'type': 'string', 'enum': list(self.files)},
                    'startLine': {'type': 'integer', 'minimum': 1},
                    'endLine': {'type': 'integer', 'minimum': 1}})
            result = {key: project(item) for key, item in value.items()}
            if 'factIds' in result.get('properties', {}):
                result['properties']['factIds']['items'] = {'type': 'string',
                    'pattern': '^(symbol|call|entry|import):' + self.task['id'][:10] + '_[0-9]+$'}
            return result
        result = project(canonical_schema)
        result['properties']['wireSha256'] = {'type': 'string', 'const': self.task['wireSha256']}
        result['required'].append('wireSha256')
        return result

    def context(self, canonical):
        result = self._walk(canonical, True)
        result['task'].pop('wireBinding')
        for item in result['inventory']['files']:
            item['ref'] = self.path_refs[item['path']]
        structure = result['structure']
        for item in structure['files']:
            item['ref'] = self.path_refs[item['path']]
        for name in ('symbols', 'calls', 'entries', 'imports'):
            table = structure[name]
            for row in table['rows']:
                for column in ('id', 'callerId', 'symbolId'):
                    if column in table['columns']:
                        position = table['columns'].index(column)
                        if row[position] is not None:
                            row[position] = self.fact_refs[row[position]]
        result['wireEncoding'] = {'schema': VERSION, 'sha256': self.task['wireSha256'],
            'meaning': 'Task-local references; host expands before canonical validation.'}
        return result
