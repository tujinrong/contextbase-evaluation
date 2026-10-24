# Historical migration preserved for audit; current V2 contracts must not be downgraded.
raise SystemExit("Historical one-time migrator is disabled. Use the current checked-in production sources.")
from pathlib import Path
import re
B=Path(__file__).resolve().parents[1]
p=B/'copy/STUDSP.rpgleinc';s=p.read_text('utf8')
s=s.replace("if rc<>0;out='[Unicode/full value: F8]';endif;", "if rc<>0;out='[Unicode/full value: F8]';elseif n<128;%subst(out:n+1)=*blanks;endif;")
s=s.replace('dcl-ds check likeds(Result_t);','dcl-ds check likeds(Result_t);dcl-s full varucs2(320) ccsid(1200) dim(20);dcl-s selected int(10);')
s=s.replace('rows(i)=Render(text:122);','rows(i)=Render(text:122);full(item)=text;')
s=s.replace('CTOTAL=\'Total candidates ',"CMSG='F8: 0=full reason, 1..10=full candidate';CTOTAL='Total candidates ")
s=s.replace('*in03=*off;*in10=*off;*in12=*off;*in25=*off;*in26=*off;exfmt CNFRM;',
 '*in03=*off;*in08=*off;*in10=*off;*in12=*off;*in25=*off;*in26=*off;exfmt CNFRM;')
anchor='  if CREASON<>priorReason;'
s=s.replace(anchor,'''  if *in08;
   monitor;selected=%int(%trim(CSEL));on-error;selected=0;endmon;
   if selected=0;
    changedReason=reason;if LongEdit(changedReason:*off) and %len(changedReason)<=120;reason=changedReason;CREASON=Render(reason:122);priorReason=CREASON;endif;
   elseif selected>=1 and selected<=10 and (page-1)*10+selected<=%min(result.candidateCount:20);
    text=full((page-1)*10+selected);LongEdit(text:*on);
   endif;
   iter;
  endif;
'''+anchor)
p.write_text(s,'utf8')
p=B/'src/STUSRCH.sqlrpgle';s=p.read_text('utf8')
s=s.replace('dcl-s capacity int(10);','dcl-s askedSize int(10);dcl-s askedSort varchar(16);dcl-s askedDirection varchar(4);dcl-s optionsChanged ind;dcl-s rowAction ind;\ndcl-s capacity int(10);')
s=s.replace('ReadSearch();DrawSearch();if uiError;',
 'monitor;askedSize=%int(%trim(QSIZE));on-error;askedSize=0;endmon;askedSort=%trim(QSORT);askedDirection=%trim(QDIR);\n optionsChanged=askedSize<>context.pageSize or askedSort<>context.sortKey or askedDirection<>context.direction;\n ReadSearch();if not uiError;DrawSearch();endif;if uiError;')
s=s.replace("id=0;viewOnly=*off;notice='';StEdit", "StAuthorize('SAVE':principal:role:startup);if startup.kind<>0;QMSG=Render(UiMessage(startup):128);iter;endif;\n  id=0;viewOnly=*off;notice='';StEdit")
s=s.replace("SelectRow();if notice<>'';", "SelectRow();if rowAction;")
s=s.replace('  monitor;context.pageSize=%int(%trim(QSIZE));on-error;context.pageSize=0;endmon;\n  context.sortKey=%trim(QSORT);context.direction=%trim(QDIR);context.page=1;',
 '  context.pageSize=askedSize;context.sortKey=askedSort;context.direction=askedDirection;context.page=1;')
