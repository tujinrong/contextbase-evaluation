"""Task-bound, replayable evidence queries over a sealed source snapshot.

This module reads data on the host. It never executes source or asks the model
to launch a shell. Each returned page is explicit about its remaining coverage.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import PurePosixPath

from . import contracts
from .facts import source_texts
from .sources import source_lines


VERSION = 'contextbase-evidence/1'
MAX_REPLY_CHARS = 32_768
MAX_PAGE_SIZE = 100
_OFFSET = {'type': 'integer', 'minimum': 0}
_LIMIT = {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE}
_NULLABLE_TEXT = {'type': ['string', 'null'], 'minLength': 1}


class EvidenceRequestError(ValueError):
    """A correctable request parameter error, never a source/index integrity failure."""

    def __init__(self, code, message, correction):
        super().__init__(message)
        self.code, self.message, self.correction = code, message, correction


def _operation(name, fields):
    return contracts.obj({'operation': {'type': 'string', 'const': name}, **fields})


# Every property is required for strict provider schemas. A null filter means
# it does not constrain the query; it is not a request to access another root.
REQUEST_SCHEMA = {'anyOf': [
    _operation('inventory', {'offset': _OFFSET, 'limit': _LIMIT}),
    _operation('query', {
        'offset': _OFFSET, 'limit': _LIMIT, 'path': _NULLABLE_TEXT,
        'kind': {'type': ['string', 'null'], 'enum': ['symbol', 'call', 'entry', 'import', None]},
        'text': {**_NULLABLE_TEXT, 'maxLength': 256},
        'caller': _NULLABLE_TEXT, 'callee': _NULLABLE_TEXT, 'route': _NULLABLE_TEXT,
    }),
    _operation('search', {
        'text': {'type': 'string', 'minLength': 1, 'maxLength': 256},
        'path': _NULLABLE_TEXT, 'offset': _OFFSET, 'limit': _LIMIT,
        'caseSensitive': {'type': 'boolean'},
    }),
    _operation('read', {
        'path': contracts.TEXT, 'startLine': {'type': 'integer', 'minimum': 1},
        'endLine': {'type': ['integer', 'null'], 'minimum': 1},
    }),
]}


class EvidenceAccess:
    """A small read/query Interface with task and source identity invariants."""

    def __init__(self, source, index, task):
        if (not isinstance(task, dict) or any(not isinstance(task.get(key), str)
                or not task[key].strip() for key in ('id', 'contextId'))):
            raise ValueError('Evidence access requires a host-owned task and context identity')
        self.source, self.index = source, index
        self.task = deepcopy(task)
        index.validate()
        snapshot = source.snapshot_id
        if index.source.snapshot_id != snapshot or index.document['snapshotId'] != snapshot:
            raise ValueError('Evidence index and source snapshot differ')
        if task.get('snapshotId', snapshot) != snapshot:
            raise ValueError('Evidence task belongs to another source snapshot')
        for field in ('sourceFactsSha256', 'evidenceIndexSha256'):
            if task.get(field, index.sha256) != index.sha256:
                raise ValueError('Evidence task belongs to another source-fact index')
        self.binding = {'taskId': task['id'], 'contextId': task['contextId'],
                        'snapshotId': snapshot, 'indexSha256': index.sha256}
        self._manifest = source.manifest
        self._files = {row['path']: row for row in self._manifest['files']}
        self._index_files = {row['path']: row for row in index.document['files']}
        self._assert_binding()

    def _assert_binding(self):
        self.source.verify()
        if (self.source.snapshot_id != self.binding['snapshotId']
                or self.index.sha256 != self.binding['indexSha256']
                or contracts.digest(self.index.document) != self.binding['indexSha256']
                or self.index.document['snapshotId'] != self.binding['snapshotId']
                or self.index.by_id != {fact['id']: fact for fact in self.index.document['facts']}):
            raise ValueError('Evidence source or fact-index binding changed')

    def _path(self, path):
        if path not in self._files:
            raise EvidenceRequestError('unknown-path', 'Evidence path is outside the sealed source inventory',
                'Use an exact acquired file from inventory. Query/search also accept a canonical '
                'relative directory prefix ending in /; read requires an exact acquired file.')
        return self._files[path]

    def _selector(self, path):
        """Select only sealed manifest entries; never probe a live directory."""
        if path is None:
            return set(self._files), None
        if not path.endswith('/'):
            self._path(path)
            return {path}, None
        stem = path[:-1]
        canonical = PurePosixPath(stem)
        if (not stem or stem in {'.', '..'} or str(canonical) != stem or canonical.is_absolute()
                or '..' in canonical.parts or '\\' in stem or ':' in stem or '\x00' in stem):
            raise EvidenceRequestError('invalid-directory-prefix', 'Directory prefix is not canonical and relative',
                'Use a manifest-relative directory prefix such as deployment/; do not use absolute '
                'paths, dot segments, backslashes or repeated separators. Use path:null for the full inventory.')
        files = {name for name in self._files if name.startswith(path)}
        omitted = [row for row in self._manifest['omitted']
                   if row['path'] == stem or row['path'].startswith(path)
                   or stem.startswith(row['path'] + '/')]
        return files, {'kind': 'directory-prefix', 'path': path,
                       'matchedFileCount': len(files), 'omittedMaterialCount': len(omitted),
                       'observed': bool(files or omitted),
                       'meaning': 'Matches only sealed manifest entries. Zero acquired files do not '
                                  'prove directory existence, absence or complete source coverage. '
                                  'Omitted materials are metadata only. Use paged inventory to enumerate '
                                  'matching acquired paths and omission reasons; no full path list is repeated here.'}

    def _receipt(self, request, result, status='ok'):
        reply = {'schema': VERSION, **self.binding,
                 'requestSha256': contracts.digest(request), 'status': status,
                 'result': result, 'resultSha256': contracts.digest(result)}
        reply['replySha256'] = contracts.digest(reply)
        return reply

    def error_reply(self, request, error):
        """Return a bound diagnostic only for a recognized request error.

        Binding checks deliberately remain outside the recoverable exception
        taxonomy, so malformed requests cannot conceal a damaged snapshot.
        """
        if not isinstance(error, EvidenceRequestError):
            raise TypeError('Only EvidenceRequestError can become an invalid-request receipt')
        self._assert_binding()
        try:
            return self._receipt(request, {'error': {
                'code': error.code, 'message': error.message, 'correction': error.correction}},
                'invalid-request')
        finally:
            self._assert_binding()

    @staticmethod
    def _size(value):
        return len(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False))

    def _page(self, request, rows, field, extra=None):
        offset, limit = request['offset'], request['limit']
        count = len(rows)
        selected = []
        base = {'matchedCount': count, 'returnedCount': 0,
                'truncated': offset < count, 'nextOffset': offset if offset < count else None,
                field: [], **(extra or {})}
        for item in rows[offset:offset + limit]:
            candidate = [*selected, item]
            next_offset = offset + len(candidate)
            result = {**base, field: candidate, 'returnedCount': len(candidate),
                      'truncated': next_offset < count,
                      'nextOffset': next_offset if next_offset < count else None}
            if self._size(self._receipt(request, result)) > MAX_REPLY_CHARS:
                break
            selected = candidate
        end = offset + len(selected)
        result = {**base, field: selected, 'returnedCount': len(selected),
                  'truncated': end < count, 'nextOffset': end if end < count else None}
        if not selected and offset < count:
            result['unavailableReason'] = 'One complete result exceeds the evidence reply capacity'
            return self._receipt(request, result, 'oversized-item')
        return self._receipt(request, result)

    def _coverage(self, path=None):
        if path is not None and path.endswith('/'):
            selected, selector = self._selector(path)
            files = [row for key, row in self._index_files.items() if key in selected]
        else:
            # Keep successful exact-file and null-path receipts unchanged.
            files = list(self._index_files.values()) if path is None else [self._index_files[path]]
            selector = None
        result = {'fileCount': len(files),
                  'parserStatusCounts': dict(Counter(row['status'] for row in files)),
                  'meaning': 'Syntax observations only; unsupported or partial files are not evidence of absence.'}
        if selector is not None:
            result['selector'] = selector
        return result

    def _inventory(self, request):
        rows = []
        for entry in self._manifest['files']:
            parsed = self._index_files[entry['path']]
            rows.append({'materialKind': 'acquired', **deepcopy(entry),
                         'parserStatus': parsed['status'],
                         'language': parsed.get('language'),
                         'diagnosticCount': len(parsed.get('diagnostics', []))})
        rows.extend({'materialKind': 'omitted', **deepcopy(row)}
                    for row in self._manifest['omitted'])
        return self._page(request, rows, 'materials', {
            'acquiredCount': len(self._files), 'omittedCount': len(self._manifest['omitted']),
            'coverage': self._coverage()})

    def _query(self, request):
        path = request['path']
        selected, selector = self._selector(path)
        values = {key: request[key] for key in ('text', 'path', 'kind', 'caller', 'callee', 'route')
                  if request[key] is not None}
        if selector is not None:
            # Query filtering is not an extractor change. Existing FactIndex
            # IDs and hashes remain valid for exact and prefix selectors.
            values.pop('path', None)
        found = self.index.query(**values)
        facts = [row for row in found['facts'] if row['path'] in selected] if selector is not None else found['facts']
        return self._page(request, facts, 'facts', {
            'matchBasis': found['matchBasis'], 'coverage': self._coverage(path)})

    def _search(self, request, texts=None):
        path, needle = request['path'], request['text']
        selected, _ = self._selector(path)
        texts = (source_texts(self.source) if texts is None else texts) if selected else {}
        if not request['caseSensitive']:
            needle = needle.casefold()
        rows = []
        for current in sorted(texts):
            if current not in selected:
                continue
            entry = self._files[current]
            for number, line in enumerate(source_lines(texts[current]), 1):
                if needle not in (line if request['caseSensitive'] else line.casefold()):
                    continue
                rows.append({'evidence': {'path': current, 'startLine': number, 'endLine': number,
                                         'sha256': entry['sha256']}, 'sourceText': line})
        return self._page(request, rows, 'matches', {
            'matchBasis': 'Literal source-text search; a matching name does not resolve a semantic relation.',
            'coverage': self._coverage(path)})

    def _read(self, request, texts=None):
        path, start = request['path'], request['startLine']
        entry = self._path(path)
        end = entry['lines'] if request['endLine'] is None else request['endLine']
        if entry['lines'] == 0 and start == 1 and request['endLine'] is None:
            text = self.source.read(path) if texts is None else texts[path]
            return self._receipt(request, {'path': path, 'requestedStartLine': start,
                'requestedEndLine': end, 'matchedCount': 0, 'returnedCount': 0,
                'truncated': False, 'nextLine': None, 'evidence': None, 'sourceText': text})
        if not 1 <= start <= end <= entry['lines']:
            raise EvidenceRequestError('invalid-line-range', 'Evidence requires a nonempty exact source line range',
                'Use 1-based LF line numbers within this acquired file; endLine:null reads through its final line.')
        text = (self.source.read(path, start, end) if texts is None else
                ''.join(source_lines(texts[path])[start - 1:end]))
        lines = source_lines(text)
        count = end - start + 1
        base = {'path': path, 'requestedStartLine': start, 'requestedEndLine': end,
                'matchedCount': count, 'returnedCount': 0, 'truncated': True,
                'nextLine': start, 'evidence': None, 'sourceText': ''}
        selected, encoded_chars = [], 0
        for line in lines:
            count_selected = len(selected) + 1
            last = start + count_selected - 1
            result = {**base, 'returnedCount': count_selected, 'truncated': last < end,
                      'nextLine': last + 1 if last < end else None,
                      'evidence': {'path': path, 'startLine': start, 'endLine': last,
                                   'sha256': entry['sha256']}}
            line_chars = self._size(line) - 2
            # Hash fields have fixed width. Measure the small empty-text receipt
            # plus encoded rows, avoiding quadratic joins of long source pages.
            if self._size(self._receipt(request, result)) + encoded_chars + line_chars > MAX_REPLY_CHARS:
                break
            selected.append(line)
            encoded_chars += line_chars
        if not selected:
            return self._receipt(request, {**base,
                'unavailableReason': 'One complete source line exceeds the evidence reply capacity'}, 'oversized-item')
        last = start + len(selected) - 1
        return self._receipt(request, {**base, 'returnedCount': len(selected),
            'truncated': last < end, 'nextLine': last + 1 if last < end else None,
            'evidence': {'path': path, 'startLine': start, 'endLine': last, 'sha256': entry['sha256']},
            'sourceText': ''.join(selected)})

    @staticmethod
    def _validate_request(request):
        try:
            contracts.validate(request, REQUEST_SCHEMA)
        except ValueError as exc:
            raise EvidenceRequestError('invalid-request-schema', 'Evidence request parameters do not match the operation schema',
                'Use the provided operation schema with all required fields, supported filters, '
                'positive page limits and exact integer positions.') from exc
        # JSON Schema's integer definition admits 1.0, but source positions and
        # pagination deliberately use exact integer values, never booleans.
        for key in ('offset', 'limit', 'startLine', 'endLine'):
            if key in request and request[key] is not None and type(request[key]) is not int:
                raise EvidenceRequestError('invalid-integer-position',
                    'Evidence range and pagination values must be exact integers',
                    'Use JSON integer positions and page sizes, not floating-point values or booleans.')

    def _response(self, request, texts=None):
        self._validate_request(request)
        operation = request['operation']
        reply = (getattr(self, '_' + operation)(request, texts=texts) if operation in {'read', 'search'}
                 else getattr(self, '_' + operation)(request))
        if self._size(reply) > MAX_REPLY_CHARS:
            raise ValueError('Evidence reply metadata exceeds its capacity')
        return reply

    def handle(self, request):
        """Validate and return one complete host-bound page, never silent truncation."""
        self._assert_binding()
        try:
            return self._response(request)
        finally:
            # Changes in unreferenced source also invalidate this operation.
            self._assert_binding()

    def verify_reply(self, request, reply):
        """Replay against the bound task and current sealed bytes before acceptance."""
        try:
            expected = self.handle(request)
        except EvidenceRequestError as exc:
            expected = self.error_reply(request, exc)
        if reply != expected:
            raise ValueError('Evidence reply differs from its task-bound source replay')

    def verify_replies(self, pairs):
        """Replay a transcript with operation-local source reads and integrity fences.

        ``pairs`` yields (request, reply). Pinned texts do not survive this call;
        the complete snapshot and index are checked before and after the batch.
        """
        self._assert_binding()
        try:
            texts = source_texts(self.source)
            for request, reply in pairs:
                try:
                    expected = self._response(request, texts=texts)
                except EvidenceRequestError as exc:
                    expected = self.error_reply(request, exc)
                if reply != expected:
                    raise ValueError('Evidence reply differs from its task-bound source replay')
        finally:
            self._assert_binding()
