       >>SOURCE FORMAT FREE
identification division.
program-id. STRENDER.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
copy "ST-FIELDS.cpy".
copy "ST-APP.cpy".
copy "ST-LOCAL.cpy".
01 DIRTY-FLAG PIC S9(9) COMP-5.
01 APPLIED-COPY.
  05 APPLIED-VALUE OCCURS 64 TIMES PIC X(1032).
01 PAGE-TARGET PIC S9(9) COMP-5.
01 PAGE-LABEL PIC X(12).
01 DATE-E.
  05 filler pic X(1032).
01 DATE-Y.
  05 filler pic X(1032).
01 DATE-M.
  05 filler pic X(1032).
01 DATE-D.
  05 filler pic X(1032).

procedure division.
    CALL "STMSG" END-CALL
    IF APP-STATUS = 200 CALL "STHINT" END-CALL END-IF
    CALL "STOUTPUTBEGIN" RETURNING RC END-CALL
    IF RC NOT = 0
      MOVE 503 TO APP-STATUS
      CALL "STHEADER" USING BY VALUE APP-STATUS END-CALL
      DISPLAY "E-COM-004: 応答を作成できません。" GOBACK END-IF
    DISPLAY '<!doctype html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>学生管理</title><link rel="st'
      'ylesheet" href="/student-assets/style.css"><script defer src="/student-assets/site.js"></script></head><body><header><strong>学生管理</strong></he' 'ader><main>' WITH NO ADVANCING
    IF APP-STATUS NOT = 401 AND OWNER-LENGTH > 0
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
    DISPLAY '<input type="hidden" name="contextId" value="' WITH NO ADVANCING
    CALL "STESC" USING CONTEXT-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<input type="hidden" name="tabId" value="' WITH NO ADVANCING
    CALL "STESC" USING TAB-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<input type="hidden" name="csrfToken" value="' WITH NO ADVANCING
    CALL "STESC" USING CSRF-TOKEN BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    MOVE CONTEXT-REVISION TO V PERFORM ID-AS-TEMP
    DISPLAY '<input type="hidden" name="contextRevision" value="' WITH NO ADVANCING
    CALL "STESC" USING TMP-DATA BY VALUE TMP-LENGTH END-CALL
    DISPLAY '">' WITH NO ADVANCING
.
EDITOR-HIDDEN.
    PERFORM COMMON-HIDDEN
    DISPLAY '<input type="hidden" name="editorId" value="' WITH NO ADVANCING
    CALL "STESC" USING EDITOR-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    IF STUDENT-ID > 0
      MOVE STUDENT-ID TO V PERFORM ID-AS-TEMP
    DISPLAY '<input type="hidden" name="studentId" value="' WITH NO ADVANCING
    CALL "STESC" USING TMP-DATA BY VALUE TMP-LENGTH END-CALL
    DISPLAY '">' WITH NO ADVANCING
      MOVE EXPECTED-VERSION TO V PERFORM ID-AS-TEMP
    DISPLAY '<input type="hidden" name="expectedVersion" value="' WITH NO ADVANCING
    CALL "STESC" USING TMP-DATA BY VALUE TMP-LENGTH END-CALL
    DISPLAY '">' WITH NO ADVANCING
    END-IF.