s=s.replace(' StSearchStudents(raw:context:not(*in07', ' if optionsChanged and context.hasApplied;context.page=1;context.pageSize=askedSize;context.sortKey=askedSort;context.direction=askedDirection;endif;\n StSearchStudents(raw:context:not(*in07')
s=s.replace('dcl-proc SelectRow;\n dcl-s row int(10);','dcl-proc SelectRow;\n dcl-s row int(10);\n rowAction=*off;')
s=s.replace("if SOPT='9';FullRow(page.rows(row));", "if SOPT='9';rowAction=*on;FullRow(page.rows(row));")
s=s.replace("elseif SOPT='2' or SOPT='5';", "elseif SOPT='2' or SOPT='5';rowAction=*on;")
p.write_text(s,'utf8')
p=B/'src/STUEDIT.sqlrpgle';s=p.read_text('utf8')
s=s.replace('dcl-s occupancy int(10);','dcl-s deleteReason varucs2(120) ccsid(1200);\ndcl-s lookupValues varchar(24) dim(20);dcl-s lookupLabels varucs2(320) ccsid(1200) dim(20);dcl-s lookupCount int(10);dcl-ds lookupResult likeds(Result_t);\ndcl-s occupancy int(10);')
s=s.replace("protected=readOnly or role=1;LoadForm();", "if studentId=0;StAuthorize('SAVE':principal:role:result);if result.kind<>0;notice=Render(UiMessage(result):128);*inlr=*on;return;endif;endif;\nprotected=readOnly or role=1;LoadForm();")
s=s.replace(' DrawForm();*in75=protected;', ' if not uiError;DrawForm();endif;*in75=protected;')
s=s.replace("if Question('W-STU-103':hints.reason:*on:result);\n   StDeleteStudent(studentId:rec.rowVersion:hints.reason:result);", "StAuthorize('DELETE':principal:role:result);if result.kind<>0;iter;endif;\n  if Question('W-STU-103':deleteReason:*on:result);\n   StDeleteStudent(studentId:rec.rowVersion:deleteReason:result);")
s=s.replace('hints.reason=%ucs2(\'\');original=raw;oldHints=hints;',
 "hints.reason=%ucs2('');original=raw;oldHints=hints;\n StLookupChoice('CLASS':1:0:'':lookupValues:lookupLabels:lookupCount:lookupResult);\n if lookupResult.kind<>0;result=lookupResult;elseif lookupCount=0;result.messageId='W-STU-108';endif;")
# Result messages remain available across class info rendering and conversion failures.
p.write_text(s,'utf8')
p=B/'src/STUSVC.sqlrpgle';s=p.read_text('utf8')
s=s.replace("when %subst(state:1:2)='40' or state='57033';", "when %subst(state:1:2)='40';")
s=s.replace("result.token=confirmations(slot).token;result.kind=RK_CONFIRM;result.messageId='W-STU-101';", "result.token=confirmations(slot).token;result.kind=RK_CONFIRM;result.messageId='W-STU-101';if confirmation<>'';result.messageId='W-STU-102';endif;")
# Use local host DS instead of indexed nested SQL host targets.
s=s.replace('dcl-s id int(20);dcl-s version int(20);dcl-s piece', 'dcl-ds candidate likeds(StudentRecord_t);\n dcl-s id int(20);dcl-s version int(20);dcl-s piece')
s=s.replace(':result.candidates(result.candidateCount).work.', ':candidate.work.')
s=s.replace('if SQLCOD<>0;SqlFailure(result:SQLSTT);leave;endif;\n  endif;\n enddo;\n exec sql CLOSE dup;', 'if SQLCOD<>0;SqlFailure(result:SQLSTT);leave;endif;\n   result.candidates(result.candidateCount)=candidate;\n  endif;\n enddo;\n exec sql CLOSE dup;')
# Capacity procedure runs only behind the update gate, once final eligibility is known.
old='''exec sql SELECT COUNT(*) INTO :occupancy FROM STUDAPP.M_STUDENT
    WHERE class_id=:work.classId AND is_deleted=0 AND enrollment_status_code IN ('01','02') AND student_id<>:studentId;
   if SQLCOD<>0;SqlFailure(result:SQLSTT);return;endif;
   if cls.capacityInd=0 and occupancy+1>cls.capacity;StError(result:'classId':'E-STU-102');endif;'''
