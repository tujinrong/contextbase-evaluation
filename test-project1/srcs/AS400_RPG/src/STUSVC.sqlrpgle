**free
 ctl-opt nomain option( *srcstmt :*nodebugio ) ccsid( *ucs2 :1200 ) ;
/copy '../copy/STUTYPES.rpgleinc'
/copy '../copy/STUPROTO.rpgleinc'
 exec sql set option commit=*cs , naming=*sql , datfmt=*iso , closqlcsr=*endactgrp ;
// Activation-group storage belongs to one job. Entries are keyed by the editor
// instance and token, not a shared confirmation flag. No transaction crosses EXFMT.
 dcl-ds confirmations likeds( Confirmation_t ) dim( 64 ) inz ;
 dcl-pr StBeginWork ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr SqlFailure ;
 result likeds( Result_t ) ;
 state char( 5 ) const ;
 purpose varchar( 16 ) const options( *nopass ) ;
 end-pr ;
 dcl-pr LoadInternal ;
 id int( 20 ) const ;
 rec likeds( StudentRecord_t ) ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr LoadRow ;
 id int( 20 ) const ;
 rec likeds( StudentRecord_t ) ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr CheckCode ;
 category varchar( 24 ) const ;
 value varchar( 10 ) const ;
 oldValue varchar( 10 ) const ;
 save ind const ;
 day date const ;
 field varchar( 32 ) const ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr StCheckRules ;
 work likeds( StudentWork_t ) const ;
 old likeds( StudentRecord_t ) const ;
 hints likeds( StudentHints_t ) const ;
 studentId int( 20 ) const ;
 role int( 10 ) const ;
 day date const ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr StFindDuplicates ;
 work likeds( StudentWork_t ) const ;
 studentId int( 20 ) const ;
 digest char( 64 ) ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr StAppendAudit ;
 table varchar( 21 ) const ;
 key varchar( 35 ) const ;
 operation varchar( 11 ) const ;
 before int( 20 ) const ;
 after int( 20 ) const ;
 columns varchar( 16000 ) const ;
 principal varchar( 128 ) const ;
 utc timestamp const ;
 reason varucs2( 120 ) ccsid( 1200 ) const ;
 confirmed int( 5 ) const ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr StCheckCapacity ;
 classId int( 20 ) const ;
 excludeId int( 20 ) const ;
 capacity int( 10 ) const ;
 capacityInd int( 5 ) const ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-pr NormalizeSearch ;
 raw likeds( SearchRaw_t ) const ;
 criteria likeds( SearchCriteria_t ) ;
 day date const ;
 result likeds( Result_t ) ;
 end-pr ;
 dcl-proc StBeginWork export ;
 dcl-pi *n ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s affected int( 10 ) ;
 exec sql UPDATE STUDAPP.T_WRITE_GUARD SET LOCK_BIT=1-LOCK_BIT WHERE GUARD_ID=1 ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 exec sql GET DIAGNOSTICS :affected=ROW_COUNT ;
 if affected<>1 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 endif ;
 end-proc ;
 dcl-proc SqlFailure ;
 dcl-pi *n ;
 result likeds( Result_t ) ;
 state char( 5 ) const ;
 purpose varchar( 16 ) const options( *nopass ) ;
 end-pi ;
 select ;
 when state= '23505' ;
 if %parms( ) =3 and purpose= 'MASTER' ;
 StError( result :'master' :'E-MST-002' ) ;
 else ;
 StError( result :'studentNo' :'E-STU-101' ) ;
 endif ;
 when state= '23503' ;
 StError( result :'master' :'E-STU-009' ) ;
 when %subst( state :1 :2 ) = '40' ;
 result.kind=RK_CONFLICT ;
 result.messageId= 'E-STU-105' ;
 other ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 endsl ;
 end-proc ;
 dcl-proc LoadInternal ;
 dcl-pi *n ;
 id int( 20 ) const ;
 rec likeds( StudentRecord_t ) ;
 result likeds( Result_t ) ;
 end-pi ;
 clear rec ;
