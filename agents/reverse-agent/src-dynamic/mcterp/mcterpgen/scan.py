"""Conservative lexical source extraction and read-only archive metadata."""
from __future__ import annotations
from pathlib import Path
from html.parser import HTMLParser
import bisect, hashlib, json, re, struct, zipfile
import xml.etree.ElementTree as ET


def sha(b):
    return hashlib.sha256(b.encode() if isinstance(b,str) else b).hexdigest()


def read(path):
    raw=path.read_bytes()
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')): return raw.decode('utf-16')
    for enc in ('utf-8-sig','cp932'):
        try:return raw.decode(enc).replace('\r\n','\n').replace('\r','\n')
        except UnicodeError:pass
    raise ValueError('Unsupported source encoding')


def masked(text):
    # Keep offsets/lines stable. Covers quoted, verbatim and template strings and comments.
    pattern=r'//[^\n]*|/\*[\s\S]*?\*/|@"(?:""|[^"])*"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`'
    return re.sub(pattern,lambda m:re.sub(r'[^\n]',' ',m[0]),text)


def pairs(text):
    stack=[];out={}
    for i,c in enumerate(text):
        if c in '({[':stack.append((c,i))
        elif c in ')}]' and stack and stack[-1][0]=={')':'(',']':'[','}':'{'}[c]:
            _,s=stack.pop();out[s]=i
    return out


def comment_summary(text,start):
    previous=text[max(0,start-1800):start]
    hit=re.search(r'<summary>([\s\S]*?)</summary>\s*(?:\[[^\]]+\]\s*)*$',previous)
    if hit: return ' '.join(re.sub(r'<[^>]+>|///',' ',hit[1]).split())
    hit=re.search(r'/\*\*?([\s\S]*?)\*/\s*(?:export\s+)?$',previous)
    if hit:return ' '.join(hit[1].replace('*',' ').split())
    return ''


def functions(text,path,lang):
    mask=masked(text);pm=pairs(mask);out=[];seen=set()
    if lang=='cs':
        pat=r'(?m)^\s*(?:\[[^\n]+\]\s*)?(?:(?:public|private|protected|internal|static|async|virtual|override|sealed|new|partial)\s+)+(?:[\w?.<>\[\],]+\s+)+(?P<name>[\w]+)(?:<[^\n;{}]+>)?\s*(?P<open>\()'
    else:
        pat=r'(?m)(?:\b(?:async\s+)?function\s+(?P<fn>\w+)|\b(?:const|let|var)\s+(?P<name>\w+)\s*(?::[^=\n]+)?=\s*(?:async\s+)?)\s*(?P<open>\()'
    for m in re.finditer(pat,mask):
        op=m.start('open');endparams=pm.get(op)
        if endparams is None:continue
        j=endparams+1
        while j<len(mask) and mask[j] not in '{;\n=':j+=1
        tail=mask[endparams+1:endparams+300]
        bodymatch=re.match(r'\s*(?::[^;={}]+)?(?:where\s+[^={;]+)?\s*(?:=>\s*)?(\{)',tail)
        if not bodymatch:continue
        opening=endparams+1+bodymatch.start(1);end=pm.get(opening)
        if end is None or opening in seen:continue
        seen.add(opening);name=m.groupdict().get('name') or m.groupdict().get('fn')
        start=m.start();line=text.count('\n',0,start)+1
        attrs=text[max(0,start-350):opening]
        disp=re.findall(r'DisplayName\(\s*"([^"]+)"',attrs)
        namespace=re.search(r'\bnamespace\s+([\w.]+)',mask)
        classes=list(re.finditer(r'\b(?:class|struct)\s+(\w+)',mask[:start]))
        cls=classes[-1][1] if classes else Path(path).stem
        body=text[opening+1:end]
        comments=[{'line':line+text[start:opening+1+x.start()].count('\n'),'text':x[1].strip()} for x in re.finditer(r'(?m)^\s*//([^\n]+)',body)]
        conditions=[{'line':text.count('\n',0,opening+1+x.start())+1,'text':x[1].strip()} for x in re.finditer(r'\b(?:if|else if)\s*\(([^\n{}]+)\)',body)]
        calls=[]
        for c in re.finditer(r'(?<![\w])([A-Za-z_][\w]*(?:\s*\.\s*[\w]+)*)\s*(?:<[^<>\n;{}]+>)?\s*\(',masked(body)):
            name_=re.sub(r'\s','',c[1])
            if name_ not in {'if','for','foreach','while','switch','catch','nameof','typeof','using','return','lock'}:calls.append(name_)
        out.append({'id':path+'#'+name+'@'+str(line),'path':path,'name':name,'namespace':namespace[1] if namespace else '', 'class':cls,'line':line,'end':text.count('\n',0,end)+1,'signature':text[start:opening].strip(),'summary':disp[-1] if disp else comment_summary(text,start),'body':body,'comments':comments,'conditions':conditions,'calls':list(dict.fromkeys(calls))})
    return out


