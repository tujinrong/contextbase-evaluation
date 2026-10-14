"""Independent visible literals/order/blank/pagination audit, never writes prose."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from PIL import Image, ImageChops
from pypdf import PdfReader
from delivery_model import load_bound, document_model, sha
from verify_xlsx import unzip, worksheets, values, bounds

ROOT=Path(__file__).resolve().parent
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
def read(path):return json.loads(Path(path).read_bytes())
def digest(path):return sha(Path(path).read_bytes())
def normalize(value):return ''.join(value.split()).replace('\u00ad','')
def literal(node):
    node=BeautifulSoup(str(node),'html.parser')
    for br in node.select('br'):
        following=br.next_sibling
        if isinstance(following,str) and following.startswith('\n'):following.replace_with(following[1:])
        br.replace_with('\n')
    return node.get_text()
def image_record(item):
    assert digest(item['path'])==item['sha256']
    with Image.open(item['path']) as im:dimensions=list(im.size)
    return {**item,'dimensions':dimensions,'actuallyViewed':False,'visualReview':'PENDING'}

def main():
    output=ROOT/'assisted-tables-r02-mechanical-qa.json'
    if output.exists():raise FileExistsError('Fresh audit required')
    binding=ROOT/'binding-assisted-tables-r02.json';bound,entries,provenance=load_bound(binding)
    model_path=ROOT/'model-assisted-tables-r02.json';model=read(model_path)
    assert model['referenceMode']==bound['referenceMode']=='training-assisted' and len(entries)==2
    xmanifest_path=ROOT/'xlsx-assisted-tables-r02/delivery-manifest.json';pmanifest_path=ROOT/'pdf-assisted-tables-r02/delivery-manifest.json'
    xmanifest,pmanifest=read(xmanifest_path),read(pmanifest_path);html_qa=read(ROOT/'html-assisted-tables-r02b/qa.json')
    assert xmanifest['modelSha256']==digest(model_path) and xmanifest['bindingSha256']==provenance['bindingSha256']
    outputs=[]
    for entry,document,hdoc in zip(entries,model['documents'],html_qa['documents'],strict=True):
        assert document==document_model(entry,model['projection']['imageMaxWidth'],model['projection']['previewMaxHeight'])
        assert digest(entry['draftResult'])==entry['draftResultSha256']
        approval=entry['separateApprovedReview']
        assert digest(approval['handoff'])==approval['handoffSha256'] and digest(approval['review'])==approval['reviewSha256']
        sheet=document['sheets'][0];assert len(document['sheets'])==1 and sheet['role']=='table' and sheet['columns']==9
        assert document['sourceMetadata']['layout']=='TABLE' and document['sourceMetadata']['schema']=='spec-md/1.1'
        assert sheet['name']==document['sourceMetadata']['sheets'][0]['sheet']
        original_meta=re.match(r'<!--\s*spec-meta:\s*(.*?)\s*-->',Path(entry['markdown']).read_text(encoding='utf-8'),re.S)
        assert original_meta and document['sourceMetadata']==json.loads(original_meta[1])
        soup=BeautifulSoup(Path(entry['canonicalHtml']).read_bytes(),'html.parser');expected=[];tables=[];headings=[]
        for node in soup.body.find_all(['h1','p','h2','table'],recursive=False):
            if node.name=='table':
                matrix=[[literal(cell) for cell in row.find_all(['th','td'],recursive=False)] for row in node.select('tr')]
                tables.append(matrix);expected.extend(value for row in matrix for value in row)
            else:
                expected.append(literal(node))
                if node.name=='h2':headings.append(literal(node))
        actual=[op['value'] for op in sheet['operations']]
        assert actual==expected, 'HTML visible literal or blank order differs from model'
        assert headings==['テーブルヘッダー','項目詳細'] and [len(t[0]) for t in tables]==[2,9]
        assert tables[1][0]==document['sourceMetadata']['columns']
        keys=[row[0] for row in tables[1][1:]];assert keys==list(map(str,range(1,len(keys)+1)))
        expected_count=len(tables[1])-1
        assert len(keys)==expected_count
        xdoc=next(d for d in xmanifest['documents'] if d['documentId']==entry['documentId'])
        pdoc=next(d for d in pmanifest['documents'] if d['documentId']==entry['documentId'])
        assert digest(xdoc['xlsx'])==xdoc['xlsxSha256'] and xdoc['independentCellVerification']=='PASS'
        members=unzip(Path(xdoc['xlsx']).read_bytes());_,xmls=worksheets(members)
        assert len(xmls)==1 and xmls[0][0]==sheet['name']
        cells=values(xmls[0][2],members);assert cells=={op['range'].split(':')[0]:op['value'] for op in sheet['operations'] if op['value']}
        assert xdoc['readbackChecks']['formulaCount']==0
        widths=[]
        for i in range(1,10):
            matches=[c for c in xmls[0][2].findall(f'{{{NS}}}cols/{{{NS}}}col') if int(c.get('min'))<=i<=int(c.get('max'))]
            assert len(matches)==1;widths.append(float(matches[0].get('width')))
        assert widths==sheet['columnWidths']
        span=[bounds(p['range']) for p in xdoc['previews']]
        assert span[0][1]==1 and span[-1][3]==sheet['lastRow'] and all(a[3]+1==b[1] for a,b in zip(span,span[1:]))
        assert all(a[0]==1 and a[2]==9 for a in span)
        assert pdoc['htmlSha256']==digest(pdoc['html'])==digest(entry['canonicalHtml'])
        assert pdoc['pdfSha256']==digest(pdoc['pdf']) and pdoc['textCoverage']=='PASS'
        pdf=PdfReader(pdoc['pdf']);text=[normalize(p.extract_text() or '') for p in pdf.pages]
        partitions=pdoc['tablePartitions'];assert len(partitions)==len(tables)==2
        assert len(pdf.pages)==pdoc['pages']==sum(len(p['parts']) for p in partitions), 'Unexpected extra/blank/overflow print page'
        page_index=0;headers=[]
        for matrix,partition in zip(tables,partitions,strict=True):
            assert partition['bodyRowOrderAndHtmlEqual'] and partition['bodyRows']==len(matrix)-1
            assert partition['parts'][0]['firstOriginalBodyRow']==1 and partition['parts'][-1]['lastOriginalBodyRow']==len(matrix)-1
            assert all(p['headerDuplicatedExactly'] and p['columnDefinitionEqual'] for p in partition['parts'])
            assert all(a['lastOriginalBodyRow']+1==b['firstOriginalBodyRow'] for a,b in zip(partition['parts'],partition['parts'][1:]))
            for part in partition['parts']:
                present=[normalize(h) in text[page_index] for h in matrix[0]]
                assert all(present), 'PDF actual page omits a repeated column header'
                headers.append({'page':page_index+1,'originalTable':partition['originalTable'],'headers':matrix[0],'allPresent':True});page_index+=1
        joined=''.join(text);position=0
        for matrix in tables:
            for row in matrix[1:]:
                value=normalize(''.join(row));found=joined.find(value,position)
                assert found>=0, 'PDF body-row missing or out of order';position=found+len(value)
        all_source_values=[v for v in expected if normalize(v)]
        assert all(normalize(v) in joined for v in all_source_values)
        png=Path(entry['renderDirectory'])/'document.png';crops=[]
        with Image.open(png) as original:
            end=0
            for tile in hdoc['crops']:
                assert digest(png)==tile['sourcePngSha256']
                with Image.open(tile['path']) as cropped:assert ImageChops.difference(original.crop(tuple(tile['sourceRectangle'])),cropped).getbbox() is None
                left,top,right,bottom=tile['sourceRectangle'];assert left==0 and right==original.width and top<=end;end=max(end,bottom)
                crops.append(image_record(tile))
            assert end==original.height
        outputs.append({'documentId':entry['documentId'],'canonicalDocumentPath':entry['canonicalDocumentPath'],'markdown':entry['markdown'],'markdownSha256':entry['markdownSha256'],
            'referenceMode':'training-assisted','sourceSnapshotManifestSha256':bound['sourceSnapshotManifestSha256'],
            'draftResult':entry['draftResult'],'draftResultSha256':entry['draftResultSha256'],'approvalBinding':approval,
            'sourceMetadataExact':document['sourceMetadata'],'sourceHtmlToCellLiteralAndBlankSequenceEqual':True,
            'orderedValuesIncludingBlanks':len(actual),'blankValues':actual.count(''),'nonemptyLiteralCells':len(cells),
            'sourceItemKeys':keys,'sourceHeaderRecords':len(tables[0])-1,'sourceDetailRecords':len(tables[1])-1,
            'titlePreambleAndSectionHeadingsInOriginalOrder':True,'oneDeclared9ColumnSheet':sheet['name'],'xmlWidths':widths,'printArea':sheet['printArea'],
            'html':{'path':pdoc['html'],'sha256':pdoc['htmlSha256'],'immutableCanonicalBytes':True,'fullCanvasPixelCoverage':True,'crops':crops,'visualReview':'PENDING'},
            'pdf':{'path':pdoc['pdf'],'sha256':pdoc['pdfSha256'],'pages':pdoc['pages'],'checkedVisibleStrings':pdoc['checkedVisibleStrings'],
                'allActualPdfRowsInSourceOrder':True,'allSourceVisibleLiteralsPresent':True,'everyPageColumnHeaders':headers,'tablePartitions':partitions,
                'safeBrowser':{'javascriptEnabled':False,'networkRequestsAborted':True,'applicationExecuted':False},
                'pageImages':[image_record(p) for p in pdoc['pageImages']],'visualReview':'PENDING'},
            'xlsx':{'path':xdoc['xlsx'],'sha256':xdoc['xlsxSha256'],'author':'@oai/artifact-tool','markerReexecuted':False,'readbackChecks':xdoc['readbackChecks'],
                'printMetadataConnection':xdoc['printMetadataConnection'],'previews':[image_record(p) for p in xdoc['previews']],
                'previewRangesCoverAllRowsAnd9Columns':True,'nativePreviewsBeforePrintMetadataConnection':True,'liveExcelDisplayOrPrintQa':'NOT_EXECUTED','visualReview':'PENDING'}})
    load_bound(binding)
    report={'schema':'reverse-agent-assisted-table-delivery-qa/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'MECHANICALLY_VERIFIED_NATIVE_VISUAL_REVIEW_PENDING','published':False,'formalQualityGatePassed':False,'formalScoring':'PENDING_ROOT_PROCESS',
        'binding':str(binding),'bindingSha256':digest(binding),'model':str(model_path),'modelSha256':digest(model_path),'documents':outputs,
        'rendererPreparation':{'qa':str(ROOT/'html-assisted-tables-r02b/qa.json'),'sha256':digest(ROOT/'html-assisted-tables-r02b/qa.json'),
            'rootReportedRevision':'r12','coreSha256AtPreparation':html_qa['rendererCoreAtPreparationSha256']},
        'inputsAndReceiptsUnchanged':True,'specOrSpecEvalRead':False,'applicationOrDbExecuted':False,'bodyAuthoredByThisHelper':False,
        'helpers':[{'path':str(ROOT/n),'sha256':digest(ROOT/n)} for n in ['recover_assisted_tables_r02.py','delivery_model.py','build_xlsx.mjs','verify_xlsx.py','export_pdf.py','audit_assisted_tables.py']],
        'manifests':[{'path':str(p),'sha256':digest(p)} for p in [xmanifest_path,pmanifest_path]],
        'remaining':['Native all-image visual review pending; current report is mechanical only.',
            'Formal quality scoring/publication remain parent-controlled.',
            'No original application/DB or whole-workbook live Excel printing was performed.']}
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(output),'sha256':digest(output),'documents':[{k:d[k] for k in ['documentId','orderedValuesIncludingBlanks','nonemptyLiteralCells','sourceHeaderRecords','sourceDetailRecords']} for d in outputs]},ensure_ascii=False))

if __name__=='__main__':main()
