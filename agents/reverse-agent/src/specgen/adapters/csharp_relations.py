"""Source-grounded receiver resolution and storage effects for C# services.

No application code is executed. This deliberately does not claim compiler-grade
binding: unresolved overloads/registrations are retained, not matched by name.
Works on any supported collection/DI pattern, without screen IDs or domain text.
"""
from __future__ import annotations
from collections import defaultdict
import re
from specgen.common import tokens


COLLECTION = r'(?:List|IList|IReadOnlyList|Dictionary|ConcurrentDictionary|HashSet|ICollection|IEnumerable|DbSet)'
READS = ('FirstOrDefault', 'First', 'FindIndex', 'Find', 'Where', 'Select', 'Any', 'Count', 'ToArray', 'TryGetValue', 'ContainsKey')
MUTATIONS = {'Add': 'create', 'Insert': 'create', 'Remove': 'delete', 'RemoveAll': 'delete', 'Clear': 'delete',
             'AddOrUpdate': 'upsert', 'TryAdd': 'create', 'TryRemove': 'delete'}
PRIMITIVES = {'string', 'int', 'long', 'bool', 'byte', 'char', 'double', 'decimal', 'float', 'object'}


def split_args(value: str) -> list[str]:
    ts = tokens(value); start = 0; depth = 0; result = []
    for t in ts:
        if t['kind'] != 'symbol':
            continue
        if t['text'] in {'(', '[', '{', '<'}: depth += 1
        elif t['text'] in {')', ']', '}', '>'}: depth = max(0, depth-1)
        elif t['text'] == ',' and depth == 0:
            result.append(value[start:t['start']].strip()); start = t['end']
    if value[start:].strip(): result.append(value[start:].strip())
    return result