class VueReader(HTMLParser):
    def __init__(self,text,path):
        super().__init__(convert_charrefs=True);self.path=path;self.nodes=[];self.stack=[];self.events=[];self.skip=0
        self.feed(text)
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style'}:self.skip+=1
        if self.skip:return
        a=dict(attrs);node={'tag':tag,'attrs':a,'line':self.getpos()[0],'parent':self.stack[-1] if self.stack else None,'text':''}
        idx=len(self.nodes);self.nodes.append(node)
        for k,v in attrs:
            if k.startswith('@') or k.startswith('v-on:'):self.events.append({'trigger':k,'handler':v or '', 'line':node['line'],'node':idx})
        if tag not in {'input','br','hr','img','meta','link','area','source'}:self.stack.append(idx)
    def handle_endtag(self,tag):
        if tag in {'script','style'} and self.skip:self.skip-=1;return
        if self.skip:return
        for i in range(len(self.stack)-1,-1,-1):
            if self.nodes[self.stack[i]]['tag']==tag:self.stack=self.stack[:i];break
    def handle_data(self,s):
        if self.skip:return
        for i in self.stack:self.nodes[i]['text']+=s
    def items(self):
        rows=[]
        for idx,n in enumerate(self.nodes):
            a=n['attrs'];tag=n['tag'];binding=next((str(v) for k,v in a.items() if k.startswith('v-model')), '')
            iscolumn=tag in {'vxe-column','a-table-column','el-table-column'}
            op=tag.endswith('button')
            control=bool(binding) and tag not in {'ai-modal','a-modal','a-pagination','vxe-table','a-table'}
            control=control or tag in {'input','textarea','select','a-input','a-input-number','ai-select','a-select','a-date-picker','datejp','monthjp','van-field'}
            if not (op or control or iscolumn):continue
            label=a.get('title') if iscolumn else a.get('aria-label') or a.get('label')
            parent=n['parent'];condition=[]
            while parent is not None:
                p=self.nodes[parent];pa=p['attrs']
                for k in ['v-if','v-else-if',':is-edit-mode']:
                    if pa.get(k):condition.append(k+' '+pa[k])
                if not label and pa.get('label'):label=pa['label']
                parent=p['parent']
            if not label and not op:
                prior=[p for p in self.nodes[:idx] if p['tag'] in {'th','label'} and p['parent']==n['parent']]
                if not prior and n['parent'] is not None:
                    prior=[p for p in self.nodes[:idx] if p['tag'] in {'th','label'} and p['parent']==self.nodes[n['parent']]['parent']]
                if prior:label=prior[-1]['text']
            if op:label=' '.join(n['text'].split()) or a.get('title') or 'アイコン操作'
            label=' '.join(str(label or a.get('placeholder') or binding or a.get('field') or tag).split())
            role='操作' if op else '表示' if iscolumn or 'readonly' in a or 'disabled' in a else '入力'
            role+='（条件で切替）' if any(k in a for k in [':disabled',':readonly']) else ''
            field=a.get('field','') if iscolumn else binding.split('.')[-1]
            if not field and not op:field=a.get('name','')
            typ='操作ボタン' if op else '一覧表示' if iscolumn else '日付' if 'date' in tag or 'month' in tag else '数値' if 'number' in tag else '選択' if any(k in tag for k in ['select','radio','check']) else '文字'
            required='入力対象外' if role.startswith(('操作','表示')) else ('必須' if 'required' in a else '未明記（検証規則参照）')
            rows.append({'id':'UI-'+sha(self.path+':'+str(idx))[:10],'name':label,'tag':tag,'field':field or '', 'binding':binding,'role':role,'type':typ,'required':required,'length':a.get('maxlength',a.get(':maxlength',a.get('max-length',a.get(':max-length','未明記')))) if typ not in {'操作ボタン','一覧表示'} else '対象外','line':n['line'],'order':len(rows)+1,'condition':'; '.join(list(reversed(condition))+[str(a[k]) for k in ['v-if','v-else-if',':disabled',':readonly'] if a.get(k)]),'attributes':{k:v for k,v in a.items() if k in {':min',':max',':step',':precision',':options',':format','placeholder','type',':type','v-for'}}})
        return rows