s=s.replace(old,'StCheckCapacity(work.classId:studentId:cls.capacity:cls.capacityInd:result);')
proto='''
dcl-pr StCheckCapacity;classId int(20) const;excludeId int(20) const;capacity int(10) const;capacityInd int(5) const;result likeds(Result_t);end-pr;
'''
s=s.replace('dcl-pr NormalizeSearch;',proto+'dcl-pr NormalizeSearch;')
i=s.index('dcl-proc StFindDuplicates export;')
s=s[:i]+'''
dcl-proc StCheckCapacity export;
 dcl-pi *n;classId int(20) const;excludeId int(20) const;capacity int(10) const;capacityInd int(5) const;result likeds(Result_t);end-pi;
 dcl-s occupancy int(10);
 exec sql SELECT COUNT(*) INTO :occupancy FROM STUDAPP.M_STUDENT
  WHERE class_id=:classId AND is_deleted=0 AND enrollment_status_code IN ('01','02') AND student_id<>:excludeId;
 if SQLCOD<>0;SqlFailure(result:SQLSTT);return;endif;
 if capacityInd=0 and occupancy+1>capacity;StError(result:'classId':'E-STU-102');endif;
end-proc;
'''+s[i:]
s+='''
dcl-proc StLookupCodes export;
 dcl-pi *n;kind varchar(24) const;page int(10) const;values varchar(24) dim(20);labels varucs2(320) ccsid(1200) dim(20);count int(10);result likeds(Result_t);end-pi;
 StLookupChoice(kind:page:0:'':values:labels:count:result);
end-proc;
dcl-proc StLookupClasses export;
 dcl-pi *n;page int(10) const;year int(10) const;grade varchar(2) const;values varchar(24) dim(20);labels varucs2(320) ccsid(1200) dim(20);count int(10);result likeds(Result_t);end-pi;
 StLookupChoice('CLASS':page:year:grade:values:labels:count:result);
end-proc;
dcl-proc StEndWork export;
 dcl-pi *n;commit ind const;result likeds(Result_t);end-pi;
 if commit;exec sql COMMIT;if SQLCOD<>0;result.kind=RK_UNKNOWN;result.messageId='E-COM-004';exec sql ROLLBACK;endif;
 else;exec sql ROLLBACK;endif;
end-proc;
'''
p.write_text(s,'utf8')
# Route transaction statements through the one public end-work implementation.
for name in ['src/STUSVC.sqlrpgle','src/STUMASTER.rpgleinc']:
 p=B/name;s=p.read_text('utf8');parts=s.split('dcl-proc StEndWork export;',1)
 parts[0]=re.sub(r'exec sql ROLLBACK;', 'StEndWork(*off:result);',parts[0],flags=re.I)
 # Search returns page.result; its local Result_t alias must be the caller's result.
 if name.endswith('STUSVC.sqlrpgle'):
  a=parts[0].index('dcl-proc StSearchStudents export;');tail=parts[0][a:].replace('StEndWork(*off:result);','StEndWork(*off:page.result);');parts[0]=parts[0][:a]+tail
 s='dcl-proc StEndWork export;'.join(parts);p.write_text(s,'utf8')
p=B/'copy/STUPROTO.rpgleinc';s=p.read_text('utf8')
s=s.replace('/endif','''dcl-pr StEndWork;commit ind const;result likeds(Result_t);end-pr;
dcl-pr StLookupCodes;kind varchar(24) const;page int(10) const;values varchar(24) dim(20);labels varucs2(320) ccsid(1200) dim(20);count int(10);result likeds(Result_t);end-pr;
dcl-pr StLookupClasses;page int(10) const;year int(10) const;grade varchar(2) const;values varchar(24) dim(20);labels varucs2(320) ccsid(1200) dim(20);count int(10);result likeds(Result_t);end-pr;
/endif''');p.write_text(s,'utf8')
# DDS row mode uses same generic helper; class and code responsibilities are explicit.
p=B/'copy/STUDSP.rpgleinc';s=p.read_text('utf8')
s=s.replace('StLookupChoice(kind:page:year:grade:values:labels:count:result);',
 "if kind='CLASS';StLookupClasses(page:year:grade:values:labels:count:result);elseif kind='YEAR';StLookupChoice(kind:page:year:grade:values:labels:count:result);else;StLookupCodes(kind:page:values:labels:count:result);endif;")
