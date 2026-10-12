"""Generate executable UI members and UI metadata procedures; no spec-eval access."""
from pathlib import Path
import runpy,json
B=Path(__file__).resolve().parents[1]
def put(p,s):
 (B/p).parent.mkdir(parents=True,exist_ok=True)
 (B/p).write_text(s.strip()+'\n',encoding='utf8')
dds=(B/'tools/generate_dds.py').read_text('utf8')
dds=dds.replace("keyword('DSPSIZ(27 132 *DS4)'),keyword('INDARA')","keyword('DSPSIZ(27 132 *DS4)')")
dds=dds.replace("('Era / year / month / day',9)","('Birth (era Y M D)',9)")
dds=dds.replace("edit+=field('OCCUPANCY',95,23,3,'O')","edit+=field('EFIELD2',2,22,119,dtype='A')+field('OCCUPANCY',95,23,3,'O')")
dds=dds.replace("edit=aux(edit)","edit+=field('EFIELD3',2,22,119,dtype='A')\nedit=aux(edit)")
dds=dds.replace('F14=Reload','F14=Reload F20=Errors')
(B/'tools/generate_dds.py').write_text(dds,'utf8');runpy.run_path(str(B/'tools/generate_dds.py'))
names={'studentNo':'学籍番号','studentName':'氏名','studentNameKana':'氏名カナ','birthDate':'生年月日','genderCode':'性別','postalCode':'郵便番号','prefectureCode':'都道府県','addressLine1':'住所1','addressLine2':'住所2','phoneNumber':'電話番号','emailAddress':'メールアドレス','admissionDate':'入学日','enrollmentStatusCode':'在籍状態','enrollmentEndDate':'在籍終了日','classId':'クラス','emergencyContactName':'緊急連絡先氏名','relationshipCode':'続柄','emergencyPhoneNumber':'緊急連絡先電話番号','remarks':'備考','schoolYear':'年度','gradeCode':'学年','reason':'理由','admissionFrom':'入学日開始','admissionTo':'入学日終了','unassignedOnly':'未所属のみ'}
fields=json.loads((B/'metadata/field-map.json').read_text('utf8'))
extra='''
dcl-proc FieldName;
 dcl-pi *n varucs2(64) ccsid(1200);property varchar(32) const;end-pi;
 select;
'''
for k,v in names.items():extra+=f" when property='{k}';return %ucs2('{v}');\n"
extra+=" other;return %ucs2(property);endsl;\nend-proc;\n"
extra+='dcl-proc FieldMax;\n dcl-pi *n varchar(4);property varchar(32) const;end-pi;\n select;\n'
for f in fields:
 if f['rawMax']:extra+=f" when property='{f['property']}';return '{f['rawMax']}';\n"