SEARCH-SCREEN.
    DISPLAY '<h1>学生検索</h1><form method="post" action="student.cgi"><fieldset><legend>検索条件</legend>' WITH NO ADVANCING
    PERFORM COMMON-HIDDEN
    MOVE 4 TO I
    DISPLAY '<label for="studentNo">学籍番号</label><input id="studentNo" name="studentNo" type="text" maxlength="30" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    IF STUDENT-ID > 0 DISPLAY '" readonly' WITH NO ADVANCING
    ELSE DISPLAY '"' WITH NO ADVANCING END-IF
    DISPLAY '>' WITH NO ADVANCING
    MOVE 5 TO I
    DISPLAY '<label for="studentName">氏名</label><input id="studentName" name="studentName" type="text" maxlength="16" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 6 TO I
    DISPLAY '<label for="studentNameKana">氏名カナ</label><input id="studentNameKana" name="studentNameKana" type="text" maxlength="72" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    DISPLAY '<label for="schoolYear">年度</label><select id="schoolYear" name="schoolYear"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 26 TO UI-FIELD MOVE "YEAR" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    DISPLAY '<label for="gradeCode">学年</label><select id="gradeCode" name="gradeCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 27 TO UI-FIELD MOVE "GRADE" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    DISPLAY '<label for="classId">クラス</label><select id="classId" name="classId"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 21 TO UI-FIELD MOVE "CLASS" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    DISPLAY '<label><input type="checkbox" name="unassignedOnly" value="1"' WITH NO ADVANCING
    IF R-DATA(41)(1:1) = "1" DISPLAY " checked" WITH NO ADVANCING END-IF
    DISPLAY '>未所属のみ</label>' WITH NO ADVANCING
    DISPLAY '<label><input type="checkbox" name="status01" value="1"' WITH NO ADVANCING
    IF R-DATA(42)(1:1) = "1" DISPLAY " checked" WITH NO ADVANCING END-IF
    DISPLAY '>在学</label>' WITH NO ADVANCING
    DISPLAY '<label><input type="checkbox" name="status02" value="1"' WITH NO ADVANCING
    IF R-DATA(43)(1:1) = "1" DISPLAY " checked" WITH NO ADVANCING END-IF
    DISPLAY '>休学</label>' WITH NO ADVANCING
    DISPLAY '<label><input type="checkbox" name="status03" value="1"' WITH NO ADVANCING
    IF R-DATA(44)(1:1) = "1" DISPLAY " checked" WITH NO ADVANCING END-IF
    DISPLAY '>卒業</label>' WITH NO ADVANCING
    DISPLAY '<label><input type="checkbox" name="status04" value="1"' WITH NO ADVANCING
    IF R-DATA(45)(1:1) = "1" DISPLAY " checked" WITH NO ADVANCING END-IF
    DISPLAY '>退学</label>' WITH NO ADVANCING
    DISPLAY '<label for="prefectureCode">都道府県</label><select id="prefectureCode" name="prefectureCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 13 TO UI-FIELD MOVE "PREFECTURE" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    MOVE 16 TO I
    DISPLAY '<label for="phoneNumber">電話（本人・緊急）</label><input id="phoneNumber" name="phoneNumber" type="text" maxlength="40" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 46 TO I
    DISPLAY '<label for="admissionFrom">入学日開始</label><input id="admissionFrom" name="admissionFrom" type="date" maxlength="20" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 47 TO I
    DISPLAY '<label for="admissionTo">入学日終了</label><input id="admissionTo" name="admissionTo" type="date" maxlength="20" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    DISPLAY '</fieldset><button name="action" value="SEARCH">検索</button><button name="action" value="OPTIONS">候補更新</button><button name="action" value='
      '"CLEAR" data-confirm="検索条件を初期化しますか。">クリア</button>' WITH NO ADVANCING
    PERFORM DISPLAY-SETTINGS
    IF ROLE-CODE > 0 DISPLAY '<button name="action" value="NEW">新規登録</button>' WITH NO ADVANCING END-IF
    IF SEARCH-EXECUTED = 0
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
    DISPLAY '<table><thead><tr><th>学籍番号</th><th>氏名</th><th>カナ</th><th>生年月日</th><th>年度・学年</th><th>クラス</th><th>在籍</th><th'
      '>住所</th><th>本人電話</th><th>更新日時</th><th>編集／参照</th></tr></thead><tbody>' WITH NO ADVANCING
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
    DISPLAY '<input type="hidden" name="studentId" value="' WITH NO ADVANCING
    CALL "STESC" USING ROW-DATA(I,1) BY VALUE ROW-LENGTH(I,1) END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<input type="hidden" name="contextId" value="' WITH NO ADVANCING
    CALL "STESC" USING CONTEXT-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<input type="hidden" name="tabId" value="' WITH NO ADVANCING
    CALL "STESC" USING TAB-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
