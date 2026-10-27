"""Static adapters. Application code is text, never imported or executed.

VB/WPF uses a conservative lexical adapter, not a VB compiler. Other languages
bridge the existing specgen adapters. Unknown formats remain in the inventory.
"""
from __future__ import annotations
import ast
import bisect
import re
from pathlib import Path
from xml.parsers import expat

VERSION = '2.0.2'
EXTENSIONS = {'.vb': 'vb', '.xaml': 'xaml', '.sql': 'sql', '.py': 'Python', '.cs': 'C#', '.java': 'Java', '.js': 'JavaScript', '.jsx': 'JavaScript', '.ts': 'TypeScript', '.tsx': 'TypeScript'}
STRING = re.compile(r'"(?:""|[^"])*"')
METHOD = re.compile(r'^\s*(?:(?:Public|Private|Protected|Friend|Shared|Overrides|Overloads|Async|NotOverridable|Overridable|Shadows|Partial|MustOverride)\s+)*(Sub|Function)\s+(\w+)\s*(?:\(Of\b[^)]*\))?\s*\(', re.I)
PROP = re.compile(r'^\s*(?:(?:Public|Private|Protected|Friend|Shared|ReadOnly|WriteOnly|Overrides|Default)\s+)*Property\s+(\w+)(?:\([^\n]*?\))?\s+As\s+(.+)', re.I)
IDENT = r'(?:"[^"]+"|\[[^\]]+\]|`[^`]+`|[A-Za-z_][\w$]*)(?:\.(?:"[^"]+"|\[[^\]]+\]|`[^`]+`|[A-Za-z_][\w$]*))*'


def decode(raw: bytes) -> str:
    encs = ['utf-16'] if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else ['utf-8-sig', 'cp932']
    for enc in encs:
        try:
            value = raw.decode(enc)
            if '\x00' in value:
                raise ValueError('binary source')
            return value.replace('\r\n', '\n').replace('\r', '\n')
        except UnicodeError:
            continue
    raise ValueError('unsupported encoding')


def clean_vb(line: str) -> str:
    quoted, out, i = False, [], 0
    while i < len(line):
        c = line[i]
        if c == '"':
            if quoted and i + 1 < len(line) and line[i + 1] == '"':
                out.append('""'); i += 2; continue
            quoted = not quoted
        if c == "'" and not quoted:
            break
        out.append(c); i += 1
    return ''.join(out)


def mask(value: str) -> str:
    value = re.sub(r'(?i)((?:password|passwd|secret|api_?key|connectionstring|DBPass)\s*[:=]\s*)"(?:""|[^"])*"', r'\1"[REDACTED]"', value)
    return value.strip().replace('\t', ' ')


def doccomment(lines: list[str], i: int) -> str:
    acc = []
    for k in range(i - 1, max(-1, i - 20), -1):
        s = lines[k].strip()
        if s.startswith("'''"):
            acc.insert(0, s[3:].strip())
        elif not s or re.match(r'Private\s+_\w+\s+As\b', s, re.I):
            continue
        else:
            break
    m = re.search(r'<summary>(.*?)</summary>', ' '.join(acc), re.S | re.I)
    return re.sub('<[^>]*>', '', m.group(1)).strip() if m else ''


def logical_lines(lines: list[str], first: int, last: int) -> list[dict]:
    out, parts, begin, balance = [], [], first, 0
    for n in range(first, last):
        s = clean_vb(lines[n]).strip()
        if not s: continue
        if not parts: begin = n
        parts.append(s[:-1].rstrip() if s.endswith(' _') else s)
        no_strings = STRING.sub('""', s)
        balance += no_strings.count('(') - no_strings.count(')') + no_strings.count('{') - no_strings.count('}')
        if not s.endswith((' _',',')) and balance <= 0:
            out.append({'line': begin + 1, 'end': n + 1, 'text': mask(' '.join(parts))})
            parts, balance = [], 0
    if parts: out.append({'line': begin + 1, 'end': last, 'text': mask(' '.join(parts))})
    return out


