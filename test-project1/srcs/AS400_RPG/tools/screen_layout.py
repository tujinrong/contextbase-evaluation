"""Current production DDS layouts for the compact 27 by 132 terminal contract."""
def generate(base,header,record,field,literal,keyword,aux):
 search=header()+[keyword('CF11(11)'),keyword('CF15(15)')]+record('COND','OVERLAY')
 search+=[literal('学生検索 Enter=検索 F4=全年度クラス候補',1,3)]
 for name,width,row,col,typ in [('QSTUNO',30,2,12,'O'),('QNAME',16,2,66,'O'),('QCLASS',19,3,12,'A'),('QST01',1,4,12,'A'),('QST02',1,4,29,'A'),('QST03',1,4,46,'A'),('QST04',1,4,63,'A'),('QSIZE',3,5,12,'A'),('QSORT',16,5,33,'A'),('QDIR',4,5,65,'A'),('QFIELD',2,5,97,'A')]:search+=field(name,width,row,col,dtype=typ)
 for label,row,col in [('学籍番号',2,2),('氏名',2,55),('クラスID',3,2),('在学',4,3),('休学',4,20),('卒業',4,37),('退学',4,54),('件数',5,2),('順序',5,23),('方向',5,55),('F4/F8項目',5,80)]:search+=[literal(label,row,col)]
 search+=field('QMSG',128,6,3,'O')
 search+=[literal('選 学籍番号       氏名 / カナ    生年月日 / 年度学年 / クラス / 在籍',7,3)]
 search+=record('SFLROW','SFL')
 search+=field('SOPT',1,8,3,dtype='A')
 for name,width,row,col,typ in [('SNO',15,8,6,'A'),('SNAME',16,8,23,'O'),('SBIRTH',26,8,43,'O'),('SYEARGR',22,8,72,'O'),('SSTATUS',24,8,106,'O'),('SKANA',72,9,6,'O'),('SCLASS',48,9,81,'O')]:search+=field(name,width,row,col,'O',typ)
 search+=field('SROWID',19,0,0,'H','A')
 search+=record('SFLCTL','SFLCTL(SFLROW)','OVERLAY','SFLSIZ(101)','SFLPAG(8)')
 search+=[keyword('SFLDSP','90'),keyword('SFLDSPCTL','91'),keyword('SFLCLR','92')]
 search+=field('RESULT_CNT',128,24,3,'O')+field('SEARCH_AT',30,25,3,'O')
 search+=[literal('PageUp/Down=8学生 F7=前DB頁 F10=次DB頁 F15=先頭 F16=最後',26,3),literal('2編集 5参照 9全文 F9順序 F11件数 F5クリア F6新規 F12戻る',27,3)]
 search=aux(search)
 edit=header()
 def common(lines,index):
  lines+=field('ESTUID',19,2,14,'O','A')+field('EVERSION',19,2,69,'O','A')
  lines+=field('UPDATEDAT',26,23,12,'O','A')+field('UPDATEDBY',90,23,40,'O')
  lines+=field('EMSG'+str(index),128,24,3,'O')
  lines+=[literal('管理番号',2,3),literal('版',2,64),literal('更新JST',23,3),literal('F9切替 F4候補 F8全文 F10保存 F5取消 F14再読込 F12戻る F23削除',26,3)]
  return lines
 edit+=record('EDBASE')+[literal('学生編集 1/2 基本・住所・本人連絡先',1,3)]
 for name,width,row,col,typ in [('ESTUNO',30,3,12,'O'),('ENAME',16,3,56,'O'),('EGENDER',1,3,122,'A'),('EKANA',72,5,22,'O'),('EBERA',10,7,12,'A'),('EBYEAR',8,7,43,'O'),('EBMONTH',4,7,65,'O'),('EBDAY',4,7,80,'O'),('EPOSTAL',20,9,12,'O'),('EPREF',2,9,56,'A'),('EADDR1',90,11,22,'O'),('EADDR2',90,13,22,'O'),('EPHONE',40,15,22,'O'),('EEMAIL',60,17,22,'O')]:
  edit+=field(name,width,row,col,dtype=typ,readonly=True)
  if name=='ESTUNO':edit.append(keyword('DSPATR(PR)','76'))
 for label,row,col in [('学籍番号',3,2),('氏名',3,46),('性別',3,112),('氏名カナ',5,2),('生年月日',7,2),('年',7,39),('月',7,61),('日',7,76),('郵便番号',9,2),('県',9,51),('住所1',11,2),('住所2',13,2),('本人電話',15,2),('メール',17,2)]:edit+=[literal(label,row,col)]
 edit+=field('EFIELD',2,21,22,dtype='A')+[literal('F4/F8項目番号',21,2)]
 edit=common(edit,1)
 edit+=record('EDENROLL')+[literal('学生編集 2/2 在籍・所属・緊急連絡先・備考',1,3)]
 for name,width,row,col,typ in [('EADMDATE',10,3,22,'A'),('ESTATUS',2,3,70,'A'),('EENDDATE',10,5,22,'A'),('EYEAR',4,7,22,'A'),('EGRADE',2,7,70,'A'),('ECLASS',19,9,22,'A'),('EEMGNAME',16,13,22,'O'),('EREL',2,13,70,'A'),('EEMGPHONE',40,15,22,'O'),('EREMARKS',90,17,22,'O'),('EREASON',90,19,22,'O')]:edit+=field(name,width,row,col,dtype=typ,readonly=True)
 for label,row,col in [('入学日',3,2),('在籍',3,62),('卒業退学日',5,2),('年度補助',7,2),('学年補助',7,58),('クラスID',9,2),('緊急氏名',13,2),('続柄',13,62),('緊急電話',15,2),('備考 F8=19',17,2),('理由 F8=24',19,2)]:edit+=[literal(label,row,col)]
 edit+=field('OCCUPANCY',128,11,3,'O')+field('EFIELD2',2,21,22,dtype='A')+[literal('F4/F8項目番号',21,2)]
 edit=common(edit,2)
 edit=aux(edit)
 for name,lines in [('STUSCHD',search),('STUEDTD',edit)]:
  (base/'dds'/f'{name}.dspf').write_text('\n'.join(lines)+'\n','utf8')
 print('Generated current DDS: 4 search conditions, SFLPAG(8) x 2 lines, 2 editor panels; auxiliary full text preserves raw values.')
