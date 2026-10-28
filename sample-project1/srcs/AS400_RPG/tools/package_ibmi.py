"""Close deployment references and aligned physical procedure names."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import re,json
B=Path(__file__).resolve().parents[1]
def put(p,s):(B/p).parent.mkdir(parents=True,exist_ok=True);(B/p).write_text(s.strip()+'\n','utf8')
p=B/'tools/generate_dds.py';s=p.read_text('utf8').replace("f'CF({key:02d} {key:02d})'","f'CF{key:02d}({key:02d})'")
s=s.replace('(3,4,5,6,8,9,10,12,14,16,17,18,19,20,23)','(3,4,5,6,7,8,9,10,12,14,16,17,18,19,20,23)')
s=s.replace('F16=First F17=Last F18=Previous SQL page F19=Next SQL page','F7=First F10=Last PgUp=Previous PgDn=Next F14=Row action')
s=s.replace('F9=Next panel F4=Choice','F7=Previous F9=Next panel F4=Choice')
p.write_text(s,'utf8')
import runpy
runpy.run_path(str(p))
p=B/'src/STUSRCH.sqlrpgle';s=p.read_text('utf8')
s=s.replace('*in10=*off;*in14=*off;*in16=*off;*in17=*off;*in18=*off;*in19=*off;',
 '*in07=*off;*in10=*off;*in14=*off;*in25=*off;*in26=*off;')
start=s.index(' if *in10;\n  SelectRow()');end=s.index(' if *in14;',start)
s=s[:start]+s[end:]
s=s.replace('if *in14;SelectRow();iter;endif;','if *in14;SelectRow();if context.hasApplied;StSearchStudents(raw:context:*off:page);ShowRows();endif;iter;endif;')
s=s.replace('*in16','*in07').replace('*in17','*in10').replace('*in18','*in26').replace('*in19','*in25')
# Enter with an explicit READC row option invokes the row event; Enter without it searches.
s=s.replace(' if *in07;context.page=1;',
 ' if not (*in07 or *in10 or *in25 or *in26);SelectRow();if notice<>\'\';if context.hasApplied;StSearchStudents(raw:context:*off:page);ShowRows();endif;notice=\'\';iter;endif;endif;\n if *in07;context.page=1;')
s=s.replace("StNewId(context.instanceId);raw.selected(1)","StNewId(context.instanceId);context.owner=principal;raw.selected(1)")
s=s.replace('ReadSearch();if uiError;', 'ReadSearch();DrawSearch();if uiError;')
# DrawSearch also updates prior buffers after ordinary edits, preventing stale placeholder writes.
p.write_text(s,'utf8')
p=B/'src/STUEDIT.sqlrpgle';s=p.read_text('utf8')
s=s.replace('*in03=*off;*in04=*off;*in05=*off;*in08=*off;*in09=*off;',
 '*in03=*off;*in04=*off;*in05=*off;*in07=*off;*in08=*off;*in09=*off;')
s=s.replace(' if *in09;panel=%rem(panel:3)+1;iter;endif;',
 ' if *in07;panel=%max(1:panel-1);iter;endif;\n if *in09;panel=%min(3:panel+1);iter;endif;')
s=s.replace("raw.values(5)=%ucs2('0');raw.values(12)","hints.schoolYear=%char(%subdt(day:*years));if %subdt(day:*months)<4;hints.schoolYear=%char(%subdt(day:*years)-1);endif;hints.gradeCode='';\n  raw.values(5)=%ucs2('0');raw.values(12)")
s=s.replace("if uiError;result.kind=RK_VALIDATION;result.messageId='E-COM-003';iter;endif;", "if uiError;result.kind=RK_VALIDATION;result.messageId='E-COM-003';iter;endif;")
p.write_text(s,'utf8')
for member in ['src/STUSVC.sqlrpgle','src/STUMASTER.rpgleinc']:
 p=B/member;s=p.read_text('utf8')
 for old,new in [('BeginWork','StBeginWork'),('CheckRules','StCheckRules'),('FindDuplicates','StFindDuplicates'),('AppendAudit','StAppendAudit')]:s=re.sub(r'\b'+old+r'\b',new,s)
 for name in ['StBeginWork','StCheckRules','StFindDuplicates','StAppendAudit']:s=s.replace('dcl-proc '+name+';','dcl-proc '+name+' export;')
 p.write_text(s,'utf8')
# Confirmation resides in COMMON; the save service generates and consumes native tokens.
p=B/'src/STUSVC.sqlrpgle';s=p.read_text('utf8')
a=s.index('if slot>0 and not confirmations(slot).consumed');b=s.index('    confirmed=1;',a)
s=s[:a]+'''if slot>0 and StConfirm(confirmations(slot):principal:job:hints.instanceId:studentId:expectedVersion:businessHash:candidatesHash:utc:reason);
'''+s[b:];p.write_text(s,'utf8')
confirm='''
dcl-pr StConfirm ind;
 value likeds(Confirmation_t) const;owner varchar(128) const;job varchar(28) const;
 instance char(36) const;id int(20) const;version int(20) const;
 business char(64) const;candidates char(64) const;utc timestamp const;
 reason varucs2(120) ccsid(1200) const;
end-pr;
'''
p=B/'copy/STUPROTO.rpgleinc';s=p.read_text('utf8').replace('/endif',confirm+'/endif');p.write_text(s,'utf8')
p=B/'src/STUCOMMON.sqlrpgle';s=p.read_text('utf8');i=s.index('dcl-proc StMessage export;')
s=s[:i]+'''
dcl-proc StConfirm export;
 dcl-pi *n ind;
  value likeds(Confirmation_t) const;owner varchar(128) const;job varchar(28) const;
  instance char(36) const;id int(20) const;version int(20) const;
  business char(64) const;candidates char(64) const;utc timestamp const;
  reason varucs2(120) ccsid(1200) const;
 end-pi;
 return not value.consumed and value.owner=owner and value.job=job and
  value.instanceId=instance and value.studentId=id and value.expectedVersion=version and
  value.businessHash=business and value.candidatesHash=candidates and
  value.expiresAt>utc and %len(reason)>0;
end-proc;
'''+s[i:];p.write_text(s,'utf8')
# Published ABI signatures use exported procedure symbols in exact source order.
for name in ['STUCOMMON','STUSVC']:
 source=(B/'src'/f'{name}.sqlrpgle').read_text('utf8')
 if name=='STUSVC':source+=(B/'src/STUMASTER.rpgleinc').read_text('utf8')
 names=re.findall(r'dcl-proc\s+(\w+)\s+export;',source,re.I)
 put(f'binder/{name}.bnd',f"STRPGMEXP PGMLVL(*CURRENT) SIGNATURE('{name}_V1')\n"+'\n'.join(f" EXPORT SYMBOL('{n.upper()}')" for n in names)+'\nENDPGMEXP')
cnames=['StUnicodeScalars','StUnicodeNormalize','StUnicodeToJob','StUnicodeFromJob','StUnicodeEscape','StUnicodeDigest','StApprovedOpen','StApprovedLine','StApprovedClose']
put('binder/STUNICODE.bnd',"STRPGMEXP PGMLVL(*CURRENT) SIGNATURE('STUNICODE_V1')\n"+'\n'.join(f" EXPORT SYMBOL('{n.upper()}')" for n in cnames)+'\nENDPGMEXP')
put('cl/BUILD.clle',r'''
PGM
/* Fixed reviewed IFS installation path. Run in controlled development job. */
CRTLIB LIB(STUDPGM) TYPE(*PROD) AUT(*EXCLUDE)
MONMSG MSGID(CPF2111)
CHGCURLIB CURLIB(STUDPGM)
CHGJOB CCSID(1399) DFTWAIT(15)
CRTSRCPF FILE(STUDPGM/QDDSSRC) RCDLEN(112) CCSID(1399)
MONMSG MSGID(CPF7302)
ADDPFM FILE(STUDPGM/QDDSSRC) MBR(STUSCHD) SRCTYPE(DSPF)
MONMSG MSGID(CPF5813)
ADDPFM FILE(STUDPGM/QDDSSRC) MBR(STUEDTD) SRCTYPE(DSPF)
MONMSG MSGID(CPF5813)
CPYFRMSTMF FROMSTMF('/stuapp/source/dds/STUSCHD.dspf') +
 TOMBR('/qsys.lib/studpgm.lib/qddssrc.file/stuschd.mbr') +
 MBROPT(*REPLACE) STMFCODPAG(1208)
CPYFRMSTMF FROMSTMF('/stuapp/source/dds/STUEDTD.dspf') +
 TOMBR('/qsys.lib/studpgm.lib/qddssrc.file/stuedtd.mbr') +
 MBROPT(*REPLACE) STMFCODPAG(1208)
CRTDSPF FILE(STUDPGM/STUSCHD) SRCFILE(STUDPGM/QDDSSRC) +
 SRCMBR(STUSCHD) REPLACE(*YES) AUT(*EXCLUDE)
CRTDSPF FILE(STUDPGM/STUEDTD) SRCFILE(STUDPGM/QDDSSRC) +
 SRCMBR(STUEDTD) REPLACE(*YES) AUT(*EXCLUDE)
CRTCMOD MODULE(STUDPGM/STUNICODE) +
 SRCSTMF('/stuapp/source/c/STUNICODE.c') +
 INCDIR('/stuapp/source/c' '/QIBM/ProdData/OS400/ICU/include') +
 SYSIFCOPT(*IFSIO) DBGVIEW(*SOURCE) REPLACE(*YES)
CRTCMOD MODULE(STUDPGM/STUINPUT) +
 SRCSTMF('/stuapp/source/c/STUINPUT.c') +
 INCDIR('/stuapp/source/c' '/QIBM/ProdData/OS400/ICU/include') +
 SYSIFCOPT(*IFSIO) DBGVIEW(*SOURCE) REPLACE(*YES)
CRTSRVPGM SRVPGM(STUDPGM/STUNICODE) +
 MODULE(STUDPGM/STUNICODE STUDPGM/STUINPUT) +
 EXPORT(*SRCFILE) SRCSTMF('/stuapp/source/binder/STUNICODE.bnd') +
 BNDDIR(QICU/QICU) ACTGRP(*CALLER) REPLACE(*YES) AUT(*EXCLUDE)
CRTSQLRPGI OBJ(STUDPGM/STUCOMMON) +
 SRCSTMF('/stuapp/source/src/STUCOMMON.sqlrpgle') OBJTYPE(*MODULE) +
 COMMIT(*CS) RPGPPOPT(*LVL2) DBGVIEW(*SOURCE) +
 COMPILEOPT('INCDIR(''/stuapp/source/src'' ''/stuapp/source/copy'')')
CRTSRVPGM SRVPGM(STUDPGM/STUCOMMON) MODULE(STUDPGM/STUCOMMON) +
 EXPORT(*SRCFILE) SRCSTMF('/stuapp/source/binder/STUCOMMON.bnd') +
 BNDSRVPGM(STUDPGM/STUNICODE) ACTGRP(*CALLER) REPLACE(*YES) +
 AUT(*EXCLUDE)
CRTSQLRPGI OBJ(STUDPGM/STUSVC) +
 SRCSTMF('/stuapp/source/src/STUSVC.sqlrpgle') OBJTYPE(*MODULE) +
 COMMIT(*CS) RPGPPOPT(*LVL2) DBGVIEW(*SOURCE) +
 COMPILEOPT('INCDIR(''/stuapp/source/src'' ''/stuapp/source/copy'')')
CRTSRVPGM SRVPGM(STUDPGM/STUSVC) MODULE(STUDPGM/STUSVC) +
 EXPORT(*SRCFILE) SRCSTMF('/stuapp/source/binder/STUSVC.bnd') +
 BNDSRVPGM(STUDPGM/STUCOMMON STUDPGM/STUNICODE) +
 ACTGRP(*CALLER) REPLACE(*YES) AUT(*EXCLUDE)
CRTBNDDIR BNDDIR(STUDPGM/STUBND) AUT(*EXCLUDE)
MONMSG MSGID(CPF2112)
ADDBNDDIRE BNDDIR(STUDPGM/STUBND) +
 OBJ((STUDPGM/STUSVC *SRVPGM) (STUDPGM/STUCOMMON *SRVPGM) +
 (STUDPGM/STUNICODE *SRVPGM))
MONMSG MSGID(CPF2178)
CRTSQLRPGI OBJ(STUDPGM/STUEDIT) +
 SRCSTMF('/stuapp/source/src/STUEDIT.sqlrpgle') OBJTYPE(*MODULE) +
 COMMIT(*CS) RPGPPOPT(*LVL2) DBGVIEW(*SOURCE) +
 COMPILEOPT('INCDIR(''/stuapp/source/src'' ''/stuapp/source/copy'')')
CRTPGM PGM(STUDPGM/STUEDIT) MODULE(STUDPGM/STUEDIT) +
 BNDDIR(STUDPGM/STUBND) ACTGRP(STUDAG) REPLACE(*YES) AUT(*EXCLUDE)
CRTSQLRPGI OBJ(STUDPGM/STUSRCH) +
 SRCSTMF('/stuapp/source/src/STUSRCH.sqlrpgle') OBJTYPE(*MODULE) +
 COMMIT(*CS) RPGPPOPT(*LVL2) DBGVIEW(*SOURCE) +
 COMPILEOPT('INCDIR(''/stuapp/source/src'' ''/stuapp/source/copy'')')
CRTPGM PGM(STUDPGM/STUSRCH) MODULE(STUDPGM/STUSRCH) +
 BNDDIR(STUDPGM/STUBND) ACTGRP(STUDAG) REPLACE(*YES) AUT(*EXCLUDE)
CRTSQLRPGI OBJ(STUDPGM/STUMNT) +
 SRCSTMF('/stuapp/source/src/STUMNT.sqlrpgle') OBJTYPE(*MODULE) +
 COMMIT(*CS) RPGPPOPT(*LVL2) DBGVIEW(*SOURCE) +
 COMPILEOPT('INCDIR(''/stuapp/source/src'' ''/stuapp/source/copy'')')
CRTPGM PGM(STUDPGM/STUMNT) MODULE(STUDPGM/STUMNT) +
 BNDDIR(STUDPGM/STUBND) ACTGRP(STUDAG) REPLACE(*YES) AUT(*EXCLUDE)
ENDPGM
''')
put('cl/JOURNAL.clle',r'''
PGM
/* Run after schema.sql and before application starts. All six are mandatory. */
CRTJRNRCV JRNRCV(STUDAPP/STURCV0001) THRESHOLD(100000)
CRTJRN JRN(STUDAPP/STUJRN) JRNRCV(STUDAPP/STURCV0001) +
 MNGRCV(*SYSTEM) DLTRCV(*NO) AUT(*EXCLUDE)
STRJRNPF FILE(STUDAPP/M_STUDENT) JRN(STUDAPP/STUJRN) IMAGES(*BOTH)
STRJRNPF FILE(STUDAPP/M_CLASS) JRN(STUDAPP/STUJRN) IMAGES(*BOTH)
STRJRNPF FILE(STUDAPP/MCAT) JRN(STUDAPP/STUJRN) IMAGES(*BOTH)
STRJRNPF FILE(STUDAPP/M_CODE) JRN(STUDAPP/STUJRN) IMAGES(*BOTH)
STRJRNPF FILE(STUDAPP/T_OPLOG) JRN(STUDAPP/STUJRN) IMAGES(*BOTH)
STRJRNPF FILE(STUDAPP/STGUARD) JRN(STUDAPP/STUJRN) IMAGES(*BOTH)
ENDPGM
''')
put('cl/START.clle',r'''
PGM
CHGJOB CCSID(1399) DFTWAIT(15)
STRCMTCTL LCKLVL(*CS) CMTSCOPE(*JOB)
MONMSG MSGID(CPF8351) EXEC(DO)
 SNDPGMMSG MSG('Start in a clean job without existing commitment scope.') +
 MSGTYPE(*ESCAPE)
ENDDO
CALL PGM(STUDPGM/STUSRCH)
MONMSG MSGID(CPF0000) EXEC(DO)
 ROLLBACK
 ENDCMTCTL
 SNDPGMMSG MSG('Student application failed; inspect joblog.') MSGTYPE(*ESCAPE)
ENDDO
ROLLBACK
ENDCMTCTL
RCLACTGRP ACTGRP(STUDAG)
ENDPGM
''')
put('cl/SECURITY.clle',r'''
PGM
/* Security administrator: create STUOWNER minimal profile and role groups first. */
CHGOBJOWN OBJ(STUDPGM/STUCOMMON) OBJTYPE(*SRVPGM) NEWOWN(STUOWNER)
CHGOBJOWN OBJ(STUDPGM/STUSVC) OBJTYPE(*SRVPGM) NEWOWN(STUOWNER)
CHGOBJOWN OBJ(STUDPGM/STUEDIT) OBJTYPE(*PGM) NEWOWN(STUOWNER)
CHGOBJOWN OBJ(STUDPGM/STUSRCH) OBJTYPE(*PGM) NEWOWN(STUOWNER)
CHGOBJOWN OBJ(STUDPGM/STUMNT) OBJTYPE(*PGM) NEWOWN(STUOWNER)
CHGSRVPGM SRVPGM(STUDPGM/STUCOMMON) USRPRF(*OWNER)
CHGSRVPGM SRVPGM(STUDPGM/STUSVC) USRPRF(*OWNER)
CHGPGM PGM(STUDPGM/STUSRCH) USRPRF(*OWNER) USEADPAUT(*YES)
CHGPGM PGM(STUDPGM/STUEDIT) USRPRF(*OWNER) USEADPAUT(*YES)
CHGPGM PGM(STUDPGM/STUMNT) USRPRF(*OWNER) USEADPAUT(*YES)
GRTOBJAUT OBJ(STUDPGM/STUSRCH) OBJTYPE(*PGM) +
 USER(STUADMIN STUSTAFF STUVIEW) AUT(*USE)
GRTOBJAUT OBJ(STUDPGM/STUEDIT) OBJTYPE(*PGM) +
 USER(STUADMIN STUSTAFF STUVIEW) AUT(*USE)
GRTOBJAUT OBJ(STUDPGM/STUMNT) OBJTYPE(*PGM) USER(STUADMIN) AUT(*USE)
/* Assign minimal table rights only to STUOWNER; public/role profiles EXCLUDE. */
ENDPGM
''')
put('config/class-approved.example.txt',r'''
# UTF8; approved leaf /stuapp/approved/class-2026.txt; all values escape-decoded.
TYPE=CLASS
classId=0
expectedVersion=0
schoolYear=2026
gradeCode=01
classCode=C-A
className=Aクラス
validFrom=2026-04-01
validTo=2027-03-31
capacity=30
displayOrder=10
isActive=1
remarks=
reason=年度開始の承認済みクラス登録
END
''')
put('config/code-approved.example.txt',r'''
TYPE=CODE
categoryId=RELATIONSHIP
codeValue=08
expectedVersion=0
codeName=承認済み続柄
displayOrder=80
isActive=1
validFrom=2026-10-12
validTo=
remarks=
reason=承認済みコード追加
END
''')
print('Generated binder/CL/config; public symbols and display keys aligned')
