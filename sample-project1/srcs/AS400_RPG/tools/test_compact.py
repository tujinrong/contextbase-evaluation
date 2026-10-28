"""Current source/DDS contract checks. Never claims RPG compilation or 5250 execution."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse,json,re,hashlib,unicodedata
from output_paths import result_dir
B=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report-dir',type=Path);p.add_argument('--run-id',default='current');a=p.parse_args();R=result_dir('compact',a.report_dir);dest=R/'compact-static.json'
checks=[]
def check(id,ok,detail=''):checks.append(dict(id=id,passed=bool(ok),detail=detail))
def text(path):return (B/path).read_text('utf8')
types=text('copy/STUTYPES.rpgleinc');svc=text('src/STUSVC.sqlrpgle');search=text('src/STUSRCH.sqlrpgle');editor=text('src/STUEDIT.sqlrpgle')
raw=types[types.index(' dcl-ds SearchRaw_t'):types.index(' dcl-ds StudentListWork_t')]
check('compact-raw-criteria',all(x not in raw for x in ['kanaKey','schoolYear','gradeCode','unassigned','prefectureCode','fromDate','toDate','phone']))
check('raw-retained-separately',' dim( 3 )' in raw and 'raw likeds( SearchRaw_t )' in search and 'applied likeds( SearchCriteria_t )' in types)
check('schema-owner-before-reuse',all(x in svc for x in ["searchStates( slot ).owner=principal","context.criteriaFormatVersion",'c=searchStates( slot ).applied']))
normal=svc[svc.index(' dcl-proc NormalizeSearch ;'):svc.index(' dcl-proc LoadListRow ;')]
check('class-id-exists-all-years','M_CLASS' in normal and 'criteria.classId' in normal and 'valid_from' not in normal and 'is_active' not in normal)
pred=svc[svc.index(' predicate= '):svc.index(' monitor ;',svc.index(' predicate= '))]
check('four-predicate-shapes',all(x not in pred for x in ['kana_key','school_year','grade_code','prefecture_code','phone_number','admission_date']) and all(x in pred for x in ['student_no','name_key','class_id','enrollment_status']))
projection=svc[svc.index(' dcl-proc LoadListRow ;'):svc.index(' dcl-proc StSearchStudents export ;')]
check('lean-list-projection',all(x not in projection for x in ['address','phone','updatedAt','updated_at','email','remarks']))
check('no-full-row-in-search','LoadRow( id :page.rows' not in svc and 'LoadListRow( id :page.rows' in svc)
check('literal-like-normalization',all(x in normal for x in [":15 :15 :5",":8 :160 :2",'StEscapeLike']))
check('server-sort-four','s.name_key' in svc and all("context.sortKey= '"+x+"'" in svc for x in ['studentNo','name','admissionDate','updatedAt']))
check('applied-paging-reuse','StSearchStudents( raw :context :*off :page )' in search)
check('native-eight-student-roll','block+=8' in search and 'block-=8' in search and '%min( 8 :page.rowCount-block )' in search and 'block+=10' not in search)
check('native-db-page-keys',all(x in search for x in ['*in07','*in10','*in15','*in16','page.total>10000','context.page=idx']))
check('roll-does-not-cross-db-page',search.index(' if *in25 or *in26 ;')<search.index(' if *in07 or *in10 or *in15 or *in16 ;') and 'block+8<page.rowCount' in search)
for size,expected in [(20,[8,8,4]),(50,[8]*6+[2]),(100,[8]*12+[4])]:
 actual=[min(8,size-i) for i in range(0,size,8)];check('terminal-partitions-'+str(size),actual==expected,actual)
flat=re.sub(r'\s+','',editor);uiflat=re.sub(r'\s+','',text('copy/STUDSP.rpgleinc'))
check('single-editor-all-inputs','exfmtEDSTUDENT;' in flat and 'EDBASE' not in editor and 'EDENROLL' not in editor)
check('raw-read-before-editor-keys',editor.index(' ReadForm( ) ;')<editor.index(' if *in09'))
check('f9-error-focus','errorIndex=%rem(errorIndex:result.errorCount)+1;' in flat and 'CSRROW=13;CSRCOL=12;' in flat)
check('new-admission-empty',"raw.values(12)=%ucs2(%char(day:*iso))" not in flat and 'REG-013' in editor)
check('unicode-era-raw-buffer','birthEra varucs2( 20 )' in types and 'rawSchoolYear varucs2( 8 )' in types)
check('full-raw-before-auxiliary','LongEdit( raw.values' in editor and "Question( result.messageId :hints.reason :*on :result )" in editor)
check('cursor-addressed-native-fields','CSRFLD=' in search and 'CSRREL' in search and 'QFIELD' not in search and 'EFIELD' not in editor)
check('row-selection-validated-before-open','ifcount<>1;' in re.sub(r'\s+','',search) and search.index("if count<>1")<search.index(' StEdit( id :viewOnly :notice )',search.index(' dcl-proc SelectRow')))
check('row-options-survive-readc', 'selectedOptions' in search and 'selectedOptions( rrn ) =ROPT' in search and 'clear selectedOptions' in search)
check('fixed-sort-page-pickers',"Choice( 'PAGE'" in search and "Choice( 'SORT'" in search and "kind='SORT';offset=0;count=8;" in uiflat)
check('candidate-frozen-until-page', 'ifnotfetched;' in uiflat and 'fetched=*on;' in uiflat and 'exfmtPICK;' in uiflat)
check('candidate-enter-one-selection',"iftotal<>1orchosen<0orchosen>count;" in uiflat and "selections(i)<>'1'" in uiflat)
check('longtext-explicit-mode', 'if*in06;unicode=notunicode;' in uiflat and 'StTextEscapeWindow' in uiflat and 'StTextSplice' in uiflat)
check('confirmation-explicit-delete-key',"if(deletingand*in23)or(notdeletingand*in10);" in uiflat and 'CSRROW=26;CSRCOL=2;' in uiflat)
longflat=uiflat[uiflat.index('dcl-procLongEdit;'):uiflat.index('dcl-procQuestion;')]
check('aux-limit-before-apply',longflat.index('rc=StTextLimit(')<longflat.index('value=draft;') and "ifrc<>0;LMSG='Rawfieldlimitexceeded:correctthiswindoworF12cancel';iter;endif;" in uiflat)
check('narrow-edit-limit-explicit',all(x in flat for x in ['LongEdit(text:protected:20:10)','LongEdit(text:protected:8:4)','LongEdit(text:protected:4:2)','LongEdit(text:protected:120:60)']) and 'LongEdit(reasonDraft:*off:120:60)' in uiflat)
check('continuation-raw-lf-independent','StTextWindow' in text('c/STUNICODE.c') and 'cp==0x0a' in text('c/STUNICODE.c') and 'MergeParts' in editor)
fields={};formats={}
for path in ['dds/STUSCHD.dspf','dds/STUEDTD.dspf']:
 source=text(path);current=None;fields[path]={};formats[path]=set();bad=[];overlap=[];occupied={}
 for i,line in enumerate(source.splitlines(),1):
  if len(line)>16 and line[16]=='R':current=line[18:28].strip();formats[path].add(current);fields[path][current]=set();occupied[current]=set()
  if len(line)>43 and line[38:41].strip().isdigit() and line[41:44].strip().isdigit():
   row=int(line[38:41]);col=int(line[41:44]);name=line[18:28].strip();length=0
   if name and line[29:34].strip().isdigit():length=int(line[29:34]);fields[path][current].add(name)
   elif line[44:].startswith("'"):
    value=line[45:-1];length=sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in value)
   if length:
    cells={(row,c) for c in range(col,col+length)}
    if not (1<=row<=27 and 1<=col and col+length<=133):bad.append(i)
    if cells&occupied[current]:overlap.append((i,name))
    occupied[current]|=cells
 check(path+'-source80',all(len(line.encode('utf8'))<=80 for line in source.splitlines()))
 check(path+'-cells',not bad,bad);check(path+'-overlap',not overlap,overlap)
check('search-four-native-fields',all(x not in text('dds/STUSCHD.dspf') for x in ['QKANA','QYEAR','QGRADE','QUNASS','QPREF','QPHONE','QADMFROM','QADMTO']))
check('two-line-eight-records',all(x in text('dds/STUSCHD.dspf') for x in ['SFLPAG(8)','SFLSIZ(101)','RKANA']))
editfields=fields['dds/STUEDTD.dspf'];normal=editfields['EDSTUDENT']
check('all-editor-inputs-one-record',{'STUID','ESTUNO','ENAME','EKANA','EBERA','EBYEAR','EBMONTH','EBDAY','EGENDER','EPOSTAL','EPREF','EADDR1','EADDR2','EPHONE','EEMAIL','EADMDATE','ESTATUS','EENDDATE','EYEAR','EGRADE','ECLASS','CLCOUNT','EEMGNAME','EREL','EEMGPHONE','EREM1','EREM2','EREM3','EREAS1','EREAS2','UPDINFO'}<=normal)
check('separate-auxiliary-records',{'PICK','CNFRM','LONGTXT'}<=formats['dds/STUEDTD.dspf'])
check('single-longtext-window',fields['dds/STUEDTD.dspf']['LONGTXT']>={'TEXT','LTITLE','LPOS','LMSG'} and 'LTXT1' not in text('dds/STUEDTD.dspf'))
check('eight-pick-inputs',{'PSEL'+str(i) for i in range(1,9)}<=fields['dds/STUEDTD.dspf']['PICK'] and 'PSEL9' not in text('dds/STUEDTD.dspf'))
check('cursor-native-return',all(k in text('dds/STUSCHD.dspf') for k in ['RTNCSRLOC','SFLCSRRRN','CSRLOC']))
record=dict(runId=a.run_id,scope='Static source/DDS layout and reference checks only; no IBM i compile, bind, Db2, CCSID roundtrip or 5250 execution',formalScore=None,checks=checks,passed=sum(x['passed'] for x in checks),total=len(checks),sourceHashes={p.relative_to(B).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['src','copy','dds','c','tools'] for p in sorted((B/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts})
dest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(dict(passed=record['passed'],total=record['total'],failed=[x['id'] for x in checks if not x['passed']]),ensure_ascii=False));raise SystemExit(0 if record['passed']==record['total'] else 1)
