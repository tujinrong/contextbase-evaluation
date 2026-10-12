       >>SOURCE FORMAT FREE
identification division.
program-id. STVALID.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
copy "ST-FIELDS.cpy".
copy "ST-APP.cpy".
copy "ST-LOCAL.cpy".

procedure division.
    IF N-NULL(1) = -1
      MOVE "E-STU-001: 項目1を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(2) = -1
      MOVE "E-STU-001: 項目2を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(3) = -1
      MOVE "E-STU-001: 項目3を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(4) = -1
      MOVE "E-STU-001: 項目4を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(5) = -1
      MOVE "E-STU-001: 項目5を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(6) = -1
      MOVE "E-STU-001: 項目6を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(7) = -1
      MOVE "E-STU-001: 項目7を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(8) = -1
      MOVE "E-STU-001: 項目8を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(12) = -1
      MOVE "E-STU-001: 項目12を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(13) = -1
      MOVE "E-STU-001: 項目13を入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-NULL(1) = 0
      PERFORM VARYING I FROM 1 BY 1 UNTIL I > N-LENGTH(1)
        IF (N-DATA(1)(I:1) < "A" OR > "Z") AND
           (N-DATA(1)(I:1) < "0" OR > "9") AND
           (I = 1 OR N-DATA(1)(I:1) NOT = "-")
          MOVE "E-STU-003: 学籍番号の形式を確認してください。" TO ERROR-TEXT
          PERFORM ADD-ERROR EXIT PERFORM
        END-IF
      END-PERFORM
    END-IF
    CALL "STKANA" USING N-VALUE(3) RETURNING RC END-CALL
    IF RC NOT = 0
      MOVE "E-STU-004: 氏名カナを確認してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    PERFORM VARYING I FROM 5 BY 1 UNTIL I > 17
      IF I = 5 OR 7 OR 13 OR 17
        IF N-NULL(I) = 0
          IF (I = 5 AND N-LENGTH(I) NOT = 1) OR
             (I NOT = 5 AND N-LENGTH(I) NOT = 2)
            MOVE "E-STU-009: コードの桁数が無効です。" TO ERROR-TEXT
            PERFORM ADD-ERROR
          END-IF
          PERFORM VARYING J FROM 1 BY 1 UNTIL J > N-LENGTH(I)
            IF N-DATA(I)(J:1) < "0" OR > "9"
              MOVE "E-STU-009: コードは数字です。" TO ERROR-TEXT
              PERFORM ADD-ERROR EXIT PERFORM
            END-IF
          END-PERFORM
        END-IF
      END-IF
    END-PERFORM
    IF N-LENGTH(6) NOT = 7 OR N-DATA(6)(1:7) IS NOT NUMERIC
      MOVE "E-STU-015: 郵便番号は7桁です。" TO ERROR-TEXT PERFORM ADD-ERROR
    END-IF
    PERFORM VARYING I FROM 10 BY 8 UNTIL I > 18
      IF N-NULL(I) = 0
        MOVE 0 TO K
        IF N-DATA(I)(1:1) = "0" AND (N-LENGTH(I) = 10 OR 11)
          MOVE 1 TO K
          PERFORM VARYING J FROM 1 BY 1 UNTIL J > N-LENGTH(I)
            IF N-DATA(I)(J:1) < "0" OR > "9" MOVE 0 TO K END-IF
          END-PERFORM
        END-IF
        IF N-DATA(I)(1:1) = "+" AND N-LENGTH(I) >= 8 AND <= 16
          AND N-DATA(I)(2:1) >= "1" AND <= "9"
          MOVE 1 TO K
          PERFORM VARYING J FROM 2 BY 1 UNTIL J > N-LENGTH(I)
            IF N-DATA(I)(J:1) < "0" OR > "9" MOVE 0 TO K END-IF
          END-PERFORM
        END-IF
        IF K = 0
          MOVE "E-STU-016: 電話番号の形式を確認してください。" TO ERROR-TEXT
          PERFORM ADD-ERROR
        END-IF
      END-IF
    END-PERFORM
    CALL "STEMAIL" USING N-VALUE(11) RETURNING RC END-CALL
    IF RC NOT = 0
      MOVE "E-STU-017: メールの形式を確認してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    PERFORM VARYING I FROM 12 BY 2 UNTIL I > 14
      IF N-NULL(I) = 0
        MOVE N-VALUE(I) TO TMP-VALUE PERFORM ISO-DATE
        IF RC NOT = 0 OR DATE-OUT > BUSINESS-DAY
          MOVE "E-STU-005: 正しい西暦日付を入力してください。" TO ERROR-TEXT
          PERFORM ADD-ERROR
        END-IF
      END-IF
    END-PERFORM
    IF N-DATA(4)(1:10) > N-DATA(12)(1:10)
      MOVE "E-STU-007: 生年月日≦入学日としてください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    IF N-DATA(13)(1:2) = "01" OR "02"
      IF N-NULL(14) NOT = -1
        MOVE "E-STU-008: 在学・休学の終了日は未設定です。" TO ERROR-TEXT
        PERFORM ADD-ERROR
      END-IF
      IF N-NULL(15) = -1
        MOVE "E-STU-012: 在学・休学はクラス必須です。" TO ERROR-TEXT
        PERFORM ADD-ERROR
      END-IF
    ELSE
      IF N-DATA(13)(1:2) NOT = "03" AND "04"
        MOVE "E-STU-009: 在籍区分が無効です。" TO ERROR-TEXT PERFORM ADD-ERROR
      END-IF
      IF N-NULL(14) = -1 OR N-DATA(14)(1:10) < N-DATA(12)(1:10)
        MOVE "E-STU-008: 終了日は入学日以降としてください。" TO ERROR-TEXT
        PERFORM ADD-ERROR
      END-IF
    END-IF
    IF N-NULL(15) = 0
      CALL "STINTEGER" USING N-VALUE(15) V RETURNING RC END-CALL
      IF RC NOT = 0 OR V < 1
        MOVE "E-STU-010: クラスIDが不正です。" TO ERROR-TEXT PERFORM ADD-ERROR
      END-IF
    END-IF
    IF N-NULL(10) = -1 AND N-NULL(11) = -1 AND N-NULL(18) = -1
      MOVE "E-STU-018: 連絡先を1つ以上入力してください。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    MOVE 0 TO K
    IF N-NULL(16) = 0 ADD 1 TO K END-IF
    IF N-NULL(17) = 0 ADD 1 TO K END-IF
    IF N-NULL(18) = 0 ADD 1 TO K END-IF
    IF K NOT = 0 AND 3
      MOVE "E-STU-019: 緊急連絡先は3項目一式です。" TO ERROR-TEXT
      PERFORM ADD-ERROR
    END-IF
    GOBACK.
