"""Generate Access schema/initial masters exclusively from this project's spec.

DAO field/table properties and enforced relations are applied by Build-Access.ps1.
No DB is opened here. No other project, profile, or evaluation input is read.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SPEC = BASE / "spec"
DEST = BASE / "database"


def read(path: Path) -> str:
    if not path.resolve().is_relative_to(SPEC.resolve()):
        raise ValueError("Inputs must remain inside Access/spec")
    return path.read_text(encoding="utf-8")


def table(path: Path) -> dict:
    text = read(path)
    meta = json.loads(re.match(r"<!-- spec-meta: (.+) -->", text).group(1))
    columns = []
    for line in text.splitlines():
        if re.match(r"\| \d+ \|", line):
            c = [s.strip() for s in line.strip("|").split("|")]
            columns.append(dict(number=int(c[0]), logical=c[1], name=c[2], pk=c[3] == "〇",
                                required=c[4] == "〇", type=c[5], length=c[6], default=c[7], description=c[8]))
    return dict(name=meta["table"]["physicalName"], version=meta["version"],
                source=path.relative_to(BASE).as_posix(), sourceSha256=hashlib.sha256(text.encode()).hexdigest(), columns=columns)


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def vb(value) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    return '"' + value.replace('"', '""') + '"'


categories = dict(性別=("GENDER", 1, False), 在籍区分=("ENROLLMENT_STATUS", 2, False),
                  都道府県=("PREFECTURE", 2, False), 緊急連絡先続柄=("RELATIONSHIP", 2, True), 学年=("GRADE", 2, True))
codes = []
for line in read(SPEC / "共通/10_業務コード定義.md").splitlines():
    if re.match(r"\| (性別|在籍区分|都道府県|緊急連絡先続柄|学年)-", line):
        c = [s.strip() for s in line.strip("|").split("|")]
        cat = categories[c[1]][0]
        codes.append(dict(category=cat, value=c[2], name=c[3], order=int(c[4]),
                          protected=(c[5] == "対象" or cat == "ENROLLMENT_STATUS")))
assert len(codes) == 70 and len(categories) == 5
order = ["m_code_category", "m_code", "m_class", "m_student", "t_operation_log", "t_write_guard"]
tables = sorted([table(p) for p in (SPEC / "DB定義/Access/テーブル").glob("*.md")], key=lambda t: order.index(t["name"]))
assert len(tables) == 6 and sum(len(t["columns"]) for t in tables if t["name"] != "t_write_guard") == 89
student = next(t for t in tables if t["name"] == "m_student")
assert all(not c["required"] and not c["default"] for c in student["columns"] if c["name"] in {"relationship_category", "relationship_code"})
foreign = [
    ("m_code", "fk_code_category", "category_id", "m_code_category", "category_id"),
    ("m_class", "fk_class_grade", "grade_category,grade_code", "m_code", "category_id,code_value"),
    ("m_student", "fk_student_class", "class_id", "m_class", "class_id"),
] + [("m_student", "fk_student_" + prefix, prefix + "_category," + value, "m_code", "category_id,code_value")
     for prefix, value in [("gender", "gender_code"), ("prefecture", "prefecture_code"),
                           ("enrollment", "enrollment_status_code"), ("relationship", "relationship_code")]]
DEST.mkdir(parents=True, exist_ok=True)
for name, value in [("schema", tables), ("relations", [dict(child=o, name=n, child_columns=c.split(","), parent=t, parent_columns=r.split(",")) for o,n,c,t,r in foreign]),
                    ("seed", dict(categories=[dict(id=x[0], name=k, length=x[1], allow_add=x[2]) for k,x in categories.items()], codes=codes))]:
    (DEST / (name + ".json")).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sql = ["-- Generated exclusively from Access/spec. Apply DAO properties/relations through Build-Access.ps1."]
for t in tables:
    columns = []
    for c in t["columns"]:
        default = ""
        if c["default"] and c["default"] != "自動採番" and not c["default"].startswith("処理:"):
            default = " DEFAULT " + (c["default"] if c["default"] in {"0", "1", "True", "False"} else q(c["default"]))
        columns.append("  " + c["name"] + " " + c["type"] + (" NOT NULL" if c["required"] else "") + default)
    columns.append("  CONSTRAINT pk_" + t["name"] + " PRIMARY KEY (" + ",".join(c["name"] for c in t["columns"] if c["pk"]) + ")")
    sql.append("CREATE TABLE " + t["name"] + " (\n" + ",\n".join(columns) + "\n);")
sql += ["CREATE UNIQUE INDEX uq_student_no ON m_student(student_no);", "CREATE UNIQUE INDEX uq_class_year_code ON m_class(school_year,class_code);"]
for owner, name, columns, target, refs in foreign:
    sql.append(f"ALTER TABLE {owner} ADD CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {target}({refs});")
for name, columns in [("birth", "birth_date"), ("class_status", "is_deleted,class_id,enrollment_status_code"), ("admission", "admission_date"), ("updated", "updated_at"), ("phone", "phone_number"), ("emergency_phone", "emergency_phone_number")]:
    sql.append(f"CREATE INDEX ix_student_{name} ON m_student({columns});")
sql += ["CREATE INDEX ix_operation_target ON t_operation_log(target_table,target_key,executed_at);", "INSERT INTO t_write_guard(guard_id,lock_bit) VALUES(1,False);"]
(DEST / "schema.sql").write_text("\n\n".join(sql) + "\n", encoding="utf-8")
module = ['Attribute VB_Name = "modApprovedSeed"', 'Option Explicit', 'Option Compare Binary',
          "' Generated exclusively from this project's spec/共通/10_業務コード定義.md.",
          'Public Function ApprovedCategories() As Collection', '    Set ApprovedCategories = New Collection']
for k, x in categories.items():
    module.append("    ApprovedCategories.Add Array(" + ",".join(vb(v) for v in (x[0], k, x[1], x[2])) + ")")
module += ['End Function', 'Public Function ApprovedCodes() As Collection', '    Set ApprovedCodes = New Collection']
for c in codes:
    module.append("    ApprovedCodes.Add Array(" + ",".join(vb(c[v]) for v in ["category", "value", "name", "order", "protected"]) + ")")
module += ['End Function']
(BASE / "Modules/modApprovedSeed.bas").write_text("\n".join(module) + "\n", encoding="utf-8")
print("Access-only: 6 tables / 89 business columns / 7 enforced relations / 5 categories / 70 codes.")
