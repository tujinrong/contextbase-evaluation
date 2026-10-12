       >>SOURCE FORMAT FREE
identification division.
program-id. STISODATE.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
01 YY pic S9(9) comp-5.
01 MM pic S9(9) comp-5.
01 DD pic S9(9) comp-5.
01 MDAYS pic S9(9) comp-5.
linkage section.
01 INPUT-V. 05 LL pic S9(9) comp-5. 05 NN pic S9(4) comp-5.
  05 filler pic X(2). 05 VV pic X(1024).
01 TODAY pic X(10).
procedure division using INPUT-V TODAY.
    move -1 to return-code
    if LL not = 10 or VV(5:1) not = "-" or VV(8:1) not = "-"
      or VV(1:4) is not numeric or VV(6:2) is not numeric
      or VV(9:2) is not numeric goback end-if
    compute YY = function numval(VV(1:4))
    compute MM = function numval(VV(6:2))
    compute DD = function numval(VV(9:2))
    if YY < 1900 or > 9999 or MM < 1 or > 12 or DD < 1
      or VV(1:10) > TODAY goback end-if
    move 31 to MDAYS
    if MM = 4 or 6 or 9 or 11 move 30 to MDAYS end-if
    if MM = 2
      move 28 to MDAYS
      if function mod(YY,400) = 0 or (function mod(YY,4) = 0
        and function mod(YY,100) not = 0) move 29 to MDAYS end-if
    end-if
    if DD > MDAYS goback end-if
    move 0 to return-code goback.
end program STISODATE.
