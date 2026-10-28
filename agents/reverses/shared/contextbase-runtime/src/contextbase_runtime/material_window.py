"""Retain origin-labelled candidate pages without promoting claims to evidence.

This is a pure selection/deduplication helper. The caller owns the shared
source/candidate memory budget, execution binding, progress and acceptance.
Offsets are Python Unicode character offsets into the host's canonical JSON;
retained bodyText is sliced only from an actually delivered response page.
"""
from __future__ import annotations

from copy import deepcopy
import json

from . import contracts as c


_OFFSET = {'type': 'integer', 'minimum': 0}
_REQUESTS = {
    'listing': c.obj({'operation': {'type': 'string', 'const': 'listing'},
                      'collection': c.TEXT, 'offset': _OFFSET,
                      'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100}}),
    'material': c.obj({'operation': {'type': 'string', 'const': 'material'},
                       'collection': c.TEXT, 'key': c.TEXT, 'offset': _OFFSET,
                       'limit': {'type': 'integer', 'minimum': 1, 'maximum': 12000}}),
}
_REPLY = c.obj({'schema': {'type': 'string', 'const': 'contextbase-incremental/1'},
                'taskId': c.TEXT, 'contextId': c.TEXT, 'snapshotId': c.SHA256,
                'collection': c.TEXT, 'requestSha256': c.SHA256, 'status': c.TEXT,
                'result': {'type': 'object'}, 'resultSha256': c.SHA256,
                'replySha256': c.SHA256})
_NEXT = {'type': ['integer', 'null'], 'minimum': 0}
_SUMMARY = c.obj({'key': c.TEXT, 'sha256': c.SHA256, 'name': c.TEXT,
                  'kind': c.TEXT, 'ownerRequirement': c.TEXT}, required=['key', 'sha256'])
_RESULTS = {
    'listing': c.obj({'items': c.arr(_SUMMARY), 'matchedCount': _OFFSET,
                      'returnedCount': _OFFSET, 'truncated': {'type': 'boolean'}, 'nextOffset': _NEXT}),
    'material': c.obj({'key': c.TEXT, 'sha256': c.SHA256, 'offset': _OFFSET,
                       'totalChars': _OFFSET, 'bodyText': {'type': 'string'},
                       'truncated': {'type': 'boolean'}, 'nextOffset': _NEXT}),
}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _integer_fields(value, fields):
    if any(value[field] is not None and type(value[field]) is not int for field in fields):
        raise ValueError('Candidate material positions require exact integer values')


def _origin(request, reply):
    return {'replySha256': reply['replySha256'], 'requestSha256': reply['requestSha256'],
            'taskId': reply['taskId'], 'contextId': reply['contextId'],
            'snapshotId': reply['snapshotId'], 'operation': request['operation'],
            'requestOffset': request['offset'], 'requestLimit': request['limit']}


def _items(pair, current_materials, objects):
    if not isinstance(pair, dict) or not isinstance(pair.get('request'), dict):
        raise ValueError('Candidate cache requires request/reply delivery pairs')
    request = pair['request']
    operation = request.get('operation')
    if operation not in _REQUESTS:
        # Source text, fact IDs and inventory have their own evidence window.
        return []
    c.validate(request, _REQUESTS[operation])
    _integer_fields(request, ('offset', 'limit'))
    reply = pair.get('reply')
    c.validate(reply, _REPLY)
    if (reply['collection'] != request['collection']
            or reply['requestSha256'] != c.digest(request)
            or reply['resultSha256'] != c.digest(reply['result'])
            or reply['replySha256'] != c.digest({key: value for key, value in reply.items()
                                                if key != 'replySha256'})):
        raise ValueError('Candidate material delivery hashes or collection changed')
    if reply['status'] != 'ok':
        return []
    result = reply['result']
    c.validate(result, _RESULTS[operation])
    collection = request['collection']
    origin = _origin(request, reply)

    def current(key, version):
        identity = (collection, key)
        if identity not in objects:
            value = current_materials.get(collection, {}).get(key)
            objects[identity] = None if value is None else (value, c.digest(value), _json(value))
        item = objects[identity]
        return item if item is not None and item[1] == version else None

    if operation == 'material':
        _integer_fields(result, ('offset', 'totalChars', 'nextOffset'))
        if result['key'] != request['key'] or result['offset'] != request['offset']:
            raise ValueError('Candidate body identity or delivered offset changed')
        item = current(result['key'], result['sha256'])
        if item is None:
            return []
        encoded = item[2]
        offset = request['offset']
        end = min(len(encoded), offset + request['limit'])
        truncated = end < len(encoded)
        if (result['totalChars'] != len(encoded) or result['bodyText'] != encoded[offset:end]
                or result['truncated'] != truncated
                or result['nextOffset'] != (end if truncated else None)):
            raise ValueError('Candidate body does not match the current exact delivered JSON page')
        if not result['bodyText']:
            return []
        return [{'kind': 'candidate-material', 'collection': collection, 'key': result['key'],
                 'sha256': result['sha256'], 'bodyText': result['bodyText'], 'offset': offset,
                 'totalChars': result['totalChars'],
                 'origin': {**origin, 'deliveredOffset': offset,
                            'deliveredEndOffset': offset + len(result['bodyText'])}}]

    _integer_fields(result, ('matchedCount', 'returnedCount', 'nextOffset'))
    end = request['offset'] + len(result['items'])
    truncated = end < result['matchedCount']
    if (result['returnedCount'] != len(result['items']) or len(result['items']) > request['limit']
            or result['truncated'] != truncated
            or result['nextOffset'] != (end if truncated else None)
            or (result['items'] and end > result['matchedCount'])):
        raise ValueError('Candidate listing does not match its delivered page bounds')
    keys = [row['key'] for row in result['items']]
    if len(keys) != len(set(keys)):
        raise ValueError('A candidate listing page contains duplicate object identities')
    items = []
    for ordinal, row in enumerate(result['items']):
        item = current(row['key'], row['sha256'])
        if item is None:
            continue
        if any(field not in item[0] or item[0][field] != value
               for field, value in row.items() if field not in {'key', 'sha256'}):
            raise ValueError('Candidate summary metadata differs from its current object')
        text = _json(row)
        items.append({'kind': 'candidate-summary', 'collection': collection, 'key': row['key'],
                      'sha256': row['sha256'], 'bodyText': text, 'offset': 0, 'totalChars': len(text),
                      'origin': {**origin, 'listingIndex': request['offset'] + ordinal}})
    return items


def _subtract(start, end, covered):
    remaining = [(start, end)]
    for left, right in covered:
        following = []
        for first, last in remaining:
            if right <= first or left >= last:
                following.append((first, last))
            else:
                if first < left:
                    following.append((first, left))
                if right < last:
                    following.append((right, last))
        remaining = following
    return remaining


def collect_materials(latest_pairs, prior_pairs, current_materials):
    """Return ``(latest_visible, newest_prior)`` with precise origin and no budget.

    Body ranges use half-open character intervals and are deduplicated by
    collection, key and object SHA. Summary identities are separate from body
    delivery. Removed/revised objects are omitted even when old receipts remain.
    No returned item is a source evidence reference, fact ID or semantic pass.
    """
    if (not isinstance(current_materials, dict)
            or any(not isinstance(value, dict) for value in current_materials.values())):
        raise ValueError('Current candidate materials must map collections to object dictionaries')
    objects, intervals, summaries = {}, {}, set()

    def select(pairs):
        selected = []
        for pair in reversed(list(pairs)):
            for item in _items(pair, current_materials, objects):
                identity = (item['collection'], item['key'], item['sha256'])
                if item['kind'] == 'candidate-summary':
                    if identity not in summaries:
                        selected.append(item)
                        summaries.add(identity)
                    continue
                covered = intervals.setdefault(identity, [])
                offset = item['offset']
                for start, end in _subtract(offset, offset + len(item['bodyText']), covered):
                    selected.append({**item, 'offset': start,
                                     'bodyText': item['bodyText'][start - offset:end - offset],
                                     'origin': deepcopy(item['origin'])})
                    covered.append((start, end))
        return selected

    visible = select(latest_pairs)
    prior = select(prior_pairs)
    return visible, prior
