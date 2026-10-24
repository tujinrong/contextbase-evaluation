"""Generate fixed column assignments and COPY contracts. Does not read spec-eval.
Run from this directory with Python 3.11+. Handwritten behavior lives in src/.
"""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
FIELDS = [
    ('studentNo','student_no','varchar(15)',15,15,5,True,'ESTUNO',30),
    ('studentName','student_name','varucs2(16) ccsid(1200)',8,8,0,True,'ENAME',16),
    ('studentNameKana','student_name_kana','varucs2(36) ccsid(1200)',36,18,3,True,'EKANA',72),
    ('birthDate','birth_date','date',0,0,0,True,'',0),
    ('genderCode','gender_code','varchar(1)',1,1,6,True,'EGENDER',1),
    ('postalCode','postal_code','varchar(7)',10,7,7,True,'EPOSTAL',20),
    ('prefectureCode','prefecture_code','varchar(2)',2,2,6,True,'EPREF',2),
    ('addressLine1','address_line1','varucs2(90) ccsid(1200)',45,45,0,True,'EADDR1',90),
    ('addressLine2','address_line2','varucs2(90) ccsid(1200)',45,45,0,False,'EADDR2',90),
    ('phoneNumber','phone_number','varchar(16)',20,16,8,False,'EPHONE',40),
    ('emailAddress','email_address','varchar(60)',60,60,9,False,'EEMAIL',60),
    ('admissionDate','admission_date','date',10,10,10,True,'EADMDATE',10),
    ('enrollmentStatusCode','enrollment_status_code','varchar(2)',2,2,6,True,'ESTATUS',2),
    ('enrollmentEndDate','enrollment_end_date','date',10,10,10,False,'EENDDATE',10),
    ('classId','class_id','int(20)',19,19,12,False,'ECLASS',19),
    ('emergencyContactName','emergency_contact_name','varucs2(16) ccsid(1200)',8,8,0,False,'EEMGNAME',16),
    ('relationshipCode','relationship_code','varchar(2)',2,2,6,False,'EREL',2),
    ('emergencyPhoneNumber','emergency_phone_number','varchar(16)',20,16,8,False,'EEMGPHONE',40),
    ('remarks','remarks','varucs2(240) ccsid(1200)',120,120,1,False,'EREMARKS',90),
]
def write(path, content):
    target=BASE/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(content.rstrip()+'\n',encoding='utf-8')

