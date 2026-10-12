from emit_cobol import program,put
def html(text):return "    DISPLAY '"+text.replace("'","''")+"' WITH NO ADVANCING\n"
def inputfield(name,label,index,kind='text',maxlen=120):
 return (f'    MOVE {index} TO I\n'+html(f'<label for="{name}">{label}</label><input id="{name}" name="{name}" type="{kind}" maxlength="{maxlen*2}" value="')+'''    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
'''+("    IF STUDENT-ID > 0 DISPLAY '\" readonly' WITH NO ADVANCING\n    ELSE DISPLAY '\"' WITH NO ADVANCING END-IF\n" if name=='studentNo' else html('"'))+html('>'))
def hidden(name,data,length):return html(f'<input type="hidden" name="{name}" value="')+f'    CALL "STESC" USING {data} BY VALUE {length} END-CALL\n'+html('">')
def selectfield(name,label,index,category):
 return html(f'<label for="{name}">{label}</label><select id="{name}" name="{name}"><option value="">未選択／すべて</option>')+f'    MOVE {index} TO UI-FIELD MOVE "{category}" TO UI-CATEGORY\n    CALL "STMLOOK" END-CALL\n'+html('</select>')
program('STMCHECK','''    MOVE "INIT-CHECK" TO COMMAND-NAME PERFORM DB-RESET
    PERFORM DB-EXECUTE IF RC NOT = 0 GOBACK END-IF
    CALL "STFETCH" USING ST-DB-RESULT RETURNING RC END-CALL
    IF RC NOT = 1 MOVE 503 TO APP-STATUS GOBACK END-IF
    MOVE 1 TO K PERFORM FETCH-TEMP
    IF TMP-DATA(1:1) NOT = "5" PERFORM MISSING-MASTERS END-IF
    MOVE 2 TO K PERFORM FETCH-TEMP
    IF TMP-DATA(1:1) NOT = "6" PERFORM MISSING-MASTERS END-IF
    CALL "STCURSOR" USING ST-DB-RESULT END-CALL GOBACK.
MISSING-MASTERS.
    MOVE 503 TO APP-STATUS MOVE "SystemError" TO APP-OUTCOME
    MOVE "E-MST-001: マスタ初期設定が不足しています。" TO ERROR-TEXT
    PERFORM ADD-ERROR.
''')
program('STMSG','''    IF APP-MESSAGE-LENGTH = 0
      EVALUATE APP-OUTCOME
        WHEN "NoChange" MOVE "I-STU-004: 変更内容がありません。" TO APP-MESSAGE
        WHEN "Unknown" MOVE "E-COM-004: 結果不明です。再送せず検索で確認してください。" TO APP-MESSAGE
        WHEN "Conflict" MOVE "E-STU-105: 最新情報へ再読込してください。" TO APP-MESSAGE
        WHEN "NotFound" MOVE "E-STU-103: 対象が見つかりません。" TO APP-MESSAGE
      END-EVALUATE
      COMPUTE APP-MESSAGE-LENGTH = FUNCTION LENGTH(FUNCTION TRIM(APP-MESSAGE))
    END-IF
    GOBACK.
''')
program('STFLASH','''    MOVE "Flash" TO STATE-KIND
    IF APP-OUTCOME = "Saved"
      INITIALIZE FLASH-PAYLOAD
      EVALUATE R-DATA(F-ACTION)
        WHEN "DELETE" MOVE "I-STU-003: 学生情報を論理削除しました。" TO FLASH-MESSAGE
        WHEN OTHER
          IF STUDENT-ID = 0
            MOVE "I-STU-001: 学生を登録しました。" TO FLASH-MESSAGE
          ELSE MOVE "I-STU-002: 学生情報を更新しました。" TO FLASH-MESSAGE END-IF
      END-EVALUATE
      COMPUTE FLASH-LENGTH = FUNCTION LENGTH(FUNCTION TRIM(FLASH-MESSAGE))
      CALL "STSTATEIO" USING BY VALUE DB-HANDLE 1
        BY REFERENCE FLASH-ID STATE-KIND OWNER-VALUE SESSION-VALUE TAB-ID
          FLASH-PAYLOAD BY VALUE LENGTH OF FLASH-PAYLOAD
        BY REFERENCE FLASH-REVISION BY VALUE 10 RETURNING RC END-CALL
      IF RC NOT = 0 MOVE SPACES TO FLASH-ID END-IF
    ELSE
      IF R-NULL(F-FLASHID) = 0
        MOVE R-DATA(F-FLASHID) TO FLASH-ID
        CALL "STSTATEIO" USING BY VALUE DB-HANDLE 2
          BY REFERENCE FLASH-ID STATE-KIND OWNER-VALUE SESSION-VALUE TAB-ID
            FLASH-PAYLOAD BY VALUE LENGTH OF FLASH-PAYLOAD
          BY REFERENCE FLASH-REVISION BY VALUE 10 RETURNING RC END-CALL
        IF RC = 0
          CALL "STSTATEIO" USING BY VALUE DB-HANDLE 4
            BY REFERENCE FLASH-ID STATE-KIND OWNER-VALUE SESSION-VALUE TAB-ID
              FLASH-PAYLOAD BY VALUE LENGTH OF FLASH-PAYLOAD
            BY REFERENCE FLASH-REVISION BY VALUE 10 RETURNING RC END-CALL
          IF RC = 0 AND FLASH-LENGTH >= 0 AND <= 1024
            MOVE FLASH-MESSAGE TO APP-MESSAGE
            MOVE FLASH-LENGTH TO APP-MESSAGE-LENGTH
          END-IF
        END-IF
      END-IF
    END-IF
    GOBACK.
''')
program('STCAND','''    CALL "STHINT" END-CALL
    IF APP-STATUS NOT = 200 GOBACK END-IF
    IF N-DATA(28)(1:2) = "01" OR "02"
      INITIALIZE R-VALUE(F-ENROLLMENTENDDATE)
      MOVE -1 TO R-NULL(F-ENROLLMENTENDDATE)
    END-IF
    IF R-NULL(F-CLASSID) = 0
      MOVE "ST-CLASS" TO COMMAND-NAME PERFORM DB-RESET
      MOVE 3 TO PARAM-TYPE MOVE F-CLASSID TO PARAM-FIELD PERFORM ADD-RAW
      PERFORM DB-EXECUTE IF RC NOT = 0 GOBACK END-IF
      CALL "STFETCH" USING ST-DB-RESULT RETURNING RC END-CALL
      IF RC NOT = 1 PERFORM CLEAR-CLASS
      ELSE
        MOVE 1 TO K PERFORM FETCH-TEMP
        IF N-NULL(27) = 0 AND N-DATA(27) NOT = TMP-DATA
          PERFORM CLEAR-CLASS
        ELSE MOVE TMP-VALUE TO R-VALUE(F-SCHOOLYEAR) END-IF
        MOVE 2 TO K PERFORM FETCH-TEMP
        IF N-NULL(26) = 0 AND N-DATA(26) NOT = TMP-DATA
          PERFORM CLEAR-CLASS
        ELSE MOVE TMP-VALUE TO R-VALUE(F-GRADECODE) END-IF
      END-IF
      CALL "STCURSOR" USING ST-DB-RESULT END-CALL
    END-IF
    GOBACK.
CLEAR-CLASS.
    INITIALIZE R-VALUE(F-CLASSID) MOVE -1 TO R-NULL(F-CLASSID)
    MOVE "W-STU-107: 選択条件が変わったためクラス選択を解除しました。"
      TO APP-MESSAGE
    COMPUTE APP-MESSAGE-LENGTH = FUNCTION LENGTH(FUNCTION TRIM(APP-MESSAGE)).
''')
lookup='''    IF UI-CATEGORY = "CLASS" OR "YEAR"
      IF VIEW-MODE = "Edit" MOVE "CLASS-EDIT" TO COMMAND-NAME
      ELSE MOVE "CLASS-LIST" TO COMMAND-NAME END-IF
    ELSE MOVE "CODE-LIST" TO COMMAND-NAME END-IF
    PERFORM DB-RESET PERFORM DB-EXECUTE IF RC NOT = 0 GOBACK END-IF
    MOVE SPACES TO PREVIOUS-YEAR
    PERFORM UNTIL EXIT
      CALL "STFETCH" USING ST-DB-RESULT RETURNING RC END-CALL
      IF RC NOT = 1 EXIT PERFORM END-IF
      IF UI-CATEGORY = "CLASS" OR "YEAR"
        MOVE 10 TO COLUMN-COUNT
        IF VIEW-MODE = "Edit" MOVE 11 TO COLUMN-COUNT END-IF
      ELSE MOVE 7 TO COLUMN-COUNT END-IF
      PERFORM VARYING K FROM 1 BY 1 UNTIL K > COLUMN-COUNT
        CALL "STCOLUMN" USING BY REFERENCE ST-DB-RESULT BY VALUE K
          BY REFERENCE LOOKUP-VALUE(K) RETURNING RC END-CALL
        IF RC NOT = 0 EXIT PERFORM END-IF
      END-PERFORM
      IF RC NOT = 0 EXIT PERFORM END-IF
      MOVE 1 TO SELECTABLE SHOW-OPTION
      IF UI-CATEGORY = "YEAR"
        IF LOOKUP-DATA(2) = PREVIOUS-YEAR MOVE 0 TO SHOW-OPTION
        ELSE MOVE LOOKUP-DATA(2) TO PREVIOUS-YEAR END-IF
        MOVE LOOKUP-VALUE(2) TO TMP-VALUE
      ELSE
        IF UI-CATEGORY = "CLASS"
          MOVE LOOKUP-VALUE(1) TO TMP-VALUE
          IF N-NULL(27) = 0 AND LOOKUP-DATA(2) NOT = N-DATA(27)
            MOVE 0 TO SHOW-OPTION END-IF
          IF N-NULL(26) = 0 AND LOOKUP-DATA(3) NOT = N-DATA(26)
            MOVE 0 TO SHOW-OPTION END-IF
          IF VIEW-MODE = "Edit"
            IF N-DATA(28)(1:2) = "03" OR "04"
              IF R-NULL(F-ADMISSIONDATE) = -1 OR R-NULL(F-ENROLLMENTENDDATE) = -1
                OR LOOKUP-DATA(6)(1:10) > R-DATA(F-ENROLLMENTENDDATE)(1:10)
                OR LOOKUP-DATA(7)(1:10) < R-DATA(F-ADMISSIONDATE)(1:10)
                MOVE 0 TO SELECTABLE END-IF
            ELSE
              IF LOOKUP-DATA(8)(1:1) NOT = "1" OR
                LOOKUP-DATA(6)(1:10) > BUSINESS-DAY OR
                LOOKUP-DATA(7)(1:10) < BUSINESS-DAY MOVE 0 TO SELECTABLE END-IF
            END-IF
            IF LOOKUP-DATA(1) = UI-CURRENT MOVE 1 TO SELECTABLE END-IF
          END-IF
        ELSE
          IF LOOKUP-DATA(1) NOT = UI-CATEGORY MOVE 0 TO SHOW-OPTION END-IF
          MOVE LOOKUP-VALUE(2) TO TMP-VALUE
          IF VIEW-MODE = "Edit"
            IF LOOKUP-DATA(4)(1:1) NOT = "1" OR LOOKUP-DATA(5)(1:1) NOT = "1"
              OR LOOKUP-DATA(6)(1:10) > BUSINESS-DAY OR
              (LOOKUP-NULL(7) = 0 AND LOOKUP-DATA(7)(1:10) < BUSINESS-DAY)
              MOVE 0 TO SELECTABLE END-IF
            IF LOOKUP-DATA(2) = UI-CURRENT MOVE 1 TO SELECTABLE END-IF
          END-IF
        END-IF
      END-IF
      IF SHOW-OPTION = 1
'''+html('<option value="')+'''        CALL "STESC" USING TMP-DATA BY VALUE TMP-LENGTH END-CALL
'''+html('"')+'''        IF R-LENGTH(UI-FIELD) = TMP-LENGTH AND R-DATA(UI-FIELD) = TMP-DATA
          DISPLAY ' selected' WITH NO ADVANCING END-IF
        IF SELECTABLE = 0 DISPLAY ' disabled' WITH NO ADVANCING END-IF
        DISPLAY '>' WITH NO ADVANCING
        EVALUATE UI-CATEGORY
          WHEN "YEAR" CALL "STESC" USING LOOKUP-DATA(2) BY VALUE LOOKUP-LENGTH(2) END-CALL
          WHEN "CLASS"
            CALL "STESC" USING LOOKUP-DATA(2) BY VALUE LOOKUP-LENGTH(2) END-CALL
            DISPLAY '／' WITH NO ADVANCING
            IF LOOKUP-NULL(10) = -1 DISPLAY "不整合" WITH NO ADVANCING
            ELSE CALL "STESC" USING LOOKUP-DATA(10) BY VALUE LOOKUP-LENGTH(10) END-CALL END-IF
            DISPLAY '／' WITH NO ADVANCING
            CALL "STESC" USING LOOKUP-DATA(4) BY VALUE LOOKUP-LENGTH(4) END-CALL
            DISPLAY ' ' WITH NO ADVANCING
            CALL "STESC" USING LOOKUP-DATA(5) BY VALUE LOOKUP-LENGTH(5) END-CALL
            IF LOOKUP-DATA(8)(1:1) NOT = "1" DISPLAY '（停止）' WITH NO ADVANCING END-IF
            IF LOOKUP-DATA(6)(1:10) > BUSINESS-DAY OR LOOKUP-DATA(7)(1:10) < BUSINESS-DAY
              DISPLAY '（期間外）' WITH NO ADVANCING END-IF
            IF VIEW-MODE = "Edit"
              DISPLAY ' 人数参考 ' WITH NO ADVANCING
              CALL "STESC" USING LOOKUP-DATA(11) BY VALUE LOOKUP-LENGTH(11) END-CALL
              DISPLAY '／定員 ' WITH NO ADVANCING
              IF LOOKUP-NULL(9) = -1 DISPLAY '制限なし' WITH NO ADVANCING
              ELSE CALL "STESC" USING LOOKUP-DATA(9) BY VALUE LOOKUP-LENGTH(9) END-CALL END-IF
            END-IF
          WHEN OTHER
            CALL "STESC" USING LOOKUP-DATA(3) BY VALUE LOOKUP-LENGTH(3) END-CALL
            IF LOOKUP-DATA(4)(1:1) NOT = "1" DISPLAY '（停止）' WITH NO ADVANCING END-IF
        END-EVALUATE
        DISPLAY '</option>' WITH NO ADVANCING
      END-IF
    END-PERFORM
    CALL "STCURSOR" USING ST-DB-RESULT END-CALL GOBACK.
'''
program('STMLOOK',lookup,'''01 SELECTABLE PIC S9(9) COMP-5.
01 SHOW-OPTION PIC S9(9) COMP-5.
01 COLUMN-COUNT PIC S9(9) COMP-5.
01 PREVIOUS-YEAR PIC X(1024).
''')
render='''    CALL "STMSG" END-CALL
    IF APP-STATUS = 200 CALL "STHINT" END-CALL END-IF
    CALL "STOUTPUTBEGIN" RETURNING RC END-CALL
    IF RC NOT = 0
      MOVE 503 TO APP-STATUS
      CALL "STHEADER" USING BY VALUE APP-STATUS END-CALL
      DISPLAY "E-COM-004: 応答を作成できません。" GOBACK END-IF
'''+html('<!doctype html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>学生管理</title><link rel="stylesheet" href="/student-assets/style.css"><script defer src="/student-assets/site.js"></script></head><body><header><strong>学生管理</strong></header><main>')+'''    IF APP-STATUS NOT = 401 AND OWNER-LENGTH > 0
      DISPLAY '<nav><a href="/student-assets/index.html">メニュー</a> 利用者：' WITH NO ADVANCING
      CALL "STESC" USING OWNER-DATA BY VALUE OWNER-LENGTH END-CALL
      EVALUATE ROLE-CODE
        WHEN 0 DISPLAY ' 参照者' WITH NO ADVANCING
        WHEN 1 DISPLAY '担当者' WITH NO ADVANCING
        WHEN 2 DISPLAY '管理者' WITH NO ADVANCING
      END-EVALUATE
      DISPLAY ' 業務日 ' BUSINESS-DAY '</nav>' WITH NO ADVANCING
    END-IF
    IF APP-MESSAGE-LENGTH > 0
      DISPLAY '<p role="status">' WITH NO ADVANCING
      CALL "STESC" USING APP-MESSAGE BY VALUE APP-MESSAGE-LENGTH END-CALL
      DISPLAY '</p>' WITH NO ADVANCING
    END-IF
    IF APP-ERRORS-LENGTH > 1
      DISPLAY '<pre role="alert">' WITH NO ADVANCING
      COMPUTE K = APP-ERRORS-LENGTH - 1
      CALL "STESC" USING APP-ERRORS BY VALUE K END-CALL
      DISPLAY '</pre>' WITH NO ADVANCING
    END-IF
    IF DB-HANDLE = NULL OR APP-STATUS = 401 OR 400 OR 405
      DISPLAY '</main></body></html>'
      CALL "STOUTPUTEND" USING BY VALUE APP-STATUS END-CALL GOBACK END-IF
    IF VIEW-MODE = "Edit" PERFORM EDIT-SCREEN
    ELSE PERFORM SEARCH-SCREEN END-IF
    DISPLAY '</main></body></html>'
    CALL "STOUTPUTEND" USING BY VALUE APP-STATUS END-CALL GOBACK.
COMMON-HIDDEN.
'''+hidden('contextId','CONTEXT-ID',64)+hidden('tabId','TAB-ID',64)+hidden('csrfToken','CSRF-TOKEN',64)+'''    MOVE CONTEXT-REVISION TO V PERFORM ID-AS-TEMP
'''+hidden('contextRevision','TMP-DATA','TMP-LENGTH')+'''.
EDITOR-HIDDEN.
    PERFORM COMMON-HIDDEN
'''+hidden('editorId','EDITOR-ID',64)+'''    IF STUDENT-ID > 0
      MOVE STUDENT-ID TO V PERFORM ID-AS-TEMP
'''+hidden('studentId','TMP-DATA','TMP-LENGTH')+'''      MOVE EXPECTED-VERSION TO V PERFORM ID-AS-TEMP
'''+hidden('expectedVersion','TMP-DATA','TMP-LENGTH')+'''    END-IF.
SEARCH-SCREEN.
'''+html('<h1>学生検索</h1><form method="post" action="student.cgi"><fieldset><legend>検索条件</legend>')+'''    PERFORM COMMON-HIDDEN
'''
for name,label,index,maxlen in [('studentNo','学籍番号',4,15),('studentName','氏名',5,8),('studentNameKana','氏名カナ',6,36)]:render+=inputfield(name,label,index,maxlen=maxlen)
render+=selectfield('schoolYear','年度',26,'YEAR')+selectfield('gradeCode','学年',27,'GRADE')+selectfield('classId','クラス',21,'CLASS')
for name,label,index in [('unassignedOnly','未所属のみ',41),('status01','在学',42),('status02','休学',43),('status03','卒業',44),('status04','退学',45)]:
 render+=html(f'<label><input type="checkbox" name="{name}" value="1"')+f'    IF R-DATA({index})(1:1) = "1" DISPLAY " checked" WITH NO ADVANCING END-IF\n'+html(f'>{label}</label>')
