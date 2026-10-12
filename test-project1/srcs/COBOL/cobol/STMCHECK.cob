       >>SOURCE FORMAT FREE
identification division.
program-id. STMCHECK.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
copy "ST-FIELDS.cpy".
copy "ST-APP.cpy".
copy "ST-LOCAL.cpy".

procedure division.
    MOVE "INIT-CHECK" TO COMMAND-NAME PERFORM DB-RESET
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

copy "ST-HELPERS.cpy".
end program STMCHECK.