/copy '../copy/STULOAD.rpgleinc'
 if SQLCOD=100 ;
 result.kind=RK_NOTFOUND ;
 result.messageId= 'E-STU-103' ;
 elseif SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 endif ;
 end-proc ;
 dcl-proc LoadRow ;
 dcl-pi *n ;
 id int( 20 ) const ;
 rec likeds( StudentRecord_t ) ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s classInd int( 5 ) ;
 dcl-s gradeNameInd int( 5 ) ;
 dcl-s statusInd int( 5 ) ;
 dcl-s prefectureInd int( 5 ) ;
 dcl-s classCodeInd int( 5 ) ;
 clear rec ;
 exec sql SELECT s.student_id , s.row_version , s.student_no , s.student_name ,
 s.student_name_kana ,
 s.birth_date , s.admission_date , s.class_id , s.updated_at , c.school_year , c.grade_code ,
 c.class_code , c.class_name , g.code_name , e.code_name , p.code_name
 INTO
 :rec.studentId , :rec.rowVersion , :rec.work.studentNo , :rec.work.studentName , :
 rec.work.studentNameKana ,
 :rec.work.birthDate , :rec.work.admissionDate , :rec.work.classId :rec.work.classIdInd ,
 :rec.updatedAt , :rec.schoolYear :rec.schoolYearInd , :rec.gradeCode :rec.gradeInd ,
 :rec.classCode :classCodeInd , :rec.className :classInd , :rec.gradeName :gradeNameInd ,
 :rec.enrollmentName :statusInd , :rec.prefectureName :prefectureInd
 FROM STUDAPP.M_STUDENT s LEFT JOIN STUDAPP.M_CLASS c ON c.class_id=s.class_id
 LEFT JOIN STUDAPP.M_CODE g ON g.category_id= 'GRADE' AND g.code_value=c.grade_code
 LEFT JOIN STUDAPP.M_CODE e ON e.category_id= 'ENROLLMENT_STATUS' AND
 e.code_value=s.enrollment_status_code
 LEFT JOIN STUDAPP.M_CODE p ON p.category_id= 'PREFECTURE' AND p.code_value=s.prefecture_code
 WHERE s.student_id= :id AND s.is_deleted=0 ;
 if SQLCOD=100 ;
 result.kind=RK_NOTFOUND ;
 result.messageId= 'E-STU-103' ;
 return ;
 elseif SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 if gradeNameInd<0 and rec.schoolYearInd=0 ;
 rec.gradeName=%ucs2( '不整合' ) ;
 endif ;
 if classInd<0 ;
 rec.className=%ucs2( '－' ) ;
 endif ;
 if classCodeInd<0 ;
 rec.classCode= '-' ;
 endif ;
 if statusInd<0 ;
 rec.enrollmentName=%ucs2( '不整合' ) ;
 endif ;
 if prefectureInd<0 ;
 rec.prefectureName=%ucs2( '不整合' ) ;
 endif ;
 end-proc ;
 dcl-proc StLoadStudent export ;
 dcl-pi *n ;
 studentId int( 20 ) const ;
 record likeds( StudentRecord_t ) ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s principal varchar( 128 ) ;
 dcl-s role int( 10 ) ;
 clear result ;
 StNewId( result.requestId ) ;
 StAuthorize( 'READ' :principal :role :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 if studentId<=0 ;
 StError( result :'studentId' :'E-COM-003' ) ;
 return ;
 endif ;
 monitor ;
 StBeginWork( result ) ;
 if result.kind=0 ;
 LoadInternal( studentId :record :result ) ;
 endif ;
 StEndWork( *off :result ) ;
 on-error ;
 StEndWork( *off :result ) ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 endmon ;
 end-proc ;
 dcl-proc CheckCode ;
 dcl-pi *n ;
 category varchar( 24 ) const ;
 value varchar( 10 ) const ;
 oldValue varchar( 10 ) const ;
 save ind const ;
 day date const ;
 field varchar( 32 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s active int( 5 ) ;
 dcl-s categoryActive int( 5 ) ;
 dcl-s from date ;
 dcl-s to date ;
 dcl-s toInd int( 5 ) ;
 dcl-s length int( 5 ) ;
 if value= '' ;
 return ;
 endif ;
 exec sql SELECT c.is_active , c.valid_from , c.valid_to , k.is_active , k.code_length
 INTO :active , :from , :to :toInd , :categoryActive , :length
 FROM STUDAPP.M_CODE c JOIN STUDAPP.M_CODE_CATEGORY k ON k.category_id=c.category_id
 WHERE c.category_id= :category AND c.code_value= :value ;
 if SQLCOD=100 ;
 StError( result :field :'E-STU-009' ) ;
 return ;
 elseif SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 if %len( value ) <>length ;
 StError( result :field :'E-STU-009' ) ;
 endif ;
 if save and value<>oldValue and( active<>1 or categoryActive<>1 or from>day or( toInd=0 and
 to<day ) ) ;
 StError( result :field :'E-STU-011' ) ;
 endif ;
 end-proc ;
 dcl-proc StCheckRules export ;
 dcl-pi *n ;
 work likeds( StudentWork_t ) const ;
 old likeds( StudentRecord_t ) const ;
 hints likeds( StudentHints_t ) const ;
 studentId int( 20 ) const ;
 role int( 10 ) const ;
 day date const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s count int( 10 ) ;
 dcl-ds cls likeds( ClassWork_t ) ;
 dcl-s occupancy int( 10 ) ;
 dcl-s year int( 10 ) ;
 dcl-s retained ind ;
 dcl-s reason varucs2( 320 ) ccsid( 1200 ) ;
 CheckCode( 'GENDER' :work.genderCode :old.work.genderCode :*on :day :'genderCode' :
 result ) ;
 CheckCode( 'PREFECTURE' :work.prefectureCode :old.work.prefectureCode :*on :day :
 'prefectureCode'
 :result ) ;
 CheckCode( 'ENROLLMENT_STATUS'
 :work.enrollmentStatusCode :old.work.enrollmentStatusCode :*on :day :
 'enrollmentStatusCode'
 :result ) ;
 CheckCode( 'RELATIONSHIP' :work.relationshipCode :old.work.relationshipCode :*on :day :
 'relationshipCode' :result ) ;
 if studentId>0 and work.studentNo<>old.work.studentNo ;
 StError( result :'studentNo' :'E-STU-104' ) ;
 endif ;
 if studentId=0 ;
 exec sql SELECT COUNT( * ) INTO :count FROM STUDAPP.M_STUDENT WHERE student_no= :
 work.studentNo ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 if count>0 ;
 StError( result :'studentNo' :'E-STU-101' ) ;
 endif ;
 endif ;
 reason=StNormalizeText( hints.reason :60 :60 :1 :*off :'reason' :result ) ;
 if studentId>0 and( old.work.enrollmentStatusCode= '03' or old.work.enrollmentStatusCode= '04'
 ) and work.enrollmentStatusCode<>old.work.enrollmentStatusCode ;
 if role<3 ;
 result.kind=RK_FORBIDDEN ;
 result.messageId= 'E-COM-002' ;
 return ;
 endif ;
 if %len( reason ) =0 ;
 StError( result :'reason' :'E-STU-106' ) ;
 endif ;
 endif ;
 if hints.schoolYear<> '' ;
 year=StLong( %ucs2( hints.schoolYear ) :*on :'schoolYear' :result ) ;
 if %len( hints.schoolYear ) <>4 or year<1900 or year>9998 ;
 StError( result :'schoolYear' :'E-DATE-003' ) ;
 endif ;
 endif ;
 CheckCode( 'GRADE' :hints.gradeCode :'' :*off :day :'gradeCode' :result ) ;
 if work.classIdInd<0 ;
 return ;
 endif ;
 exec sql SELECT
 class_id , school_year , grade_code , class_code , class_name , valid_from , valid_to ,
 capacity , is_active
 INTO
 :cls.classId , :cls.schoolYear , :cls.gradeCode , :cls.classCode , :cls.className , :
 cls.validFrom , :cls.validTo , :cls.capacity
 :cls.capacityInd , :cls.isActive
 FROM STUDAPP.M_CLASS WHERE class_id= :work.classId ;
 if SQLCOD=100 ;
 StError( result :'classId' :'E-STU-010' ) ;
 return ;
 elseif SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 if( hints.schoolYear<> '' and year<>cls.schoolYear ) or( hints.gradeCode<> '' and
 hints.gradeCode<>cls.gradeCode ) ;
 StError( result :'classId' :'E-STU-014' ) ;
 endif ;
 retained=studentId>0 and old.work.classIdInd=0 and old.work.classId=work.classId and
 ( old.work.enrollmentStatusCode= '01' or old.work.enrollmentStatusCode= '02' ) ;
 if work.enrollmentStatusCode= '01' or work.enrollmentStatusCode= '02' ;
 if not retained ;
 if cls.isActive<>1 or day<cls.validFrom or day>cls.validTo ;
 StError( result :'classId' :'E-STU-013' ) ;
 endif ;
 CheckCode( 'GRADE' :cls.gradeCode :'' :*on :day :'classId' :result ) ;
 StCheckCapacity( work.classId :studentId :cls.capacity :cls.capacityInd :result ) ;
 endif ;
 else ;
 if( studentId=0 or old.work.classIdInd<>work.classIdInd or old.work.classId<>work.classId or
 old.work.admissionDate<>work.admissionDate or
 old.work.enrollmentEndDateInd<>work.enrollmentEndDateInd or
 old.work.enrollmentEndDate<>work.enrollmentEndDate or
 old.work.enrollmentStatusCode<>work.enrollmentStatusCode ) and( work.admissionDate>cls.validTo
 or work.enrollmentEndDate<cls.validFrom ) ;
 StError( result :'classId' :'E-STU-108' ) ;
 endif ;
 endif ;
 end-proc ;
 dcl-proc StCheckCapacity export ;
 dcl-pi *n ;
 classId int( 20 ) const ;
 excludeId int( 20 ) const ;
 capacity int( 10 ) const ;
 capacityInd int( 5 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s occupancy int( 10 ) ;
 exec sql SELECT COUNT( * ) INTO :occupancy FROM STUDAPP.M_STUDENT
 WHERE class_id= :classId AND is_deleted=0 AND enrollment_status_code IN( '01' , '02' ) AND
 student_id<> :excludeId ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 if capacityInd=0 and occupancy+1>capacity ;
 StError( result :'classId' :'E-STU-102' ) ;
 endif ;
 end-proc ;
 dcl-proc StFindDuplicates export ;
 dcl-pi *n ;
 work likeds( StudentWork_t ) const ;
 studentId int( 20 ) const ;
 digest char( 64 ) ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-ds candidate likeds( StudentRecord_t ) ;
 dcl-s id int( 20 ) ;
 dcl-s version int( 20 ) ;
 dcl-s piece varucs2( 8000 ) ccsid( 1200 ) ;
 exec sql DECLARE dup CURSOR FOR SELECT student_id , row_version FROM STUDAPP.M_STUDENT
 WHERE is_deleted=0 AND student_id<> :studentId AND birth_date= :work.birthDate
 AND( name_key= :work.nameKey OR kana_key= :work.kanaKey ) ORDER BY student_id ;
 result.candidateCount=0 ;
 digest=StHash( %ucs2( 'candidates/v1' ) ) ;
 exec sql OPEN dup ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 dou *off ;
 exec sql FETCH dup INTO :id , :version ;
 if SQLCOD=100 ;
 leave ;
 endif ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 leave ;
 endif ;
 result.candidateCount+=1 ;
 piece=%ucs2( digest+ '|' +%char( id ) + ':' +%char( version ) ) ;
 digest=StHash( piece ) ;
 if result.candidateCount<=20 ;
 exec sql SELECT student_no , student_name , student_name_kana , birth_date
 INTO :candidate.work.studentNo ,
 :candidate.work.studentName ,
 :candidate.work.studentNameKana ,
 :candidate.work.birthDate
 FROM STUDAPP.M_STUDENT WHERE student_id= :id ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 leave ;
 endif ;
 result.candidates( result.candidateCount ) =candidate ;
 endif ;
 enddo ;
 exec sql CLOSE dup ;
 digest=StHash( %ucs2( digest+ '|count:' +%char( result.candidateCount ) ) ) ;
 end-proc ;
 dcl-proc StAppendAudit export ;
 dcl-pi *n ;
 table varchar( 21 ) const ;
 key varchar( 35 ) const ;
 operation varchar( 11 ) const ;
 before int( 20 ) const ;
 after int( 20 ) const ;
 columns varchar( 16000 ) const ;
 principal varchar( 128 ) const ;
 utc timestamp const ;
 reason varucs2( 120 ) ccsid( 1200 ) const ;
 confirmed int( 5 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s beforeInd int( 5 ) ;
 dcl-s reasonInd int( 5 ) ;
 beforeInd=0 ;
 reasonInd=0 ;
 if before=0 ;
 beforeInd=-1 ;
 endif ;
 if %len( reason ) =0 ;
 reasonInd=-1 ;
 endif ;
 exec sql INSERT INTO
 STUDAPP.T_OPERATION_LOG( target_table , target_key , operation_type , before_version ,
 after_version ,
 changed_columns , executed_by , executed_at , correlation_id , operation_reason ,
 duplicate_confirmed )
 VALUES( :table , :key , :operation , :before
 :beforeInd , :after , :columns , :principal , :utc , :result.requestId , :reason :
 reasonInd , :confirmed ) ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 endif ;
 end-proc ;
 dcl-proc StSaveStudent export ;
 dcl-pi *n ;
 input likeds( StudentWork_t ) const ;
 hints likeds( StudentHints_t ) const ;
 studentId int( 20 ) const ;
 expectedVersion int( 20 ) const ;
 confirmation char( 36 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-ds raw likeds( StudentRaw_t ) ;
 dcl-ds rec likeds( StudentRecord_t ) ;
 dcl-s wareki varucs2( 80 ) ccsid( 1200 ) ;
 dcl-ds work likeds( StudentWork_t ) ;
 dcl-ds old likeds( StudentRecord_t ) ;
 dcl-s principal varchar( 128 ) ;
 dcl-s role int( 10 ) ;
 dcl-s utc timestamp ;
 dcl-s day date ;
 dcl-s job varchar( 28 ) ;
 dcl-s reason varucs2( 120 ) ccsid( 1200 ) ;
 dcl-s businessHash char( 64 ) ;
 dcl-s candidatesHash char( 64 ) ;
 dcl-s slot int( 10 ) ;
 dcl-s i int( 10 ) ;
 dcl-s confirmed int( 5 ) ;
 dcl-s affected int( 10 ) ;
 dcl-s changed varchar( 16000 ) ;
 dcl-s state char( 5 ) ;
 clear result ;
 clear old ;
 StNewId( result.requestId ) ;
 StAuthorize( 'SAVE' :principal :role :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 if studentId<0 or( studentId=0 and expectedVersion<>0 ) or( studentId>0 and
 expectedVersion<=0 )
 ;
 StError( result :'studentId' :'E-COM-003' ) ;
 return ;
 endif ;
 if hints.instanceId= '' ;
 StError( result :'instanceId' :'E-COM-003' ) ;
 return ;
 endif ;
 rec.work=input ;
/copy '../copy/STUTORAW.rpgleinc'
 StClock( utc :day ) ;
 StNormalize( raw :work :day :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 StValidate( work :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 reason=StNormalizeText( hints.reason :60 :60 :1 :*off :'reason' :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 exec sql VALUES QSYS2.JOB_NAME INTO :job ;
 monitor ;
 StBeginWork( result ) ;
 if result.kind=0 and studentId>0 ;
 LoadInternal( studentId :old :result ) ;
 endif ;
 if result.kind=0 and studentId>0 and old.rowVersion<>expectedVersion ;
 result.kind=RK_CONFLICT ;
 result.messageId= 'E-STU-105' ;
 endif ;
 if result.kind=0 ;
 StCheckRules( work :old :hints :studentId :role :day :result ) ;
 endif ;
 businessHash=StBusinessHash( work ) ;
 if result.kind=0 and studentId>0 and businessHash=StBusinessHash( old.work ) ;
 result.kind=RK_NOCHANGE ;
 result.messageId= 'I-STU-004' ;
 result.studentId=studentId ;
 result.rowVersion=expectedVersion ;
 endif ;
 if result.kind=0 ;
 StFindDuplicates( work :studentId :candidatesHash :result ) ;
 endif ;
 if result.kind=0 and( result.candidateCount>0 or confirmation<> '' ) ;
 slot=0 ;
 for i=1 to 64 ;
 if confirmations( i ).token=confirmation and confirmation<> '' ;
 slot=i ;
 leave ;
 endif ;
 endfor ;
 if slot>0 and
 StConfirm( confirmations( slot ) :principal :job :hints.instanceId :studentId :
 expectedVersion :businessHash :candidatesHash :utc :reason )
 ;
 confirmed=1 ;
 else ;
 slot=0 ;
 for i=1 to 64 ;
 if confirmations( i ).token= '' or confirmations( i ).consumed or confirmations( i )
 .expiresAt<=utc ;
 slot=i ;
 leave ;
 endif ;
 endfor ;
 if slot=0 ;
 slot=1 ;
 for i=2 to 64 ;
 if confirmations( i ).expiresAt<confirmations( slot ).expiresAt ;
 slot=i ;
 endif ;
 endfor ;
 endif ;
 clear confirmations( slot ) ;
 StNewId( confirmations( slot ).token ) ;
 confirmations( slot ).owner=principal ;
 confirmations( slot ).job=job ;
 confirmations( slot ).instanceId=hints.instanceId ;
 confirmations( slot ).studentId=studentId ;
 confirmations( slot ).expectedVersion=expectedVersion ;
 confirmations( slot ).businessHash=businessHash ;
 confirmations( slot ).candidatesHash=candidatesHash ;
 confirmations( slot ).expiresAt=utc+%minutes( 10 ) ;
 result.token=confirmations( slot ).token ;
 result.kind=RK_CONFIRM ;
 result.messageId= 'W-STU-101' ;
 if confirmation<> '' ;
 result.messageId= 'W-STU-102' ;
 endif ;
 endif ;
 endif ;
 if result.kind=0 ;
 if studentId=0 ;
/copy '../copy/STUINSERT.rpgleinc'
 if SQLCOD=0 ;
// Identity is retrieved BEFORE the audit INSERT on this same connection.
 exec sql VALUES BIGINT( IDENTITY_VAL_LOCAL( ) ) INTO :result.studentId ;
 result.rowVersion=1 ;
 endif ;
 else ;
/copy '../copy/STUUPDATE.rpgleinc'
 if SQLCOD=0 ;
 exec sql GET DIAGNOSTICS :affected=ROW_COUNT ;
 if affected<>1 ;
 result.kind=RK_CONFLICT ;
 result.messageId= 'E-STU-105' ;
 endif ;
 endif ;
 result.studentId=studentId ;
 result.rowVersion=expectedVersion+1 ;
 endif ;
 if SQLCOD<>0 ;
 state=SQLSTT ;
 SqlFailure( result :state ) ;
 endif ;
 if result.kind=0 ;
/copy '../copy/STUCHANGED.rpgleinc'
 if studentId=0 ;
 StAppendAudit( 'm_student' :%char( result.studentId ) :'CREATE'
 :0 :1 :changed :principal :utc :reason :confirmed :result ) ;
 else ;
 StAppendAudit( 'm_student' :%char( studentId ) :'UPDATE'
 :expectedVersion :result.rowVersion :changed :principal :utc :reason :confirmed :result
 ) ;
 endif ;
 endif ;
 if result.kind=0 ;
 StEndWork( *on :result ) ;
 if result.kind=0 ;
 if confirmed=1 ;
 confirmations( slot ).consumed=*on ;
 endif ;
 result.kind=RK_SAVED ;
 if studentId=0 ;
 result.messageId= 'I-STU-001' ;
 else ;
 result.messageId= 'I-STU-002' ;
 endif ;
 else ;
 result.kind=RK_UNKNOWN ;
 result.messageId= 'E-COM-004' ;
 StEndWork( *off :result ) ;
 endif ;
 else ;
 StEndWork( *off :result ) ;
 endif ;
 else ;
 StEndWork( *off :result ) ;
 endif ;
 on-error ;
 StEndWork( *off :result ) ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 endmon ;
 end-proc ;
 dcl-proc StClassInfo export ;
 dcl-pi *n ;
 classId int( 20 ) const ;
 year varchar( 4 ) ;
 grade varchar( 2 ) ;
 occupancy int( 10 ) ;
 capacity int( 10 ) ;
 capacityInd int( 5 ) ;
 result likeds( Result_t ) ;
 registration ind const options( *nopass ) ;
 end-pi ;
 dcl-s y int( 10 ) ;
 dcl-s principal varchar( 128 ) ;
 dcl-s role int( 10 ) ;
 clear result ;
 StAuthorize( 'READ' :principal :role :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 exec sql SELECT school_year , grade_code , capacity INTO :y , :grade , :capacity :
 capacityInd FROM
 STUDAPP.M_CLASS WHERE class_id= :classId ;
 if SQLCOD=100 ;
 result.kind=RK_NOTFOUND ;
 result.messageId= 'E-STU-010' ;
 return ;
 elseif SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 year=%char( y ) ;
 occupancy=0 ;
 if %parms( ) <8 or registration ;
 exec sql SELECT COUNT( * ) INTO :occupancy FROM STUDAPP.M_STUDENT WHERE class_id= :classId
 AND
 is_deleted=0 AND enrollment_status_code IN( '01' , '02' ) ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 endif ;
 endif ;
 StEndWork( *off :result ) ;
 end-proc ;
 dcl-proc StLookupChoice export ;
 dcl-pi *n ;
 kind varchar( 24 ) const ;
 page int( 10 ) const ;
 schoolYear int( 10 ) const ;
 grade varchar( 2 ) const ;
 values varchar( 24 ) dim( 20 ) ;
 labels varucs2( 320 ) ccsid( 1200 ) dim( 20 ) ;
 count int( 10 ) ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s principal varchar( 128 ) ;
 dcl-s role int( 10 ) ;
 dcl-s first int( 10 ) ;
 dcl-s last int( 10 ) ;
 dcl-s code varchar( 24 ) ;
 dcl-s name varucs2( 320 ) ccsid( 1200 ) ;
 dcl-s active int( 5 ) ;
 dcl-s from date ;
 dcl-s to date ;
 dcl-s toInd int( 5 ) ;
 dcl-s utc timestamp ;
 dcl-s day date ;
 exec sql DECLARE codeChoice CURSOR FOR SELECT
 code_value , code_name , is_active , valid_from , valid_to FROM
 ( SELECT c.* , ROW_NUMBER( ) OVER( ORDER BY display_order , code_value ) rn FROM
 STUDAPP.M_CODE c WHERE
 category_id= :kind ) q
 WHERE rn BETWEEN :first AND :last ORDER BY rn ;
 exec sql DECLARE classChoice CURSOR FOR SELECT VARCHAR( class_id ) , VARCHAR( school_year )
 CONCAT
 ' / ' CONCAT class_code CONCAT ' / ' CONCAT class_name , is_active , valid_from , valid_to FROM
 ( SELECT c.* , ROW_NUMBER( ) OVER( ORDER BY school_year
 DESC , grade_code , display_order , class_code , class_id ) rn FROM STUDAPP.M_CLASS c
 WHERE( :schoolYear=0 OR school_year= :schoolYear ) AND( :grade= '' OR grade_code= :grade
 ) ) q
 WHERE rn BETWEEN :first AND :last ORDER BY rn ;
 exec sql DECLARE yearChoice CURSOR FOR SELECT VARCHAR( school_year ) , VARCHAR( school_year )
 FROM
 ( SELECT school_year , ROW_NUMBER( ) OVER( ORDER BY school_year DESC ) rn FROM( SELECT
 DISTINCT
 school_year FROM STUDAPP.M_CLASS ) d ) q
 WHERE rn BETWEEN :first AND :last ORDER BY rn ;
 clear result ;
 clear values ;
 clear labels ;
 count=0 ;
 StAuthorize( 'READ' :principal :role :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 if page<1 ;
 StError( result :'page' :'E-COM-003' ) ;
 return ;
 endif ;
 first=( page-1 ) *20+1 ;
 last=first+19 ;
 StClock( utc :day ) ;
 if kind= 'CLASS' ;
 exec sql OPEN classChoice ;
 elseif kind= 'YEAR' ;
 exec sql OPEN yearChoice ;
 elseif kind= 'GENDER' or kind= 'GRADE' or kind= 'PREFECTURE' or kind= 'RELATIONSHIP' or kind=
 'ENROLLMENT_STATUS' ;
 exec sql OPEN codeChoice ;
 else ;
 StError( result :'category' :'E-COM-003' ) ;
 return ;
 endif ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 dou *off ;
 if kind= 'CLASS' ;
 exec sql FETCH classChoice INTO :code , :name , :active , :from , :to :toInd ;
 elseif kind= 'YEAR' ;
 exec sql FETCH yearChoice INTO :code , :name ;
 active=1 ;
 from=d'1900-01-01' ;
 toInd=-1 ;
 else ;
 exec sql FETCH codeChoice INTO :code , :name , :active , :from , :to :toInd ;
 endif ;
 if SQLCOD=100 ;
 leave ;
 endif ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 leave ;
 endif ;
 count+=1 ;
 values( count ) =code ;
 labels( count ) =name ;
 if active<>1 or day<from or( toInd=0 and day>to ) ;
 labels( count ) +=%ucs2( ' [停止・期間外]' ) ;
 endif ;
 enddo ;
 if kind= 'CLASS' ;
 exec sql CLOSE classChoice ;
 elseif kind= 'YEAR' ;
 exec sql CLOSE yearChoice ;
 else ;
 exec sql CLOSE codeChoice ;
 endif ;
 StEndWork( *off :result ) ;
 end-proc ;
/copy 'STUMASTER.rpgleinc'
 dcl-proc StDeleteStudent export ;
 dcl-pi *n ;
 studentId int( 20 ) const ;
 expectedVersion int( 20 ) const ;
 reason varucs2( 120 ) ccsid( 1200 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-ds old likeds( StudentRecord_t ) ;
 dcl-s principal varchar( 128 ) ;
 dcl-s role int( 10 ) ;
 dcl-s utc timestamp ;
 dcl-s day date ;
 dcl-s normalized varucs2( 120 ) ccsid( 1200 ) ;
 dcl-s affected int( 10 ) ;
 clear result ;
 StNewId( result.requestId ) ;
 StAuthorize( 'DELETE' :principal :role :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 if studentId<=0 or expectedVersion<=0 ;
 StError( result :'studentId' :'E-COM-003' ) ;
 return ;
 endif ;
 normalized=StNormalizeText( reason :60 :60 :1 :*on :'deleteReason' :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 StClock( utc :day ) ;
 monitor ;
 StBeginWork( result ) ;
 if result.kind=0 ;
 LoadInternal( studentId :old :result ) ;
 endif ;
 if result.kind=0 and old.rowVersion<>expectedVersion ;
 result.kind=RK_CONFLICT ;
 result.messageId= 'E-STU-105' ;
 endif ;
 if result.kind=0 ;
// The deletion entry has no StudentRaw parameter: dirty screen values cannot leak.
 exec sql UPDATE STUDAPP.M_STUDENT SET
 is_deleted=1 , deleted_at= :utc , deleted_by= :principal , delete_reason= :normalized ,
 updated_at= :utc , updated_by= :principal , row_version=row_version+1
 WHERE student_id= :studentId AND row_version= :expectedVersion AND is_deleted=0 ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 else ;
 exec sql GET DIAGNOSTICS :affected=ROW_COUNT ;
 if affected<>1 ;
 result.kind=RK_CONFLICT ;
 result.messageId= 'E-STU-105' ;
 endif ;
 endif ;
 endif ;
 if result.kind=0 ;
 StAppendAudit( 'm_student' :%char( studentId ) :'DELETE' :expectedVersion :
 expectedVersion+1 :
 '["is_deleted","deleted_at","deleted_by","delete_reas' +
 'on","updated_at","updated_by","row_version"]' :principal :utc :normalized :0 :result ) ;
 endif ;
 if result.kind=0 ;
 StEndWork( *on :result ) ;
 if result.kind=0 ;
 result.kind=RK_SAVED ;
 result.messageId= 'I-STU-003' ;
 result.studentId=studentId ;
 result.rowVersion=expectedVersion+1 ;
 else ;
 result.kind=RK_UNKNOWN ;
 result.messageId= 'E-COM-004' ;
 StEndWork( *off :result ) ;
 endif ;
 else ;
 StEndWork( *off :result ) ;
 endif ;
 on-error ;
 StEndWork( *off :result ) ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 endmon ;
 end-proc ;
 dcl-proc NormalizeSearch ;
 dcl-pi *n ;
 raw likeds( SearchRaw_t ) const ;
 criteria likeds( SearchCriteria_t ) ;
 day date const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s temp varucs2( 320 ) ccsid( 1200 ) ;
 dcl-ds rec likeds( ClassWork_t ) ;
 dcl-s count int( 10 ) ;
 dcl-s i int( 10 ) ;
 clear criteria ;
 temp=StNormalizeText( raw.values( 1 ) :15 :15 :5 :*off :'studentNo' :result ) ;
 criteria.studentNo=%char( StEscapeLike( temp :*on ) ) ;
 temp=StNormalizeText( raw.values( 2 ) :8 :160 :2 :*off :'studentName' :result ) ;
 criteria.nameKey=StEscapeLike( temp :*off ) ;
 temp=StNormalizeText( raw.values( 3 ) :36 :18 :4 :*off :'studentNameKana' :result ) ;
 criteria.kanaKey=StEscapeLike( temp :*off ) ;
 if %len( raw.values( 4 ) ) >0 ;
 temp=StNormalizeText( raw.values( 4 ) :4 :4 :11 :*on :'schoolYear' :result ) ;
 criteria.schoolYear=StLong( temp :*on :'schoolYear' :result ) ;
 if criteria.schoolYear<1900 or criteria.schoolYear>9998 ;
 StError( result :'schoolYear' :'E-DATE-003' ) ;
 endif ;
 exec sql SELECT COUNT( * ) INTO :count FROM STUDAPP.M_CLASS WHERE
 school_year= :criteria.schoolYear ;
 if SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 endif ;
 if count=0 ;
 StError( result :'schoolYear' :'E-STU-010' ) ;
 endif ;
 endif ;
 temp=StNormalizeText( raw.values( 5 ) :2 :2 :6 :*off :'gradeCode' :result ) ;
 criteria.gradeCode=%char( temp ) ;
 CheckCode( 'GRADE' :criteria.gradeCode :'' :*off :day :'gradeCode' :result ) ;
 criteria.classId=StLong( raw.values( 6 ) :*off :'classId' :result ) ;
 if raw.values( 7 ) =%ucs2( '1' ) ;
 criteria.unassigned=1 ;
 elseif %len( raw.values( 7 ) ) >0 and raw.values( 7 ) <>%ucs2( '0' ) ;
 StError( result :'unassignedOnly' :'E-COM-003' ) ;
 endif ;
 if criteria.unassigned=1 and( criteria.schoolYear<>0 or criteria.gradeCode<> '' or
 criteria.classId<>0 ) ;
 StError( result :'unassignedOnly' :'E-SRC-001' ) ;
 endif ;
 if criteria.classId>0 ;
 exec sql SELECT school_year , grade_code INTO :rec.schoolYear , :rec.gradeCode FROM
 STUDAPP.M_CLASS
 WHERE class_id= :criteria.classId ;
 if SQLCOD=100 ;
 StError( result :'classId' :'E-STU-010' ) ;
 elseif SQLCOD<>0 ;
 SqlFailure( result :SQLSTT ) ;
 return ;
 elseif( criteria.schoolYear<>0 and criteria.schoolYear<>rec.schoolYear ) or
 ( criteria.gradeCode<> '' and criteria.gradeCode<>rec.gradeCode ) ;
 StError( result :'classId' :'E-STU-014' ) ;
 endif ;
 endif ;
 for i=1 to 4 ;
 if raw.selected( i ) ;
 criteria.status( i ) =1 ;
 criteria.anyStatus=1 ;
 endif ;
 endfor ;
 temp=StNormalizeText( raw.values( 9 ) :2 :2 :6 :*off :'prefectureCode' :result ) ;
 criteria.prefectureCode=%char( temp ) ;
 CheckCode( 'PREFECTURE' :criteria.prefectureCode :'' :*off :day :'prefectureCode' :
 result ) ;
 temp=StNormalizeText( raw.values( 10 ) :20 :16 :8 :*off :'phoneNumber' :result ) ;
 criteria.phone=%char( temp ) ;
 if %len( raw.values( 11 ) ) >0 ;
 criteria.fromFlag=1 ;
 temp=StNormalizeText( raw.values( 11 ) :10 :10 :10 :*on :'admissionFrom' :result ) ;
 StIsoDate( temp :day :criteria.fromDate :'admissionFrom' :result ) ;
 endif ;
 if %len( raw.values( 12 ) ) >0 ;
 criteria.toFlag=1 ;
 temp=StNormalizeText( raw.values( 12 ) :10 :10 :10 :*on :'admissionTo' :result ) ;
 StIsoDate( temp :day :criteria.toDate :'admissionTo' :result ) ;
 endif ;
 if criteria.fromFlag=1 and criteria.toFlag=1 and criteria.fromDate>criteria.toDate ;
 StError( result :'admissionTo' :'E-STU-007' ) ;
 endif ;
 end-proc ;
 dcl-proc StSearchStudents export ;
 dcl-pi *n ;
 raw likeds( SearchRaw_t ) const ;
 context likeds( SearchContext_t ) ;
 newSearch ind const ;
 page likeds( SearchPage_t ) ;
 end-pi ;
 dcl-ds c likeds( SearchCriteria_t ) ;
 dcl-s principal varchar( 128 ) ;
 dcl-s role int( 10 ) ;
 dcl-s utc timestamp ;
 dcl-s day date ;
 dcl-s sqlText varchar( 16000 ) ;
 dcl-s predicate varchar( 8000 ) ;
 dcl-s order varchar( 128 ) ;
 dcl-s id int( 20 ) ;
 dcl-s first int( 10 ) ;
 dcl-s last int( 10 ) ;
 dcl-s maxPage int( 10 ) ;
 exec sql DECLARE countCursor CURSOR FOR countStmt ;
 exec sql DECLARE pageCursor CURSOR FOR pageStmt ;
 clear page ;
 StNewId( page.result.requestId ) ;
 StAuthorize( 'READ' :principal :role :page.result ) ;
 if page.result.kind<>0 ;
 return ;
 endif ;
 StClock( utc :day ) ;
 if context.owner<> '' and context.owner<>principal ;
 page.result.kind=RK_FORBIDDEN ;
 page.result.messageId= 'E-COM-002' ;
 return ;
 endif ;
 if context.pageSize<>20 and context.pageSize<>50 and context.pageSize<>100 ;
 StError( page.result :'pageSize' :'E-COM-003' ) ;
 return ;
 endif ;
 if context.page<=0 ;
 StError( page.result :'page' :'E-COM-003' ) ;
 return ;
 endif ;
 select ;
 when context.sortKey= 'studentNo' ;
 order= 's.student_no' ;
 when context.sortKey= 'name' ;
 order= 's.student_name' ;
 when context.sortKey= 'admissionDate' ;
 order= 's.admission_date' ;
 when context.sortKey= 'updatedAt' ;
 order= 's.updated_at' ;
 other ;
 StError( page.result :'sortKey' :'E-COM-003' ) ;
 return ;
 endsl ;
 if context.direction<> 'asc' and context.direction<> 'desc' ;
 StError( page.result :'sortDirection' :'E-COM-003' ) ;
 return ;
 endif ;
 order+= ' ' +context.direction+ ',s.student_id ASC' ;
 if newSearch ;
 NormalizeSearch( raw :c :day :page.result ) ;
 if page.result.kind<>0 ;
 return ;
 endif ;
 context.page=1 ;
 else ;
 if not context.hasApplied ;
 return ;
 endif ;
 if utc>context.lastUsed+%minutes( 30 ) ;
 context.hasApplied=*off ;
 page.result.messageId= 'W-SRC-002' ;
 return ;
 endif ;
 c=context.applied ;
 endif ;
 predicate= ' FROM STUDAPP.M_STUDENT s LEFT JOIN STUDAPP.M_CLASS ' +
 'c ON c.class_id=s.class_id WHERE s.is_deleted=0' +
 ' AND s.student_no LIKE ? ESCAPE ''!'' AND s.name_key' +
 ' LIKE ? ESCAPE ''!'' AND s.kana_key LIKE ? ESCAPE ''' + '!''' +
 ' AND(?=0 OR c.school_year=?) AND(?='''' OR c.grade' + '_code=?) AND(?=0 OR s.class_id=?)' +
 ' AND(?=0 OR s.class_id IS NULL) AND(?=0 OR(?=1 AN' +
 'D s.enrollment_status_code=''01'') OR(?=1 AND s.enr' +
 'ollment_status_code=''02'') OR(?=1 AND s.enrollment' +
 '_status_code=''03'') OR(?=1 AND s.enrollment_status' + '_code=''04''))' +
 ' AND(?='''' OR s.prefecture_code=?) AND(?='''' OR ' +
 's.phone_number=? OR s.emergency_phone_number=?)' +
 ' AND(?=0 OR s.admission_date>=?) AND(?=0 OR s.admission_date<=?)' ;
 monitor ;
 StBeginWork( page.result ) ;
 if page.result.kind<>0 ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 sqlText= 'SELECT s.student_id' +predicate+ ' FETCH FIRST 10001 ROWS ONLY' ;
 exec sql PREPARE countStmt FROM :sqlText ;
 if SQLCOD<>0 ;
 SqlFailure( page.result :SQLSTT ) ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 exec sql OPEN countCursor USING :c.studentNo , :c.nameKey , :c.kanaKey , :c.schoolYear , :
 c.schoolYear ,
 :c.gradeCode , :c.gradeCode , :c.classId , :c.classId , :c.unassigned , :c.anyStatus , :
 c.status( 1 ) , :c.status( 2 ) , :c.status( 3 ) , :c.status( 4 ) ,
 :c.prefectureCode , :c.prefectureCode , :c.phone , :c.phone , :c.phone , :c.fromFlag , :
 c.fromDate , :c.toFlag , :c.toDate
 ;
 if SQLCOD<>0 ;
 SqlFailure( page.result :SQLSTT ) ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 dou *off ;
 exec sql FETCH countCursor INTO :id ;
 if SQLCOD=100 ;
 leave ;
 endif ;
 if SQLCOD<>0 ;
 SqlFailure( page.result :SQLSTT ) ;
 leave ;
 endif ;
 page.total+=1 ;
 enddo ;
 exec sql CLOSE countCursor ;
 if page.result.kind<>0 ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 if page.total>10000 ;
 page.result.kind=RK_LIMIT ;
 page.result.messageId= 'W-SRC-001' ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 maxPage=%div( page.total+context.pageSize-1 :context.pageSize ) ;
 if maxPage<1 ;
 maxPage=1 ;
 endif ;
 if context.page>maxPage ;
 context.page=maxPage ;
 endif ;
 first=( context.page-1 ) *context.pageSize+1 ;
 last=first+context.pageSize-1 ;
 sqlText= 'WITH result AS(SELECT s.student_id,ROW_NUMBER() OVER(ORDER BY ' +order+ ') rn'
 +predicate+
 ') SELECT student_id FROM result WHERE rn BETWEEN ? AND ? ORDER BY rn' ;
 exec sql PREPARE pageStmt FROM :sqlText ;
 if SQLCOD<>0 ;
 SqlFailure( page.result :SQLSTT ) ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 exec sql OPEN pageCursor USING :c.studentNo , :c.nameKey , :c.kanaKey , :c.schoolYear , :
 c.schoolYear ,
 :c.gradeCode , :c.gradeCode , :c.classId , :c.classId , :c.unassigned , :c.anyStatus , :
 c.status( 1 ) , :c.status( 2 ) , :c.status( 3 ) , :c.status( 4 ) ,
 :c.prefectureCode , :c.prefectureCode , :c.phone , :c.phone , :c.phone , :c.fromFlag , :
 c.fromDate , :c.toFlag , :c.toDate , :first , :last
 ;
 if SQLCOD<>0 ;
 SqlFailure( page.result :SQLSTT ) ;
 StEndWork( *off :page.result ) ;
 return ;
 endif ;
 dou *off ;
 exec sql FETCH pageCursor INTO :id ;
 if SQLCOD=100 ;
 leave ;
 endif ;
 if SQLCOD<>0 ;
 SqlFailure( page.result :SQLSTT ) ;
 leave ;
 endif ;
 page.rowCount+=1 ;
 LoadRow( id :page.rows( page.rowCount ) :page.result ) ;
 if page.result.kind<>0 ;
 leave ;
 endif ;
 enddo ;
 exec sql CLOSE pageCursor ;
 StEndWork( *off :page.result ) ;
 if page.result.kind<>0 ;
 page.rowCount=0 ;
 return ;
 endif ;
 context.owner=principal ;
 context.applied=c ;
 context.hasApplied=*on ;
 context.lastUsed=utc ;
 page.searchedAt=utc ;
 if page.total=0 ;
 page.rangeFrom=0 ;
 page.rangeTo=0 ;
 page.result.messageId= 'I-SRC-001' ;
 else ;
 page.rangeFrom=first ;
 page.rangeTo=%min( last :page.total ) ;
 endif ;
 on-error ;
 exec sql CLOSE countCursor ;
 exec sql CLOSE pageCursor ;
 StEndWork( *off :page.result ) ;
 page.rowCount=0 ;
 page.result.kind=RK_SYSTEM ;
 page.result.messageId= 'E-COM-004' ;
 endmon ;
 end-proc ;
 dcl-proc StLookupCodes export ;
 dcl-pi *n ;
 kind varchar( 24 ) const ;
 page int( 10 ) const ;
 values varchar( 24 ) dim( 20 ) ;
 labels varucs2( 320 ) ccsid( 1200 ) dim( 20 ) ;
 count int( 10 ) ;
 result likeds( Result_t ) ;
 end-pi ;
 StLookupChoice( kind :page :0 :'' :values :labels :count :result ) ;
 end-proc ;
 dcl-proc StLookupClasses export ;
 dcl-pi *n ;
 page int( 10 ) const ;
 year int( 10 ) const ;
 grade varchar( 2 ) const ;
 values varchar( 24 ) dim( 20 ) ;
 labels varucs2( 320 ) ccsid( 1200 ) dim( 20 ) ;
 count int( 10 ) ;
 result likeds( Result_t ) ;
 end-pi ;
 StLookupChoice( 'CLASS' :page :year :grade :values :labels :count :result ) ;
 end-proc ;
 dcl-proc StEndWork export ;
 dcl-pi *n ;
 commit ind const ;
 result likeds( Result_t ) ;
 end-pi ;
 if commit ;
 exec sql COMMIT ;
 if SQLCOD<>0 ;
 result.kind=RK_UNKNOWN ;
 result.messageId= 'E-COM-004' ;
 exec sql ROLLBACK ;
 endif ;
 else ;
 exec sql ROLLBACK ;
 endif ;
 end-proc ;
