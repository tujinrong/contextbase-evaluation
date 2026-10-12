       >>SOURCE FORMAT FREE
identification division.
program-id. STDATEOUT.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
01 YY pic 9(4).
01 MM pic 9(2).
01 DD pic 9(2).
01 ERA-YEAR pic Z(3)9.
01 ERA-NAME pic X(12).
01 ERA-KEY pic X(6).
01 OFFSET-N pic S9(9) comp-5.
01 PTR pic S9(9) comp-5.
linkage section.
01 ISO-DATE pic X(10).
01 ERA-V. 05 EL pic S9(9) comp-5. 05 EN pic S9(4) comp-5.
  05 filler pic X(2). 05 ED pic X(1024).
01 YEAR-V. 05 YL pic S9(9) comp-5. 05 YN pic S9(4) comp-5.
  05 filler pic X(2). 05 YD pic X(1024).
01 MONTH-V. 05 ML pic S9(9) comp-5. 05 MN pic S9(4) comp-5.
  05 filler pic X(2). 05 MD pic X(1024).
01 DAY-V. 05 DL pic S9(9) comp-5. 05 DN pic S9(4) comp-5.
  05 filler pic X(2). 05 DDATA pic X(1024).
01 OUT-TEXT pic X(64).
01 OUT-LENGTH pic S9(9) comp-5.
procedure division using ISO-DATE ERA-V YEAR-V MONTH-V DAY-V
    OUT-TEXT OUT-LENGTH.
    if ISO-DATE(1:4) is not numeric or ISO-DATE < "1900-01-01"
      move -1 to return-code goback end-if
    evaluate true
      when ISO-DATE >= "2019-05-01"
        move "REIWA" to ERA-KEY move "令和" to ERA-NAME move 2018 to OFFSET-N
      when ISO-DATE >= "1989-01-08"
        move "HEISEI" to ERA-KEY move "平成" to ERA-NAME move 1988 to OFFSET-N
      when ISO-DATE >= "1926-12-25"
        move "SHOWA" to ERA-KEY move "昭和" to ERA-NAME move 1925 to OFFSET-N
      when ISO-DATE >= "1912-07-30"
        move "TAISHO" to ERA-KEY move "大正" to ERA-NAME move 1911 to OFFSET-N
      when other
        move "MEIJI" to ERA-KEY move "明治" to ERA-NAME move 1867 to OFFSET-N
    end-evaluate
    initialize ERA-V YEAR-V MONTH-V DAY-V
    move ERA-KEY to ED compute EL = function length(function trim(ERA-KEY))
    compute YY = function numval(ISO-DATE(1:4)) - OFFSET-N
    move YY to ERA-YEAR
    move function trim(ERA-YEAR) to YD
    compute YL = function length(function trim(ERA-YEAR))
    move ISO-DATE(6:2) to MD move 2 to ML
    move ISO-DATE(9:2) to DDATA move 2 to DL
    move spaces to OUT-TEXT move 1 to PTR
    string function trim(ERA-NAME) into OUT-TEXT with pointer PTR end-string
    if YY = 1
      string "元" into OUT-TEXT with pointer PTR end-string
    else
      string function trim(ERA-YEAR) into OUT-TEXT with pointer PTR end-string
    end-if
    string "年" MD(1:2) "月" DDATA(1:2) "日"
      into OUT-TEXT with pointer PTR end-string
    compute OUT-LENGTH = PTR - 1
    move 0 to return-code goback.
end program STDATEOUT.
