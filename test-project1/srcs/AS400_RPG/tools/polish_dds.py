import sys
sys.dont_write_bytecode = True
from pathlib import Path
import runpy
B=Path(__file__).resolve().parents[1]
p=B/'tools/generate_dds.py';s=p.read_text('utf8')
short={
'Student search: Enter=Search F5=Clear F6=New F3=Return':'Student search Enter=Search',
'F10=Confirm  F12=Cancel (default)  PgUp/PgDn=more':'F10=Confirm F12=Cancel PgUp/PgDn',
'Explicit Unicode mode: \\u{HEX}; \\\\ = backslash':'Unicode: \\u{HEX}; \\\\ = slash',
'F10=Apply  F12=Cancel  PgUp/PgDn=all text pages':'F10=Apply F12=Cancel PgUp/PgDn',
'2=Edit 5=View 9=Full row (11 columns) F9=next 10 rows':'2=Edit 5=View 9=Full F9=More',
'F7=First F10=Last PgUp=Previous PgDn=Next F14=Row action':'F7=First F10=Last PgUp/PgDn',
'Student edit 1/3 F7=Previous F9=Next panel F4=Choice F8=Full/Unicode field':'Edit F7=Prev F9=Next F8=Unicode',
'F10=Save F5=Cancel edits F14=Reload F20=Errors F12=Return F23=Delete':'F10=Save F5=Reset F12=Return',
'Student edit 2/3 (dates ISO yyyy-mm-dd)':'Enrolment (dates ISO yyyy-mm-dd)',
'Student edit 3/3 F8=Full text; no hidden value is overwritten':'Notes / update information',
'Remarks (full editing: F8 field 19)':'Remarks (F8 field 19)',
'Change reason (field 24; max 60 scalars)':'Operation reason (F8 field 24)',
}
for a,b in short.items():s=s.replace(a,b)
s='\n'.join("    lines += [literal('Unicode escapes / doubled slash',5,3)]" if "literal('Explicit Unicode mode:" in line else line for line in s.splitlines())+'\n'
p.write_text(s,'utf8');runpy.run_path(str(p))
# These fields use no source continuation and remain within the DDS functions area.
labels={'StudentNo':'学籍番号','Name':'氏名','Kana':'氏名カナ','Year':'年度','Grade':'学年','Class ID':'クラスID','Unassigned':'未所属','Prefecture':'都道府県','Phone':'電話','From':'開始','To':'終了','Size':'件数','Sort':'順序','Dir':'方向','Gender':'性別','Postal':'郵便番号','Address1':'住所1','Address2':'住所2','Email':'メール','Admission':'入学日','Status':'在籍状態','End date':'在籍終了日','Year hint':'年度補助','Grade hint':'学年補助','Emergency name':'緊急連絡先氏名','Relationship':'続柄','Emergency phone':'緊急電話','Student ID':'学生管理番号','Version':'更新版','Updated JST':'更新日時JST','Updated by':'更新者','Birth (era Y M D)':'生年月日'}
for p in (B/'dds').glob('*.dspf'):
 s=p.read_text('utf8')
 for a,b in labels.items():s=s.replace("'"+a+"'","'"+b+"'")
 p.write_text(s,'utf8')
print('DDS literals abbreviated for source functions area, field labels Japanese')