types=r'''// STUTYPES V1: SQL bigints are signed 64bit; UTF16 regions are 2N.
/if not defined(STUTYPES_DEFINED)
/define STUTYPES_DEFINED
 dcl-c RK_SAVED 1 ;
 dcl-c RK_NOCHANGE 2 ;
 dcl-c RK_VALIDATION 3 ;
 dcl-c RK_FORBIDDEN 4 ;
 dcl-c RK_NOTFOUND 5 ;
 dcl-c RK_CONFLICT 6 ;
 dcl-c RK_CONFIRM 7 ;
 dcl-c RK_SYSTEM 8 ;
 dcl-c RK_UNKNOWN 9 ;
 dcl-c RK_LIMIT 10 ;
 dcl-ds FieldError_t qualified template ;
 field varchar( 32 ) ;
 messageId char( 16 ) ;
 end-ds ;
 dcl-ds StudentRaw_t qualified template ;
 values varucs2( 320 ) ccsid( 1200 ) dim( 19 ) ;
 birthEra varchar( 10 ) ;
 birthYear varucs2( 8 ) ccsid( 1200 ) ;
 birthMonth varucs2( 4 ) ccsid( 1200 ) ;
 birthDay varucs2( 4 ) ccsid( 1200 ) ;
 end-ds ;
 dcl-ds StudentHints_t qualified template ;
 schoolYear varchar( 4 ) ;
 gradeCode varchar( 2 ) ;
 reason varucs2( 120 ) ccsid( 1200 ) ;
 instanceId char( 36 ) ;
 end-ds ;
 dcl-ds StudentWork_t qualified template ;
 studentNo varchar( 15 ) ;
 studentName varucs2( 16 ) ccsid( 1200 ) ;
 studentNameKana varucs2( 36 ) ccsid( 1200 ) ;
 birthDate date ;
 genderCode varchar( 1 ) ;
 postalCode varchar( 7 ) ;
 prefectureCode varchar( 2 ) ;
 addressLine1 varucs2( 90 ) ccsid( 1200 ) ;
 addressLine2 varucs2( 90 ) ccsid( 1200 ) ;
 addressLine2Ind int( 5 ) inz( -1 ) ;
 phoneNumber varchar( 16 ) ;
 phoneNumberInd int( 5 ) inz( -1 ) ;
 emailAddress varchar( 60 ) ;
 emailAddressInd int( 5 ) inz( -1 ) ;
 admissionDate date ;
 enrollmentStatusCode varchar( 2 ) ;
 enrollmentEndDate date ;
 enrollmentEndDateInd int( 5 ) inz( -1 ) ;
 classId int( 20 ) ;
 classIdInd int( 5 ) inz( -1 ) ;
 emergencyContactName varucs2( 16 ) ccsid( 1200 ) ;
 emergencyContactNameInd int( 5 ) inz( -1 ) ;
 relationshipCode varchar( 2 ) ;
 relationshipCodeInd int( 5 ) inz( -1 ) ;
 emergencyPhoneNumber varchar( 16 ) ;
 emergencyPhoneNumberInd int( 5 ) inz( -1 ) ;
 remarks varucs2( 240 ) ccsid( 1200 ) ;
 remarksInd int( 5 ) inz( -1 ) ;
 relationshipCategory varchar( 24 ) ;
 relationshipCategoryInd int( 5 ) inz( -1 ) ;
 nameKey varucs2( 320 ) ccsid( 1200 ) ;
 kanaKey varucs2( 36 ) ccsid( 1200 ) ;
 end-ds ;
 dcl-ds StudentRecord_t qualified template ;
 studentId int( 20 ) ;
 rowVersion int( 20 ) ;
 work likeds( StudentWork_t ) ;
 updatedAt timestamp ;
 updatedBy varucs2( 128 ) ccsid( 1200 ) ;
 schoolYear int( 10 ) ;
 schoolYearInd int( 5 ) ;
 gradeCode varchar( 2 ) ;
 gradeInd int( 5 ) ;
 gradeName varucs2( 24 ) ccsid( 1200 ) ;
 classCode varchar( 9 ) ;
 className varucs2( 36 ) ccsid( 1200 ) ;
 enrollmentName varucs2( 24 ) ccsid( 1200 ) ;
 prefectureName varucs2( 24 ) ccsid( 1200 ) ;
 end-ds ;
 dcl-ds DuplicateCandidate_t qualified template ;
 studentNo varchar( 15 ) ;
 studentName varucs2( 16 ) ccsid( 1200 ) ;
 birthDate date ;
 classCode varchar( 9 ) ;
 className varucs2( 36 ) ccsid( 1200 ) ;
 end-ds ;
 dcl-ds Result_t qualified template ;
 kind int( 10 ) ;
 messageId char( 16 ) ;
 errorCount int( 10 ) ;
 fieldErrors likeds( FieldError_t ) dim( 30 ) ;
 studentId int( 20 ) ;
 rowVersion int( 20 ) ;
 requestId char( 36 ) ;
 token char( 36 ) ;
 candidateCount int( 10 ) ;
 candidates likeds( DuplicateCandidate_t ) dim( 20 ) ;
 end-ds ;
// SRC-001/002/006/008: raw text is separate from normalized criteria.
 dcl-ds SearchRaw_t qualified template ;
 criteriaFormatVersion int( 10 ) ;
 keyNames varchar( 128 ) ;
 values varucs2( 320 ) ccsid( 1200 ) dim( 3 ) ;
 selected ind dim( 4 ) ;
 end-ds ;
 dcl-ds SearchCriteria_t qualified template ;
 studentNo varchar( 32 ) ;
 nameKey varucs2( 642 ) ccsid( 1200 ) ;
 classId int( 20 ) ;
 anyStatus int( 5 ) ;
 status int( 5 ) dim( 4 ) ;
 end-ds ;
 dcl-ds StudentListWork_t qualified template ;
 studentNo varchar( 15 ) ;
 studentName varucs2( 16 ) ccsid( 1200 ) ;
 studentNameKana varucs2( 36 ) ccsid( 1200 ) ;
 birthDate date ;
 classId int( 20 ) ;
 classIdInd int( 5 ) ;
 end-ds ;
 dcl-ds StudentListRow_t qualified template ;
 studentId int( 20 ) ;
 work likeds( StudentListWork_t ) ;
 schoolYear int( 10 ) ;
 schoolYearInd int( 5 ) ;
 gradeName varucs2( 24 ) ccsid( 1200 ) ;
 classCode varchar( 9 ) ;
 className varucs2( 36 ) ccsid( 1200 ) ;
 enrollmentName varucs2( 24 ) ccsid( 1200 ) ;
 end-ds ;
 dcl-ds SearchContext_t qualified template ;
 criteriaFormatVersion int( 10 ) ;
 owner varchar( 128 ) ;
 session varchar( 28 ) ;
 revision int( 20 ) ;
 expectedRevision int( 20 ) ;
 instanceId char( 36 ) ;
 applied likeds( SearchCriteria_t ) ;
 hasApplied ind ;
 lastUsed timestamp ;
 page int( 10 ) inz( 1 ) ;
 pageSize int( 10 ) inz( 20 ) ;
 sortKey varchar( 16 ) inz( 'studentNo' ) ;
 direction varchar( 4 ) inz( 'asc' ) ;
 end-ds ;
 dcl-ds SearchPage_t qualified template ;
 result likeds( Result_t ) ;
 total int( 10 ) ;
 rowCount int( 10 ) ;
 rangeFrom int( 10 ) ;
 rangeTo int( 10 ) ;
 searchedAt timestamp ;
 rows likeds( StudentListRow_t ) dim( 100 ) ;
 end-ds ;
 dcl-ds Confirmation_t qualified template ;
 token char( 36 ) ;
 owner varchar( 128 ) ;
 job varchar( 28 ) ;
 instanceId char( 36 ) ;
 studentId int( 20 ) ;
 expectedVersion int( 20 ) ;
 businessHash char( 64 ) ;
 candidatesHash char( 64 ) ;
 expiresAt timestamp ;
 consumed ind ;
 end-ds ;
 dcl-ds ClassWork_t qualified template ;
 classId int( 20 ) ;
 expectedVersion int( 20 ) ;
 schoolYear int( 10 ) ;
 gradeCode varchar( 2 ) ;
 classCode varchar( 9 ) ;
 className varucs2( 36 ) ccsid( 1200 ) ;
 validFrom date ;
 validTo date ;
 capacity int( 10 ) ;
 capacityInd int( 5 ) ;
 displayOrder int( 10 ) ;
 isActive int( 5 ) ;
 remarks varucs2( 240 ) ccsid( 1200 ) ;
 remarksInd int( 5 ) ;
 reason varucs2( 120 ) ccsid( 1200 ) ;
 end-ds ;
 dcl-ds CodeWork_t qualified template ;
 categoryId varchar( 24 ) ;
 codeValue varchar( 10 ) ;
 expectedVersion int( 20 ) ;
 codeName varucs2( 24 ) ccsid( 1200 ) ;
 displayOrder int( 10 ) ;
 isActive int( 5 ) ;
 validFrom date ;
 validTo date ;
 validToInd int( 5 ) ;
 remarks varucs2( 240 ) ccsid( 1200 ) ;
 remarksInd int( 5 ) ;
 reason varucs2( 120 ) ccsid( 1200 ) ;
 end-ds ;
/endif
'''
write('copy/STUTYPES.rpgleinc',types)

