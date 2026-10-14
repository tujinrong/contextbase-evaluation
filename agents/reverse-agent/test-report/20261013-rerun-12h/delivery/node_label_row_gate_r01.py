"""Candidate-only literal/visible-row proof for trusted parsed flowchart nodes.

No label is rewritten. Unsupported literal mappings fail instead of qualifying.
The caller must bind the trusted parser, original MMD, SVG and capture bytes.
"""
from html.parser import HTMLParser
from html import unescape
import re


class NodeLabelProofError(ValueError):
    pass


TOKEN = re.compile(r"[A-Za-z0-9_]+(?:[.\-][A-Za-z0-9_]+)*")


class _Literal(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.casefold() != 'br' or attrs:
            raise NodeLabelProofError('Unsupported node-label markup; literal mapping unknown')
        self.parts.append('\n')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        raise NodeLabelProofError('Unsupported node-label closing tag')

    def handle_comment(self, data):
        raise NodeLabelProofError('Unsupported node-label comment')

    def handle_decl(self, decl):
        raise NodeLabelProofError('Unsupported node-label declaration')

    def handle_data(self, data):
        self.parts.append(data)


def literal_label(vertex):
    if vertex.get('labelType') not in {'text', 'string'}:
        raise NodeLabelProofError('Unsupported Markdown or unknown node label type')
    for key in ('icon', 'img'):
        if vertex.get(key):
            raise NodeLabelProofError('Unsupported icon/image node literal mapping')
    value = vertex.get('text')
    if value is None:
        value = vertex.get('id')
    if not isinstance(value, str):
        raise NodeLabelProofError('Missing parsed node literal')
    parser = _Literal()
    parser.feed(value)
    parser.close()
    return ''.join(parser.parts)


def _compact(text):
    return ''.join(char for char in text if not char.isspace())


def _contains(outer, inner, tolerance=1.5):
    return (inner['x'] >= outer['x'] - tolerance and
            inner['y'] >= outer['y'] - tolerance and
            inner['x'] + inner['width'] <= outer['x'] + outer['width'] + tolerance and
            inner['y'] + inner['height'] <= outer['y'] + outer['height'] + tolerance)


def prove_node_rows(vertices, actual_nodes, canvas):
    """Require exact literal characters and each whole token in one visible row.

    Expected tokens come from parser literals, not concatenated rendered rows:
    ordinary whitespace-separated words therefore remain separate tokens.
    Bounds are browser measurements of the captured, sanitized SVG.
    """
    expected = {}
    for vertex in vertices:
        key = vertex.get('domId')
        if not key or key in expected:
            raise NodeLabelProofError('Missing or duplicate parser DOM node ID')
        expected[key] = (vertex, literal_label(vertex))
    actual = {}
    for node in actual_nodes:
        key = node.get('id')
        if not key or key in actual:
            raise NodeLabelProofError('Missing or duplicate actual DOM node ID')
        actual[key] = node
    if set(actual) != set(expected):
        raise NodeLabelProofError('Parsed/visible node set differs')
    proof = []
    for key, (vertex, literal) in expected.items():
        node = actual[key]
        row_records = node.get('rows')
        if not isinstance(row_records, list) or not row_records:
            raise NodeLabelProofError('Missing visible SVG node rows')
        intervals = []
        compact_rows = []
        cursor = 0
        for row in row_records:
            text = row.get('text')
            bounds = row.get('bounds')
            if not isinstance(text, str) or not isinstance(bounds, dict):
                raise NodeLabelProofError('Incomplete actual SVG row measurement')
            if _compact(text):
                if (row.get('display') == 'none' or row.get('visibility') != 'visible' or
                        float(row.get('opacity', 1)) <= 0 or bounds['width'] <= 0 or bounds['height'] <= 0 or
                        not _contains(canvas, bounds) or not _contains(node['bounds'], bounds)):
                    raise NodeLabelProofError('SVG node row hidden or outside node/canvas')
            compact = _compact(text)
            intervals.append((cursor, cursor + len(compact)))
            compact_rows.append(compact)
            cursor += len(compact)
        if ''.join(compact_rows) != _compact(literal):
            raise NodeLabelProofError('Parsed node literal/actual SVG rows differ')
        token_proof = []
        for token in TOKEN.finditer(literal):
            begin = len(_compact(literal[:token.start()]))
            end = begin + len(token.group())
            row_index = next((i for i, (a, b) in enumerate(intervals) if a <= begin and end <= b), None)
            if row_index is None:
                raise NodeLabelProofError(f'Indivisible node token crosses visible SVG rows: {token.group()}')
            token_proof.append({'token': token.group(), 'rowIndex': row_index})
        proof.append({'id': vertex['id'], 'domId': key, 'literal': literal,
                      'visibleRows': [row['text'] for row in row_records], 'tokens': token_proof})
    return {'status': 'PASS_VISIBLE_WHOLE_NODE_TOKENS', 'nodes': proof,
            'scope': 'candidate technical proof only; no native human approval'}
