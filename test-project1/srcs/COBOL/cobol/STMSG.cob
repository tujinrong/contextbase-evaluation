       >>SOURCE FORMAT FREE
identification division.
program-id. STMSG.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
copy "ST-FIELDS.cpy".
copy "ST-APP.cpy".
copy "ST-LOCAL.cpy".

procedure division.
    IF APP-MESSAGE-LENGTH = 0
      EVALUATE APP-OUTCOME
        WHEN "NoChange" MOVE "I-STU-004: 変更内容がありません。" TO APP-MESSAGE
        WHEN "Unknown" MOVE "E-COM-004: 結果不明です。再送せず検索で確認してください。" TO APP-MESSAGE
        WHEN "Conflict" MOVE "E-STU-105: 最新情報へ再読込してください。" TO APP-MESSAGE
        WHEN "NotFound" MOVE "E-STU-103: 対象が見つかりません。" TO APP-MESSAGE
      END-EVALUATE
      COMPUTE APP-MESSAGE-LENGTH = FUNCTION LENGTH(FUNCTION TRIM(APP-MESSAGE))
    END-IF
    GOBACK.

copy "ST-HELPERS.cpy".
end program STMSG.