protos='''/if not defined(STUPROTO_DEFINED)
/define STUPROTO_DEFINED
'''
PROCS={
 'StError':[('result','likeds(Result_t)'),('field','varchar(32) const'),('message','char(16) const')],
 'StAuthorize':[('operation','varchar(16) const'),('principal','varchar(128)'),('role','int(10)'),('result','likeds(Result_t)')],
 'StClock':[('utc','timestamp'),('businessDay','date')],
 'StNewId':[('id','char(36)')],
 'StStartup':[('result','likeds(Result_t)')],
 'StNormalize':[('raw','likeds(StudentRaw_t) const'),('work','likeds(StudentWork_t)'),('businessDay','date const'),('result','likeds(Result_t)')],
 'StValidate':[('work','likeds(StudentWork_t) const'),('result','likeds(Result_t)')],
 'StParseBirthDate':[('era','varchar(10) const'),('year','varucs2(8) ccsid(1200) const'),('month','varucs2(4) ccsid(1200) const'),('day','varucs2(4) ccsid(1200) const'),('businessDay','date const'),('birth','date'),('result','likeds(Result_t)')],
 'StFormatBirthDate':[('birth','date const'),('era','varchar(10)'),('year','varucs2(8) ccsid(1200)'),('month','varucs2(4) ccsid(1200)'),('day','varucs2(4) ccsid(1200)'),('display','varucs2(80) ccsid(1200)')],
 'StNormalizeText':[('raw','varucs2(320) ccsid(1200) const'),('rawMax','int(10) const'),('savedMax','int(10) const'),('mode','int(10) const'),('required','ind const'),('field','varchar(32) const'),('result','likeds(Result_t)')],
 'StIsoDate':[('raw','varucs2(320) ccsid(1200) const'),('maximum','date const'),('value','date'),('field','varchar(32) const'),('result','likeds(Result_t)')],
 'StLong':[('raw','varucs2(320) ccsid(1200) const'),('required','ind const'),('field','varchar(32) const'),('result','likeds(Result_t)')],
 'StEscapeLike':[('value','varucs2(320) ccsid(1200) const'),('prefix','ind const')],
 'StHash':[('value','varucs2(8000) ccsid(1200) const')],
 'StBusinessHash':[('work','likeds(StudentWork_t) const')],
 'StMessage':[('code','char(16) const')],
 'StLoadStudent':[('studentId','int(20) const'),('record','likeds(StudentRecord_t)'),('result','likeds(Result_t)')],
 'StCancelConfirmation':[('instance','char(36) const'),('result','likeds(Result_t)')],
 'StCreateSearchContext':[('raw','likeds(SearchRaw_t)'),('context','likeds(SearchContext_t)'),('page','likeds(SearchPage_t)')],
 'StClearSearchContext':[('raw','likeds(SearchRaw_t)'),('context','likeds(SearchContext_t)'),('page','likeds(SearchPage_t)')],
 'StCloseSearchContext':[('context','likeds(SearchContext_t)'),('result','likeds(Result_t)')],
 'StSearchStudents':[('raw','likeds(SearchRaw_t)'),('context','likeds(SearchContext_t)'),('newSearch','ind const'),('page','likeds(SearchPage_t)')],
 'StSaveStudent':[('input','likeds(StudentWork_t) const'),('hints','likeds(StudentHints_t) const'),('studentId','int(20) const'),('expectedVersion','int(20) const'),('confirmation','char(36) const'),('result','likeds(Result_t)')],
 'StDeleteStudent':[('studentId','int(20) const'),('expectedVersion','int(20) const'),('reason','varucs2(120) ccsid(1200) const'),('result','likeds(Result_t)')],
 'StLookupChoice':[('kind','varchar(24) const'),('page','int(10) const'),('schoolYear','int(10) const'),('grade','varchar(2) const'),('values','varchar(24) dim(20)'),('labels','varucs2(320) ccsid(1200) dim(20)'),('count','int(10)'),('result','likeds(Result_t)')],
 'StClassInfo':[('classId','int(20) const'),('year','varchar(4)'),('grade','varchar(2)'),('occupancy','int(10)'),('capacity','int(10)'),('capacityInd','int(5)'),('result','likeds(Result_t)')],
 'StMaintainClass':[('work','likeds(ClassWork_t) const'),('result','likeds(Result_t)')],
 'StMaintainCode':[('work','likeds(CodeWork_t) const'),('result','likeds(Result_t)')],
}
returns={'StNormalizeText':'varucs2(320) ccsid(1200)','StLong':'int(20)','StEscapeLike':'varucs2(642) ccsid(1200)','StHash':'char(64)','StBusinessHash':'char(64)','StMessage':'varucs2(320) ccsid(1200)'}
for name,args in PROCS.items():
    protos+=f'dcl-pr {name} {returns.get(name,"")};\n'+''.join(f'  {a} {t};\n' for a,t in args)+'end-pr;\n'
