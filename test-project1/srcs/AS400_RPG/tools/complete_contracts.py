"""Regenerate fixed COPY and current message catalogue from permitted specs.
Does not alter specifications, database resources, reports or another profile.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import re, runpy, json
BASE=Path(__file__).resolve().parents[1]
PROJECT=BASE
SPEC=PROJECT.parent.parent/'spec'/PROJECT.name
runpy.run_path(str(BASE/'tools/generate_sources.py'))
def alter(path, old, new):
    p=BASE/path;s=p.read_text(encoding='utf8')
    if old in s:p.write_text(s.replace(old,new),encoding='utf8')
alter('copy/STULOAD.rpgleinc','s.name_key, s.kana_key','s.relationship_category, s.name_key, s.kana_key')
alter('copy/STULOAD.rpgleinc',':rec.work.nameKey, :rec.work.kanaKey',':rec.work.relationshipCategory :rec.work.relationshipCategoryInd, :rec.work.nameKey, :rec.work.kanaKey')
alter('copy/STUCHANGED.rpgleinc',',"relationship_category","created_at"',',"created_at"')
p=BASE/'copy/STUCHANGED.rpgleinc';s=p.read_text(encoding='utf8')
line='''if studentId=0 or work.relationshipCategoryInd<>old.work.relationshipCategoryInd or (work.relationshipCategoryInd=0 and work.relationshipCategory<>old.work.relationshipCategory);if changed<>'[';changed+=',';endif;changed+='"relationship_category"';endif;\n'''
s=s.replace("if studentId=0;changed+=",line+"if studentId=0;changed+=");p.write_text(s,encoding='utf8')
p=BASE/'src/STUSVC.sqlrpgle';s=p.read_text(encoding='utf8')
s=s.replace("result.messageId='E-COM-001';return;endif;","result.messageId='E-COM-002';return;endif;")
s=s.replace('dcl-pi *n;raw likeds(StudentRaw_t) const;hints','dcl-pi *n;input likeds(StudentWork_t) const;hints')
anchor='dcl-proc StSaveStudent export;'
before,after=s.split(anchor,1)
after=after.replace(' dcl-ds work likeds(StudentWork_t);',' dcl-ds raw likeds(StudentRaw_t);dcl-ds rec likeds(StudentRecord_t);dcl-s wareki varucs2(80) ccsid(1200);\n dcl-ds work likeds(StudentWork_t);',1) if 'dcl-ds raw likeds(StudentRaw_t)' not in after.split('end-proc;',1)[0] else after
after=after.replace(' StClock(utc:day);StNormalize(raw:work:day:result);',' rec.work=input;\n /copy \'../copy/STUTORAW.rpgleinc\'\n StClock(utc:day);StNormalize(raw:work:day:result);',1) if 'rec.work=input;' not in after else after
s=before+anchor+after
# A retained final class does not need fresh period overlap for address-only changes.
s=s.replace("if work.admissionDate>cls.validTo or work.enrollmentEndDate<cls.validFrom;", "if (studentId=0 or old.work.classIdInd<>work.classIdInd or old.work.classId<>work.classId or old.work.admissionDate<>work.admissionDate or old.work.enrollmentEndDateInd<>work.enrollmentEndDateInd or old.work.enrollmentEndDate<>work.enrollmentEndDate or old.work.enrollmentStatusCode<>work.enrollmentStatusCode) and (work.admissionDate>cls.validTo or work.enrollmentEndDate<cls.validFrom);")
p.write_text(s,encoding='utf8')
catalog={}
for line in (SPEC/'共通/05_チェック・メッセージ設計.md').read_text(encoding='utf8').splitlines():
    m=re.match(r'\| ([IEW]-[A-Z]+-\d{3}) \| (.*?) \|$',line)
    if m:catalog[m[1]]=m[2]
assert len(catalog)==58
(BASE/'metadata/messages.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cases='\n'.join(" when code='"+k+"';text=%ucs2('"+v.replace("'","''")+"');" for k,v in catalog.items())
message='''dcl-proc StMessage export;
 dcl-pi *n varucs2(320) ccsid(1200);code char(16) const;end-pi;
 dcl-s text varucs2(320) ccsid(1200);
 select;
'''+cases+'''
 other;text=%ucs2('画面情報が無効です。画面を開き直してください。');endsl;
 return text;
end-proc;
'''
p=BASE/'src/STUCOMMON.sqlrpgle';s=p.read_text(encoding='utf8')
s=s[:s.index('dcl-proc StMessage export;')]+message
s=s.replace("result.messageId='E-COM-004';return;endif;\n exec sql SELECT COUNT(*) INTO :count FROM STUDAPP.M_CODE", "result.messageId='E-MST-001';return;endif;\n exec sql SELECT COUNT(*) INTO :count FROM STUDAPP.M_CODE")
p.write_text(s,encoding='utf8')
print('7.4 contracts: paired relationship NULL, audit derived category, authorization, 58 messages')