def vue(text,path):
    p=VueReader(text,path);methods=[]
    for m in re.finditer(r'<script\b[^>]*>([\s\S]*?)</script\s*>',text,re.I):
        chunk='\n'*text.count('\n',0,m.start(1))+m[1];methods+=functions(chunk,path,'ts')
    items=p.items();mask=masked(text);pm=pairs(mask)
    validations={}
    for hit in re.finditer(r'(?:const|let)\s+\w*[Rr]ules\w*\s*=\s*(?:(?:reactive|ref|computed)\s*\(\s*)?({)',mask):
        opening=hit.start(1);end=pm.get(opening)
        if end is None:continue
        for field in re.finditer(r'(\w+)\s*:\s*(\[)',mask[opening:end]):
            op=opening+field.start(2);finish=pm.get(op)
            if finish is None:continue
            rule=text[op:finish+1];validations[field[1]]={'required':bool(re.search(r'\brequired\s*:\s*true\b',rule)), 'custom':bool(re.search(r'\bvalidator\s*:',rule)), 'line':text.count('\n',0,op)+1}
    for item in items:
        rule=validations.get(item['field'])
        if rule:
            item['attributes']['validation_source_line']=rule['line']
            if rule['custom']:item['attributes']['custom_validator']='独自検証あり・原本の条件参照'
            if rule['required'] and item['role'].startswith('入力'):item['required']='必須（画面検証定義・実効表示条件参照）'
    return {'items':items,'events':p.events,'methods':methods,'components':list(dict.fromkeys(n['tag'] for n in p.nodes if '-' in n['tag']))}


def archive_schema(raw):
    """Only validated length-prefixed UTF-8 DDL strings in PostgreSQL custom TOC. Never rows."""
    if not raw.startswith(b'PGDMP') or raw[8]!=4:raise ValueError('Unsupported PostgreSQL custom archive header')
    entries=[]
    for hit in re.finditer(rb'(?:CREATE (?:OR REPLACE )?(?:TABLE |FUNCTION |PROCEDURE |VIEW |SEQUENCE |(?:UNIQUE )?INDEX )|COMMENT ON (?:TABLE |COLUMN )|ALTER TABLE (?:ONLY )?public\.)',raw):
        i=hit.start()
        if i<5 or raw[i-5]!=0:continue
        n=struct.unpack('<I',raw[i-4:i])[0]
        if n<=0 or n>2_000_000 or i+n>len(raw):continue
        chunk=raw[i:i+n]
        if not chunk.endswith(b'\n') or b'\0' in chunk:continue
        try:value=chunk.decode('utf-8')
        except UnicodeError:continue
        entries.append({'offset':i,'sql':value})
    if not entries:raise ValueError('No validated schema strings in archive')
    return entries


def workbook_structure(path):
    """Read XML cells, never VBA/macros/formulas or external workbook references."""
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        if sum(x.file_size for x in z.infolist())>200_000_000:raise ValueError('Workbook expansion limit')
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')):
                ss.append(''.join(x.text or '' for x in si.findall('s:t',ns)+si.findall('s:r/s:t',ns)))
        rel={x.get('Id'):x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets=[]
        for s in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns):
            target=rel[s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
            member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            rows=[]
            for row in ET.fromstring(z.read(member)).findall('.//s:sheetData/s:row',ns):
                cells={}
                for c in row:
                    value=c.find('s:v',ns)
                    v=value.text if value is not None else ''.join(x.text or '' for x in c.findall('s:is/s:t',ns))
                    if c.get('t')=='s' and v:v=ss[int(v)]
                    if v:cells[c.get('r')]=v
                if cells:rows.append(cells)
            sheets.append({'name':s.get('name'),'rows':rows,'cached_values_only':True})
        return sheets