protos+='''dcl-pr StSearchStateCheck int(10) extproc('StSearchStateCheck');
 identity int(10) value; expected int(20) value; actual int(20) value;
 storedFormat int(10) value; requestFormat int(10) value; expired int(10) value;
end-pr;
dcl-pr StSearchKeysValid int(10) extproc('StSearchKeysValid');
 keys pointer value; length int(10) value;
end-pr;
dcl-pr StSearchBlock int(10) extproc('StSearchBlock');
 block int(10) value; count int(10) value;
end-pr;
'''
protos+='''dcl-pr StUnicodeNormalize int(10) extproc('StUnicodeNormalize');
  input pointer value; units int(10) value; rawMax int(10) value;
  savedMax int(10) value; mode int(10) value; required int(10) value;
  output pointer value; capacity int(10) value; written int(10);
end-pr;
dcl-pr StUnicodeScalars int(10) extproc('StUnicodeScalars');
  input pointer value; units int(10) value;
end-pr;
dcl-pr StUnicodeToJob int(10) extproc('StUnicodeToJob');
  input pointer value; units int(10) value; ccsid int(10) value;
  output pointer value; capacity int(10) value; written int(10);
end-pr;
dcl-pr StUnicodeFromJob int(10) extproc('StUnicodeFromJob');
  input pointer value; bytes int(10) value; ccsid int(10) value;
  output pointer value; capacity int(10) value; written int(10);
end-pr;
dcl-pr StUnicodeEscape int(10) extproc('StUnicodeEscape');
  input pointer value; units int(10) value; decode int(10) value;
  output pointer value; capacity int(10) value; written int(10);
end-pr;
dcl-pr StUnicodeDigest extproc('StUnicodeDigest');
  input pointer value; units int(10) value; output char(64);
end-pr;
dcl-pr StEdit extpgm('STUEDIT');
  studentId int(20); readOnly ind; notice char(128);
end-pr;
/endif
'''
write('copy/STUPROTO.rpgleinc',protos)
write('metadata/field-map.json',json.dumps([dict(index=i+1,property=p,column=c,type=t,rawMax=rm,savedMax=nm,normalization=mo,required=r,dds=ct) for i,(p,c,t,rm,nm,mo,r,ct,w) in enumerate(FIELDS)],ensure_ascii=False,indent=2))

