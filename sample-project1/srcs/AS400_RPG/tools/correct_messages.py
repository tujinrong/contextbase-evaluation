import sys
sys.dont_write_bytecode = True
from pathlib import Path
base=Path(__file__).resolve().parents[1]
for path in [base/'src/STUSVC.sqlrpgle',base/'src/STUMASTER.rpgleinc']:
    text=path.read_text(encoding='utf-8')
    text=text.replace("result.messageId='E-STU-104'", "result.messageId='E-STU-105'")
    text=text.replace("page.result.messageId='E-COM-001'", "page.result.messageId='E-COM-002'")
    text=text.replace("StError(result:'studentNo':'E-STU-004')", "StError(result:'studentNo':'E-STU-104')")
    text=text.replace("if count>0;StError(result:'studentNo':'E-STU-003')", "if count>0;StError(result:'studentNo':'E-STU-101')")
    text=text.replace("StError(result:'reason':'E-STU-025')", "StError(result:'reason':'E-STU-106')")
    text=text.replace("StError(result:field:'E-STU-010')", "StError(result:field:'E-STU-009')")
    text=text.replace("StError(result:'classId':'E-STU-013')", "StError(result:'classId':'E-STU-014')")
    text=text.replace("StError(result:'classId':'E-STU-015')", "StError(result:'classId':'E-STU-102')")
    text=text.replace("StError(result:'unassignedOnly':'E-STU-029')", "StError(result:'unassignedOnly':'E-SRC-001')")
    text=text.replace("StError(result:'classId':'E-STU-014');endif;\n   CheckCode", "StError(result:'classId':'E-STU-013');endif;\n   CheckCode")
    text=text.replace("work.enrollmentEndDate<cls.validFrom;StError(result:'classId':'E-STU-014')", "work.enrollmentEndDate<cls.validFrom;StError(result:'classId':'E-STU-108')")
    if 'MASTER' in path.name:
        text=text.replace('SqlFailure(result:SQLSTT)', "SqlFailure(result:SQLSTT:'MASTER')")
    path.write_text(text,encoding='utf-8')
path=base/'src/STUCOMMON.sqlrpgle'
text=path.read_text(encoding='utf-8').replace("result.messageId='E-COM-001'", "result.messageId='E-COM-002'")
text=text.replace("when rc=2;StError(result:field:'E-STU-002');other;StError(result:field:'E-COM-003')", "when rc=2;StError(result:field:'E-STU-002');other;select;when mode=3 or mode=4;StError(result:field:'E-STU-004');when mode=5;StError(result:field:'E-STU-003');when mode=7;StError(result:field:'E-STU-015');when mode=8;StError(result:field:'E-STU-016');when mode=9;StError(result:field:'E-STU-017');when mode=10;StError(result:field:'E-STU-005');other;StError(result:field:'E-COM-003');endsl")
text=text.replace("when code='E-STU-104'", "when code='E-STU-105'").replace("when code='E-COM-001'", "when code='E-COM-002'")
path.write_text(text,encoding='utf-8')
print('aligned RPG result message identifiers with common05')
