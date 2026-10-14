"""Relocate only raw UTF-8 a[href] path values into final HTML locations.

Derived HTML only. Original Markdown/HTML remain authoritative converter inputs.
No DOM serialization, source execution, provider, renderer, or native claims.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata
from urllib.parse import quote, unquote

REPO = Path(r'D:/開発/contextbase-evaluation')
WORK = REPO / 'agents/spec-agent/.tmp/20261014-nenkin-high-01'
REPORT = REPO / 'agents/spec-agent/report/20261014-nenkin-high-01'
OUTPUT_BASE = WORK / 'delivery/html-routing-results'
RUN_ID = '20261014-nenkin-high-01'
PROJECT_ID = 'nenkin'
CAPSULE_SHA = 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445'
CONTEXT_SHA = '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605'
WS = ' \t\r\n\f'
RESERVED = {'CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$',
            *('COM' + n for n in '123456789¹²³'), *('LPT' + n for n in '123456789¹²³')}
ENTITY = re.compile(r'&(?:#[xX][0-9A-Fa-f]+;?|#[0-9]+;?|[A-Za-z][A-Za-z0-9]*;?)')

class RoutingHold(ValueError):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}

def require(condition, message, details=None):
    if not condition:
        raise RoutingHold(message, details)

def digest(value):
    return hashlib.sha256(value).hexdigest()

def exact_keys(value, keys, name):
    require(isinstance(value, dict) and set(value) == set(keys), name + ' fields differ')

def sha_arg(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'Exact lowercase SHA256 required')
    return value

def json_pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON member')
        result[key] = value
    return result

def parse_json(data):
    return json.loads(data.decode('utf-8-sig'), object_pairs_hook=json_pairs,
                      parse_constant=lambda value: require(False, 'Nonfinite JSON constant'))

def windows_component(value):
    require(isinstance(value, str) and value and value not in {'.', '..'} and
            value == unicodedata.normalize('NFC', value) and not value.endswith((' ', '.')) and
            not any(ord(c) < 32 or ord(c) == 127 or c in '<>:"/\\|?*' for c in value) and
            value.split('.', 1)[0].upper() not in RESERVED,
            'Windows-unsafe or noncanonical path component')
    return value

def relative_path(value):
    require(isinstance(value, str) and value and not value.startswith('/') and '\\' not in value,
            'Normalized relative path required')
    parts = value.split('/')
    for part in parts:
        windows_component(part)
    path = PurePosixPath(value)
    require(path.as_posix() == value, 'Path is not normalized')
    return path

def validate_allowlist(value):
    exact_keys(value, {'schema', 'runId', 'projectId', 'capsuleManifestSha256', 'executionContextSha256',
                      'planSha256', 'sourceOnly', 'originalApplicationExecuted', 'formalPercentage',
                      'published', 'documents'}, 'Allowlist')
    require(value['schema'] == 'spec-agent-html-publication-routing/1' and
            value['runId'] == RUN_ID and value['projectId'] == PROJECT_ID and
            value['capsuleManifestSha256'] == CAPSULE_SHA and value['executionContextSha256'] == CONTEXT_SHA and
            value['sourceOnly'] is True and value['originalApplicationExecuted'] is False and
            value['formalPercentage'] is None and value['published'] is False,
            'Allowlist identity, authority, or execution boundary differs')
    sha_arg(value['planSha256'])
    require(isinstance(value['documents'], list) and value['documents'], 'Complete publication document allowlist required')
    ids, paths, documents = set(), set(), {}
    for item in value['documents']:
        exact_keys(item, {'documentId', 'kind', 'canonicalMarkdownPath', 'locations'}, 'Document allowlist')
        require(isinstance(item['documentId'], str) and item['documentId'].strip() == item['documentId'] and
                item['documentId'] and item['documentId'] not in ids, 'Duplicate or invalid document ID')
        ids.add(item['documentId'])
        require(isinstance(item['kind'], str) and item['kind'] and item['kind'].strip() == item['kind'] and
                item['kind'] != 'analysis-report', 'Only final specification documents may enter publication allowlist')
        canonical = relative_path(item['canonicalMarkdownPath'])
        require(canonical.suffix == '.md', 'Canonical Markdown extension must be .md')
        exact_keys(item['locations'], {'md', 'html', 'pdf', 'xlsx'}, 'Four-format locations')
        stem = canonical.with_suffix('')
        expected = {'md': 'md/' + canonical.as_posix(),
                    'html': 'html/' + stem.as_posix() + '/' + stem.name + '.html',
                    'pdf': 'PDF/' + stem.as_posix() + '.pdf',
                    'xlsx': 'Excel/' + stem.as_posix() + '.xlsx'}
        require(item['locations'] == expected, 'Final four-folder canonical document mapping differs')
        for format_name, location in item['locations'].items():
            relative_path(location)
            require(location.casefold() not in paths, 'Duplicate or case-colliding publication path')
            paths.add(location.casefold())
        documents[item['documentId']] = item
    return documents

def decoded_attribute(raw_value):
    """Decode HTML entities while mapping decoded characters to raw char spans."""
    decoded, spans, cursor = [], [], 0
    for match in ENTITY.finditer(raw_value):
        for index in range(cursor, match.start()):
            decoded.append(raw_value[index]); spans.append((index, index + 1))
        entity = html.unescape(match.group())
        for character in entity:
            decoded.append(character); spans.append((match.start(), match.end()))
        cursor = match.end()
    for index in range(cursor, len(raw_value)):
        decoded.append(raw_value[index]); spans.append((index, index + 1))
    result = ''.join(decoded)
    require(result == html.unescape(raw_value), 'Unsupported ambiguous HTML attribute entity decoding')
    return result, spans

def raw_span(decoded, spans, start, end, raw_value):
    if start == end:
        point = spans[start][0] if start < len(spans) else len(raw_value)
        return point, point
    left, right = spans[start][0], spans[end - 1][1]
    require((start == 0 or spans[start - 1][1] <= left) and
            (end == len(spans) or spans[end][0] >= right), 'Entity crosses a structural URL boundary')
    return left, right

def split_url_raw(raw_value):
    decoded, spans = decoded_attribute(raw_value)
    question, fragment = decoded.find('?'), decoded.find('#')
    path_end = min([point for point in (question, fragment) if point >= 0] or [len(decoded)])
    left, right = raw_span(decoded, spans, 0, path_end, raw_value)
    suffix_start = right
    query_raw, fragment_raw = '', ''
    if question >= 0 and (fragment < 0 or question < fragment):
        q_left, q_right = raw_span(decoded, spans, question, fragment if fragment >= 0 else len(decoded), raw_value)
        query_raw = raw_value[q_left:q_right]
    if fragment >= 0:
        f_left, f_right = raw_span(decoded, spans, fragment, len(decoded), raw_value)
        fragment_raw = raw_value[f_left:f_right]
    return {'decoded': decoded, 'spans': spans, 'path': decoded[:path_end], 'pathRaw': raw_value[left:right],
            'suffixRaw': raw_value[suffix_start:], 'queryRaw': query_raw, 'fragmentRaw': fragment_raw,
            'hasFragment': fragment >= 0, 'pathEnd': path_end}

def decoded_segment(value):
    require(not re.search(r'%(?![0-9a-fA-F]{2})', value), 'Invalid percent escape in local URL')
    try:
        decoded = unquote(value, encoding='utf-8', errors='strict')
    except UnicodeError as exc:
        raise RoutingHold('Local URL percent escapes are not UTF-8') from exc
    require('/' not in decoded and '\\' not in decoded, 'Encoded path separator refused')
    if decoded in {'.', '..'}:
        require(decoded == value, 'Encoded navigation component refused')
    else:
        windows_component(decoded)
    return decoded

def route_href(raw_value, origin, targets):
    parts = split_url_raw(raw_value)
    decoded = parts['decoded']
    scheme = re.match(r'^([A-Za-z][A-Za-z0-9+.-]*):', decoded)
    if scheme:
        require(scheme.group(1).lower() in {'http', 'https', 'data'}, 'Unsupported URL scheme', {'hrefRaw': raw_value})
        return raw_value, {'classification': 'external-unchanged', 'hrefRaw': raw_value}
    require(not decoded.startswith('//') and not parts['path'].startswith('/') and
            not any(ord(c) < 32 or ord(c) == 127 for c in decoded), 'Absolute, authority, or control-bearing local URL refused')
    require(not parts['hasFragment'], 'Local fragments HOLD pending actual anchor proof',
            {'hrefRaw': raw_value, 'queryRaw': parts['queryRaw'], 'fragmentRaw': parts['fragmentRaw']})
    html_origin = origin['locations']['html']
    if not parts['path']:
        # A query-only/empty link retains the same rendered document identity.
        target = html_origin
        new_path = ''
    else:
        stack = [(segment, None) for segment in PurePosixPath(origin['locations']['md']).parent.parts]
        cursor = 0
        for raw_component in parts['path'].split('/'):
            require(raw_component, 'Empty local URL path component')
            component = decoded_segment(raw_component)
            start, end = raw_span(decoded, parts['spans'], cursor, cursor + len(raw_component), raw_value)
            lexical = raw_value[start:end]
            cursor += len(raw_component) + 1
            if component == '..':
                require(stack, 'Local link escapes publication root')
                stack.pop()
            elif component != '.':
                stack.append((component, lexical))
        target = '/'.join(component for component, lexical in stack)
        require(target in targets, 'Local link target is outside exact publication allowlist',
                {'hrefRaw': raw_value, 'resolvedTarget': target, 'queryRaw': parts['queryRaw'], 'fragmentRaw': parts['fragmentRaw']})
        target_parts = [component for component, lexical in stack]
        current = list(PurePosixPath(html_origin).parent.parts)
        common = 0
        while common < min(len(current), len(target_parts)) and current[common] == target_parts[common]:
            common += 1
        path_parts = ['..'] * (len(current) - common)
        path_parts.extend(lexical if lexical is not None else quote(component, safe='-._~')
                          for component, lexical in stack[common:])
        new_path = '/'.join(path_parts)
    require(target in targets, 'Self link is not in publication allowlist')
    destination = targets[target]
    rewritten = new_path + parts['suffixRaw']
    return rewritten, {'classification': 'allowlisted-local', 'hrefRaw': raw_value,
            'targetDocumentId': destination['documentId'], 'targetFormat': destination['format'],
            'targetLocation': target, 'targetExtension': PurePosixPath(target).suffix,
            'pathRawBefore': parts['pathRaw'], 'pathRawAfter': new_path,
            'queryRaw': parts['queryRaw'], 'fragmentRaw': parts['fragmentRaw'], 'fragmentProof': 'not-applicable'}

def href_value_span(raw_tag):
    """Lex one observed a tag. Return only href value indices; other bytes untouched."""
    match = re.match(r'<\s*[A-Za-z][^\s/>]*', raw_tag)
    require(match is not None, 'Malformed observed anchor start tag')
    cursor, found = match.end(), None
    while cursor < len(raw_tag):
        while cursor < len(raw_tag) and raw_tag[cursor] in WS:
            cursor += 1
        if raw_tag[cursor:] in {'>', '/>'}:
            break
        start = cursor
        while cursor < len(raw_tag) and raw_tag[cursor] not in WS + '=/>':
            cursor += 1
        require(cursor > start, 'Malformed anchor attribute name')
        name = raw_tag[start:cursor].lower()
        while cursor < len(raw_tag) and raw_tag[cursor] in WS:
            cursor += 1
        if cursor >= len(raw_tag) or raw_tag[cursor] != '=':
            require(name != 'href', 'Value-less href refused')
            continue
        cursor += 1
        while cursor < len(raw_tag) and raw_tag[cursor] in WS:
            cursor += 1
        require(cursor < len(raw_tag), 'Missing anchor attribute value')
        if raw_tag[cursor] in {'"', "'"}:
            delimiter = raw_tag[cursor]; left = cursor + 1
            right = raw_tag.find(delimiter, left)
            require(right >= 0, 'Unterminated quoted anchor attribute')
            cursor = right + 1
        else:
            left = cursor
            while cursor < len(raw_tag) and raw_tag[cursor] not in WS + '>':
                require(raw_tag[cursor] not in '"\'<=`', 'Ambiguous unquoted anchor attribute')
                cursor += 1
            right = cursor
        if name == 'href':
            require(found is None, 'Duplicate href attribute refused')
            found = (left, right)
    return found

class AnchorSpans(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.line_starts = [0] + [match.end() for match in re.finditer('\n', text)]
        self.spans = []
        self.inert_tag = None
    def capture(self, tag):
        if tag.lower() != 'a':
            return
        raw_tag = self.get_starttag_text()
        value = href_value_span(raw_tag)
        if value is not None:
            line, column = self.getpos()
            offset = self.line_starts[line - 1] + column
            self.spans.append((offset + value[0], offset + value[1]))
    def handle_starttag(self, tag, attrs):
        if self.inert_tag is not None:
            return
        if tag.lower() in {'script', 'style', 'textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes', 'plaintext'}:
            self.inert_tag = tag.lower()
            return
        self.capture(tag)
    def handle_startendtag(self, tag, attrs):
        if self.inert_tag is not None:
            return
        require(tag.lower() not in {'script', 'style', 'textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes', 'plaintext'},
                'Ambiguous self-closing raw-text container refused')
        self.capture(tag)
    def handle_endtag(self, tag):
        if self.inert_tag != 'plaintext' and tag.lower() == self.inert_tag:
            self.inert_tag = None

def inverse_bytes(final_bytes, replacements):
    restored = final_bytes
    for item in reversed(replacements):
        start, end = item['finalByteStart'], item['finalByteEnd']
        require(restored[start:end] == item['after'].encode('utf-8'), 'Inverse proof replacement bytes differ')
        restored = restored[:start] + item['before'].encode('utf-8') + restored[end:]
    return restored

def project_html(original_bytes, allowlist, document_id):
    require(isinstance(original_bytes, bytes), 'Original HTML must be raw bytes')
    documents = validate_allowlist(allowlist)
    require(document_id in documents, 'Origin document missing from exact allowlist')
    bom = b'\xef\xbb\xbf' if original_bytes.startswith(b'\xef\xbb\xbf') else b''
    try:
        text = original_bytes[len(bom):].decode('utf-8')
    except UnicodeError as exc:
        raise RoutingHold('Original HTML is not UTF-8') from exc
    parser = AnchorSpans(text)
    parser.feed(text); parser.close()
    targets = {location: {'documentId': item['documentId'], 'format': format_name}
               for item in documents.values() for format_name, location in item['locations'].items()}
    routes, replacements, chunks, cursor, shift = [], [], [], 0, 0
    for left, right in parser.spans:
        start = len(bom) + len(text[:left].encode('utf-8'))
        end = len(bom) + len(text[:right].encode('utf-8'))
        require(start >= cursor and end >= start, 'Overlapping or unordered raw href spans')
        before = text[left:right]
        after, route = route_href(before, documents[document_id], targets)
        route.update({'originalByteStart': start, 'originalByteEnd': end, 'hrefRawAfter': after})
        routes.append(route)
        chunks.extend([original_bytes[cursor:start], after.encode('utf-8')])
        if before != after:
            replacements.append({'originalByteStart': start, 'originalByteEnd': end,
                                 'finalByteStart': start + shift, 'finalByteEnd': start + shift + len(after.encode('utf-8')),
                                 'before': before, 'after': after, 'route': route})
        shift += len(after.encode('utf-8')) - (end - start)
        cursor = end
    chunks.append(original_bytes[cursor:])
    final = b''.join(chunks)
    restored = inverse_bytes(final, replacements)
    require(restored == original_bytes, 'Inverse byte proof failed')
    return final, {'schema': 'spec-agent-html-routing-projection/1', 'documentId': document_id,
            'originMarkdownLocation': documents[document_id]['locations']['md'],
            'finalHtmlLocation': documents[document_id]['locations']['html'],
            'originalSha256': digest(original_bytes), 'finalSha256': digest(final),
            'originalBytes': len(original_bytes), 'finalBytes': len(final),
            'anchorHrefCount': len(routes), 'replacementCount': len(replacements),
            'routes': routes, 'replacements': replacements, 'inverseByteProofPassed': True,
            'nonHrefBytesChanged': False, 'markdownChanged': False, 'sourceHtmlChanged': False,
            'proseLabelsImagesCssOrOtherAttributesChanged': False, 'domSerialized': False,
            'localFragmentPolicy': 'HOLD_UNTIL_ACTUAL_ANCHOR_PROOF',
            'originalHtmlRemainsExcelAndPdfConverterSource': True,
            'visualFidelityVerified': False, 'published': False}

def safe(path):
    original = Path(path).absolute()
    for node in (original, *original.parents):
        require(not node.is_symlink() and not (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0) & 0x400),
                'Linked or reparse path refused before IO')
    return original.resolve()

def owned_input(path, suffix):
    path = safe(path)
    require(path.suffix == suffix and path.is_file() and any(path != safe(root) and path.is_relative_to(safe(root))
            for root in (WORK, REPORT)), 'Input leaves the owned current run or has unexpected extension')
    for root in (WORK, REPORT):
        if path.is_relative_to(safe(root)):
            require(not any(part.startswith('snapshot') or part == 'jobs' for part in path.relative_to(safe(root)).parts),
                    'Source capsules and author job records are outside projection IO')
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allowlist', required=True)
    parser.add_argument('--allowlist-sha256', required=True)
    parser.add_argument('--html', required=True)
    parser.add_argument('--html-sha256', required=True)
    parser.add_argument('--document-id', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--helper-sha256', required=True)
    args = parser.parse_args()
    helper = safe(__file__)
    helper_sha = sha_arg(args.helper_sha256)
    require(digest(helper.read_bytes()) == helper_sha, 'Projection helper changed')
    allowlist_path, html_path = owned_input(args.allowlist, '.json'), owned_input(args.html, '.html')
    output = safe(args.output)
    require(output != safe(OUTPUT_BASE) and output.is_relative_to(safe(OUTPUT_BASE)) and not output.exists(),
            'Fresh owned HTML routing result directory required')
    for part in output.relative_to(safe(OUTPUT_BASE)).parts:
        windows_component(part)
    allowlist_sha, html_sha = sha_arg(args.allowlist_sha256), sha_arg(args.html_sha256)
    allowlist_bytes, original = allowlist_path.read_bytes(), html_path.read_bytes()
    require(digest(allowlist_bytes) == allowlist_sha and digest(original) == html_sha, 'Pinned projection input changed')
    final, proof = project_html(original, parse_json(allowlist_bytes), args.document_id)
    inputs = {str(allowlist_path): allowlist_sha, str(html_path): html_sha, str(helper): helper_sha}
    def recheck():
        for path, expected in inputs.items():
            require(digest(safe(path).read_bytes()) == expected, 'Projection input drift')
    recheck()
    output.mkdir(parents=True, exist_ok=False)
    source_copy, projected = safe(output / 'source-original.html'), safe(output / 'routed-final.html')
    for path, data in ((source_copy, original), (projected, final)):
        with path.open('xb') as stream:
            stream.write(data)
        require(path.read_bytes() == data, 'Projection output byte verification failed')
    recheck()
    receipt = {'schema': 'spec-agent-html-routing-projection-receipt/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'status': 'ROUTING_PROJECTED_NATIVE_REVIEW_PENDING',
        'runId': RUN_ID, 'projectId': PROJECT_ID, 'pinnedInputs': inputs,
        'sourceHtml': {'path': str(html_path), 'sha256': html_sha},
        'preservedOriginalHtml': {'path': str(source_copy), 'sha256': html_sha},
        'derivedFinalHtml': {'path': str(projected), 'sha256': digest(final)}, 'proof': proof,
        'inputsBeforeAfterUnchanged': True, 'atomicOrRaceFreeProof': False,
        'allPublicationAllowlistFilesExistenceVerified': False, 'providerOrApplicationExecuted': False,
        'frozenRendererModifiedOrImported': False, 'visualFidelityVerified': False,
        'formalPercentage': None, 'published': False}
    receipt_path = safe(output / 'routing-receipt.json')
    with receipt_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2); stream.write('\n')
    recheck()
    print(json.dumps({'status': receipt['status'], 'receipt': str(receipt_path), 'sha256': digest(receipt_path.read_bytes()),
                      'replacementCount': proof['replacementCount']}))

if __name__ == '__main__':
    try:
        main()
    except RoutingHold as exc:
        print(json.dumps({'status': 'HOLD_HTML_ROUTING', 'error': str(exc), 'details': exc.details}, ensure_ascii=False))
        raise SystemExit(1)
