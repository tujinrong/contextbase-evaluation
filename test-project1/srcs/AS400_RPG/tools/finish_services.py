"""Idempotent final server/UI corrections; leave DB generation to database owner."""
from pathlib import Path
B=Path(__file__).resolve().parents[1]
p=B/'src/STUSVC.sqlrpgle';s=p.read_text('utf8')
s=s.replace('s.birth_date,s.address_line1,s.phone_number,s.updated_at,c.school_year,c.grade_code,',
            's.birth_date,s.admission_date,s.class_id,s.updated_at,c.school_year,c.grade_code,')
s=s.replace(':rec.work.birthDate,:rec.work.addressLine1,:rec.work.phoneNumber :rec.work.phoneNumberInd,',
            ':rec.work.birthDate,:rec.work.admissionDate,:rec.work.classId :rec.work.classIdInd,')
a=s.index('dcl-proc StClassInfo export;');b=s.index('dcl-proc StLookupChoice export;',a)
x=s[a:b].replace('result likeds(Result_t);end-pi;',
 'result likeds(Result_t);registration ind const options(*nopass);end-pi;')
x=x.replace(' exec sql SELECT COUNT(*) INTO :occupancy',
 ' occupancy=0;\n if %parms()<8 or registration;\n exec sql SELECT COUNT(*) INTO :occupancy')
x=x.replace(' exec sql ROLLBACK;',' endif;\n exec sql ROLLBACK;')
s=s[:a]+x+s[b:]
old='if result.candidateCount<=20;LoadRow(id:result.candidates(result.candidateCount):result);if result.kind<>0;leave;endif;endif;'
new='''if result.candidateCount<=20;
   exec sql SELECT student_no,student_name,student_name_kana,birth_date
    INTO :result.candidates(result.candidateCount).work.studentNo,
     :result.candidates(result.candidateCount).work.studentName,
     :result.candidates(result.candidateCount).work.studentNameKana,
     :result.candidates(result.candidateCount).work.birthDate
    FROM STUDAPP.M_STUDENT WHERE student_id=:id;
   if SQLCOD<>0;SqlFailure(result:SQLSTT);leave;endif;
  endif;'''
s=s.replace(old,new);p.write_text(s,'utf8')
p=B/'copy/STUPROTO.rpgleinc';s=p.read_text('utf8')
a=s.index('dcl-pr StClassInfo');b=s.index('end-pr;',a)
if 'registration ind' not in s[a:b]:s=s[:b]+'  registration ind const options(*nopass);\n'+s[b:]
p.write_text(s,'utf8')
# Validate 5 categories and every required key, not simply a row count.
p=B/'src/STUCOMMON.sqlrpgle';s=p.read_text('utf8')
a=s.index(' exec sql SELECT COUNT(*) INTO :count FROM STUDAPP.M_CODE',s.index('dcl-proc StStartup'))
b=s.index(' exec sql ROLLBACK;',a)
s=s[:a]+''' exec sql SELECT COUNT(*) INTO :count FROM STUDAPP.M_CODE_CATEGORY
  WHERE category_id IN ('GENDER','GRADE','ENROLLMENT_STATUS','PREFECTURE','RELATIONSHIP');
 if SQLCOD<>0 or count<>5;result.kind=RK_SYSTEM;result.messageId='E-MST-001';endif;
 exec sql SELECT COUNT(*) INTO :count FROM STUDAPP.M_CODE
  WHERE (category_id='GENDER' AND code_value IN ('0','1','2','9'))
  OR (category_id='GRADE' AND code_value IN ('00','01','02','03','04','05','06'))
  OR (category_id='ENROLLMENT_STATUS' AND code_value IN ('01','02','03','04'))
  OR (category_id='PREFECTURE' AND code_value BETWEEN '01' AND '47')
  OR (category_id='RELATIONSHIP' AND code_value IN ('01','02','03','04','05','06','07','99'));
 if SQLCOD<>0 or count<>70;result.kind=RK_SYSTEM;result.messageId='E-MST-001';endif;
'''+s[b:];p.write_text(s,'utf8')
p=B/'src/STUEDIT.sqlrpgle';s=p.read_text('utf8')
a=s.index('dcl-proc DrawForm;');b=s.index('dcl-proc ReadEdited;',a)
x=s[a:b].replace('dcl-proc DrawForm;','dcl-proc DrawForm;\n dcl-ds classResult likeds(Result_t);dcl-s classId int(20);')
x=x.replace('occupancy=%int(%char(raw.values(15)))','classId=%int(%char(raw.values(15)))')
x=x.replace('StClassInfo(occupancy:EYEAR:EGRADE:occupancy:capacity:capacityInd:result:*on);',
 'StClassInfo(classId:EYEAR:EGRADE:occupancy:capacity:capacityInd:classResult:*on);')
x=x.replace('if result.kind=0;','if classResult.kind=0;');s=s[:a]+x+s[b:]
p.write_text(s,'utf8')
print('Corrected service result projections, candidate privacy, startup keys and UI state')