def hv(prefix, f):
    p,c,t,rm,nm,mode,req,ctl,width=f
    return ':'+prefix+p+(' :'+prefix+p+'Ind' if not req else '')
cols=', '.join(x[1] for x in FIELDS)+', name_key, kana_key'
host=',\n    '.join(hv('rec.work.',x) for x in FIELDS)+',\n    :rec.work.nameKey, :rec.work.kanaKey'
select=',\n    '.join('s.'+x[1] for x in FIELDS)+',\n    s.name_key, s.kana_key'
load=f'''// Explicit fixed host variables. Caller owns the commitment gate.
exec sql SELECT s.student_id, s.row_version, {select}, s.updated_at, s.updated_by
  INTO :rec.studentId, :rec.rowVersion, {host}, :rec.updatedAt, :rec.updatedBy
  FROM STUDAPP.M_STUDENT s WHERE s.student_id=:id AND s.is_deleted=0;
'''
write('copy/STULOAD.rpgleinc',load)
insert=f'''exec sql INSERT INTO STUDAPP.M_STUDENT
  ({cols},gender_category,prefecture_category,enrollment_category,relationship_category,
   created_at,created_by,updated_at,updated_by,row_version,is_deleted)
  VALUES ({', '.join(hv('work.',f) for f in FIELDS)}, :work.nameKey,:work.kanaKey,
    'GENDER','PREFECTURE','ENROLLMENT_STATUS',:work.relationshipCategory :work.relationshipCategoryInd,:utc,:principal,:utc,:principal,1,0);
'''
write('copy/STUINSERT.rpgleinc',insert)
update='exec sql UPDATE STUDAPP.M_STUDENT SET\n'
update+=',\n'.join('  '+f[1]+'='+hv('work.',f) for f in FIELDS[1:])
update+=''', name_key=:work.nameKey, kana_key=:work.kanaKey,
  relationship_category=:work.relationshipCategory :work.relationshipCategoryInd,
  updated_at=:utc,updated_by=:principal,row_version=row_version+1
  WHERE student_id=:studentId AND row_version=:expectedVersion AND is_deleted=0;
'''
write('copy/STUUPDATE.rpgleinc',update)