extra+=" when property='reason';return '60';other;return '320';endsl;\nend-proc;\n"
extra+='''
dcl-proc ErrorList;
 dcl-pi *n;result likeds(Result_t) const;end-pi;
 dcl-s page int(10) inz(1);dcl-s i int(10);dcl-s item int(10);
 dcl-s text varucs2(320) ccsid(1200);dcl-s rows char(122) dim(10);
 dcl-ds one likeds(Result_t);
 dou *off;
  clear rows;
  for i=1 to 10;item=(page-1)*10+i;
   if item<=result.errorCount;
    clear one;one.kind=RK_VALIDATION;one.errorCount=1;
    one.fieldErrors(1)=result.fieldErrors(item);
    text=FieldName(one.fieldErrors(1).field)+%ucs2(': ')+UiMessage(one);
    rows(i)=Render(text:122);
   endif;
  endfor;
  C01=rows(1);C02=rows(2);C03=rows(3);C04=rows(4);C05=rows(5);
  C06=rows(6);C07=rows(7);C08=rows(8);C09=rows(9);C10=rows(10);
  CTITLE='All field errors (F8 with 1..10 opens full message)';
  CTOTAL=%char(result.errorCount)+' errors, page '+%char(page);CREASON='';CSEL='';
  *in03=*off;*in08=*off;*in10=*off;*in12=*off;*in25=*off;*in26=*off;
  exfmt CNFRM;
  if *in03 or *in12 or *in10;return;endif;
  if *in25 and page*10<result.errorCount;page+=1;endif;
  if *in26 and page>1;page-=1;endif;
  if *in08;
   monitor;item=(page-1)*10+%int(%trim(CSEL));on-error;iter;endmon;
   if item>0 and item<=result.errorCount;
    clear one;one.kind=RK_VALIDATION;one.errorCount=1;
    one.fieldErrors(1)=result.fieldErrors(item);text=UiMessage(one);
    LongEdit(text:*on);
   endif;
  endif;
 enddo;
end-proc;
'''
put('copy/STUFIELDUI.rpgleinc',extra)
decl=(B/'copy/STUDSPDECL.rpgleinc').read_text('utf8')
if 'dcl-pr ErrorList' not in decl:decl+='\ndcl-pr ErrorList;result likeds(Result_t) const;end-pr;\n'
put('copy/STUDSPDECL.rpgleinc',decl)
put('src/STUSRCH.sqlrpgle',r'''
**free
ctl-opt dftactgrp(*no) option(*srcstmt:*nodebugio) ccsid(*ucs2:1200);
dcl-f STUSCHD workstn sfile(SFLROW:rrn);
/copy '../copy/STUTYPES.rpgleinc'
/copy '../copy/STUPROTO.rpgleinc'
/copy '../copy/STUDSPDECL.rpgleinc'
dcl-pr ShowRows;end-pr;
dcl-pr ReadSearch;end-pr;
dcl-pr DrawSearch;end-pr;
dcl-pr ReadQ;index int(10) const;value varchar(128) const;end-pr;
dcl-pr SelectRow;end-pr;
dcl-pr FullRow;row likeds(StudentRecord_t) const;end-pr;
dcl-s rrn int(5);dcl-s block int(10) inz(0);dcl-s idx int(10);
dcl-s prior char(128) dim(12);dcl-ds raw likeds(SearchRaw_t);
dcl-ds context likeds(SearchContext_t);dcl-ds page likeds(SearchPage_t);
dcl-ds startup likeds(Result_t);dcl-s principal varchar(128);dcl-s role int(10);
dcl-s id int(20);dcl-s viewOnly ind;dcl-s notice char(128);
dcl-s text varucs2(320) ccsid(1200);dcl-s chosen varchar(24);dcl-s choiceField int(10);
dcl-s year varchar(4);dcl-s grade varchar(2);dcl-s occupancy int(10);
dcl-s capacity int(10);dcl-s capacityInd int(5);
exec sql SET OPTION COMMIT=*CS,CLOSQLCSR=*ENDMOD,DATFMT=*ISO;
StStartup(startup);
if startup.kind<>0;notice=Render(UiMessage(startup):128);dsply notice;*inlr=*on;return;endif;
StAuthorize('READ':principal:role:startup);
if startup.kind<>0;notice=Render(UiMessage(startup):128);dsply notice;*inlr=*on;return;endif;
StNewId(context.instanceId);raw.selected(1)=*on;raw.selected(2)=*on;
DrawSearch();ShowRows();
dou *off;
 write COND;
 *in03=*off;*in04=*off;*in05=*off;*in06=*off;*in08=*off;*in09=*off;
 *in10=*off;*in14=*off;*in16=*off;*in17=*off;*in18=*off;*in19=*off;
 *in20=*off;exfmt SFLCTL;
 if *in03;leave;endif;
 ReadSearch();if uiError;QMSG='Invalid conversion: original values retained; F8 explicit Unicode';iter;endif;
 if *in05;
  clear raw;clear context;clear page;StNewId(context.instanceId);
  context.page=1;context.pageSize=20;context.sortKey='studentNo';context.direction='asc';
  raw.selected(1)=*on;raw.selected(2)=*on;block=0;QMSG='';DrawSearch();ShowRows();iter;
 endif;
 if *in06;
  id=0;viewOnly=*off;notice='';StEdit(id:viewOnly:notice);QMSG=notice;
  if context.hasApplied;StSearchStudents(raw:context:*off:page);block=0;ShowRows();endif;
  iter;
 endif;
 if *in08;
  monitor;idx=%int(%trim(QFIELD));on-error;idx=0;endmon;
  if idx>=1 and idx<=12;LongEdit(raw.values(idx):*off);DrawSearch();endif;iter;
 endif;
 if *in20;ErrorList(page.result);iter;endif;
 if *in04;
  monitor;choiceField=%int(%trim(QFIELD));on-error;choiceField=0;endmon;
  year=%char(raw.values(4));grade=%char(raw.values(5));idx=0;
  monitor;idx=%int(year);on-error;idx=0;endmon;
  select;
  when choiceField=4;
   chosen=Choice('YEAR':year:0:'':*off);
   if chosen<>year;raw.values(4)=%ucs2(chosen);raw.values(6)=%ucs2('');endif;
  when choiceField=5;
   chosen=Choice('GRADE':grade:idx:'':*off);
   if chosen<>grade;raw.values(5)=%ucs2(chosen);raw.values(6)=%ucs2('');endif;
  when choiceField=6;
   chosen=Choice('CLASS':%char(raw.values(6)):idx:grade:*off);
   raw.values(6)=%ucs2(chosen);
   if chosen<>'';
    id=%int(chosen);StClassInfo(id:year:grade:occupancy:capacity:capacityInd:startup:*off);
    if startup.kind=0;raw.values(4)=%ucs2(year);raw.values(5)=%ucs2(grade);raw.values(7)=%ucs2('0');endif;
   endif;
  when choiceField=9;raw.values(9)=%ucs2(Choice('PREFECTURE':%char(raw.values(9)):0:'':*off));
  endsl;
  DrawSearch();iter;
 endif;
 if *in09 and page.rowCount>0;
  block+=10;if block>=page.rowCount;block=0;endif;ShowRows();iter;
 endif;
 if *in10;
  SelectRow();if context.hasApplied;StSearchStudents(raw:context:*off:page);ShowRows();endif;iter;
 endif;
 if *in14;SelectRow();iter;endif;
 if *in16;context.page=1;
 elseif *in17;context.page=%max(1:%div(page.total+context.pageSize-1:context.pageSize));
 elseif *in18;context.page=%max(1:context.page-1);
 elseif *in19;context.page+=1;
 else;
  monitor;context.pageSize=%int(%trim(QSIZE));on-error;context.pageSize=0;endmon;
  context.sortKey=%trim(QSORT);context.direction=%trim(QDIR);context.page=1;
 endif;
 StSearchStudents(raw:context:not(*in16 or *in17 or *in18 or *in19):page);
 block=0;QMSG=Render(UiMessage(page.result):128);ShowRows();
enddo;
*inlr=*on;return;
dcl-proc ReadQ;
 dcl-pi *n;index int(10) const;value varchar(128) const;end-pi;
 dcl-s next varucs2(320) ccsid(1200);
 if value<>prior(index);
  next=ReadBuffer(%trimr(value));if not uiError;raw.values(index)=next;endif;
 endif;
end-proc;
dcl-proc ReadSearch;
 uiError=*off;
 ReadQ(1:QSTUNO);ReadQ(2:QNAME);ReadQ(3:QKANA);ReadQ(4:QYEAR);ReadQ(5:QGRADE);
 ReadQ(6:QCLASS);ReadQ(7:QUNASS);ReadQ(9:QPREF);ReadQ(10:QPHONE);
 ReadQ(11:QADMFROM);ReadQ(12:QADMTO);
 raw.selected(1)=QST01='1';raw.selected(2)=QST02='1';
 raw.selected(3)=QST03='1';raw.selected(4)=QST04='1';
 if raw.values(7)=%ucs2('1');raw.values(4)=%ucs2('');raw.values(5)=%ucs2('');raw.values(6)=%ucs2('');endif;
end-proc;
dcl-proc DrawSearch;
 QSTUNO=Render(raw.values(1):30);prior(1)=QSTUNO;
 QNAME=Render(raw.values(2):40);prior(2)=QNAME;QKANA=Render(raw.values(3):72);prior(3)=QKANA;
 QYEAR=Render(raw.values(4):4);prior(4)=QYEAR;QGRADE=Render(raw.values(5):2);prior(5)=QGRADE;
 QCLASS=Render(raw.values(6):19);prior(6)=QCLASS;QUNASS=Render(raw.values(7):1);prior(7)=QUNASS;
 QPREF=Render(raw.values(9):2);prior(9)=QPREF;QPHONE=Render(raw.values(10):40);prior(10)=QPHONE;
 QADMFROM=Render(raw.values(11):10);prior(11)=QADMFROM;QADMTO=Render(raw.values(12):10);prior(12)=QADMTO;
 QST01='0';QST02='0';QST03='0';QST04='0';
 if raw.selected(1);QST01='1';endif;if raw.selected(2);QST02='1';endif;
 if raw.selected(3);QST03='1';endif;if raw.selected(4);QST04='1';endif;
 QSIZE=%char(context.pageSize);QSORT=context.sortKey;QDIR=context.direction;
end-proc;
dcl-proc ShowRows;
 dcl-s i int(10);dcl-s row int(10);dcl-s era varchar(10);
 dcl-s y varucs2(8) ccsid(1200);dcl-s m varucs2(4) ccsid(1200);dcl-s d varucs2(4) ccsid(1200);
 dcl-s birth varucs2(80) ccsid(1200);
 *in90=*off;*in91=*on;*in92=*on;write SFLCTL;*in92=*off;
 for i=1 to %min(10:page.rowCount-block);
  row=block+i;rrn=i;SOPT='';SROWID=%char(page.rows(row).studentId);
  SNO=page.rows(row).work.studentNo;SNAME=Render(page.rows(row).work.studentName:20);
  StFormatBirthDate(page.rows(row).work.birthDate:era:y:m:d:birth);SBIRTH=Render(birth:26);
  SYEARGR='';SCLASS='';
  if page.rows(row).work.classIdInd=0;
   SYEARGR=Render(%ucs2(%char(page.rows(row).schoolYear)+' ')+page.rows(row).gradeName:10);
   SCLASS=Render(%ucs2(page.rows(row).classCode+' ')+page.rows(row).className:30);
  endif;
  SSTATUS=Render(page.rows(row).enrollmentName:18);write SFLROW;
 endfor;
 *in90=page.rowCount>0;RESULT_CNT='Total '+%char(page.total)+' SQL page '+%char(context.page)+' block '+%char(%div(block:10)+1);
 SEARCH_AT=%char(page.searchedAt:*iso);
end-proc;
dcl-proc SelectRow;
 dcl-s row int(10);
 readc SFLROW;
 dow not %eof(STUSCHD);
  row=block+rrn;
  if row>=1 and row<=page.rowCount;
   if SOPT='9';FullRow(page.rows(row));
   elseif SOPT='2' or SOPT='5';
    id=page.rows(row).studentId;viewOnly=SOPT='5';notice='';StEdit(id:viewOnly:notice);QMSG=notice;
   endif;
  endif;
  readc SFLROW;
 enddo;
end-proc;
dcl-proc FullRow;
 dcl-pi *n;row likeds(StudentRecord_t) const;end-pi;
 dcl-s lines varucs2(320) ccsid(1200) dim(11);dcl-s i int(10);dcl-s selected int(10);
 dcl-s era varchar(10);dcl-s y varucs2(8) ccsid(1200);dcl-s m varucs2(4) ccsid(1200);dcl-s d varucs2(4) ccsid(1200);dcl-s birth varucs2(80) ccsid(1200);
 StFormatBirthDate(row.work.birthDate:era:y:m:d:birth);
 lines(1)=%ucs2(row.work.studentNo);lines(2)=row.work.studentName;
 lines(3)=row.work.studentNameKana;lines(4)=birth;lines(5)=%ucs2(%char(row.schoolYear));
 lines(6)=row.gradeName;lines(7)=%ucs2(row.classCode+' ')+row.className;
 lines(8)=row.enrollmentName;lines(9)=%ucs2(%char(row.work.admissionDate:*iso));
 lines(10)=row.prefectureName;lines(11)=%ucs2(%char(row.updatedAt+%hours(9):*iso));
 for i=1 to 11;text=%ucs2(%char(i)+': ')+lines(i);LongEdit(text:*on);endfor;
end-proc;
/copy '../copy/STUDSP.rpgleinc'
/copy '../copy/STUFIELDUI.rpgleinc'
''')
put('src/STUEDIT.sqlrpgle',r'''
**free
ctl-opt dftactgrp(*no) option(*srcstmt:*nodebugio) ccsid(*ucs2:1200);
dcl-f STUEDTD workstn;
/copy '../copy/STUTYPES.rpgleinc'
/copy '../copy/STUPROTO.rpgleinc'
/copy '../copy/STUDSPDECL.rpgleinc'
dcl-pi *n;studentId int(20);readOnly ind;notice char(128);end-pi;
dcl-pr LoadForm;end-pr;dcl-pr DrawForm;end-pr;dcl-pr ReadForm;end-pr;
dcl-pr ReadEdited;index int(10) const;value varchar(128) const;end-pr;
dcl-pr Dirty ind;end-pr;dcl-pr EditFull;field int(10) const;end-pr;
dcl-pr SaveForm;end-pr;dcl-pr Pick;field int(10) const;end-pr;
dcl-ds raw likeds(StudentRaw_t);dcl-ds original likeds(StudentRaw_t);
dcl-ds hints likeds(StudentHints_t);dcl-ds oldHints likeds(StudentHints_t);
dcl-ds rec likeds(StudentRecord_t);dcl-ds work likeds(StudentWork_t);dcl-ds result likeds(Result_t);
dcl-s principal varchar(128);dcl-s role int(10);dcl-s era varchar(10);dcl-s wareki varucs2(80) ccsid(1200);
dcl-s utc timestamp;dcl-s day date;dcl-s prior char(128) dim(19);
dcl-s priorEra char(10);dcl-s priorYear char(8);dcl-s priorMonth char(4);dcl-s priorDay char(4);
dcl-s priorHintYear char(4);dcl-s priorHintGrade char(2);dcl-s priorReason char(122);
dcl-s panel int(10) inz(1);dcl-s field int(10);dcl-s protected ind;
dcl-s committed ind;dcl-s closed ind;dcl-s reason varucs2(120) ccsid(1200);
dcl-s occupancy int(10);dcl-s capacity int(10);dcl-s capacityInd int(5);
exec sql SET OPTION COMMIT=*CS,CLOSQLCSR=*ENDMOD,DATFMT=*ISO;
StNewId(hints.instanceId);StAuthorize('READ':principal:role:result);
if result.kind<>0;notice=Render(UiMessage(result):128);*inlr=*on;return;endif;
protected=readOnly or role=1;LoadForm();
if result.kind<>0;notice=Render(UiMessage(result):128);*inlr=*on;return;endif;
dou closed;
 DrawForm();*in75=protected;*in76=studentId>0;
 *in03=*off;*in04=*off;*in05=*off;*in08=*off;*in09=*off;
 *in10=*off;*in12=*off;*in14=*off;*in20=*off;*in23=*off;
 select;when panel=1;exfmt EDBASE;when panel=2;exfmt EDENROLL;other;exfmt EDNOTE;endsl;
 ReadForm();if uiError;result.kind=RK_VALIDATION;result.messageId='E-COM-003';iter;endif;
 if *in03 or *in12;
  if not Dirty() or Question('W-STU-104':reason:*off:result);closed=*on;endif;iter;
 endif;
 if *in09;panel=%rem(panel:3)+1;iter;endif;
 if *in20;ErrorList(result);iter;endif;
 if *in05;
  if not Dirty() or Question('W-STU-104':reason:*off:result);raw=original;hints.schoolYear=oldHints.schoolYear;hints.gradeCode=oldHints.gradeCode;hints.reason=%ucs2('');clear result;endif;
  iter;
 endif;
 if *in14;
  if not Dirty() or Question('W-STU-104':reason:*off:result);LoadForm();endif;iter;
 endif;
 field=0;monitor;
  select;when panel=1;field=%int(%trim(EFIELD));when panel=2;field=%int(%trim(EFIELD2));other;field=%int(%trim(EFIELD3));endsl;
 on-error;field=0;endmon;
 if *in08;EditFull(field);iter;endif;
 if *in04 and not protected;Pick(field);iter;endif;
 if *in10 and not protected;SaveForm();iter;endif;
 if *in23 and not protected and studentId>0;
  clear result;result.messageId='W-STU-103';
  if Question('W-STU-103':hints.reason:*on:result);
   StDeleteStudent(studentId:rec.rowVersion:hints.reason:result);
   if result.kind=RK_SAVED;notice=Render(UiMessage(result):128);closed=*on;
   elseif result.kind=RK_VALIDATION;ErrorList(result);endif;
  endif;
 endif;
enddo;
*inlr=*on;return;
dcl-proc LoadForm;
 clear result;
 if studentId>0;
  StLoadStudent(studentId:rec:result);if result.kind<>0;return;endif;
  /copy '../copy/STUTORAW.rpgleinc'
  hints.schoolYear='';hints.gradeCode='';
  if rec.work.classIdInd=0;hints.schoolYear=%char(rec.schoolYear);hints.gradeCode=rec.gradeCode;endif;
 else;
  clear raw;clear rec;StClock(utc:day);
  raw.values(5)=%ucs2('0');raw.values(12)=%ucs2(%char(day:*iso));raw.values(13)=%ucs2('01');
 endif;
 hints.reason=%ucs2('');original=raw;oldHints=hints;
end-proc;
dcl-proc DrawForm;
 /copy '../copy/STUEDITOUT.rpgleinc'
 EBERA=raw.birthEra;priorEra=EBERA;EBYEAR=Render(raw.birthYear:8);priorYear=EBYEAR;
 EBMONTH=Render(raw.birthMonth:4);priorMonth=EBMONTH;EBDAY=Render(raw.birthDay:4);priorDay=EBDAY;
 EYEAR=hints.schoolYear;priorHintYear=EYEAR;EGRADE=hints.gradeCode;priorHintGrade=EGRADE;
 EREASON=Render(hints.reason:122);priorReason=EREASON;ESTUID=%char(studentId);
 EVERSION=%char(rec.rowVersion);UPDATEDAT=%char(rec.updatedAt+%hours(9):*iso);
 UPDATEDBY=Render(rec.updatedBy:90);EMSG1=Render(UiMessage(result):128);EMSG2=EMSG1;EMSG3=EMSG1;
 OCCUPANCY='';
 if %len(raw.values(15))>0;
  monitor;occupancy=%int(%char(raw.values(15)));on-error;return;endmon;
  StClassInfo(occupancy:EYEAR:EGRADE:occupancy:capacity:capacityInd:result:*on);
  if result.kind=0;
   OCCUPANCY='Current occupancy '+%char(occupancy);
   if capacityInd=0;OCCUPANCY+=' / '+%char(capacity);else;OCCUPANCY+=' / unlimited';endif;
  endif;
 endif;
end-proc;
dcl-proc ReadEdited;
 dcl-pi *n;index int(10) const;value varchar(128) const;end-pi;
 dcl-s text varucs2(320) ccsid(1200);
 if value<>prior(index);text=ReadBuffer(%trimr(value));if not uiError;raw.values(index)=text;endif;endif;
end-proc;
dcl-proc ReadForm;
 dcl-s text varucs2(320) ccsid(1200);
 uiError=*off;if protected;return;endif;
 /copy '../copy/STUEDITIO.rpgleinc'
 if EBERA<>priorEra;raw.birthEra=%trim(EBERA);endif;
 if EBYEAR<>priorYear;text=ReadBuffer(%trimr(EBYEAR));if not uiError;raw.birthYear=text;endif;endif;
 if EBMONTH<>priorMonth;text=ReadBuffer(%trimr(EBMONTH));if not uiError;raw.birthMonth=text;endif;endif;
 if EBDAY<>priorDay;text=ReadBuffer(%trimr(EBDAY));if not uiError;raw.birthDay=text;endif;endif;
 if EYEAR<>priorHintYear or EGRADE<>priorHintGrade;
  hints.schoolYear=%trim(EYEAR);hints.gradeCode=%trim(EGRADE);raw.values(15)=%ucs2('');
 endif;
 if EREASON<>priorReason;text=ReadBuffer(%trimr(EREASON));if not uiError and %len(text)<=120;hints.reason=text;endif;endif;
end-proc;
dcl-proc Dirty;
 dcl-pi *n ind;end-pi;dcl-s i int(10);
 for i=1 to 19;if raw.values(i)<>original.values(i);return *on;endif;endfor;
 return raw.birthEra<>original.birthEra or raw.birthYear<>original.birthYear or raw.birthMonth<>original.birthMonth or raw.birthDay<>original.birthDay or hints.schoolYear<>oldHints.schoolYear or hints.gradeCode<>oldHints.gradeCode;
end-proc;
dcl-proc EditFull;
 dcl-pi *n;field int(10) const;end-pi;dcl-s text varucs2(320) ccsid(1200);
 if field>=1 and field<=19 and field<>4;
  LongEdit(raw.values(field):protected or (field=1 and studentId>0));
 elseif field=20;text=%ucs2(raw.birthEra);if LongEdit(text:protected);raw.birthEra=%char(text);endif;
 elseif field=21;text=raw.birthYear;if LongEdit(text:protected);if %len(text)<=8;raw.birthYear=text;endif;endif;
 elseif field=22;text=raw.birthMonth;if LongEdit(text:protected);if %len(text)<=4;raw.birthMonth=text;endif;endif;
 elseif field=23;text=raw.birthDay;if LongEdit(text:protected);if %len(text)<=4;raw.birthDay=text;endif;endif;
 elseif field=24;text=hints.reason;if LongEdit(text:protected);if %len(text)<=120;hints.reason=text;endif;endif;
 endif;
end-proc;
dcl-proc SaveForm;
 dcl-s token char(36);
 StClock(utc:day);StNormalize(raw:work:day:result);
 if result.kind=0;StValidate(work:result);endif;
 if result.kind<>0;ErrorList(result);return;endif;
 dou *off;
  StSaveStudent(work:hints:studentId:rec.rowVersion:token:result);
  if result.kind=RK_CONFIRM;
   if not Question(result.messageId:hints.reason:*on:result);return;endif;
   token=result.token;iter;
  endif;
  if result.kind=RK_SAVED;notice=Render(UiMessage(result:work.studentNo):128);closed=*on;
  elseif result.kind=RK_NOCHANGE;notice=Render(UiMessage(result:work.studentNo):128);closed=*on;
  elseif result.kind=RK_VALIDATION;ErrorList(result);
  elseif result.kind=RK_CONFLICT;
   if Question('E-STU-105':reason:*off:result);LoadForm();endif;
  endif;
  leave;
 enddo;
end-proc;
dcl-proc Pick;
 dcl-pi *n;field int(10) const;end-pi;dcl-s kind varchar(24);dcl-s selected varchar(24);dcl-s year int(10);dcl-s id int(20);
 monitor;year=%int(hints.schoolYear);on-error;year=0;endmon;
 select;when field=5;kind='GENDER';when field=7;kind='PREFECTURE';when field=13;kind='ENROLLMENT_STATUS';when field=15;kind='CLASS';when field=17;kind='RELATIONSHIP';when field=25;kind='YEAR';when field=26;kind='GRADE';other;return;endsl;
 if field=25;
  selected=Choice(kind:hints.schoolYear:0:'':*on);if selected<>hints.schoolYear;hints.schoolYear=selected;raw.values(15)=%ucs2('');endif;
 elseif field=26;
  selected=Choice(kind:hints.gradeCode:year:'':*on);if selected<>hints.gradeCode;hints.gradeCode=selected;raw.values(15)=%ucs2('');endif;
 else;
  selected=Choice(kind:%char(raw.values(field)):year:hints.gradeCode:*on);raw.values(field)=%ucs2(selected);
  if field=15 and selected<>'';id=%int(selected);StClassInfo(id:hints.schoolYear:hints.gradeCode:occupancy:capacity:capacityInd:result:*on);endif;
 endif;
end-proc;
/copy '../copy/STUDSP.rpgleinc'
/copy '../copy/STUFIELDUI.rpgleinc'
''')
print('Generated STUSRCH / STUEDIT and field/error UI procedures')
