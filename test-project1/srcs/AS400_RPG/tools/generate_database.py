"""Generate the local Db2 physical schema from spec/ only.

This generator never reads spec-eval. It only emits artifacts; it opens no DB.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
PROJECT = Path(__file__).resolve().parents[1]
SPEC = PROJECT.parent.parent / 'spec' / PROJECT.name
OUT = PROJECT

def table(profile, path):
    text = path.read_text(encoding='utf-8')
    meta = json.loads(re.match('<!-- spec-meta: (.+) -->', text).group(1))
    rows = []
    for line in text.splitlines():
        if not re.match('\\| \\d+ \\|', line):
            continue
        c = [s.strip() for s in line.strip('|').split('|')]
        rows.append(dict(number=int(c[0]), logical=c[1], name=c[2], pk=c[3] == '〇', required=c[4] == '〇', type=c[5], length=c[6], default=c[7], description=c[8]))
    return dict(name=meta['table']['physicalName'], version=meta['version'], source=Path(os.path.relpath(path, PROJECT)).as_posix(), columns=rows)

def q(value):
    return "'" + str(value).replace("'", "''") + "'"
categories = dict(性別=('GENDER', 1, False), 在籍区分=('ENROLLMENT_STATUS', 2, False), 都道府県=('PREFECTURE', 2, False), 緊急連絡先続柄=('RELATIONSHIP', 2, True), 学年=('GRADE', 2, True))
codes = []
for line in (SPEC / '共通/10_業務コード定義.md').read_text(encoding='utf-8').splitlines():
    if not re.match('\\| (性別|在籍区分|都道府県|緊急連絡先続柄|学年)-', line):
        continue
    c = [s.strip() for s in line.strip('|').split('|')]
    cat = categories[c[1]][0]
    codes.append(dict(category=cat, value=c[2], name=c[3], order=int(c[4]), protected=c[5] == '対象' or cat == 'ENROLLMENT_STATUS'))
assert len(codes) == 70
foreign = [('m_code', 'fk_code_category', 'category_id', 'm_code_category', 'category_id'), ('m_class', 'fk_class_grade', 'grade_category,grade_code', 'm_code', 'category_id,code_value'), ('m_student', 'fk_student_class', 'class_id', 'm_class', 'class_id')] + [('m_student', 'fk_student_' + prefix, prefix + '_category,' + value, 'm_code', 'category_id,code_value') for prefix, value in [('gender', 'gender_code'), ('prefecture', 'prefecture_code'), ('enrollment', 'enrollment_status_code'), ('relationship', 'relationship_code')]]
checks = {'m_student': ['row_version > 0', "birth_date >= DATE('1900-01-01')", 'birth_date <= admission_date', "(enrollment_status_code IN ('01','02') AND class_id IS NOT NULL AND enrollment_end_date IS NULL) OR (enrollment_status_code IN ('03','04') AND enrollment_end_date IS NOT NULL AND enrollment_end_date >= admission_date)", 'phone_number IS NOT NULL OR email_address IS NOT NULL OR emergency_phone_number IS NOT NULL', "(emergency_contact_name IS NULL AND relationship_category IS NULL AND relationship_code IS NULL AND emergency_phone_number IS NULL) OR (emergency_contact_name IS NOT NULL AND relationship_category IS NOT NULL AND relationship_category='RELATIONSHIP' AND relationship_code IS NOT NULL AND emergency_phone_number IS NOT NULL)", '(is_deleted=0 AND deleted_at IS NULL AND deleted_by IS NULL AND delete_reason IS NULL) OR (is_deleted=1 AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL AND delete_reason IS NOT NULL)', "gender_category='GENDER'", "prefecture_category='PREFECTURE'", "enrollment_category='ENROLLMENT_STATUS'"], 'm_class': ['row_version > 0', 'school_year BETWEEN 1900 AND 9998', 'valid_from <= valid_to', "valid_from >= DATE(DIGITS(DECIMAL(school_year,4,0)) || '-04-01')", "valid_to <= DATE(DIGITS(DECIMAL(school_year+1,4,0)) || '-03-31')", 'capacity IS NULL OR capacity BETWEEN 1 AND 9999', 'display_order >= 0', "grade_category='GRADE'"], 'm_code_category': ['row_version > 0', 'code_length BETWEEN 1 AND 10'], 'm_code': ['row_version > 0', 'display_order >= 0', 'valid_to IS NULL OR valid_from <= valid_to'], 't_write_guard': ['guard_id=1', 'lock_bit IN (0,1)'], 't_operation_log': ['after_version > 0', 'before_version IS NULL OR before_version > 0', "operation_type IN ('CREATE','UPDATE','DELETE','DISABLE','ENABLE')"]}
order = ['m_code_category', 'm_code', 'm_class', 'm_student', 't_operation_log', 't_write_guard']
for profile, way in [('Db2_for_i', '')]:
    tables = [table(profile, p) for p in sorted((SPEC / 'DB定義' / profile / 'テーブル').glob('*.md'))]
    tables = sorted(tables, key=lambda t: order.index(t['name']))
    dest = OUT / way / 'database'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'schema.json').write_text(json.dumps(tables, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (dest / 'relations.json').write_text(json.dumps([dict(child=o, name=n, child_columns=c.split(','), parent=t, parent_columns=r.split(',')) for o, n, c, t, r in foreign], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (dest / 'seed.json').write_text(json.dumps(dict(categories=[dict(id=x[0], name=k, length=x[1], allow_add=x[2]) for k, x in categories.items()], codes=codes), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sql = ['-- Generated from test-project1 physical definitions; no actual database execution.']
    sql += ['CREATE SCHEMA STUDAPP;', 'SET CURRENT SCHEMA STUDAPP;']
    for t in tables:
        cols = []
        for c in t['columns']:
            typ = c['type']
            typ = re.sub('\\bCCSID(\\d+)\\b', 'CCSID \\1', typ)
            if profile == 'Db2_for_i' and c['default'] == '自動採番':
                typ += ' GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1)'
            null = ' NOT NULL' if c['required'] else ''
            default = ''
            if c['default'] and c['default'] != '自動採番' and (not c['default'].startswith('処理:')):
                default = ' DEFAULT ' + (c['default'] if c['default'] in {'0', '1', 'True', 'False'} else q(c['default']))
            cols.append('  ' + c['name'] + ' ' + typ + null + default)
        cols.append('  CONSTRAINT pk_' + t['name'] + ' PRIMARY KEY (' + ','.join((c['name'] for c in t['columns'] if c['pk'])) + ')')
        for i, expr in enumerate(checks.get(t['name'], [])):
            cols.append(f"  CONSTRAINT ck_{t['name']}_{i + 1} CHECK ({expr})")
        for c in t['columns']:
            if c['type'] == 'SMALLINT' and c['name'].startswith(('is_', 'allow_', 'duplicate_')):
                cols.append(f"  CHECK ({c['name']} IN (0,1))")
        systems = dict(m_code_category='MCAT', m_code='M_CODE', m_class='M_CLASS', m_student='M_STUDENT', t_operation_log='T_OPLOG', t_write_guard='STGUARD')
        name = t['name'] + ' FOR SYSTEM NAME ' + systems[t['name']]
        sql.append('CREATE TABLE ' + name + ' (\n' + ',\n'.join(cols) + '\n);')
    sql += ['CREATE UNIQUE INDEX uq_student_no ON m_student(student_no);', 'CREATE UNIQUE INDEX uq_class_year_code ON m_class(school_year,class_code);']
    for owner, name, columns, target, refs in foreign:
        sql.append(f'ALTER TABLE {owner} ADD CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {target}({refs});')
    for name, columns in [('birth', 'birth_date'), ('class_status', 'is_deleted,class_id,enrollment_status_code'), ('admission', 'admission_date'), ('updated', 'updated_at'), ('phone', 'phone_number'), ('emergency_phone', 'emergency_phone_number')]:
        sql.append(f'CREATE INDEX ix_student_{name} ON m_student({columns});')
    sql += ['CREATE INDEX ix_operation_target ON t_operation_log(target_table,target_key,executed_at);', 'INSERT INTO t_write_guard(guard_id,lock_bit) VALUES(1,' + ('0' if profile == 'Db2_for_i' else 'False') + ');']
    (dest / 'schema.sql').write_text('\n\n'.join(sql) + '\n', encoding='utf-8')
    seed = ['SET CURRENT SCHEMA STUDAPP;', '-- Fresh empty installation only. Reapplication must compare and reject differences.']
    for k, x in categories.items():
        seed.append('INSERT INTO m_code_category(category_id,category_name,code_length,allow_add,is_active,created_at,created_by,updated_at,updated_by,row_version) VALUES(' + ','.join([q(x[0]), q(k), str(x[1]), str(int(x[2])), '1', 'CURRENT_TIMESTAMP - CURRENT_TIMEZONE', 'CURRENT_USER', 'CURRENT_TIMESTAMP - CURRENT_TIMEZONE', 'CURRENT_USER', '1']) + ');')
    for c in codes:
        seed.append('INSERT INTO m_code(category_id,code_value,code_name,display_order,is_active,valid_from,valid_to,is_protected,created_at,created_by,updated_at,updated_by,row_version) VALUES(' + ','.join([q(c['category']), q(c['value']), q(c['name']), str(c['order']), '1', "DATE('1900-01-01')", 'NULL', str(int(c['protected'])), 'CURRENT_TIMESTAMP - CURRENT_TIMEZONE', 'CURRENT_USER', 'CURRENT_TIMESTAMP - CURRENT_TIMEZONE', 'CURRENT_USER', '1']) + ');')
    (dest / 'seed.sql').write_text('\n'.join(seed) + '\n', encoding='utf-8')
print('Generated local Db2 6-table schema, 89 business columns, 5 categories / 70 codes.')