render+=selectfield('prefectureCode','都道府県',13,'PREFECTURE')+inputfield('phoneNumber','電話（本人・緊急）',16,maxlen=20)+inputfield('admissionFrom','入学日開始',46,'date',10)+inputfield('admissionTo','入学日終了',47,'date',10)
render+=html('</fieldset><button name="action" value="SEARCH">検索</button><button name="action" value="OPTIONS">候補更新</button><button name="action" value="CLEAR" data-confirm="検索条件を初期化しますか。">クリア</button>')+'''    PERFORM DISPLAY-SETTINGS
'''+'''    IF ROLE-CODE > 0 DISPLAY '<button name="action" value="NEW">新規登録</button>' WITH NO ADVANCING END-IF
'''+'''    IF SEARCH-EXECUTED = 0
      DISPLAY '<p>未検索</p>' WITH NO ADVANCING
    ELSE
      MOVE TOTAL-COUNT TO NUM-OUT DISPLAY '<p>件数 ' FUNCTION TRIM(NUM-OUT) WITH NO ADVANCING
      IF ROW-COUNT > 0
        COMPUTE V = (CURRENT-PAGE - 1) * PAGE-SIZE + 1
        PERFORM ID-AS-TEMP DISPLAY ' 表示 ' FUNCTION TRIM(TMP-DATA) WITH NO ADVANCING
        COMPUTE V = (CURRENT-PAGE - 1) * PAGE-SIZE + ROW-COUNT
        PERFORM ID-AS-TEMP DISPLAY '～' FUNCTION TRIM(TMP-DATA) WITH NO ADVANCING
      END-IF
      DISPLAY '</p><p>最終取得UTC ' WITH NO ADVANCING
      CALL "STESC" USING SEARCH-TIMESTAMP BY VALUE 28 END-CALL
      DISPLAY '</p>' WITH NO ADVANCING
      MOVE SEARCH-RAW TO APPLIED-COPY MOVE 0 TO DIRTY-FLAG
      PERFORM VARYING K FROM 1 BY 1 UNTIL K > 64
        IF K = 4 OR 5 OR 6 OR 26 OR 27 OR 21 OR 41 OR 42 OR 43 OR 44
          OR 45 OR 13 OR 16 OR 46 OR 47
          IF R-VALUE(K) NOT = APPLIED-VALUE(K) MOVE 1 TO DIRTY-FLAG END-IF
        END-IF
      END-PERFORM
      IF DIRTY-FLAG = 1
        DISPLAY '<p>入力条件の変更は一覧へ未反映です。</p>' WITH NO ADVANCING
      END-IF
    END-IF
    IF ROW-COUNT > 0
      DISPLAY '<table><thead><tr><th>学籍番号</th><th>氏名</th><th>カナ</th><th>生年月日</th><th>年度・学年</th><th>クラス</th><th>在籍</th><th>住所</th><th>本人電話</th><th>更新日時</th><th>編集／参照</th></tr></thead><tbody>' WITH NO ADVANCING
      PERFORM VARYING I FROM 1 BY 1 UNTIL I > ROW-COUNT
        DISPLAY '<tr>' WITH NO ADVANCING
        PERFORM VARYING J FROM 2 BY 1 UNTIL J > 13
          IF J NOT = 7 AND 9 DISPLAY '<td>' WITH NO ADVANCING END-IF
          IF J = 5
            CALL "STDATEOUT" USING ROW-DATA(I,J) DATE-E DATE-Y DATE-M DATE-D
              WAREKI-OUT WAREKI-LENGTH RETURNING RC END-CALL
            CALL "STESC" USING WAREKI-OUT BY VALUE WAREKI-LENGTH END-CALL
          ELSE
            IF ROW-NULL(I,J) = -1 DISPLAY '－' WITH NO ADVANCING
            ELSE CALL "STESC" USING ROW-DATA(I,J) BY VALUE ROW-LENGTH(I,J) END-CALL END-IF
          END-IF
          IF J NOT = 6 AND 8 DISPLAY '</td>' WITH NO ADVANCING
          ELSE DISPLAY '／' WITH NO ADVANCING END-IF
        END-PERFORM
        DISPLAY '<td><button name="openStudentId" value="' WITH NO ADVANCING
        CALL "STESC" USING ROW-DATA(I,1) BY VALUE ROW-LENGTH(I,1) END-CALL
        DISPLAY '">編集／参照</button></td></tr>' WITH NO ADVANCING
      END-PERFORM
      DISPLAY '</tbody></table>' WITH NO ADVANCING
    END-IF
    IF SEARCH-EXECUTED = 1 AND TOTAL-COUNT <= 10000
      PERFORM PAGE-FORM
      MOVE 1 TO PAGE-TARGET MOVE "先頭" TO PAGE-LABEL PERFORM PAGE-BUTTON
      COMPUTE PAGE-TARGET = FUNCTION MAX(1,CURRENT-PAGE - 1)
      MOVE "前" TO PAGE-LABEL PERFORM PAGE-BUTTON
      COMPUTE PAGE-TARGET = FUNCTION MIN(LAST-PAGE,CURRENT-PAGE + 1)
      MOVE "次" TO PAGE-LABEL PERFORM PAGE-BUTTON
      MOVE LAST-PAGE TO PAGE-TARGET MOVE "末尾" TO PAGE-LABEL PERFORM PAGE-BUTTON
    END-IF
    DISPLAY '</form>' WITH NO ADVANCING.
PAGE-BUTTON.
    MOVE PAGE-TARGET TO V PERFORM ID-AS-TEMP
    DISPLAY '<button name="pageTarget" value="' WITH NO ADVANCING
    CALL "STESC" USING TMP-DATA BY VALUE TMP-LENGTH END-CALL
    DISPLAY '"' WITH NO ADVANCING
    IF PAGE-TARGET = CURRENT-PAGE DISPLAY ' disabled' WITH NO ADVANCING END-IF
    DISPLAY '>' FUNCTION TRIM(PAGE-LABEL) '</button>' WITH NO ADVANCING.

ROW-HIDDEN.
'''+hidden('studentId','ROW-DATA(I,1)','ROW-LENGTH(I,1)')+hidden('contextId','CONTEXT-ID',64)+hidden('tabId','TAB-ID',64)+'''.
PAGE-FORM.
'''+'''    CONTINUE
    DISPLAY '<label>ページ<input name="page" inputmode="numeric" value="' WITH NO ADVANCING
    MOVE CURRENT-PAGE TO NUM-OUT DISPLAY FUNCTION TRIM(NUM-OUT) '"></label><button name="action" value="PAGE">移動</button>' WITH NO ADVANCING.
DISPLAY-SETTINGS.
'''+html('<label>表示件数<select name="pageSize">')
for n in [20,50,100]:render+=html(f'<option value="{n}"')+f'    IF PAGE-SIZE = {n} DISPLAY " selected" WITH NO ADVANCING END-IF\n'+html(f'>{n}件</option>')
render+=html('</select></label><label>並び順<select name="sortKey">')
for key,label in [('studentNo','学籍番号'),('name','氏名'),('admissionDate','入学日'),('updatedAt','更新日時')]:render+=html(f'<option value="{key}"')+f'    IF R-DATA(F-SORTKEY) = "{key}" DISPLAY " selected" WITH NO ADVANCING END-IF\n'+html(f'>{label}</option>')
render+=html('</select></label><label>方向<select name="sortDirection">')
for key,label in [('asc','昇順'),('desc','降順')]:render+=html(f'<option value="{key}"')+f'    IF R-DATA(F-SORTDIRECTION) = "{key}" DISPLAY " selected" WITH NO ADVANCING END-IF\n'+html(f'>{label}</option>')
render+=html('</select></label>')+'''.
EDIT-SCREEN.
    IF EDITOR-NORMAL NOT = SPACES MOVE EDITOR-NORMAL TO ST-OLD END-IF
'''+'''    IF STUDENT-ID > 0
      MOVE STUDENT-ID TO V PERFORM ID-AS-TEMP
      DISPLAY '<p>学生管理番号 ' FUNCTION TRIM(TMP-DATA) WITH NO ADVANCING
      MOVE EXPECTED-VERSION TO V PERFORM ID-AS-TEMP
      DISPLAY ' 版 ' FUNCTION TRIM(TMP-DATA) ' 更新日時（日本時間） ' WITH NO ADVANCING
      CALL "STESC" USING O-DATA(23) BY VALUE O-LENGTH(23) END-CALL
      DISPLAY ' 更新者 ' WITH NO ADVANCING
      CALL "STESC" USING O-DATA(24) BY VALUE O-LENGTH(24) END-CALL
      DISPLAY '</p>' WITH NO ADVANCING
    END-IF
'''+html('<h1>学生登録・編集・参照</h1><form class="editor" method="post" action="student.cgi">')+'''    PERFORM EDITOR-HIDDEN
    IF ROLE-CODE = 0 DISPLAY '<fieldset disabled>' WITH NO ADVANCING
    ELSE DISPLAY '<fieldset>' WITH NO ADVANCING END-IF
'''
render+=inputfield('studentNo','学籍番号（既存は変更不可）',4,maxlen=15)+inputfield('studentName','氏名',5,maxlen=8)+inputfield('studentNameKana','氏名カナ',6,maxlen=36)
render+=html('<label>生年月日元号<select name="birthEra"><option value="">未選択</option>')
for key,label in [('REIWA','令和'),('HEISEI','平成'),('SHOWA','昭和'),('TAISHO','大正'),('MEIJI','明治')]:render+=html(f'<option value="{key}"')+f'    IF R-DATA(F-BIRTHERA) = "{key}" DISPLAY " selected" WITH NO ADVANCING END-IF\n'+html(f'>{label}</option>')
render+=html('</select></label>')
for name,label,index,maxlen in [('birthYear','元号年（元も可）',8,4),('birthMonth','月',9,2),('birthDay','日',10,2)]:render+=inputfield(name,label,index,maxlen=maxlen)
for name,label,index,cat,old in [('genderCode','性別',11,'GENDER',5),('prefectureCode','都道府県',13,'PREFECTURE',7),('enrollmentStatusCode','在籍区分',19,'ENROLLMENT_STATUS',13),('relationshipCode','緊急連絡先続柄',23,'RELATIONSHIP',17)]:
 render+=f'    MOVE O-DATA({old}) TO UI-CURRENT\n'+selectfield(name,label,index,cat)