def sql_info(sql: str, positions: list[tuple[int, int]]) -> dict:
    def line_at(offset):
        return positions[max(0, bisect.bisect_right([p[0] for p in positions], offset) - 1)][1] if positions else 1
    masked = re.sub(r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/", lambda m: ' ' * len(m.group()), sql)
    refs, columns = [], []
    patterns = [(r'INSERT\s+INTO', 'C'), (r'UPDATE', 'U'), (r'DELETE\s+FROM', 'D'), (r'FROM|JOIN', 'R'), (r'TRUNCATE(?:\s+TABLE)?', 'TRUNCATE'), (r'COPY', 'COPY')]
    ctes = set(re.findall(r'(?:\bWITH|,)\s*(\w+)\s+AS\s*\(', masked, re.I))
    for pre, op in patterns:
        for m in re.finditer(r'\b(?:' + pre + r')\s+(' + IDENT + ')', masked, re.I):
            obj = m.group(1).strip('"`[]')
            if obj.upper() in {'SET', 'SELECT', 'CASCADE', 'NO', 'ON'} or obj in ctes: continue
            if op == 'R' and re.search(r'DELETE\s*$', masked[max(0, m.start()-12):m.start()], re.I): continue
            if op == 'U' and re.search(r'ON\s*$', masked[max(0, m.start()-6):m.start()], re.I): continue
            refs.append({'object': obj, 'operation': op, 'line': line_at(m.start()), 'origin': 'literal_sql'})
    for m in re.finditer(r'\bINSERT\s+INTO\s+(' + IDENT + r')\s*\(([^)]+)\)', masked, re.I):
        for col in m.group(2).split(','):
            col = col.strip().strip('"`[]')
            if re.fullmatch(r'\w+', col): columns.append({'object': m.group(1).strip('"`[]'), 'column': col, 'line': line_at(m.start()), 'role': 'write'})
    for m in re.finditer(r'\bUPDATE\s+(' + IDENT + r')\s+SET\s+(.+?)(?=\bWHERE\b|;|$)', masked, re.I | re.S):
        for col in re.findall(r'(?:^|,)\s*([\w]+)\s*=', m.group(2)):
            columns.append({'object': m.group(1).strip('"`[]'), 'column': col, 'line': line_at(m.start()), 'role': 'write'})
    aliases = {}
    for m in re.finditer(r'\b(?:FROM|JOIN)\s+(' + IDENT + r')(?:\s+(?:AS\s+)?(\w+))?', masked, re.I):
        obj = m.group(1).strip('"`[]'); aliases[obj] = obj
        if m.group(2) and m.group(2).upper() not in {'WHERE', 'ON', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'GROUP', 'ORDER', 'UNION'}:
            aliases[m.group(2)] = obj
    for m in re.finditer(r'\b(\w+)\.(\w+)\b', masked):
        if m.group(1) in aliases: columns.append({'object': aliases[m.group(1)], 'column': m.group(2), 'line': line_at(m.start()), 'role': 'reference'})
    functions = sorted(set(re.findall(r'\bfunc_\w+\b', sql, re.I)))
    sequences = sorted(set(re.findall(r"\b(?:nextval|setval|currval)\s*\(\s*'([^']+)'", sql, re.I)))
    return {'db': refs, 'columns': columns, 'db_functions': functions, 'sequences': sequences, 'sql': sql}


def vb(text: str, path: str) -> dict:
    lines = text.splitlines(); code = [clean_vb(x) for x in lines]
    starts = [(i, m) for i, s in enumerate(code) if (m := METHOD.match(s))]
    methods, props, classes = [], [], []
    for index, (i, m) in enumerate(starts):
        ceiling = starts[index+1][0] if index+1 < len(starts) else len(lines)
        ends = [n for n in range(i+1, ceiling) if re.match(r'^\s*End\s+'+m.group(1)+r'\s*$', code[n], re.I)]
        end = ends[-1] if ends else ceiling-1
        statements = logical_lines(lines, i, end+1)
        signature = statements[0]['text'] if statements else code[i]
        body = '\n'.join(code[i:end+1])
        comments = [{'line': k+1, 'text': lines[k].strip().lstrip("'").strip()} for k in range(i+1,end+1) if lines[k].strip().startswith("'") and not lines[k].strip().startswith("'''")]
        builders = {}
        for stmt in statements:
            s = stmt['text']
            b = re.search(r'(\w+)\.Append(?:Line)?\(', s)
            if b and any(k in b.group(1).lower() for k in ('sql', 'query')):
                vals = [x.group()[1:-1].replace('""','"') for x in STRING.finditer(s)]
                builders.setdefault(b.group(1), []).append((' '.join(vals), stmt['line']))
            elif re.search(r'\b(SELECT\s|INSERT\s+INTO|DELETE\s+FROM|UPDATE\s|TRUNCATE\s|COPY\s)', s, re.I):
                vals = [x.group()[1:-1].replace('""','"') for x in STRING.finditer(s)]
                builders.setdefault('__literal', []).append((' '.join(vals), stmt['line']))
        sqls = []
        for fragments in builders.values():
            sql, positions = '', []
            for fragment, ln in fragments:
                positions.append((len(sql), ln)); sql += fragment + '\n'
            sqls.append(sql_info(sql, positions))
        refs = [v for q in sqls for v in q['db']]
        for stmt in statements:
            for hit in re.finditer(r'(?:IsValidPrimary|GetNewCode)\s*\(\s*"([\w.]+)"', stmt['text'], re.I):
                refs.append({'object': hit.group(1), 'operation': 'R', 'line': stmt['line'], 'origin': 'bound_helper_argument'})
        required = []
        for hit in re.finditer(r'CtrlRequired\s*=\s*New\s+List\(Of Control\)\s+From\s*\{([^}]+)\}|CtrlRequired\.Add\((\w+)\)', body, re.I):
            required.extend(re.findall(r'\w+', hit.group(1) or hit.group(2)))
        handles = re.split(r'\sHandles\s',signature,maxsplit=1,flags=re.I)[-1] if re.search(r'\sHandles\s',signature,re.I) else ''
        calls = sorted(set(re.findall(r'\b((?:[A-Za-z_]\w*\.)?[A-Za-z_]\w*)\s*\(', body)))
        calls += re.findall(r'\bAddressOf\s+([\w.]+)', body, re.I)
        calls += re.findall(r'\b(?:Not|If)\s+(_\w+)\s+Then\b',body,re.I)
        mapping = [{'property': x.group(1), 'column': x.group(2), 'line': st['line']} for st in statements for x in re.finditer(r'\.(\w+)\s*=\s*[^\n]*?\b(?:drd|row|dr)\("(\w+)"\)', st['text'])]
        messages = [st for st in statements if re.search(r'(?:MyMessage\.Show\w+|MessageBox\.Show|\bsMessage\s*[&+]?=|sb(?:Err|Message)\.Append)',st['text'],re.I)]
        methods.append({'name':m.group(2),'line':i+1,'end':end+1,'signature':signature,'summary':doccomment(lines,i),'statements':statements[1:-1], 'comments':comments,'calls':sorted(set(calls)), 'handles':handles,'required':required,'db':refs,'columns':[v for q in sqls for v in q['columns']], 'sql_fragments':sqls,'messages':messages,'mapping':mapping,'db_functions': sorted(set(v for q in sqls for v in q['db_functions'])), 'sequences': sorted(set(v for q in sqls for v in q['sequences'])), 'windows':sorted(set(re.findall(r'\bNew\s+(\w*Window)\b',body,re.I))), 'reports':sorted(set(re.findall(r'\bNew\s+(Rpt\w+)\b',body))), 'complete':bool(ends)})
    for i, s in enumerate(code):
        if match := re.match(r'\s*(?:Public\s+|Partial\s+|Friend\s+)*(?:Class|Module)\s+(\w+)',s,re.I):
            classes.append({'name':match.group(1),'line':i+1,'summary':doccomment(lines,i)})
        if match := PROP.match(s): props.append({'name':match.group(1),'type':match.group(2),'line':i+1,'summary':doccomment(lines,i)})
    constants = [{'name':m.group(1),'value':m.group(2),'line':i+1,'summary':doccomment(lines,i)} for i,s in enumerate(code) if (m := re.search(r'\bConst\s+(\w+)(?:\s+As\s+\w+)?\s*=\s*(.*)',s,re.I))]
    types = {m.group(1):m.group(2) for m in re.finditer(r'\b(?:Dim|Private|Public)\s+(\w+)\s+As\s+(?:New\s+)?(\w+)', '\n'.join(code),re.I)}
    types.update({m.group(1):m.group(2) for m in re.finditer(r'\b(\w+)\s*=\s*New\s+(\w+)', '\n'.join(code),re.I)})
    models = sorted(set(re.findall(r'\b\w+Model\b','\n'.join(code))))
    return {'path':path,'language':'VB.NET','status':'partial','classes':classes,'fields':props,'constants':constants,'types':types,'models':models,'methods':methods,'inherits':re.findall(r'^\s*Inherits\s+(\w+)',text,re.M|re.I),'lines':len(lines)}


def xaml(text: str, path: str) -> dict:
    nodes, stack = [], []
    parser = expat.ParserCreate()
    parser.ExternalEntityRefHandler = lambda *args: 0
    def start(tag, attrs):
        nodes.append({'tag':tag.split(':')[-1], 'attrs':attrs, 'line':parser.CurrentLineNumber,'parent':stack[-1] if stack else None})
        stack.append(len(nodes)-1)
    parser.StartElementHandler = start
    parser.EndElementHandler = lambda _: stack.pop()
    if '<!DOCTYPE' in text.upper(): raise ValueError('DTD is not allowed')
    parser.Parse(text, True)
    return {'path':path,'language':'XAML','status':'partial','nodes':nodes,'class':nodes[0]['attrs'].get('x:Class',''),'title':nodes[0]['attrs'].get('Title',''),'base':nodes[0]['tag'],'lines':len(text.splitlines())}


def parse(text: str, path: str) -> dict:
    ext = Path(path).suffix.lower()
    if ext == '.vb': return vb(text,path)
    if ext == '.xaml': return xaml(text,path)
    from specgen.analyze import analyze
    out = analyze(text,path,EXTENSIONS[ext])
    result = {'path':path,'language':EXTENSIONS[ext],'status':out['status'],'classes':[],'fields':[],'constants':[],'types':{},'models':[],'methods':[],'inherits':[],'tables':out.get('tables',[]),'lines':len(text.splitlines()),'warnings':out.get('warnings',[])}
    for s in out.get('symbols',[]):
        if s['kind']=='class': result['classes'].append({'name':s['name'],'line':s['line'],'summary':s['summary']})
        else:
            refs=[c for c in out.get('crud',[]) if s['line']<=c['line']<=s['end_line']]
            result['methods'].append({'name':s['name'],'line':s['line'],'end':s['end_line'],'signature':s['signature'],'summary':s['summary'],'statements':[],'comments':[],'calls':[c['name'] for c in s['calls']],'handles':'','required':[],'db':[dict(c,object=c['table']) for c in refs],'columns':[],'sql_fragments':[],'messages':[],'mapping':[],'db_functions':[],'sequences':[],'windows':[],'reports':[],'complete':False,'routes':s.get('routes',[])})
    if ext == '.sql': result['sql_facts'] = sql_info(text,[(0,1)])
    return result
