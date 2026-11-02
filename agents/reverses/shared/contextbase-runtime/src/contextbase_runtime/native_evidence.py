"""Bounded canonical evidence batches; no projection or semantic transformation."""
from copy import deepcopy
from contextlib import contextmanager
from . import contracts as c
from .evidence import EvidenceAccess, EvidenceRequestError
from .facts import source_texts
from .native_mcp import tool_result, encode_message

BATCH_VERSION = 'contextbase-native-evidence-batch/3'
REPLY_POLICY = 'contextbase-native-evidence-budget/1'
MAX_REPLY_BYTES = 28672
MAX_BATCH_REQUESTS = 8
MAX_BATCH_BYTES = 32768


def reply_size(value):
    """UTF-8 bytes of the exact MCP tools/call result, including escaped content.

    The outer JSON-RPC request id and HTTP framing are not tool-result content.
    """
    return len(encode_message(tool_result(value)))


def native_access(source, index, task):
    """Use the legacy paginator with a version-bound native MCP byte policy."""
    policy = {'schema': REPLY_POLICY, 'maxReplyBytes': MAX_REPLY_BYTES,
              'encoding': 'compact MCP tools/call result UTF-8 including escaped JSON content'}
    return EvidenceAccess(source, index, task, reply_size=reply_size,
                          max_reply_size=MAX_REPLY_BYTES, reply_policy=policy)


def _check(check_current):
    if check_current is not None and check_current() is False:
        raise RuntimeError('Native evidence batch cancelled')


def _response(access, request, texts):
    try:
        return access._response(request, texts=texts)
    except EvidenceRequestError as error:
        return access._receipt(request, {'error': {'code':error.code,'message':error.message,
                                                 'correction':error.correction}},'invalid-request')


def _validate_batch(requests, max_bytes):
    if (not isinstance(requests,list) or not 1 <= len(requests) <= MAX_BATCH_REQUESTS
            or any(not isinstance(r,dict) or r.get('operation') not in {'read','query','search'} for r in requests)):
        raise ValueError('Evidence batch requires 1..8 independent read/query/search requests')
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BATCH_BYTES:
        raise ValueError('Evidence batch reply budget is invalid')


def _batch(access, requests, texts, check_current, max_bytes):
    """Canonical batch core; caller owns the complete integrity fence."""
    _validate_batch(requests,max_bytes)
    requests = deepcopy(requests)
    def envelope(replies, next_index, unavailable=False):
        result = {'schema': BATCH_VERSION, **deepcopy(access.binding), 'requestSha256': c.digest(requests),
                  'requestCount':len(requests),'returnedCount':len(replies),'replies':replies,
                  'next_request_index':next_index,'maxBytes':max_bytes}
        if unavailable:
            result['unavailableReason'] = 'One complete subreply exceeds the batch capacity; no request advanced'
        result['batchSha256'] = c.digest(result)
        return result
    if reply_size(envelope([],0,True)) > max_bytes:
        raise ValueError('Evidence batch budget cannot contain its metadata')
    replies, pairs = [], []
    for position, request in enumerate(requests):
        _check(check_current)
        canonical = _response(access, request, texts)
        candidate = [*replies, {'request':request, 'reply':canonical}]
        next_index = position + 1 if position + 1 < len(requests) else None
        if reply_size(envelope(candidate,next_index)) > max_bytes:
            return envelope(replies,position,not replies), pairs
        replies = candidate
        pairs.append({'request':request,'reply':canonical})
    return envelope(replies,None), pairs


def run_batch(access, requests, check_current=None, *, max_bytes=MAX_BATCH_BYTES):
    """Return complete subreplies only. Unreturned work grants no evidence rights."""
    _validate_batch(requests,max_bytes)
    _check(check_current)
    access._assert_binding()
    try:
        texts = source_texts(access.source) if any(r['operation'] in {'read','search'} for r in requests) else None
        return _batch(access, requests, texts, check_current, max_bytes)
    finally:
        access._assert_binding()
        _check(check_current)


@contextmanager
def replay_evidence(access, check_current=None):
    """Host-only operation-local acquisition; never persists texts or delivery rights.

    The caller must compare each returned receipt before committing its pairs at
    that original transcript ordinal. All mutations remain inside the exit fence.
    """
    _check(check_current)
    access._assert_binding()
    active = True
    texts = None
    try:
        texts = source_texts(access.source)
        def acquire(name, args):
            if not active:
                raise RuntimeError('Evidence replay context is closed')
            _check(check_current)
            if not isinstance(args,dict) or 'operation' in args:
                raise ValueError('Evidence replay arguments cannot override the operation')
            if name == 'evidence_batch':
                if set(args) != {'requests'}:
                    raise ValueError('Evidence replay batch requires only requests')
                return _batch(access,args['requests'],texts,check_current,MAX_BATCH_BYTES)
            if name not in {'inventory','read','query','search'}:
                raise ValueError('Unsupported evidence replay operation')
            request = {**deepcopy(args),'operation':name}
            reply = _response(access,request,texts)
            return reply,[{'request':request,'reply':reply}]
        yield acquire
    finally:
        active = False
        texts = None
        access._assert_binding()
        _check(check_current)
