       >>SOURCE FORMAT FREE
identification division.
program-id. validation-probe.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
copy "ST-FIELDS.cpy".
copy "ST-APP.cpy".
01 RC pic S9(9) comp-5.
01 STATUS-OUT pic 9(3).
procedure division.
    initialize APP
    move 200 to APP-STATUS move 1 to APP-ERRORS-LENGTH
    move "2026-10-10" to BUSINESS-DAY
    call "STHTTP" using ST-RAW returning RC end-call
    if RC not = 0 move 400 to APP-STATUS
    else
      call "STNORM" end-call
      if APP-STATUS = 200 call "STVALID" end-call end-if
    end-if
    move APP-STATUS to STATUS-OUT
    if APP-STATUS = 200
      display STATUS-OUT "|" N-DATA(26)(1:2) "|" N-DATA(27)(1:4)
    else display STATUS-OUT end-if
    stop run.
end program validation-probe.