norm='// raw checks precede transformations; failed conversions never become NULL.\n'
for i,f in enumerate(FIELDS,1):
    p,col,typ,rm,nm,mode,req,ctl,w=f
    if i==4: continue
    norm+=f"temp=StNormalizeText(raw.values({i}):{rm}:{nm}:{mode}:{'*on' if req else '*off'}:'{p}':result);\n"
    if 'date'==typ:
        norm+=f"if %len(temp)>0; StIsoDate(temp:businessDay:work.{p}:'{p}':result); endif;\n"
    elif 'int(20)'==typ:
        norm+=f"work.{p}=StLong(temp:*off:'{p}':result);\n"
    elif 'varucs2' in typ: norm+=f'work.{p}=temp;\n'
    else: norm+=f'work.{p}=%char(temp);\n'
    if not req: norm+=f'if %len(temp)=0;work.{p}Ind=-1;else;work.{p}Ind=0;endif;\n'
norm+='''StParseBirthDate(raw.birthEra:raw.birthYear:raw.birthMonth:raw.birthDay:businessDay:work.birthDate:result);
if work.relationshipCodeInd<0;work.relationshipCategory='';work.relationshipCategoryInd=-1;
else;work.relationshipCategory='RELATIONSHIP';work.relationshipCategoryInd=0;endif;
work.nameKey=StNormalizeText(raw.values(2):8:160:2:*on:'studentName':result);
work.kanaKey=StNormalizeText(raw.values(3):36:18:4:*on:'studentNameKana':result);
'''
write('copy/STUNORM.rpgleinc',norm)

hashtext="canonical=%ucs2('student/v1');\n"
changes="changed='[';\n"
for i,f in enumerate(FIELDS,1):
    p,c,t,*_=f
    req=f[6]
    value=f'work.{p}' if t.startswith('varucs2') else f'%ucs2(%char(work.{p}))'
    hashtext+=f"canonical+=%ucs2('|{i}:');\n"
    if not req: hashtext+=f"if work.{p}Ind<0; canonical+=%ucs2('NULL'); else;\n"
    hashtext+=f"piece={value}; canonical+=%ucs2(%char(%len(piece))+':')+piece;\n"
    if not req: hashtext+='endif;\n'
    condition=f'work.{p}<>old.work.{p}'
    if not req: condition=f'(work.{p}Ind<>old.work.{p}Ind) or (work.{p}Ind=0 and {condition})'
    changes+=f"if studentId=0 or {condition}; if changed<>'['; changed+=','; endif; changed+='\"{c}\"'; endif;\n"
changes+="""if studentId=0 or work.nameKey<>old.work.nameKey;if changed<>'[';changed+=',';endif;changed+='\"name_key\"';endif;
if studentId=0 or work.kanaKey<>old.work.kanaKey;if changed<>'[';changed+=',';endif;changed+='\"kana_key\"';endif;
if studentId=0;changed+=',\"gender_category\",\"prefecture_category\",\"enrollment_category\",\"relationship_category\",\"created_at\",\"created_by\",\"is_deleted\"';endif;
changed+=',\"updated_at\",\"updated_by\",\"row_version\"]';
"""
write('copy/STUHASH.rpgleinc',hashtext)
write('copy/STUCHANGED.rpgleinc',changes)
reload='// Values loaded from DB become raw without going through display substitution.\n'
for i,f in enumerate(FIELDS,1):
    p,c,t,*_=f;req=f[6]
    if i==4: continue
    value=f'rec.work.{p}' if t.startswith('varucs2') else f'%ucs2(%char(rec.work.{p}))'
    if not req: reload+=f"if rec.work.{p}Ind<0; raw.values({i})=%ucs2(''); else; raw.values({i})={value}; endif;\n"
    else: reload+=f'raw.values({i})={value};\n'
reload+='''StFormatBirthDate(rec.work.birthDate:raw.birthEra:raw.birthYear:raw.birthMonth:raw.birthDay:wareki);
'''
write('copy/STUTORAW.rpgleinc',reload)
write('copy/STUEDITIO.rpgleinc','\n'.join(f"ReadEdited({i}:{ctl});" for i,f in enumerate(FIELDS,1) if (ctl:=f[7]))+'\n')
write('copy/STUEDITOUT.rpgleinc','\n'.join(f"{f[7]}=Render(raw.values({i}):{f[8]}); prior({i})={f[7]};" for i,f in enumerate(FIELDS,1) if f[7])+'\n')
print('generated COPY contracts, 19 fixed CRUD/normalize/binding assignments, field map')
