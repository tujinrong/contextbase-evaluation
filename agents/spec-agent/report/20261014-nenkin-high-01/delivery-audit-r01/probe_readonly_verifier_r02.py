"""Meaningful synthetic XML-only fixtures. No actual XLSX/file authoring or application."""
import copy,hashlib,importlib.util,json
from pathlib import Path
from xml.etree import ElementTree as ET
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
O=Path(__file__).parent
p=D/'verify_xlsx_v2_62_r02.py';before=p.read_bytes();assert hashlib.sha256(before).hexdigest()=='bf6f59881cd0377dca8dada139f47b000688019683dc07203629558e4c12ab09'
spec=importlib.util.spec_from_file_location('readonly_format_r02',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
S=m.S
checks=[]
def check(name,expected,fn):
    try:fn();seen=True
    except ValueError:seen=False
    checks.append({'name':name,'expectedAccepted':expected,'observedAccepted':seen,'pass':seen==expected});assert seen==expected,name
styles=ET.Element(f'{{{S}}}styleSheet');borders=ET.SubElement(styles,f'{{{S}}}borders');ET.SubElement(borders,f'{{{S}}}border')
xfs=ET.SubElement(styles,f'{{{S}}}cellXfs');ET.SubElement(xfs,f'{{{S}}}xf',borderId='0',fontId='0',fillId='0',numFmtId='0')
stylecache={():0}
def style_id(edges):
    key=tuple(sorted(edges.items()))
    if key not in stylecache:
        bid=len(borders);b=ET.SubElement(borders,f'{{{S}}}border')
        for side,wanted in key:ET.SubElement(b,f'{{{S}}}'+side,style=wanted)
        stylecache[key]=len(xfs);ET.SubElement(xfs,f'{{{S}}}xf',borderId=str(bid),fontId='0',fillId='0',numFmtId='0')
    return stylecache[key]
def sheet_for(specification):
    sh=ET.Element(f'{{{S}}}worksheet');cols=ET.SubElement(sh,f'{{{S}}}cols')
    ET.SubElement(cols,f'{{{S}}}col',min='1',max=str(specification['columns']),width='3')
    sd=ET.SubElement(sh,f'{{{S}}}sheetData');rows={};cells={};edge_map={}
    def setedge(x,y,edges):edge_map.setdefault((x,y),{}).update(edges)
    for op in specification['operations']:
        a,r,b,t=m.bounds(op['range'])
        if specification['role']=='cover':
            sides={'top':'thin'} if op['style']=='cover-company-band' else {s:('double' if op['style']=='cover-title' else 'thin') for s in ('top','bottom','left','right')}
            setedge(a,r,sides)
            for y in range(r,t+1):
                for x in range(a,b+1):
                    if (x,y)==(a,r):continue
                    perimeter={s:v for s,v in sides.items() if (s=='left' and x==a) or (s=='right' and x==b) or (s=='top' and y==r) or (s=='bottom' and y==t)}
                    setedge(x,y,perimeter)
    if specification['role']=='normal':
        last=specification['lastRow']
        for x in range(1,63):setedge(x,1,{'top':'medium','bottom':'double'});setedge(x,last,{'bottom':'medium'})
        for y in range(1,last+1):setedge(1,y,{'left':'medium'});setedge(62,y,{'right':'medium'})
    for (x,y),edges in sorted(edge_map.items(),key=lambda item:(item[0][1],item[0][0])):
        if y not in rows:rows[y]=ET.SubElement(sd,f'{{{S}}}row',r=str(y))
        cells[(x,y)]=ET.SubElement(rows[y],f'{{{S}}}c',r=f'{m.col(x)}{y}',s=str(style_id(edges)))
    merges=ET.SubElement(sh,f'{{{S}}}mergeCells')
    for op in specification['operations']:
        a,r,b,t=m.bounds(op['range'])
        if (a,r)!=(b,t):ET.SubElement(merges,f'{{{S}}}mergeCell',ref=op['range'])
    return sh
cover={'role':'cover','columns':47,'printArea':'O6:AU36','lastRow':36,'tables':[],'operations':[{'range':r,'value':'','style':'cover-company-band' if r=='O36:AU36' else 'cover-title' if r=='O6:AU9' else 'cover-cell'} for r in sorted(m.COVER_RANGES)]}
sh=sheet_for(cover)
def covers(s=sh,definition=cover):m.border_check(s,styles,definition);m.format_assertions(s,styles,definition)
check('14frame cover thin/double/company top-only accepted',True,covers)
for side in ('left','right','bottom'):
    wrong=copy.deepcopy(sh);anchor=wrong.find(f'.//{{{S}}}c[@r="O36"]');anchor.set('s',str(style_id({'top':'thin',side:'thin'})))
    check('company extra '+side+' refused',False,lambda wrong=wrong:covers(wrong))
wrong=copy.deepcopy(sh);anchor=wrong.find(f'.//{{{S}}}c[@r="O36"]');anchor.set('s','0')
check('company top missing refused',False,lambda:covers(wrong))
wrong=copy.deepcopy(sh)
for x in range(15,26):
    cell=wrong.find(f'.//{{{S}}}c[@r="{m.col(x)}23"]');cell.set('s','0')
check('approval frame missing refused',False,lambda:covers(wrong))
wrong=copy.deepcopy(sh);row=ET.SubElement(wrong.find(f'{{{S}}}sheetData'),f'{{{S}}}row',r='30');ET.SubElement(row,f'{{{S}}}c',r='P30',s=str(style_id({'top':'thin'})))
check('blank interframe border leak refused',False,lambda:covers(wrong))
wrong=copy.deepcopy(sh);row=wrong.find(f'{{{S}}}sheetData/{{{S}}}row');ET.SubElement(row,f'{{{S}}}c',r='AV6',s=str(style_id({'left':'thin'})))
check('border beyond AU refused',False,lambda:covers(wrong))
for label,width in [('missing',None),('nan','NaN'),('infinite','inf'),('wrong','2')]:
    wrong=copy.deepcopy(sh);column=wrong.find(f'{{{S}}}cols/{{{S}}}col')
    if width is None:del column.attrib['width']
    else:column.set('width',width)
    check('cover width '+label+' refused',False,lambda wrong=wrong:covers(wrong))
normal={'role':'normal','columns':62,'gridColumnWidth':3,'lastRow':3,'printArea':'A1:BJ3','operations':[],'tables':[]}
ns=sheet_for(normal)
check('normal62 actualwidth3 accepted',True,lambda:m.format_assertions(ns,styles,normal))
for key,value in [('columns',120),('gridColumnWidth',2)]:
    altered={**normal,key:value}
    check('normal geometry '+key+' rejected',False,lambda altered=altered:m.format_assertions(ns,styles,altered))
for kind,part in [('row',f'{{{S}}}sheetData/{{{S}}}row'),('column',f'{{{S}}}cols/{{{S}}}col')]:
    wrong=copy.deepcopy(ns);wrong.find(part).set('hidden','1')
    check('hidden '+kind+' refused',False,lambda wrong=wrong:m.format_assertions(wrong,styles,normal))
blank=ET.Element(f'{{{S}}}worksheet')
listmodel={'role':'list','columns':10,'itemList':True,'tables':[{'headerRow':1}]}
check('itemList10/header1 accepted',True,lambda:m.format_assertions(blank,styles,listmodel))
check('itemList9 refused',False,lambda:m.format_assertions(blank,styles,{**listmodel,'columns':9}))
check('itemList header2 refused',False,lambda:m.format_assertions(blank,styles,{**listmodel,'tables':[{'headerRow':2}]}))
check('generalLIST3 unchanged',True,lambda:m.format_assertions(blank,styles,{'role':'list','columns':3,'itemList':False,'tables':[{'headerRow':1}]}))
check('TABLE9 accepted',True,lambda:m.format_assertions(blank,styles,{'role':'table','columns':9}))
check('TABLE10 refused',False,lambda:m.format_assertions(blank,styles,{'role':'table','columns':10}))
def literal_sheet(kind='str',value='001',formula=False):
    s=ET.Element(f'{{{S}}}worksheet');sd=ET.SubElement(s,f'{{{S}}}sheetData');row=ET.SubElement(sd,f'{{{S}}}row',r='1');c=ET.SubElement(row,f'{{{S}}}c',r='A1',t=kind);ET.SubElement(c,f'{{{S}}}v').text=value
    if formula:ET.SubElement(c,f'{{{S}}}f').text='1+1'
    return s
for value in ('001','1.0','令和01年','=literal',"'literal"):
    check('literal '+value+' exact',True,lambda value=value: m.values(literal_sheet(value=value),{})=={'A1':value} or (_ for _ in ()).throw(ValueError('literal mismatch')))
check('numeric coercion refused',False,lambda:m.values(literal_sheet(kind='n'),{}))
check('formula separately refused',False,lambda:m.values(literal_sheet(formula=True),{}))
assert p.read_bytes()==before
result={'scope':'READONLY_VERIFIER_SYNTHETIC_XML_ONLY','status':'PASS','candidate':{'path':str(p),'sha256':hashlib.sha256(before).hexdigest()},'checks':checks,'count':len(checks),'actualXlsxReads':0,'actualAuthoring':0,'providerExecuted':0,'businessReads':0,'limitations':['Synthetic XML tests do not qualify actual Artifact serialization or visual readability.','Existing full readback functions are reused; actual authored package and print metadata still require explicit binding.']}
out=O/'readonly-verifier-format-probes-r02.json'
with out.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':len(checks)}))
