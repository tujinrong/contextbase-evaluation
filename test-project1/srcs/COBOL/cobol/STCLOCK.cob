       >>SOURCE FORMAT FREE
identification division.
program-id. STCLOCK.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
copy "ST-FIELDS.cpy".
copy "ST-APP.cpy".
copy "ST-LOCAL.cpy".

procedure division.
    MOVE "CLOCK" TO COMMAND-NAME PERFORM DB-RESET
    PERFORM DB-EXECUTE
    IF RC = 0
      CALL "STFETCH" USING ST-DB-RESULT RETURNING RC END-CALL
      IF RC = 1
        MOVE 1 TO K PERFORM FETCH-TEMP MOVE TMP-DATA TO BUSINESS-DAY
        MOVE 2 TO K PERFORM FETCH-TEMP MOVE TMP-DATA TO BUSINESS-TIME
        MOVE 3 TO K PERFORM FETCH-TEMP MOVE TMP-DATA TO CORRELATION-ID
        MOVE 4 TO K PERFORM FETCH-TEMP
        IF TMP-DATA(1:1) NOT = "1"
          MOVE 503 TO APP-STATUS
          MOVE "E-COM-004: SNAPSHOT設定が必要です。" TO ERROR-TEXT
          PERFORM ADD-ERROR
        END-IF
      ELSE
        MOVE 503 TO APP-STATUS
        MOVE "E-COM-004: 業務日時を取得できません。" TO ERROR-TEXT
        PERFORM ADD-ERROR
      END-IF
    END-IF
    CALL "STCURSOR" USING ST-DB-RESULT END-CALL
    GOBACK.

copy "ST-HELPERS.cpy".
end program STCLOCK.