.
PAGE-FORM.
    CONTINUE
    DISPLAY '<label>ページ<input name="page" inputmode="numeric" value="' WITH NO ADVANCING
    MOVE CURRENT-PAGE TO NUM-OUT DISPLAY FUNCTION TRIM(NUM-OUT) '"></label><button name="action" value="PAGE">移動</button>' WITH NO ADVANCING.
DISPLAY-SETTINGS.
    DISPLAY '<label>表示件数<select name="pageSize">' WITH NO ADVANCING
    DISPLAY '<option value="20"' WITH NO ADVANCING
    IF PAGE-SIZE = 20 DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>20件</option>' WITH NO ADVANCING
    DISPLAY '<option value="50"' WITH NO ADVANCING
    IF PAGE-SIZE = 50 DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>50件</option>' WITH NO ADVANCING
    DISPLAY '<option value="100"' WITH NO ADVANCING
    IF PAGE-SIZE = 100 DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>100件</option>' WITH NO ADVANCING
    DISPLAY '</select></label><label>並び順<select name="sortKey">' WITH NO ADVANCING
    DISPLAY '<option value="studentNo"' WITH NO ADVANCING
    IF R-DATA(F-SORTKEY) = "studentNo" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>学籍番号</option>' WITH NO ADVANCING
    DISPLAY '<option value="name"' WITH NO ADVANCING
    IF R-DATA(F-SORTKEY) = "name" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>氏名</option>' WITH NO ADVANCING
    DISPLAY '<option value="admissionDate"' WITH NO ADVANCING
    IF R-DATA(F-SORTKEY) = "admissionDate" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>入学日</option>' WITH NO ADVANCING
    DISPLAY '<option value="updatedAt"' WITH NO ADVANCING
    IF R-DATA(F-SORTKEY) = "updatedAt" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>更新日時</option>' WITH NO ADVANCING
    DISPLAY '</select></label><label>方向<select name="sortDirection">' WITH NO ADVANCING
    DISPLAY '<option value="asc"' WITH NO ADVANCING
    IF R-DATA(F-SORTDIRECTION) = "asc" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>昇順</option>' WITH NO ADVANCING
    DISPLAY '<option value="desc"' WITH NO ADVANCING
    IF R-DATA(F-SORTDIRECTION) = "desc" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>降順</option>' WITH NO ADVANCING
    DISPLAY '</select></label>' WITH NO ADVANCING
