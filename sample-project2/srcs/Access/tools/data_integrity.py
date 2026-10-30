"""Read-only canonical schema and typed-row fingerprints; never log row values.

Used to prove that replacing Forms/VBA preserved an existing ACCDB, separately
from fresh DEMO initialization.  Call only on an owned copy of the input file.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse, datetime, decimal, gc, hashlib, json, os, site
ROOT=Path(__file__).resolve().parents[1]
DEPS=ROOT/'.tmp/python-deps'
if DEPS.is_dir():
    site.addsitedir(str(DEPS))
    if (DEPS/'pywin32_system32').is_dir(): os.add_dll_directory(str(DEPS/'pywin32_system32'))
import pythoncom, win32com.client
TABLES=('m_app_user','m_employee','t_career','m_code_category','m_code')
def canonical(value):
    if value is None: return ['Null']
    if isinstance(value,bool): return ['Boolean',value]
    if isinstance(value,datetime.datetime): return ['DateTime',value.isoformat(timespec='microseconds')]
    if isinstance(value,datetime.date): return ['Date',value.isoformat()]
    if isinstance(value,decimal.Decimal): return ['Decimal',str(value)]
    if isinstance(value,bytes): return ['Binary',value.hex()]
    if isinstance(value,str): return ['String',value]
    if isinstance(value,int): return ['Integer',str(value)]
    if isinstance(value,float): return ['Float',value.hex()]
    raise TypeError('Unrecognized DAO variant type: '+type(value).__name__)
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf-8')).hexdigest()
def optional_prop(obj,name):
    try: return canonical(obj.Properties(name).Value)
    except pythoncom.com_error: return ['PropertyAbsent']
def snapshot(path):
    path=Path(path).resolve()
    if '.tmp' not in path.parts: raise ValueError('Read fingerprints from an owned .tmp copy only')
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    engine=db=table=rs=field=index=relation=None
    pythoncom.CoInitialize()
    try:
        engine=win32com.client.DispatchEx('DAO.DBEngine.120')
        db=engine.OpenDatabase(str(path),False,True)
        tables=[]; schemas=[]
        actual=sorted(t.Name for t in db.TableDefs if not t.Name.startswith(('MSys','~')))
        if actual!=sorted(TABLES): raise RuntimeError('Unexpected business table inventory: '+repr(actual))
        for name in TABLES:
            table=db.TableDefs(name)
            fields=[]
            for field in table.Fields:
                fields.append({'name':field.Name,'type':field.Type,'size':field.Size,'attributes':field.Attributes,'required':bool(field.Required),'allowZeroLength':bool(field.AllowZeroLength) if field.Type in (10,12) else 'NOT_TEXT','default':optional_prop(field,'DefaultValue'),'validationRule':optional_prop(field,'ValidationRule')})
            indices=[]
            for index in table.Indexes:
                indices.append({'name':index.Name,'primary':bool(index.Primary),'unique':bool(index.Unique),'required':bool(index.Required),'ignoreNulls':bool(index.IgnoreNulls),'fields':[(f.Name,f.Attributes) for f in index.Fields]})
            schema={'table':name,'fields':fields,'indexes':sorted(indices,key=lambda i:i['name'])}
            schemas.append(schema)
            rs=db.OpenRecordset('SELECT * FROM ['+name+']',4)
            rows=[]
            while not rs.EOF:
                rows.append([canonical(rs.Fields(i).Value) for i in range(rs.Fields.Count)])
                rs.MoveNext()
            rs.Close();rs=None
            rows.sort(key=lambda row:json.dumps(row,ensure_ascii=False,separators=(',',':')))
            tables.append({'table':name,'rowCount':len(rows),'columnCount':len(fields),'typedRowsSha256':digest({'fields':[(f['name'],f['type']) for f in fields],'rows':rows}),'schemaSha256':digest(schema)})
            rows.clear();table=None
        relations=[]
        for relation in db.Relations:
            if relation.Table in TABLES or relation.ForeignTable in TABLES:
                relations.append({'name':relation.Name,'table':relation.Table,'foreignTable':relation.ForeignTable,'attributes':relation.Attributes,'fields':[(f.Name,f.ForeignName) for f in relation.Fields]})
        relations.sort(key=lambda x:x['name'])
        schema_sha=digest({'tables':schemas,'relations':relations})
        db.Close();db=None
        return {'schemaVersion':1,'databaseFileSha256':before,'tables':tables,'schemaFingerprint':schema_sha,'businessDigest':digest(tables),'allFieldsIncludingCredentialsIdsRevisions':True,'rowValuesLogged':False,'mode':'DAO read-only on owned copy','sourceUnmodified':before==hashlib.sha256(path.read_bytes()).hexdigest()}
    finally:
        if rs is not None: rs.Close()
        if db is not None: db.Close()
        rs=field=index=relation=table=db=engine=None
        gc.collect();pythoncom.CoFreeUnusedLibraries();pythoncom.CoUninitialize()
def main():
    p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    data=snapshot(a.database);out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'counts':{t['table']:t['rowCount'] for t in data['tables']},'schemaFingerprint':data['schemaFingerprint'],'businessDigest':data['businessDigest'],'sourceUnmodified':data['sourceUnmodified']}))
if __name__=='__main__':main()