ISO-DATE.
    MOVE -1 TO RC
    IF TMP-LENGTH NOT = 10 OR TMP-DATA(5:1) NOT = "-"
      OR TMP-DATA(8:1) NOT = "-" OR TMP-DATA(1:4) IS NOT NUMERIC
      OR TMP-DATA(6:2) IS NOT NUMERIC OR TMP-DATA(9:2) IS NOT NUMERIC
      EXIT PARAGRAPH END-IF
    COMPUTE YEAR-N = FUNCTION NUMVAL(TMP-DATA(1:4))
    COMPUTE MONTH-N = FUNCTION NUMVAL(TMP-DATA(6:2))
    COMPUTE DAY-N = FUNCTION NUMVAL(TMP-DATA(9:2))
    PERFORM REAL-DATE.
REAL-DATE.
    MOVE 0 TO RC
    IF YEAR-N < 1900 OR YEAR-N > 9999 OR MONTH-N < 1 OR > 12
      MOVE -1 TO RC EXIT PARAGRAPH END-IF
    MOVE 31 TO MONTH-DAYS
    IF MONTH-N = 4 OR 6 OR 9 OR 11 MOVE 30 TO MONTH-DAYS END-IF
    IF MONTH-N = 2
      MOVE 28 TO MONTH-DAYS
      IF FUNCTION MOD(YEAR-N,400) = 0 OR
        (FUNCTION MOD(YEAR-N,4) = 0 AND FUNCTION MOD(YEAR-N,100) NOT = 0)
        MOVE 29 TO MONTH-DAYS
      END-IF
    END-IF
    IF DAY-N < 1 OR > MONTH-DAYS MOVE -1 TO RC EXIT PARAGRAPH END-IF
    MOVE YEAR-N TO YEAR-OUT MOVE MONTH-N TO MONTH-OUT MOVE DAY-N TO DAY-OUT
    STRING YEAR-OUT "-" MONTH-OUT "-" DAY-OUT INTO DATE-OUT END-STRING.

copy "ST-HELPERS.cpy".
end program STVALID.
