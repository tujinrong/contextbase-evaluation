"""DDS positions 1..44 are explicit; numeric/ASCII identifiers are never DBCS."""
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def keyword(value,condition=''):
    chars=[' ']*44;chars[5]='A'
    if condition:chars[7:10]=list(condition.rjust(3))
    return ''.join(chars)+value
def record(name,*keys):
    chars=[' ']*44;chars[5]='A';chars[16]='R';chars[18:28]=list(name.ljust(10))
    return [''.join(chars).rstrip()]+[keyword(k) for k in keys]
def field(name,length,row,col,usage='B',dtype='O',readonly=False):
    chars=[' ']*44;chars[5]='A';chars[18:28]=list(name.ljust(10))
    chars[29:34]=list(str(length).rjust(5));chars[34]=dtype;chars[37]=usage
    if usage!='H':chars[38:41]=list(str(row).rjust(3));chars[41:44]=list(str(col).rjust(3))
    lines=[''.join(chars).rstrip()]
    if readonly:lines.append(keyword('DSPATR(PR)','75'))
    return lines
def literal(text,row,col):
    chars=[' ']*44;chars[5]='A';chars[38:41]=list(str(row).rjust(3));chars[41:44]=list(str(col).rjust(3))
    return ''.join(chars)+"'"+text+"'"
def header():
    return [keyword('DSPSIZ(27 132 *DS4)')]+[keyword(f'CF{key:02d}({key:02d})') for key in (3,4,5,6,7,8,9,10,12,14,16,17,18,19,20,23)]+[keyword('ROLLUP(25)'),keyword('ROLLDOWN(26)')]
def aux(lines):
    lines+=record('CNFRM')
    lines+=field('CTITLE',100,2,3,'O')
    lines+=[literal('F10=Confirm F12=Cancel PgUp/PgDn',24,3)]
    lines+=field('CREASON',122,4,3)
    lines+=field('CTOTAL',100,6,3,'O')
    lines+=field('CSEL',3,7,5,dtype='A')
    for i in range(1,11):lines+=field(f'C{i:02d}',122,i+9,3,'O')
    lines+=field('CMSG',128,26,3,'O')
    lines+=record('LONGTXT')
    lines+=field('LTITLE',100,2,3,'O')
    lines+=field('LPOS',80,3,3,'O')
    lines += [literal('Unicode escapes / doubled slash',5,3)]
    for i in range(1,7):lines+=field(f'LTXT{i}',120,i*2+5,3,readonly=True)
    lines+=[literal('F10=Apply F12=Cancel PgUp/PgDn',23,3)]
    lines+=field('LMSG',128,26,3,'O')
    return lines
search=header()+record('COND','OVERLAY')
search+=[literal('Student search Enter=Search',1,3)]
for name,width,row,col,typ in [('QSTUNO',30,2,12,'O'),('QNAME',40,2,66,'O'),('QKANA',72,3,12,'O'),('QYEAR',4,3,96,'A'),('QGRADE',2,4,12,'A'),('QCLASS',19,4,33,'A'),('QUNASS',1,4,68,'A'),('QST01',1,5,12,'A'),('QST02',1,5,27,'A'),('QST03',1,5,42,'A'),('QST04',1,5,57,'A'),('QPREF',2,5,78,'A'),('QPHONE',40,6,12,'O'),('QADMFROM',10,6,68,'A'),('QADMTO',10,6,94,'A'),('QSIZE',3,7,12,'A'),('QSORT',16,7,33,'A'),('QDIR',4,7,65,'A'),('QFIELD',2,7,97,'A')]:search+=field(name,width,row,col,dtype=typ)
for text,row,col in [('StudentNo',2,2),('Name',2,55),('Kana',3,2),('Year',3,87),('Grade',4,2),('Class ID',4,22),('Unassigned',4,55),('01',5,6),('02',5,21),('03',5,36),('04',5,51),('Prefecture',5,65),('Phone',6,2),('From',6,58),('To',6,85),('Size',7,2),('Sort',7,23),('Dir',7,55),('F4/F8 field',7,82)]:search.append(literal(text,row,col))
search+=record('SFLROW','SFL')
for name,width,col,typ in [('SOPT',1,3,'A'),('SNO',15,6,'A'),('SNAME',20,22,'O'),('SBIRTH',26,43,'O'),('SYEARGR',10,70,'O'),('SCLASS',30,81,'O'),('SSTATUS',18,112,'O')]:search+=field(name,width,11,col,dtype=typ)
search+=field('SROWID',19,0,0,'H','A')
search+=record('SFLCTL','SFLCTL(SFLROW)','OVERLAY','SFLSIZ(101)','SFLPAG(10)')
search+=[keyword('SFLDSP','90'),keyword('SFLDSPCTL','91'),keyword('SFLCLR','92')]
search+=field('RESULT_CNT',80,9,3,'O')+field('SEARCH_AT',30,9,99,'O')
search+=[literal('2=Edit 5=View 9=Full F9=More',22,3)]
search+=field('QMSG',128,24,3,'O')
search+=[literal('F7=First F10=Last PgUp/PgDn',26,3)]
search=aux(search)
edit=header()+record('EDBASE')
edit+=[literal('Edit F7=Prev F9=Next F8=Unicode',1,3)]
for name,width,row,col,typ in [('ESTUNO',30,3,22,'O'),('ENAME',40,5,22,'O'),('EKANA',72,7,22,'O'),('EBERA',10,9,22,'A'),('EBYEAR',8,9,45,'O'),('EBMONTH',4,9,66,'O'),('EBDAY',4,9,83,'O'),('EGENDER',1,11,22,'A'),('EPOSTAL',20,13,22,'O'),('EPREF',2,15,22,'A'),('EADDR1',90,17,22,'O'),('EADDR2',90,19,22,'O')]:
    edit+=field(name,width,row,col,dtype=typ,readonly=True)
    if name=='ESTUNO':edit.append(keyword('DSPATR(PR)','76'))