for name,label,index,kind,maxlen in [('postalCode','郵便番号',12,'text',10),('addressLine1','住所1',14,'text',45),('addressLine2','住所2',15,'text',45),('phoneNumber','本人電話',16,'text',20),('emailAddress','本人メール',17,'text',60),('admissionDate','入学日',18,'date',10),('enrollmentEndDate','卒業・退学日',20,'date',10),('emergencyContactName','緊急連絡先氏名',22,'text',8),('emergencyPhoneNumber','緊急連絡先電話',24,'text',20),('reason','確認・変更理由',28,'text',60)]:render+=inputfield(name,label,index,kind,maxlen)
render+=selectfield('schoolYear','年度',26,'YEAR')+selectfield('gradeCode','学年',27,'GRADE')+'''    MOVE O-DATA(15) TO UI-CURRENT
'''+selectfield('classId','クラス・人数参考',21,'CLASS')+html('<label>備考<textarea name="remarks" maxlength="240">')+'''    CALL "STESC" USING R-DATA(F-REMARKS) BY VALUE R-LENGTH(F-REMARKS) END-CALL
'''+html('</textarea></label></fieldset>')+'''    IF ROLE-CODE > 0
      DISPLAY '<button name="action" value="SAVE">保存</button><button name="action" value="EDITOPTIONS">候補更新</button>' WITH NO ADVANCING
    END-IF
    IF APP-OUTCOME = "ConfirmationRequired"
      PERFORM DUPLICATE-PANEL
    ELSE
      IF R-NULL(F-CONFIRMATIONTOKEN) = 0
        DISPLAY '<input type="hidden" name="confirmationToken" value="' WITH NO ADVANCING
        CALL "STESC" USING R-DATA(F-CONFIRMATIONTOKEN) BY VALUE R-LENGTH(F-CONFIRMATIONTOKEN) END-CALL
        DISPLAY '">' WITH NO ADVANCING
      END-IF
    END-IF
'''+html('</form><form method="post" action="student.cgi" data-confirm="入力内容を取り消しますか。">')+'''    PERFORM EDITOR-HIDDEN
'''+html('<input type="hidden" name="confirmed" value="1"><button name="action" value="RESET">取消</button></form><form method="post" action="student.cgi" data-confirm="最新情報へ再読込しますか。">')+'''    PERFORM EDITOR-HIDDEN
'''+html('<input type="hidden" name="confirmed" value="1"><button name="action" value="RELOAD">再読込</button></form><form method="get" action="student.cgi" data-leave="1"><input type="hidden" name="action" value="RESUME">')+hidden('contextId','CONTEXT-ID',64)+hidden('tabId','TAB-ID',64)+'''    MOVE CONTEXT-REVISION TO V PERFORM ID-AS-TEMP
'''+hidden('contextRevision','TMP-DATA','TMP-LENGTH')+html('<button>検索へ戻る</button></form>')+'''    IF ROLE-CODE = 2 AND STUDENT-ID > 0
      DISPLAY '<form method="post" action="student.cgi" data-confirm="この学生を論理削除しますか。">' WITH NO ADVANCING
      PERFORM EDITOR-HIDDEN
      DISPLAY '<label>削除理由<input name="deleteReason" maxlength="120"></label><input type="hidden" name="confirmed" value="1"><button name="action" value="DELETE">論理削除</button></form>' WITH NO ADVANCING
    END-IF.
DUPLICATE-PANEL.
    MOVE DUP-COUNT TO NUM-OUT
    DISPLAY '<section class="duplicates"><h2>重複候補 ' FUNCTION TRIM(NUM-OUT) '件（最大20件表示）</h2><table><tr><th>学籍番号</th><th>氏名</th><th>和暦生年月日</th><th>クラス</th></tr>' WITH NO ADVANCING
    PERFORM VARYING I FROM 1 BY 1 UNTIL I > FUNCTION MIN(DUP-COUNT,20)
      DISPLAY '<tr>' WITH NO ADVANCING
      PERFORM VARYING J FROM 3 BY 1 UNTIL J > 6
        DISPLAY '<td>' WITH NO ADVANCING
        IF J = 5
          CALL "STDATEOUT" USING ROW-DATA(I,J) DATE-E DATE-Y DATE-M DATE-D
            WAREKI-OUT WAREKI-LENGTH RETURNING RC END-CALL
          CALL "STESC" USING WAREKI-OUT BY VALUE WAREKI-LENGTH END-CALL
        ELSE
          IF ROW-NULL(I,J) = -1 DISPLAY '未所属' WITH NO ADVANCING
          ELSE CALL "STESC" USING ROW-DATA(I,J) BY VALUE ROW-LENGTH(I,J) END-CALL END-IF
        END-IF
        DISPLAY '</td>' WITH NO ADVANCING
      END-PERFORM
      DISPLAY '</tr>' WITH NO ADVANCING
    END-PERFORM
    DISPLAY '</table>' WITH NO ADVANCING
'''+hidden('confirmationToken','CONFIRM-ID',64)+html('<button name="action" value="CANCEL" autofocus>取消</button><button name="action" value="CONFIRM">別人確認後、理由を付けて続行</button></section>')+'''.
'''
local='01 DIRTY-FLAG PIC S9(9) COMP-5.\n01 APPLIED-COPY.\n  05 APPLIED-VALUE OCCURS 64 TIMES PIC X(1032).\n01 PAGE-TARGET PIC S9(9) COMP-5.\n01 PAGE-LABEL PIC X(12).\n'
for n in ['E','Y','M','D']:local+=f'01 DATE-{n}.\n  05 filler pic X(1032).\n'
program('STRENDER',render,local)
(program.__globals__['ROOT']/'assets').mkdir(exist_ok=True)
put('assets/style.css','''*{box-sizing:border-box}body{font-family:"Yu Gothic",Meiryo,sans-serif;background:#f2f5f9;color:#243448;margin:0}header{background:#153654;color:#fff;padding:1rem 2rem}main{max-width:1440px;margin:auto;padding:1.5rem;background:#fff}fieldset{display:grid;grid-template-columns:10rem 1fr 10rem 1fr;gap:.75rem;border:1px solid #ccd9e6;padding:1rem}input,select,textarea,button{font:inherit;padding:.5rem;border:1px solid #afbece;border-radius:3px}textarea{min-height:7rem}button{margin:.5rem;background:#edf4fa;cursor:pointer}table{border-collapse:collapse;width:100%;font-size:.85rem}th,td{border:1px solid #ccd9e6;padding:.5rem;vertical-align:top}th{background:#e6eef6}tr:nth-child(even){background:#f8fafc}pre{white-space:pre-wrap;background:#fff0ed;border:1px solid #c54e4e;padding:1rem}p[role=status]{padding:1rem;background:#edf7f3}.duplicates{background:#fff8eb;padding:1rem}form{margin-bottom:1rem}@media(max-width:900px){fieldset{grid-template-columns:9rem 1fr}table{display:block;overflow:auto}}
''')
put('assets/site.js','''"use strict";
let dirty=false;const editor=document.querySelector("form.editor");
editor?.addEventListener("input",()=>dirty=true);editor?.addEventListener("change",()=>dirty=true);
window.addEventListener("beforeunload",e=>{if(dirty){e.preventDefault();e.returnValue="";}});
for(const form of document.forms)form.addEventListener("submit",e=>{
 const text=form.dataset.confirm||(form.dataset.leave&&dirty?"変更を破棄して戻りますか。":null);
 if(text&&!window.confirm(text)){e.preventDefault();return;}
 dirty=false;setTimeout(()=>{for(const b of form.querySelectorAll("button"))b.disabled=true;},0);
});
document.querySelector(".cancel-duplicate")?.addEventListener("click",()=>{
 document.querySelector('[name="confirmationToken"]')?.remove();document.querySelector(".duplicates")?.remove();
});
const unassigned=document.querySelector('[name="unassignedOnly"]');
const upper=["schoolYear","gradeCode","classId"];
function assignControls(){if(!unassigned)return;for(const name of upper){const el=document.querySelector(`[name="${name}"]`);if(el){el.disabled=unassigned.checked;if(unassigned.checked)el.value="";}}}
unassigned?.addEventListener("change",assignControls);assignControls();
for(const name of ["schoolYear","gradeCode"])document.querySelector(`form.editor [name="${name}"]`)?.addEventListener("change",()=>{const c=document.querySelector('form.editor [name="classId"]');if(c)c.value="";});
''')
print('Generated COBOL lookup, master diagnostics, messages, Flash and full two HTML forms/assets.')