.
EDIT-SCREEN.
    IF EDITOR-NORMAL NOT = SPACES MOVE EDITOR-NORMAL TO ST-OLD END-IF
    IF STUDENT-ID > 0
      MOVE STUDENT-ID TO V PERFORM ID-AS-TEMP
      DISPLAY '<p>学生管理番号 ' FUNCTION TRIM(TMP-DATA) WITH NO ADVANCING
      MOVE EXPECTED-VERSION TO V PERFORM ID-AS-TEMP
      DISPLAY ' 版 ' FUNCTION TRIM(TMP-DATA) ' 更新日時（日本時間） ' WITH NO ADVANCING
      CALL "STESC" USING O-DATA(23) BY VALUE O-LENGTH(23) END-CALL
      DISPLAY ' 更新者 ' WITH NO ADVANCING
      CALL "STESC" USING O-DATA(24) BY VALUE O-LENGTH(24) END-CALL
      DISPLAY '</p>' WITH NO ADVANCING
    END-IF
    DISPLAY '<h1>学生登録・編集・参照</h1><form class="editor" method="post" action="student.cgi">' WITH NO ADVANCING
    PERFORM EDITOR-HIDDEN
    IF ROLE-CODE = 0 DISPLAY '<fieldset disabled>' WITH NO ADVANCING
    ELSE DISPLAY '<fieldset>' WITH NO ADVANCING END-IF
    MOVE 4 TO I
    DISPLAY '<label for="studentNo">学籍番号（既存は変更不可）</label><input id="studentNo" name="studentNo" type="text" maxlength="30" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    IF STUDENT-ID > 0 DISPLAY '" readonly' WITH NO ADVANCING
    ELSE DISPLAY '"' WITH NO ADVANCING END-IF
    DISPLAY '>' WITH NO ADVANCING
    MOVE 5 TO I
    DISPLAY '<label for="studentName">氏名</label><input id="studentName" name="studentName" type="text" maxlength="16" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 6 TO I
    DISPLAY '<label for="studentNameKana">氏名カナ</label><input id="studentNameKana" name="studentNameKana" type="text" maxlength="72" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    DISPLAY '<label>生年月日元号<select name="birthEra"><option value="">未選択</option>' WITH NO ADVANCING
    DISPLAY '<option value="REIWA"' WITH NO ADVANCING
    IF R-DATA(F-BIRTHERA) = "REIWA" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>令和</option>' WITH NO ADVANCING
    DISPLAY '<option value="HEISEI"' WITH NO ADVANCING
    IF R-DATA(F-BIRTHERA) = "HEISEI" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>平成</option>' WITH NO ADVANCING
    DISPLAY '<option value="SHOWA"' WITH NO ADVANCING
    IF R-DATA(F-BIRTHERA) = "SHOWA" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>昭和</option>' WITH NO ADVANCING
    DISPLAY '<option value="TAISHO"' WITH NO ADVANCING
    IF R-DATA(F-BIRTHERA) = "TAISHO" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>大正</option>' WITH NO ADVANCING
    DISPLAY '<option value="MEIJI"' WITH NO ADVANCING
    IF R-DATA(F-BIRTHERA) = "MEIJI" DISPLAY " selected" WITH NO ADVANCING END-IF
    DISPLAY '>明治</option>' WITH NO ADVANCING
    DISPLAY '</select></label>' WITH NO ADVANCING
    MOVE 8 TO I
    DISPLAY '<label for="birthYear">元号年（元も可）</label><input id="birthYear" name="birthYear" type="text" maxlength="8" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 9 TO I
    DISPLAY '<label for="birthMonth">月</label><input id="birthMonth" name="birthMonth" type="text" maxlength="4" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 10 TO I
    DISPLAY '<label for="birthDay">日</label><input id="birthDay" name="birthDay" type="text" maxlength="4" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE O-DATA(5) TO UI-CURRENT
    DISPLAY '<label for="genderCode">性別</label><select id="genderCode" name="genderCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 11 TO UI-FIELD MOVE "GENDER" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    MOVE O-DATA(7) TO UI-CURRENT
    DISPLAY '<label for="prefectureCode">都道府県</label><select id="prefectureCode" name="prefectureCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 13 TO UI-FIELD MOVE "PREFECTURE" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    MOVE O-DATA(13) TO UI-CURRENT
    DISPLAY '<label for="enrollmentStatusCode">在籍区分</label><select id="enrollmentStatusCode" name="enrollmentStatusCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 19 TO UI-FIELD MOVE "ENROLLMENT_STATUS" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    MOVE O-DATA(17) TO UI-CURRENT
    DISPLAY '<label for="relationshipCode">緊急連絡先続柄</label><select id="relationshipCode" name="relationshipCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 23 TO UI-FIELD MOVE "RELATIONSHIP" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    MOVE 12 TO I
    DISPLAY '<label for="postalCode">郵便番号</label><input id="postalCode" name="postalCode" type="text" maxlength="20" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 14 TO I
    DISPLAY '<label for="addressLine1">住所1</label><input id="addressLine1" name="addressLine1" type="text" maxlength="90" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 15 TO I
    DISPLAY '<label for="addressLine2">住所2</label><input id="addressLine2" name="addressLine2" type="text" maxlength="90" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 16 TO I
    DISPLAY '<label for="phoneNumber">本人電話</label><input id="phoneNumber" name="phoneNumber" type="text" maxlength="40" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 17 TO I
    DISPLAY '<label for="emailAddress">本人メール</label><input id="emailAddress" name="emailAddress" type="text" maxlength="120" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 18 TO I
    DISPLAY '<label for="admissionDate">入学日</label><input id="admissionDate" name="admissionDate" type="date" maxlength="20" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 20 TO I
    DISPLAY '<label for="enrollmentEndDate">卒業・退学日</label><input id="enrollmentEndDate" name="enrollmentEndDate" type="date" maxlength="20" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 22 TO I
    DISPLAY '<label for="emergencyContactName">緊急連絡先氏名</label><input id="emergencyContactName" name="emergencyContactName" type="text" maxlength="16" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 24 TO I
    DISPLAY '<label for="emergencyPhoneNumber">緊急連絡先電話</label><input id="emergencyPhoneNumber" name="emergencyPhoneNumber" type="text" maxlength="40" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    MOVE 28 TO I
    DISPLAY '<label for="reason">確認・変更理由</label><input id="reason" name="reason" type="text" maxlength="120" value="' WITH NO ADVANCING
    IF R-NULL(I) = 0
      CALL "STESC" USING R-DATA(I) BY VALUE R-LENGTH(I) END-CALL
    END-IF
    DISPLAY '"' WITH NO ADVANCING
    DISPLAY '>' WITH NO ADVANCING
    DISPLAY '<label for="schoolYear">年度</label><select id="schoolYear" name="schoolYear"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 26 TO UI-FIELD MOVE "YEAR" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    DISPLAY '<label for="gradeCode">学年</label><select id="gradeCode" name="gradeCode"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 27 TO UI-FIELD MOVE "GRADE" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    MOVE O-DATA(15) TO UI-CURRENT
    DISPLAY '<label for="classId">クラス・人数参考</label><select id="classId" name="classId"><option value="">未選択／すべて</option>' WITH NO ADVANCING
    MOVE 21 TO UI-FIELD MOVE "CLASS" TO UI-CATEGORY
    CALL "STMLOOK" END-CALL
    DISPLAY '</select>' WITH NO ADVANCING
    DISPLAY '<label>備考<textarea name="remarks" maxlength="240">' WITH NO ADVANCING
    CALL "STESC" USING R-DATA(F-REMARKS) BY VALUE R-LENGTH(F-REMARKS) END-CALL
    DISPLAY '</textarea></label></fieldset>' WITH NO ADVANCING
    IF ROLE-CODE > 0
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
    DISPLAY '</form><form method="post" action="student.cgi" data-confirm="入力内容を取り消しますか。">' WITH NO ADVANCING
    PERFORM EDITOR-HIDDEN
    DISPLAY '<input type="hidden" name="confirmed" value="1"><button name="action" value="RESET">取消</button></form><form method="post" action="student.cgi" data-confirm="最新情報へ再読込しますか。">' WITH NO ADVANCING
    PERFORM EDITOR-HIDDEN
    DISPLAY '<input type="hidden" name="confirmed" value="1"><button name="action" value="RELOAD">再読込</button></form><form method="get" action="student.cgi" ' 'data-leave="1"><input type="hidden" name="action" value="RESUME">'
      WITH NO ADVANCING
    DISPLAY '<input type="hidden" name="contextId" value="' WITH NO ADVANCING
    CALL "STESC" USING CONTEXT-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<input type="hidden" name="tabId" value="' WITH NO ADVANCING
    CALL "STESC" USING TAB-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    MOVE CONTEXT-REVISION TO V PERFORM ID-AS-TEMP
    DISPLAY '<input type="hidden" name="contextRevision" value="' WITH NO ADVANCING
    CALL "STESC" USING TMP-DATA BY VALUE TMP-LENGTH END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<button>検索へ戻る</button></form>' WITH NO ADVANCING
    IF ROLE-CODE = 2 AND STUDENT-ID > 0
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
    DISPLAY '<input type="hidden" name="confirmationToken" value="' WITH NO ADVANCING
    CALL "STESC" USING CONFIRM-ID BY VALUE 64 END-CALL
    DISPLAY '">' WITH NO ADVANCING
    DISPLAY '<button name="action" value="CANCEL" autofocus>取消</button><button name="action" value="CONFIRM">別人確認後、理由を付けて続行</button></section>' WITH NO ADVANCING
.

copy "ST-HELPERS.cpy".
end program STRENDER.
