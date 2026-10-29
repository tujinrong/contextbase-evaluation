"""Independent OOXML inspection; no Excel/Access instance or shared production code."""
from pathlib import Path
import argparse,hashlib,json,re,sys,zipfile,xml.etree.ElementTree as ET
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def text(value):
    decoded=re.sub(r'_x([0-9a-fA-F]{4})_',lambda m:chr(int(m.group(1),16)),value)
    return decoded.encode('utf-16-le',errors='surrogatepass').decode('utf-16-le')
def main():
    p=argparse.ArgumentParser(); p.add_argument('report',type=Path); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); checks=[]
    def check(name,result): checks.append({'id':name,'status':'PASS' if result else 'FAIL'})
    with zipfile.ZipFile(a.report) as z:
        members=z.namelist(); wb=ET.fromstring(z.read('xl/workbook.xml')); sheets=wb.findall('s:sheets/s:sheet',NS)
        check('two-visible-sheets',[s.attrib['name'] for s in sheets]==['職務経歴書','案件経歴'] and all(s.attrib.get('state','visible')=='visible' for s in sheets))
        check('no-external-connections-macro',not any('/externalLinks/' in n or n.endswith('connections.xml') or n.endswith('vbaProject.bin') for n in members))
        shared=[]
        if 'xl/sharedStrings.xml' in members:
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS): shared.append(text(''.join(si.itertext())))
        tables=[]
        for index in (1,2):
            xml=ET.fromstring(z.read(f'xl/worksheets/sheet{index}.xml')); rows={}
            check(f'no-formulas-{index}',not xml.findall('.//s:f',NS))
            bad_types=[]
            for c in xml.findall('.//s:c',NS):
                t=c.attrib.get('t'); v=c.find('s:v',NS); value=''
                if v is not None:
                    if t=='s': value=shared[int(v.text)]
                    elif t=='inlineStr': value=text(''.join(c.find('s:is',NS).itertext()))
                    else: bad_types.append(c.attrib['r'])
                elif t=='inlineStr': value=text(''.join(c.find('s:is',NS).itertext()))
                cell=c.attrib['r']; row=int(re.sub('[A-Z]','',cell)); col=re.sub('[0-9]','',cell)
                rows.setdefault(row,{})[col]=value
            check(f'all-values-strings-{index}',not bad_types); tables.append(rows)
        def blocks(rows,label):
            values=[]
            for row in sorted(rows):
                record=rows[row]; key=record.get('A',''); value=record.get('G','')
                if key==label: values.append(value)
                elif key==label+'（続き）' and values: values[-1]+=value
            return values
        cover,career=tables
        check('maximum-name-kana',blocks(cover,'氏名')==['界'*40+'（'+'カ'*80+'）'])
        name_rows=[r for r,v in cover.items() if v.get('A','').startswith('氏名')]
        summary_rows=[r for r,v in cover.items() if v.get('A','')=='職務要約']
        check('cover-variable-blocks-do-not-overlap',bool(name_rows and summary_rows) and max(name_rows)<min(summary_rows))
        chapter_labels=('職務要約','活かせる経験・知識・技術','資格','自己PR')
        def wide_chapter(label):
            answer=''; active=False
            for row in sorted(cover):
                value=cover[row].get('A','')
                if value==label: active=True; continue
                if value==label+'（続き）': continue
                if value in chapter_labels or any(value==x+'（続き）' for x in chapter_labels):
                    if active: break
                if active: answer+=value
            return answer
        for label,char in [('職務要約','要'),('活かせる経験・知識・技術','技'),('資格','資'),('自己PR','自')]: check('full-cover-'+label,wide_chapter(label)==char*1000)
        descriptions=blocks(career,'業務概要'); prefixes=["'ABC","''ABC","'=1+1",'_x0041_','=1+1','+1','@NAME','-1','元\n改行','e\u0301','\U0001f600']
        expected=[(prefixes[i%len(prefixes)]+'概'*(1000-len(prefixes[i%len(prefixes)]))).replace('\n','') for i in range(20)]
        check('all-twenty-description-codepoints',descriptions==expected)
        check('all-original-line-break-layout',any(v.get('G','')=='元' for v in career.values()) and any(v.get('G','').startswith('改行') for v in career.values()))
        for label,char,count in [('担当業務','担',1000),('成果・工夫','果',1000),('使用技術','技',500),('担当工程','工',200)]: check('all-twenty-'+label,blocks(career,label)==[char*count]*20)
    output={'reportSha256':hashlib.sha256(a.report.read_bytes()).hexdigest(),'checks':checks,'scope':'independent OOXML values/types/layout boundaries; not print acceptance; original-LF origin versus inserted wraps is checked against the known layout fixture','formalScore':None}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'passed':sum(c['status']=='PASS' for c in checks),'failed':[c['id'] for c in checks if c['status']!='PASS']},ensure_ascii=False)); return int(any(c['status']!='PASS' for c in checks))
if __name__=='__main__': sys.exit(main())