def mask_literals(source: str) -> str:
    """Keep code offsets; declaration regexes cannot see strings or comments."""
    out = list(source)
    for t in tokens(source):
        if t['kind'] in {'word', 'symbol', 'number'}:
            continue
        for i in range(t['start'], t['end']):
            if out[i] != '\n': out[i] = ' '
    # tokens() excludes comments entirely; mask their remaining spans separately.
    pattern = re.compile(r'@"(?:""|[^"])*"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
    for m in pattern.finditer(source):
        if m[0].startswith(('//', '/*')):
            for i in range(m.start(), m.end()):
                if out[i] != '\n': out[i] = ' '
    return ''.join(out)


class SemanticIndex:
    def __init__(self, sources: dict[str, str], methods: list[dict], names: dict | None = None):
        self.sources = sources; self.methods = methods; self.names = names or {}
        self.byname = defaultdict(list); self.registrations = defaultdict(set)
        self.receivers = defaultdict(dict); self.scopes = {}; self.stores = []; self.by_store = {}
        self.issues = []
        for m in methods: self.byname[m['name']].append(m)
        for path, source in sources.items():
            if not path.endswith('.cs'): continue
            code = mask_literals(source)
            for interface, impl in re.findall(r'Add(?:Singleton|Scoped|Transient)\s*<\s*(\w+)\s*,\s*(\w+)\s*>', code):
                self.registrations[interface].add(impl)
            types = list(re.finditer(r'\bclass\s+(\w+)', code))
            for hit in types:
                owner = hit[1]; tail = code[hit.end():]
                primary = re.match(r'\s*\(([^{}]*?)\)', tail, re.S)
                if primary:
                    self._parameters(path, owner, primary[1])
            for m in [m for m in methods if m['path']==path]:
                owner = m.get('owner', '')
                params = re.search(r'\b'+re.escape(m['name'])+r'\s*\((.*)\)', m['signature'], re.S)
                if params:
                    scope={}
                    for param in split_args(params[1]):
                        match=re.match(r'(?:this\s+|ref\s+|out\s+|in\s+)?([\w?.<>\[\]]+)\s+(\w+)',param)
                        if match:scope[match[2]]=match[1].rstrip('?')
                    self.scopes[(path,owner,m['signature'])]=scope
                    if m['name']==owner:self._parameters(path,owner,params[1])
            fields = re.finditer(r'\b(?:private|protected|public|internal)\s+(?:(?:readonly|static|virtual)\s+)*'
                                 r'('+COLLECTION+r'\s*<[^;{}=]+>|\w+\[\])\s+(\w+)\s*(?=[=;{])', code)
            for hit in fields:
                line = source.count('\n',0,hit.start())+1
                if any(m['path']==path and m['line']<line<=m['end_line'] for m in methods): continue
                preceding = [t for t in types if t.start()<hit.start()]
                if not preceding: continue
                owner = preceding[-1][1]
                typ, field = hit[1], hit[2]
                inner = typ[typ.find('<')+1:typ.rfind('>')] if '<' in typ else typ[:-2]
                element = split_args(inner)[-1].strip() if split_args(inner) else inner.strip()
                if element in PRIMITIVES: continue  # metadata strings are not domain stores
                name = self.names.get(element, element+'データ')
                kind = 'orm_entity' if typ.strip().startswith('DbSet') else 'memory'
                store = {'id':f'{"MEM" if kind=="memory" else "ORM"}-{len(self.stores)+1:03}',
                         'name':name, 'field':field, 'element_type':element, 'declaration_type':typ,
                         'kind':kind, 'owner':owner, 'path':path, 'line':line,
                         'physical_table_verified':False, 'name_basis':'reviewed_terminology' if element in self.names else 'source_type',
                         'evidence':[{'path':path,'line':line}]}
                self.stores.append(store); self.by_store[(path,owner,field)] = store
            # Conventional injected backing fields: _service = service.
            for m in methods:
                if m['path']!=path: continue
                receiver = self.receivers[(path,m.get('owner',''))]
                for target, value in re.findall(r'\b(\w+)\s*=\s*(\w+)\s*;', code):
                    if value in receiver: receiver.setdefault(target, receiver[value])

    def _parameters(self, path, owner, text):
        for param in split_args(text):
            m = re.match(r'(?:this\s+|ref\s+|out\s+|in\s+)?([\w?.<>\[\]]+)\s+(\w+)',param)
            if m: self.receivers[(path,owner)][m[2]] = m[1].rstrip('?')

    def resolve(self, caller, call, dependencies):
        parts = call['name'].replace('?.','.').split('.'); name = parts[-1]
        all_candidates = [m for m in self.byname.get(name,[]) if m['path'] in dependencies]
        if not all_candidates: return None, None
        if len(parts)==1 or parts[0] in {'this','base'}:
            candidates = [m for m in all_candidates if m.get('owner')==caller.get('owner') and m['path']==caller['path']]
        else:
            receiver = parts[-2]
            scope={**self.receivers[(caller['path'],caller.get('owner',''))],**self.scopes.get((caller['path'],caller.get('owner',''),caller['signature']),{})}
            typ = scope.get(receiver,receiver)
            owners = self.registrations.get(typ) or {typ}
            candidates = [m for m in all_candidates if m.get('owner') in owners]
            if not candidates:
                # Extension methods require an explicit 'this' receiver parameter.
                candidates = [m for m in all_candidates if re.search(r'\(\s*this\s+',m['signature'])]
        argc = len(split_args(call.get('arguments','')))
        narrowed = []
        for m in candidates:
            match = re.search(r'\b'+re.escape(name)+r'\s*\((.*)\)',m['signature'],re.S)
            params = split_args(match[1]) if match else []
            if params and params[0].startswith('this '): params=params[1:]
            mandatory=sum('=' not in p and not p.startswith('params ') for p in params)
            if mandatory<=argc<=len(params) or any(p.startswith('params ') for p in params): narrowed.append(m)
        if len(narrowed)>1:
            argtypes={**self.receivers[(caller['path'],caller.get('owner',''))],**self.scopes.get((caller['path'],caller.get('owner',''),caller['signature']),{})}
            arguments=split_args(call.get('arguments',''))
            precise=[]
            for candidate in narrowed:
                match=re.search(r'\b'+re.escape(name)+r'\s*\((.*)\)',candidate['signature'],re.S)
                params=split_args(match[1]) if match else []
                if params and params[0].startswith('this '):params=params[1:]
                if all(argtypes.get(arg) is None or argtypes[arg]==param.split()[0].rstrip('?') for arg,param in zip(arguments,params)):
                    precise.append(candidate)
            if precise:narrowed=precise
        if len(narrowed)==1: return narrowed[0], None
        reason = 'ambiguous_owner_or_overload' if narrowed else 'receiver_or_signature_unresolved'
        return None, {'reason':reason,'caller':caller['id'],'call':call,
                      'candidates':[m['id'] for m in narrowed or all_candidates]}

    def trace(self, entry, dependencies, max_visits=160, max_depth=16):
        visits=[]; edges=[]; unresolved=[]
        def visit(method, inherited, chain, active, depth):
            if depth>max_depth or len(visits)>=max_visits:
                unresolved.append({'reason':'trace_limit','method':method['id']});return
            if method['id'] in active:
                unresolved.append({'reason':'recursive_call','method':method['id']});return
            visits.append({'method':method,'guards':inherited,'chain':chain})
            for call in method.get('calls',[]):
                callee, problem = self.resolve(method,call,dependencies)
                if problem: unresolved.append(problem)
                if callee:
                    edge={'caller':method['id'],'callee':callee['id'],'line':call['line'],
                          'arguments':call.get('arguments',''),'guards':inherited+call.get('guards',[])}
                    edges.append(edge)
                    visit(callee,edge['guards'],chain+[edge],active|{method['id']},depth+1)
        visit(entry,[],[],set(),0)
        return visits,edges,unresolved

    def effects(self, entry, visits):
        effects=[]; seen=set()
        for visit in visits:
            m=visit['method']
            for step in m['steps']:
                expr=step.get('expression') or step.get('condition','')
                stores=[s for s in self.stores if (s['path']==m['path'] and s['owner']==m.get('owner')) or re.search(r'\b'+re.escape(s['owner'])+r'\.'+re.escape(s['field'])+r'\b',expr)]
                for store in stores:
                    field=store['field']; escaped=re.escape(field)
                    if not re.search(r'(?<!\w)'+escaped+r'(?!\w)',expr): continue
                    operation=None
                    if re.search(escaped+r'\s*\[[^\]]+\]\s*=(?!=)',expr): operation='update'
                    else:
                        call=re.search(escaped+r'\s*\.\s*('+ '|'.join(MUTATIONS)+r')\s*\(',expr)
                        if call:operation=MUTATIONS[call[1]]
                        elif re.search(escaped+r'\s*(?:\.|\[)',expr):operation='read'
                    if not operation:continue
                    guards=visit['guards']+step.get('guards',[])
                    key=(entry['id'],m['id'],step['line'],field,operation,tuple(guards))
                    if key in seen:continue
                    seen.add(key)
                    written=set()
                    for n in m['steps']:
                        e=n.get('expression','')
                        match=re.search(escaped+r'\s*\[[^\]]+\]\s*=\s*(\w+)',e) or re.search(escaped+r'\.Add\(\s*(\w+)\s*\)',e)
                        if match:written.add(match[1])
                    rules=[n for n in m['steps'] if '.' in n.get('target','') and n['target'].split('.')[0] in written]
                    effects.append({'kind':store['kind'],'store':store['name'],'store_id':store['id'],
                        'element_type':store['element_type'],'field':field,'operation':operation,'event':entry['name'],
                        'implementation':m['name'],'guards':guards,'expression':expr,
                        'evidence':[{'path':m['path'],'line':step['line']}],
                        'call_chain':visit['chain'],'assignments':rules,
                        'lock_expressions':[g for g in step.get('guards',[]) if any(n['kind']=='lock' and n.get('condition')==g for n in m['steps'])],
                        'physical_table_verified':False})
        return effects
