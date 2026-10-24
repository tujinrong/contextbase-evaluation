**free
 ctl-opt nomain option( *srcstmt :*nodebugio ) ccsid( *ucs2 :1200 ) ;
/copy '../copy/STUTYPES.rpgleinc'
/copy '../copy/STUPROTO.rpgleinc'
 exec sql set option commit=*cs , naming=*sql , datfmt=*iso , closqlcsr=*endactgrp ;
 dcl-proc StError export ;
 dcl-pi *n ;
 result likeds( Result_t ) ;
 field varchar( 32 ) const ;
 message char( 16 ) const ;
 end-pi ;
 result.kind=RK_VALIDATION ;
 result.messageId=message ;
 if result.errorCount<30 ;
 result.errorCount+=1 ;
 result.fieldErrors( result.errorCount ).field=field ;
 result.fieldErrors( result.errorCount ).messageId=message ;
 endif ;
 end-proc ;
 dcl-proc StAuthorize export ;
 dcl-pi *n ;
 operation varchar( 16 ) const ;
 principal varchar( 128 ) ;
 role int( 10 ) ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s allowed int( 10 ) ;
 role=0 ;
 exec sql VALUES SESSION_USER INTO :principal ;
 if SQLCOD<>0 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 return ;
 endif ;
// This COPY/compile-time group mapping is the approved deployment configuration.
// UI labels, program parameters and IFS contents never choose an execution role.
 exec sql SELECT COALESCE( MAX( CASE group_profile_name
 WHEN 'STUADMIN' THEN 3 WHEN 'STUSTAFF' THEN 2 WHEN 'STUVIEW' THEN 1 ELSE 0 END ) , 0 )
 INTO :role FROM QSYS2.GROUP_PROFILE_ENTRIES
 WHERE user_profile_name= :principal ;
 if SQLCOD<>0 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 return ;
 endif ;
 allowed=1 ;
 if role=0 ;
 allowed=0 ;
 endif ;
 if operation= 'SAVE' and role<2 ;
 allowed=0 ;
 endif ;
 if( operation= 'DELETE' or operation= 'MAINTAIN' or operation= 'CORRECT' ) and role<3 ;
 allowed=0 ;
 endif ;
 if allowed=0 ;
 result.kind=RK_FORBIDDEN ;
 result.messageId= 'E-COM-002' ;
 endif ;
 end-proc ;
 dcl-proc StClock export ;
 dcl-pi *n ;
 utc timestamp ;
 businessDay date ;
 end-pi ;
 exec sql VALUES CURRENT_TIMESTAMP - CURRENT_TIMEZONE INTO :utc ;
 businessDay=%date( utc+%hours( 9 ) ) ;
 end-proc ;
 dcl-proc StNewId export ;
 dcl-pi *n ;
 id char( 36 ) ;
 end-pi ;
 dcl-s uniqueHex char( 32 ) ;
 exec sql VALUES LOWER( HEX( GENERATE_UNIQUE( ) ) ) CONCAT '000000' INTO :uniqueHex ;
 id=%subst( uniqueHex :1 :8 ) + '-' +%subst( uniqueHex :9 :4 ) + '-' +%subst( uniqueHex :
 13 :4 ) + '-'
 +%subst( uniqueHex :17 :4 ) + '-' +%subst( uniqueHex :21 :12 ) ;
 end-proc ;
 dcl-proc StStartup export ;
 dcl-pi *n ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s count int( 10 ) ;
 dcl-s role int( 10 ) ;
 dcl-s principal varchar( 128 ) ;
 clear result ;
 StAuthorize( 'READ' :principal :role :result ) ;
 if result.kind<>0 ;
 return ;
 endif ;
 exec sql SELECT COUNT( * ) INTO :count FROM TABLE( QSYS2.OBJECT_STATISTICS( 'STUDAPP' ,
 '*FILE' ) )
 x
 WHERE OBJNAME IN( 'M_STUDENT' , 'M_CLASS' , 'MCAT' , 'M_CODE' , 'T_OPLOG' , 'STGUARD' )
 AND JOURNALED= 'YES' AND JOURNAL_NAME IS NOT NULL ;
 if SQLCOD<>0 or count<>6 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-COM-004' ;
 return ;
 endif ;
 exec sql SELECT COUNT( * ) INTO :count FROM STUDAPP.T_WRITE_GUARD WHERE GUARD_ID=1 ;
 if SQLCOD<>0 or count<>1 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-MST-001' ;
 return ;
 endif ;
 exec sql SELECT COUNT( * ) INTO :count FROM STUDAPP.M_CODE_CATEGORY
 WHERE category_id IN( 'GENDER' , 'GRADE' , 'ENROLLMENT_STATUS' , 'PREFECTURE' , 'RELATIONSHIP'
 ) ;
 if SQLCOD<>0 or count<>5 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-MST-001' ;
 endif ;
 exec sql SELECT COUNT( * ) INTO :count FROM STUDAPP.M_CODE
 WHERE( category_id= 'GENDER' AND code_value IN( '0' , '1' , '2' , '9' ) )
 OR( category_id= 'GRADE' AND code_value IN( '00' , '01' , '02' , '03' , '04' , '05' , '06' )
 )
 OR( category_id= 'ENROLLMENT_STATUS' AND code_value IN( '01' , '02' , '03' , '04' ) )
 OR( category_id= 'PREFECTURE' AND code_value BETWEEN '01' AND '47' )
 OR( category_id= 'RELATIONSHIP' AND code_value IN( '01' , '02' , '03' , '04' , '05' , '06' ,
 '07' , '99' ) ) ;
 if SQLCOD<>0 or count<>70 ;
 result.kind=RK_SYSTEM ;
 result.messageId= 'E-MST-001' ;
 endif ;
 exec sql ROLLBACK ;
 end-proc ;
 dcl-proc StNormalizeText export ;
 dcl-pi *n varucs2( 320 ) ccsid( 1200 ) ;
 raw varucs2( 320 ) ccsid( 1200 ) const ;
 rawMax int( 10 ) const ;
 savedMax int( 10 ) const ;
 mode int( 10 ) const ;
 required ind const ;
 field varchar( 32 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s out ucs2( 320 ) ccsid( 1200 ) ;
 dcl-s n int( 10 ) ;
 dcl-s rc int( 10 ) ;
 dcl-s req int( 10 ) ;
 if required ;
 req=1 ;
 else ;
 req=0 ;
 endif ;
 rc=StUnicodeNormalize( %addr( raw :*data ) :%len( raw ) :rawMax :savedMax :mode :req :
 %addr( out ) :320 :n ) ;
 if rc<>0 ;
 select ;
 when rc=1 ;
 StError( result :field :'E-STU-001' ) ;
 when rc=2 ;
 StError( result :field :'E-STU-002' ) ;
 other ;
 select ;
 when mode=3 or mode=4 ;
 StError( result :field :'E-STU-004' ) ;
 when mode=5 ;
 StError( result :field :'E-STU-003' ) ;
 when mode=7 ;
 StError( result :field :'E-STU-015' ) ;
 when mode=8 ;
 StError( result :field :'E-STU-016' ) ;
 when mode=9 ;
 StError( result :field :'E-STU-017' ) ;
 when mode=10 ;
 StError( result :field :'E-STU-005' ) ;
 other ;
 StError( result :field :'E-COM-003' ) ;
 endsl ;
 endsl ;
 return %ucs2( '' ) ;
 endif ;
 if n=0 ;
 return %ucs2( '' ) ;
 endif ;
 return %subst( out :1 :n ) ;
 end-proc ;
 dcl-proc StLong export ;
 dcl-pi *n int( 20 ) ;
 raw varucs2( 320 ) ccsid( 1200 ) const ;
 required ind const ;
 field varchar( 32 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s text varchar( 640 ) ;
 dcl-s value int( 20 ) ;
 text=%char( raw ) ;
 if text= '' ;
 if required ;
 StError( result :field :'E-STU-001' ) ;
 endif ;
 return 0 ;
 endif ;
 if %len( text ) >19 or %check( '0123456789' :text ) >0 ;
 StError( result :field :'E-COM-003' ) ;
 return 0 ;
 endif ;
 monitor ;
 value=%int( text ) ;
 on-error ;
 StError( result :field :'E-COM-003' ) ;
 return 0 ;
 endmon ;
 if value<=0 ;
 StError( result :field :'E-COM-003' ) ;
 endif ;
 return value ;
 end-proc ;
 dcl-proc StIsoDate export ;
 dcl-pi *n ;
 raw varucs2( 320 ) ccsid( 1200 ) const ;
 maximum date const ;
 value date ;
 field varchar( 32 ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s text varchar( 640 ) ;
 text=%char( raw ) ;
 if %len( text ) <>10 or %subst( text :5 :1 ) <> '-' or %subst( text :8 :1 ) <> '-' or
 %check( '0123456789' :%subst( text :1 :4 ) +%subst( text :6 :2 ) +%subst( text :9 :2
 ) ) >0 ;
 StError( result :field :'E-STU-005' ) ;
 return ;
 endif ;
 monitor ;
 value=%date( text :*iso ) ;
 on-error ;
 StError( result :field :'E-STU-005' ) ;
 return ;
 endmon ;
 if value<d '1900-01-01' or value>maximum ;
 StError( result :field :'E-DATE-002' ) ;
 endif ;
 end-proc ;
 dcl-proc StParseBirthDate export ;
 dcl-pi *n ;
 era varchar( 10 ) const ;
 year varucs2( 8 ) ccsid( 1200 ) const ;
 month varucs2( 4 ) ccsid( 1200 ) const ;
 day varucs2( 4 ) ccsid( 1200 ) const ;
 businessDay date const ;
 birth date ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s y int( 10 ) ;
 dcl-s m int( 10 ) ;
 dcl-s d int( 10 ) ;
 dcl-s offset int( 10 ) ;
 dcl-s begin date ;
 dcl-s finish date ;
 dcl-s text varucs2( 320 ) ccsid( 1200 ) ;
 dcl-s iso char( 10 ) ;
 dcl-s before int( 10 ) ;
 dcl-s reverseEra varchar( 10 ) ;
 dcl-s reverseYear varucs2( 8 ) ccsid( 1200 ) ;
 dcl-s reverseMonth varucs2( 4 ) ccsid( 1200 ) ;
 dcl-s reverseDay varucs2( 4 ) ccsid( 1200 ) ;
 dcl-s display varucs2( 80 ) ccsid( 1200 ) ;
 before=result.errorCount ;
 select ;
 when era= 'MEIJI' ;
 offset=1867 ;
 begin=d'1900-01-01' ;
 finish=d'1912-07-29' ;
 when era= 'TAISHO' ;
 offset=1911 ;
 begin=d'1912-07-30' ;
 finish=d'1926-12-24' ;
 when era= 'SHOWA' ;
 offset=1925 ;
 begin=d'1926-12-25' ;
 finish=d'1989-01-07' ;
 when era= 'HEISEI' ;
 offset=1988 ;
 begin=d'1989-01-08' ;
 finish=d'2019-04-30' ;
 when era= 'REIWA' ;
 offset=2018 ;
 begin=d'2019-05-01' ;
 finish=d'9999-12-31' ;
 other ;
 StError( result :'birthDate' :'E-DATE-001' ) ;
 return ;
 endsl ;
 if year=U '5143' ;
 y=1 ;
 else ;
 text=StNormalizeText( year :4 :4 :11 :*on :'birthDate' :result ) ;
 y=StLong( text :*on :'birthDate' :result ) ;
 endif ;
 text=StNormalizeText( month :2 :2 :11 :*on :'birthDate' :result ) ;
 m=StLong( text :*on :'birthDate' :result ) ;
 text=StNormalizeText( day :2 :2 :11 :*on :'birthDate' :result ) ;
 d=StLong( text :*on :'birthDate' :result ) ;
 if before<>result.errorCount ;
 return ;
 endif ;
 if y+offset>9999 or m>12 or d>31 ;
 StError( result :'birthDate' :'E-DATE-001' ) ;
 return ;
 endif ;
 iso=%subst( %char( 10000+y+offset ) :2 :4 ) + '-' +%subst( %char( 100+m ) :2 :2 ) + '-'
 +%subst( %char( 100+d ) :2 :2 ) ;
 StIsoDate( %ucs2( iso ) :businessDay :birth :'birthDate' :result ) ;
 if before<>result.errorCount ;
 return ;
 endif ;
 if birth<begin or birth>finish ;
 StError( result :'birthDate' :'E-DATE-001' ) ;
 return ;
 endif ;
 StFormatBirthDate( birth :reverseEra :reverseYear :reverseMonth :reverseDay :display ) ;
 if reverseEra<>era or %int( %char( reverseYear ) ) <>y ;
 StError( result :'birthDate' :'E-DATE-001' ) ;
 endif ;
 end-proc ;
 dcl-proc StFormatBirthDate export ;
 dcl-pi *n ;
 birth date const ;
 era varchar( 10 ) ;
 year varucs2( 8 ) ccsid( 1200 ) ;
 month varucs2( 4 ) ccsid( 1200 ) ;
 day varucs2( 4 ) ccsid( 1200 ) ;
 display varucs2( 80 ) ccsid( 1200 ) ;
 end-pi ;
 dcl-s offset int( 10 ) ;
 dcl-s name varucs2( 4 ) ccsid( 1200 ) ;
 dcl-s iso char( 10 ) ;
 select ;
 when birth>=d'2019-05-01' ;
 era= 'REIWA' ;
 offset=2018 ;
 name=U '4EE4548C' ;
 when birth>=d'1989-01-08' ;
 era= 'HEISEI' ;
 offset=1988 ;
 name=U '5E736210' ;
 when birth>=d'1926-12-25' ;
 era= 'SHOWA' ;
 offset=1925 ;
 name=U '662D548C' ;
 when birth>=d'1912-07-30' ;
 era= 'TAISHO' ;
 offset=1911 ;
 name=U '59276B63' ;
 other ;
 era= 'MEIJI' ;
 offset=1867 ;
 name=U '660E6CBB' ;
 endsl ;
 year=%ucs2( %char( %subdt( birth :*years ) -offset ) ) ;
 iso=%char( birth :*iso ) ;
 month=%ucs2( %subst( iso :6 :2 ) ) ;
 day=%ucs2( %subst( iso :9 :2 ) ) ;
 if year=%ucs2( '1' ) ;
 display=name+U '51435E74' +month+U '6708' +day+U '65E5' ;
 else ;
 display=name+year+U '5E74' +month+U '6708' +day+U '65E5' ;
 endif ;
 end-proc ;
 dcl-proc StNormalize export ;
 dcl-pi *n ;
 raw likeds( StudentRaw_t ) const ;
 work likeds( StudentWork_t ) ;
 businessDay date const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s temp varucs2( 320 ) ccsid( 1200 ) ;
 clear work ;
/copy '../copy/STUNORM.rpgleinc'
 end-proc ;
 dcl-proc StValidate export ;
 dcl-pi *n ;
 work likeds( StudentWork_t ) const ;
 result likeds( Result_t ) ;
 end-pi ;
 dcl-s emergency int( 10 ) ;
 if work.birthDate>work.admissionDate ;
 StError( result :'admissionDate' :'E-STU-007' ) ;
 endif ;
 if work.enrollmentStatusCode<> '01' and work.enrollmentStatusCode<> '02' and
 work.enrollmentStatusCode<> '03' and work.enrollmentStatusCode<> '04' ;
 StError( result :'enrollmentStatusCode' :'E-STU-009' ) ;
 endif ;
 if work.enrollmentStatusCode= '01' or work.enrollmentStatusCode= '02' ;
 if work.enrollmentEndDateInd>=0 ;
 StError( result :'enrollmentEndDate' :'E-STU-008' ) ;
 endif ;
 if work.classIdInd<0 ;
 StError( result :'classId' :'E-STU-012' ) ;
 endif ;
 else ;
 if work.enrollmentEndDateInd<0 or work.enrollmentEndDate<work.admissionDate ;
 StError( result :'enrollmentEndDate' :'E-STU-008' ) ;
 endif ;
 endif ;
 if work.phoneNumberInd<0 and work.emailAddressInd<0 and work.emergencyPhoneNumberInd<0 ;
 StError( result :'phoneNumber' :'E-STU-018' ) ;
 endif ;
 emergency=0 ;
 if work.emergencyContactNameInd=0 ;
 emergency+=1 ;
 endif ;
 if work.relationshipCodeInd=0 ;
 emergency+=1 ;
 endif ;
 if work.emergencyPhoneNumberInd=0 ;
 emergency+=1 ;
 endif ;
 if emergency<>0 and emergency<>3 ;
 StError( result :'emergencyContactName' :'E-STU-019' ) ;
 endif ;
 end-proc ;
 dcl-proc StEscapeLike export ;
 dcl-pi *n varucs2( 642 ) ccsid( 1200 ) ;
 value varucs2( 320 ) ccsid( 1200 ) const ;
 prefix ind const ;
 end-pi ;
 dcl-s out varucs2( 642 ) ccsid( 1200 ) ;
 dcl-s i int( 10 ) ;
 dcl-s cp ucs2( 1 ) ccsid( 1200 ) ;
 if prefix ;
 out=%ucs2( '' ) ;
 else ;
 out=%ucs2( '%' ) ;
 endif ;
 for i=1 to %len( value ) ;
 cp=%subst( value :i :1 ) ;
 if cp=U '0021' or cp=U '0025' or cp=U '005F' or cp=U '005B' ;
 out+=U '0021' ;
 endif ;
 out+=cp ;
 endfor ;
 return out+U '0025' ;
 end-proc ;
 dcl-proc StHash export ;
 dcl-pi *n char( 64 ) ;
 value varucs2( 8000 ) ccsid( 1200 ) const ;
 end-pi ;
 dcl-s digest char( 64 ) ;
 StUnicodeDigest( %addr( value :*data ) :%len( value ) :digest ) ;
 return digest ;
 end-proc ;
 dcl-proc StBusinessHash export ;
 dcl-pi *n char( 64 ) ;
 work likeds( StudentWork_t ) const ;
 end-pi ;
 dcl-s canonical varucs2( 8000 ) ccsid( 1200 ) ;
 dcl-s piece varucs2( 320 ) ccsid( 1200 ) ;
/copy '../copy/STUHASH.rpgleinc'
 return StHash( canonical ) ;
 end-proc ;
 dcl-proc StConfirm export ;
 dcl-pi *n ind ;
 value likeds( Confirmation_t ) const ;
 owner varchar( 128 ) const ;
 job varchar( 28 ) const ;
 instance char( 36 ) const ;
 id int( 20 ) const ;
 version int( 20 ) const ;
 business char( 64 ) const ;
 candidates char( 64 ) const ;
 utc timestamp const ;
 reason varucs2( 120 ) ccsid( 1200 ) const ;
 end-pi ;
 return not value.consumed and value.owner=owner and value.job=job and
 value.instanceId=instance and value.studentId=id and value.expectedVersion=version and
 value.businessHash=business and value.candidatesHash=candidates and
 value.expiresAt>utc and %len( reason ) >0 ;
 end-proc ;
 dcl-proc StMessage export ;
 dcl-pi *n varucs2( 320 ) ccsid( 1200 ) ;
 code char( 16 ) const ;
 end-pi ;
 dcl-s text varucs2( 320 ) ccsid( 1200 ) ;
 select ;
 when code= 'I-SRC-001' ;
 text=%ucs2( '該当する学生がありません。' ) ;
 when code= 'I-STU-001' ;
 text=%ucs2( '学生を登録しました。（学籍番号：{studentNo}）' ) ;
 when code= 'I-STU-002' ;
 text=%ucs2( '学生情報を更新しました。' ) ;
 when code= 'I-STU-003' ;
 text=%ucs2( '学生情報を論理削除しました。' ) ;
 when code= 'I-STU-004' ;
 text=%ucs2( '変更内容がありません。' ) ;
 when code= 'W-SRC-001' ;
 text=%ucs2( '検索結果が10,000件を超えています。検' +
 '索条件を追加してください。' ) ;
 when code= 'W-SRC-002' ;
 text=%ucs2( '検索条件の保持期限が切れました。条' +
 '件を再指定してください。' ) ;
 when code= 'W-STU-101' ;
 text=%ucs2( '同じ生年月日で氏名または氏名カナが' +
 '一致する学生が{count}件あります。別人' +
 'であることを確認してください。' ) ;
 when code= 'W-STU-102' ;
 text=%ucs2( '入力内容または重複候補が変わりまし' +
 'た。もう一度確認してください。' ) ;
 when code= 'W-STU-103' ;
 text=%ucs2( '変更内容を破棄して戻りますか。' ) ;
 when code= 'W-STU-104' ;
 text=%ucs2( '入力内容を取り消しますか。' ) ;
 when code= 'W-STU-105' ;
 text=%ucs2( 'この学生を論理削除します。削除後は' +
 '通常検索できません。よろしいですか' + '。' ) ;
 when code= 'W-STU-106' ;
 text=%ucs2( '所属クラスが利用期間外です。住所等' +
 'は変更できますが、クラスの見直しが' + '必要です。' ) ;
 when code= 'W-STU-107' ;
 text=%ucs2( '選択条件が変わったためクラスの選択' + 'を解除しました。'
 ) ;
 when code= 'W-STU-108' ;
 text=%ucs2( '登録可能なクラスがありません。クラ' +
 'スマスタを確認してください。' ) ;
 when code= 'W-STU-109' ;
 text=%ucs2( '最新情報を再読み込みすると入力中の' +
 '変更は破棄されます。続行しますか。' ) ;
 when code= 'W-MST-001' ;
 text=%ucs2( '同じ年度・学年に同名のクラスがあり' +
 'ます。クラスコードと名称を確認して' + 'ください。' ) ;
 when code= 'E-STU-001' ;
 text=%ucs2( '{field}を入力してください。' ) ;
 when code= 'E-STU-002' ;
 text=%ucs2( '{field}は{max}文字以内の使用可能な文字' +
 'で入力してください。' ) ;
 when code= 'E-STU-003' ;
 text=%ucs2( '学籍番号は半角英数字・ハイフンで15' +
 '文字以内にしてください。先頭は英数' + '字です。' ) ;
 when code= 'E-STU-004' ;
 text=%ucs2( '氏名カナはカタカナで入力してくださ' +
 'い。中点・長音・空白は使用できます' + '。' ) ;
 when code= 'E-STU-005' ;
 text=%ucs2( '{field}に正しい日付を入力してください。' ) ;
 when code= 'E-STU-006' ;
 text=%ucs2( '{fromField}は{toField}以前の日付にしてください。' ) ;
 when code= 'E-STU-007' ;
 text=%ucs2( '生年月日・入学日は本日以前とし、生' +
 '年月日≦入学日となるよう入力してく' + 'ださい。' ) ;
 when code= 'E-STU-008' ;
 text=%ucs2( '在籍区分に対応する卒業・退学日を設' + '定してください。'
 ) ;
 when code= 'E-STU-009' ;
 text=%ucs2( '{field}のコードが存在しません。選択し' + '直してください。'
 ) ;
 when code= 'E-STU-010' ;
 text=%ucs2( '指定したクラスが存在しません。選択' +
 'し直してください。' ) ;
 when code= 'E-STU-011' ;
 text=%ucs2( '{field}は現在使用できないコードです。' +
 '選択し直してください。' ) ;
 when code= 'E-STU-012' ;
 text=%ucs2( '在学・休学の学生はクラスを選択してください。' ) ;
 when code= 'E-STU-013' ;
 text=%ucs2( 'このクラスには新たに所属できません' +
 '。利用可否と利用期間を確認してくだ' + 'さい。' ) ;
 when code= 'E-STU-014' ;
 text=%ucs2( '年度・学年と選択したクラスが一致していません。' ) ;
 when code= 'E-STU-015' ;
 text=%ucs2( '郵便番号は7桁の数字で入力してください。' ) ;
 when code= 'E-STU-016' ;
 text=%ucs2( '{field}の形式が正しくありません。国内' +
 '10～11桁または国番号付きの番号を入力' + 'してください。' ) ;
 when code= 'E-STU-017' ;
 text=%ucs2( 'メールアドレスの形式が正しくありません。' ) ;
 when code= 'E-STU-018' ;
 text=%ucs2( '本人電話、本人メール、緊急連絡先電' +
 '話のいずれかを入力してください。' ) ;
 when code= 'E-STU-019' ;
 text=%ucs2( '緊急連絡先は氏名・続柄・電話番号を' +
 'すべて入力してください。' ) ;
 when code= 'E-STU-020' ;
 text=%ucs2( '削除理由を60文字以内で入力してください。' ) ;
 when code= 'E-STU-101' ;
 text=%ucs2( 'この学籍番号は使用済みです。入力を' +
 '確認してください。直前の送信結果が' +
 '不明な場合は検索で登録状況を確認し' + 'てください。' ) ;
 when code= 'E-STU-102' ;
 text=%ucs2( 'クラスの定員を超えるため保存できま' +
 'せん。別のクラスを選択してください' + '。' ) ;
 when code= 'E-STU-103' ;
 text=%ucs2( '対象の学生が見つからないか、既に削' + '除されています。'
 ) ;
 when code= 'E-STU-104' ;
 text=%ucs2( '登録済みの学籍番号は変更できません。' ) ;
 when code= 'E-STU-105' ;
 text=%ucs2( '他の操作で更新されています。入力内' +
 '容を控え、最新情報を再読み込みして' + 'ください。' ) ;
 when code= 'E-STU-106' ;
 text=%ucs2( '卒業・退学からの在籍区分変更には管' +
 '理者権限と変更理由が必要です。' ) ;
 when code= 'E-STU-107' ;
 text=%ucs2( '確認・変更理由を60文字以内で入力してください。' ) ;
 when code= 'E-SRC-001' ;
 text=%ucs2( '未所属のみを検索する場合、年度・学' +
 '年・クラスは指定できません。' ) ;
 when code= 'E-SRC-002' ;
 text=%ucs2( '検索条件または表示指定が正しくありません。' ) ;
 when code= 'E-MST-001' ;
 text=%ucs2( 'マスタの初期設定が不足しています。' +
 '管理者に連絡してください。' ) ;
 when code= 'E-MST-002' ;
 text=%ucs2( 'このコードまたはクラスコードは既に' +
 '登録されています。' ) ;
 when code= 'E-MST-003' ;
 text=%ucs2( '参照中または保護対象のため、このマ' +
 'スタ変更はできません。' ) ;
 when code= 'E-MST-004' ;
 text=%ucs2( '定員または利用期間が現在の所属状況' + 'と整合しません。'
 ) ;
 when code= 'E-COM-001' ;
 text=%ucs2( 'ログインの有効期限が切れました。再' +
 '度ログインしてください。' ) ;
 when code= 'E-COM-002' ;
 text=%ucs2( 'この操作を行う権限がありません。' ) ;
 when code= 'E-COM-003' ;
 text=%ucs2( '画面情報が無効です。画面を開き直してください。' ) ;
 when code= 'E-COM-004' ;
 text=%ucs2( '処理を完了できませんでした。受付番号：{correlationId}' ) ;
 when code= 'E-STU-108' ;
 text=%ucs2( '最終所属クラスの利用期間が学生の在' +
 '籍期間と重なっていません。クラスま' +
 'たは在籍日付を確認してください。' ) ;
 when code= 'E-DATE-001' ;
 text=%ucs2( '生年月日の元号・年・月・日を確認してください。' ) ;
 when code= 'E-DATE-002' ;
 text=%ucs2( '{field}は{minDate}から{maxDate}までの日付で' +
 '入力してください。' ) ;
 when code= 'E-DATE-003' ;
 text=%ucs2( '{field}は西暦4桁の{minYear}年から{maxYear}' +
 '年で指定してください。' ) ;
 other ;
 text=%ucs2( '画面情報が無効です。画面を開き直してください。' ) ;
 endsl ;
 return text ;
 end-proc ;