for text,row in [('StudentNo',3),('Name',5),('Kana',7),('Birth (era Y M D)',9),('Gender',11),('Postal',13),('Prefecture',15),('Address1',17),('Address2',19)]:edit.append(literal(text,row,2))
edit+=field('EFIELD',2,22,22,dtype='A')+field('EMSG1',128,24,3,'O')
edit+=[literal('F10=Save F5=Reset F12=Return',26,3)]
edit+=record('EDENROLL')
edit+=[literal('Enrolment (dates ISO yyyy-mm-dd)',1,3)]
for name,width,row,col,typ in [('EPHONE',40,3,22,'O'),('EEMAIL',60,5,22,'O'),('EADMDATE',10,7,22,'A'),('ESTATUS',2,9,22,'A'),('EENDDATE',10,11,22,'A'),('EYEAR',4,13,22,'A'),('EGRADE',2,15,22,'A'),('ECLASS',19,17,22,'A'),('EEMGNAME',40,19,22,'O'),('EREL',2,21,22,'A')]:edit+=field(name,width,row,col,dtype=typ,readonly=True)
for text,row in [('Phone',3),('Email',5),('Admission',7),('Status',9),('End date',11),('Year hint',13),('Grade hint',15),('Class ID',17),('Emergency name',19),('Relationship',21)]:edit.append(literal(text,row,2))
edit+=field('EFIELD2',2,22,119,dtype='A')+field('OCCUPANCY',95,23,3,'O')+field('EMSG2',128,24,3,'O')
edit+=record('EDNOTE')
edit+=[literal('Notes / update information',1,3)]
edit+=field('EEMGPHONE',40,3,22,readonly=True)+field('EREMARKS',120,6,3,readonly=True)+field('EREASON',122,9,3,readonly=True)
edit+=field('ESTUID',19,12,22,'O','A')+field('EVERSION',19,14,22,'O','A')+field('UPDATEDAT',26,16,22,'O','A')+field('UPDATEDBY',90,18,22,'O')+field('EMSG3',128,24,3,'O')
edit+=[literal('Emergency phone',3,2),literal('Remarks (F8 field 19)',5,3),literal('Operation reason (F8 field 24)',8,3),literal('Student ID',12,2),literal('Version',14,2),literal('Updated JST',16,2),literal('Updated by',18,2)]
edit+=field('EFIELD3',2,22,119,dtype='A')
edit=aux(edit)
for name,lines in [('STUSCHD',search),('STUEDTD',edit)]:
    p=BASE/'dds'/f'{name}.dspf';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('\n'.join(lines)+'\n',encoding='utf8')
print('DDS generated: STUSCHD/ STUEDTD, 27x132, 10-row subfile and auxiliary records')
