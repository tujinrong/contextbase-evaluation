"""Read-only OOXML delta proof. Only one width and export-generated IDs differ."""
from pathlib import Path
import argparse,hashlib,json,posixpath,zipfile,uuid,xml.etree.ElementTree as E
from delivery_model_r18 import safe_path
def sha(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def load(p):return json.loads(safe_path(p).read_text(encoding='utf8'))
def members(p):
    with zipfile.ZipFile(safe_path(p)) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        return {n:z.read(n) for n in z.namelist()}
def main():
    parser=argparse.ArgumentParser()
    for arg in ['old','new','output','plan']:parser.add_argument('--'+arg,type=Path,required=True)
    for arg in ['sheet-index','column-index']:parser.add_argument('--'+arg,type=int,required=True)
    parser.add_argument('--delta',type=float,required=True)
    args=parser.parse_args();oldm=load(args.old);newm=load(args.new)
    assert len(oldm['documents'])==len(newm['documents'])==1
    old=oldm['documents'][0];new=newm['documents'][0]
    assert old['documentId']==new['documentId'] and old['markdownSha256']==new['markdownSha256']
    assert old['writtenCells']==new['writtenCells'] and old['requestedPrintAreas']==new['requestedPrintAreas']
    assert [(x['sheet'],x['range']) for x in old['previews']]==[(x['sheet'],x['range']) for x in new['previews']]
    assert new['independentCellVerification']==old['independentCellVerification']=='PASS'
    assert sha(old['xlsx'])==old['xlsxSha256'] and sha(new['xlsx'])==new['xlsxSha256']
    a=members(old['xlsx']);b=members(new['xlsx']);assert set(a)==set(b)
    S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}';R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    maps={};relations=[]
    for name in sorted(a):
        if not name.endswith('.rels'):continue
        x=E.fromstring(a[name]);y=E.fromstring(b[name])
        key=lambda n:tuple(sorted((k,v) for k,v in n.attrib.items() if k!='Id'))
        xa={key(n):n.attrib['Id'] for n in x};ya={key(n):n.attrib['Id'] for n in y}
        assert len(xa)==len(x) and len(ya)==len(y) and xa.keys()==ya.keys()
        mapping={ya[k]:xa[k] for k in xa};maps[name]=mapping
        relations.append({'part':name,'targetsAndTypesUnchanged':True,'exportIdMapping':mapping})
    relpart=lambda name:posixpath.join(posixpath.dirname(name),'_rels',posixpath.basename(name)+'.rels')
    target=f'xl/worksheets/sheet{args.sheet_index}.xml';changes=[];objects=[];widthproof=False
    for name in sorted(a):
        if a[name]==b[name]:continue
        assert name.endswith(('.xml','.rels')),'Binary/image bytes changed: '+name
        x=E.fromstring(a[name]);y=E.fromstring(b[name]);mapping=maps.get(name if name.endswith('.rels') else relpart(name),{})
        for n in y.iter():
            for k,v in list(n.attrib.items()):
                if (name.endswith('.rels') and k=='Id') or (k.startswith(R) and k.rsplit('}',1)[-1] in {'id','embed','link'}):
                    assert v in mapping;n.set(k,mapping[v])
        if name.startswith('xl/drawings/') and not name.endswith('.rels'):
            xx=list(x.iter());yy=list(y.iter());assert len(xx)==len(yy)
            for xn,yn in zip(xx,yy):
                if xn.tag=='{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}cNvPr':
                    assert {k:v for k,v in xn.attrib.items() if k!='name'}=={k:v for k,v in yn.attrib.items() if k!='name'}
                    uuid.UUID(xn.attrib['name']);uuid.UUID(yn.attrib['name'])
                    objects.append({'part':name,'id':xn.attrib['id'],'before':xn.attrib['name'],'after':yn.attrib['name']})
                    yn.set('name',xn.attrib['name'])
        if name==target:
            xc=x.find(S+'cols');yc=y.find(S+'cols');assert xc is not None and yc is not None
            xo=[dict(c.attrib) for c in xc];yo=[dict(c.attrib) for c in yc];assert len(xo)==len(yo)
            diffs=[]
            for v,w in zip(xo,yo):
                if v==w:continue
                assert v['min']==w['min']==str(args.column_index) and v['max']==w['max']==str(args.column_index)
                assert {k:z for k,z in v.items() if k!='width'}=={k:z for k,z in w.items() if k!='width'}
                assert float(w['width'])-float(v['width'])==args.delta
                diffs.append({'columnIndexOneBased':args.column_index,'before':v,'after':w})
            assert len(diffs)==1
            x.remove(xc);y.remove(yc);assert E.tostring(x)==E.tostring(y),'Non-width worksheet change'
            changes.append({'part':name,'scope':'COLUMN_WIDTH_ONLY','differences':diffs});widthproof=True
        else:
            assert E.tostring(x)==E.tostring(y),'Other semantic XML change: '+name
            changes.append({'part':name,'scope':'ONLY_EXPORT_RELATIONSHIP_IDS_OR_XML_SERIALIZATION'})
    assert widthproof
    out=safe_path(args.output);pp=safe_path(args.plan);assert not out.exists() and not pp.exists()
    plan={'workbook':new['xlsx'],'workbookSha256':new['xlsxSha256'],'manifest':str(args.new),'manifestSha256':sha(args.new),
        'sheets':[r['sheet'] for r in new['requestedPrintAreas']],
        'cells':[{k:c[k] for k in ('sheet','cell','value')} for c in new['writtenCells']],
        'previews':[{k:p[k] for k in ('sheet','range')} for p in new['previews']],
        'documentId':new['documentId'],'canonicalDocumentPath':new['canonicalDocumentPath'],'markdownSha256':new['markdownSha256'],
        'readOnly':True,'save':False,'originalApplicationExecuted':False}
    pp.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    record={'scope':'ONE_GRID_COLUMN_WIDTH_ONLY_DERIVED_XLSX_READBACK','sourceXlsx':old['xlsx'],'sourceXlsxSha256':old['xlsxSha256'],
        'candidateXlsx':new['xlsx'],'candidateXlsxSha256':new['xlsxSha256'],'changes':changes,'relationshipComparison':relations,
        'generatedDrawingUuidNames':objects,'allLiteralsBlanksRowsMergeStylesTablesImagesOrderUnchanged':True,'formulaCount':0,
        'previewRangeOrderUnchanged':True,'plan':str(pp),'planSha256':sha(pp),'actualFullRangeReview':'PENDING','oldHoldsPreserved':True,'published':False}
    out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'delta':str(out),'deltaSha256':sha(out),'plan':str(pp),'planSha256':sha(pp),'xlsxSha256':new['xlsxSha256']},ensure_ascii=False))
if __name__=='__main__':main()
