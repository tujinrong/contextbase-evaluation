"""Explicit Japanese VBA file encoding and locale-independent VBE transport.

Editable production .bas/.cls files are CP932, without a BOM. Office native
Form exports and Unicode application data have separate encoding contracts.
"""
from pathlib import Path
import re

VBA_FILE_ENCODING = 'cp932'


def read_vba_source(path):
    data = Path(path).read_bytes()
    if data.startswith((b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff')):
        raise ValueError('Production VBA source requires CP932 without a BOM: ' + str(path))
    text = data.decode(VBA_FILE_ENCODING, errors='strict')
    if text.encode(VBA_FILE_ENCODING, errors='strict') != data:
        raise ValueError('Production VBA source is not byte-round-trippable CP932: ' + str(path))
    return text


def _literal(value):
    parts, pending = [], ''
    for char in value:
        if ord(char) < 128:
            pending += char
            continue
        if pending:
            parts.append('"' + pending.replace('"', '""') + '"')
            pending = ''
        raw = char.encode('utf-16-le', errors='strict')
        parts.extend('ChrW(&H' + format(int.from_bytes(raw[i:i + 2], 'little'), 'X') + ')'
                     for i in range(0, len(raw), 2))
    if pending:
        parts.append('"' + pending.replace('"', '""') + '"')
    if not parts:
        return '""'
    if len(parts) == 1 and parts[0].startswith('ChrW('):
        parts.insert(0, '""')
    return '(' + ' & '.join(parts) + ')' if len(parts) > 1 else parts[0]


def _wrap_line(line, number):
    lines = []
    while len(line) > 900:
        quoted, splits, i = False, [], 0
        while i < min(len(line), 899):
            if line[i] == '"':
                if quoted and i + 1 < len(line) and line[i + 1] == '"':
                    i += 2
                    continue
                quoted = not quoted
            elif not quoted and line[i] == "'":
                break
            elif (not quoted and line[i] == '&' and i > 0 and i + 1 < len(line)
                  and line[i - 1].isspace() and line[i + 1].isspace()):
                splits.append(i + 1)
            i += 1
        if not splits or len(lines) >= 24:
            raise ValueError(f'VBE transport requires manual line splitting at source line {number}')
        cut = splits[-1]
        lines.append(line[:cut] + ' _')
        line = '        ' + line[cut:].lstrip()
    return lines + [line]


def vbe_text(source):
    """Render Unicode literals as ASCII/ChrW without consulting host ACP.

    This transports exact runtime strings through VBE on ACP932, ACP936 and
    other hosts. It does not change the editable CP932 source or DB encoding.
    Comments remain comments; non-ASCII comment characters are escaped only
    in the temporary transport. Non-ASCII identifiers/constants are rejected
    instead of silently changing their meaning.
    """
    result = []
    for number, line in enumerate(source.replace('\r\n', '\n').replace('\r', '\n').split('\n'), 1):
        out, i = [], 0
        while i < len(line):
            char = line[i]
            comment = char == "'" or (re.match(r'(?i)rem\b', line[i:]) is not None
                                      and (not line[:i].strip() or line[:i].rstrip().endswith(':')))
            if comment:
                out.append(line[i:].encode('ascii', errors='backslashreplace').decode('ascii'))
                break
            if char == '"':
                start, value = i, ''
                i += 1
                while i < len(line):
                    if line[i] == '"':
                        if i + 1 < len(line) and line[i + 1] == '"':
                            value += '"'
                            i += 2
                            continue
                        i += 1
                        break
                    value += line[i]
                    i += 1
                else:
                    raise ValueError(f'Unterminated VBA literal at line {number}')
                if any(ord(c) > 127 for c in value) and re.search(r'(?i)\bconst\b|^\s*attribute\b', line[:start]):
                    raise ValueError(f'Non-ASCII constant/attribute needs an explicit source design at line {number}')
                out.append(_literal(value))
                continue
            if ord(char) > 127:
                raise ValueError(f'Non-ASCII VBA token outside a literal/comment at line {number}')
            if char == '\x00':
                raise ValueError(f'NUL in VBA source at line {number}')
            out.append(char)
            i += 1
        result.extend(_wrap_line(''.join(out), number))
    transported = '\r\n'.join(result)
    transported.encode('ascii', errors='strict')
    return transported