p.write_text(s,'utf8')
# Tight typed maintenance parser: required fields, fixed limits, no implicit truncation.
p=B/'src/STUMNT.sqlrpgle';s=p.read_text('utf8')
s=s.replace(" if line=%ucs2('END');", " if line=%ucs2('END');\n  if %lookup('expectedVersion':keys)=0 or %lookup('displayOrder':keys)=0 or %lookup('isActive':keys)=0 or %lookup('validFrom':keys)=0 or %lookup('reason':keys)=0;StError(result:'input':'E-COM-003');leave;endif;\n  if kind='CLASS' and (%lookup('classId':keys)=0 or %lookup('schoolYear':keys)=0 or %lookup('gradeCode':keys)=0 or %lookup('classCode':keys)=0 or %lookup('className':keys)=0 or %lookup('validTo':keys)=0);StError(result:'input':'E-COM-003');leave;endif;\n  if kind='CODE' and (%lookup('categoryId':keys)=0 or %lookup('codeValue':keys)=0 or %lookup('codeName':keys)=0);StError(result:'input':'E-COM-003');leave;endif;")
s=s.replace(' Assign(key:value);if result.kind<>0;leave;endif;'," monitor;Assign(key:value);on-error;StError(result:key:'E-COM-003');endmon;if result.kind<>0;leave;endif;")
s=s.replace("when key='codeName';if %len(value)>48;", "when key='codeName';if %len(value)>24;")
s=s.replace("when key='gradeCode';cw.gradeCode=%char(value);", "when key='gradeCode';value=StNormalizeText(value:2:2:6:*on:key:result);cw.gradeCode=%char(value);")
s=s.replace("when key='classCode';cw.classCode=%char(value);", "when key='classCode';value=StNormalizeText(value:9:9:5:*on:key:result);cw.classCode=%char(value);")
s=s.replace("when key='categoryId';kw.categoryId=%char(value);", "when key='categoryId';if %len(value)>24;StError(result:key:'E-COM-003');else;kw.categoryId=%char(value);endif;")
s=s.replace("when key='codeValue';kw.codeValue=%char(value);", "when key='codeValue';if %len(value)>10;StError(result:key:'E-COM-003');else;kw.codeValue=%char(value);endif;")
# CONST parameter must not be mutated: normalize a local copied input value.
s=s.replace('key varchar(32) const;value varucs2(320) ccsid(1200) const;end-pi;', 'key varchar(32) const;input varucs2(320) ccsid(1200) const;end-pi;\n dcl-s value varucs2(320) ccsid(1200);value=input;')
p.write_text(s,'utf8')
# Correct documented option-39 binding directory and standard include root.
p=B/'cl/BUILD.clle';s=p.read_text('utf8').replace('QICU/QICU','QICU/QXICUAPIBD').replace('/QIBM/ProdData/OS400/ICU/include','/QIBM/include');p.write_text(s,'utf8')
# Regenerate binder from final exported procedures only, preserving stable signatures.
for name in ['STUSVC','STUCOMMON']:
 text=(B/'src'/f'{name}.sqlrpgle').read_text('utf8')
 if name=='STUSVC':text+=(B/'src/STUMASTER.rpgleinc').read_text('utf8')
 symbols=re.findall(r'dcl-proc\s+(\w+)\s+export;',text,re.I)
 (B/'binder'/f'{name}.bnd').write_text(f"STRPGMEXP PGMLVL(*CURRENT) SIGNATURE('{name}_V1')\n"+'\n'.join(f" EXPORT SYMBOL('{x.upper()}')" for x in symbols)+'\nENDPGMEXP\n','utf8')
print('Final UI/server behavior and ABI generated')
