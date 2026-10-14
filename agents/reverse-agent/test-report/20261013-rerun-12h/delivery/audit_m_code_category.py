"""Independent literal/order/pixel proof plus observations actually made.

This is derivative-format QA for one frozen manuscript, not its formal rubric.
It authors no business prose, workbook cells, or original rendering content.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from PIL import Image, ImageChops
from pypdf import PdfReader
from delivery_model import load_bound, sha
from verify_xlsx import unzip, worksheets, values, bounds

ROOT=Path(__file__).resolve().parent
EXPECTED_MD='c43b8c5de33de810413b9b5cf306f1fd60ae4a9d054fd2be7c1a7bd6f6adab46'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'

def read(path):return json.loads(Path(path).read_bytes())
def digest(path):return sha(Path(path).read_bytes())
def normalize(value):return ''.join(value.split()).replace('\u00ad','')
def literal(node):
    node=BeautifulSoup(str(node),'html.parser')
    for linebreak in node.select('br'):
        # CommonMark serializes a hard break as <br/> plus a formatting newline.
        # Only the br is a displayed line break; remove its one serializer LF.
        following=linebreak.next_sibling
        if isinstance(following,str) and following.startswith('\n'):
            following.replace_with(following[1:])
        linebreak.replace_with('\n')
    return node.get_text()
def write(path,value):
    path=Path(path)
    if path.exists():raise FileExistsError('Fresh QA report required')
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def image_evidence(item):
    path=Path(item['path'])
    assert digest(path)==item['sha256']
    with Image.open(path) as im:dimensions=list(im.size)
    return {**item,'dimensions':dimensions,'actuallyViewed':True,'resolution':'original',
            'review':'PASS_DERIVATIVE_LAYOUT','reviewer':'delivery_tools'}

def main():
    binding=ROOT/'binding-m-code-category-r04.json'
    bound,entries,binding_info=load_bound(binding)
    assert len(entries)==1
    entry=entries[0]
    assert entry['markdownSha256']==digest(entry['markdown'])==EXPECTED_MD
    model_path=ROOT/'model-m-code-category-r05.json'
    model=read(model_path);document=model['documents'][0];sheet=document['sheets'][0]
    previous=read(ROOT/'model-m-code-category-r04.json')['documents'][0]['sheets'][0]
    assert document['rawMarkdown']==Path(entry['markdown']).read_text(encoding='utf-8')
    metadata_match=re.match(r'<!--\s*spec-meta:\s*(.*?)\s*-->',''.join(document['rawMarkdown']),re.S)
    assert metadata_match and json.loads(metadata_match[1])==document['sourceMetadata']
    assert document['sourceMetadata']['version']=='1.0'
    assert len(document['sheets'])==1 and sheet['columns']==9 and sheet['name']=='m_code_category'
    raw_html=Path(entry['renderDirectory'])/'document.html'
    soup=BeautifulSoup(raw_html.read_bytes(),'html.parser')
    html_nodes=soup.body.find_all(['h1','p','h2','table'],recursive=False)
    expected=[];tables=[];headings=[]
    for node in html_nodes:
        if node.name=='table':
            matrix=[[literal(c) for c in row.find_all(['th','td'],recursive=False)] for row in node.select('tr')]
            tables.append(matrix);expected.extend(v for row in matrix for v in row)
        else:
            expected.append(literal(node))
            if node.name=='h2':headings.append(literal(node))
    actual=[o['value'] for o in sheet['operations']]
    assert expected==actual, 'Visible HTML literal value sequence or blanks differ from cells'
    assert headings==['テーブルヘッダー','項目詳細']
    assert [len(m[0]) for m in tables]==[2,9]
    assert [r[0] for r in tables[1][1:]]==list(map(str,range(1,12)))
    assert tables[1][0]==document['sourceMetadata']['columns']
    restored=[o for o in sheet['operations'] if o['style']!='heading']
    assert [(o['value'],o['style'],o['sourceLines']) for o in previous['operations']]==[(o['value'],o['style'],o['sourceLines']) for o in restored]
    moved=[{'originalRange':a['range'],'candidateRange':b['range'],'valueSha256':sha(b['value'].encode('utf-8')),
            'sourceLines':b['sourceLines']} for a,b in zip(previous['operations'],restored,strict=True) if a['range']!=b['range']]

    xmanifest_path=ROOT/'xlsx-m-code-category-r05/delivery-manifest.json'
    xmanifest=read(xmanifest_path);xdoc=xmanifest['documents'][0]
    assert xmanifest['modelSha256']==digest(model_path)
    assert digest(xdoc['xlsx'])==xdoc['xlsxSha256']
    assert xdoc['independentCellVerification']=='PASS'
    members=unzip(Path(xdoc['xlsx']).read_bytes());_,xml_sheets=worksheets(members)
    assert len(xml_sheets)==1 and xml_sheets[0][0]==sheet['name']
    cells=values(xml_sheets[0][2],members)
    assert cells=={o['range'].split(':')[0]:o['value'] for o in sheet['operations'] if o['value']}
    assert len(cells)==142 and xdoc['readbackChecks']['formulaCount']==0
    cols=xml_sheets[0][2].findall(f'{{{NS}}}cols/{{{NS}}}col')
    widths=[]
    for index in range(1,10):
        matches=[c for c in cols if int(c.get('min'))<=index<=int(c.get('max'))]
        assert len(matches)==1
        widths.append(float(matches[0].get('width')))
    assert widths==sheet['columnWidths']
    ximages=[image_evidence(p) for p in xdoc['previews']]
    assert len(ximages)==5
    spans=[bounds(p['range']) for p in xdoc['previews']]
    assert spans[0][1]==1 and spans[-1][3]==sheet['lastRow']==47
    assert all(a[3]+1==b[1] for a,b in zip(spans,spans[1:]))
    assert all(a[0]==1 and a[2]==9 for a in spans)

    pmanifest_path=ROOT/'pdf-m-code-category-r05/delivery-manifest.json'
    pmanifest=read(pmanifest_path);pdoc=pmanifest['documents'][0]
    assert pdoc['htmlSha256']==digest(pdoc['html'])==digest(raw_html)
    assert pdoc['pdfSha256']==digest(pdoc['pdf']) and pdoc['textCoverage']=='PASS'
    assert pdoc['checkedVisibleStrings']==142
    reader=PdfReader(pdoc['pdf']);page_text=[normalize(p.extract_text() or '') for p in reader.pages]
    assert len(page_text)==pdoc['pages']==10
    for page in page_text[:7]:assert all(normalize(h) in page for h in tables[0][0])
    for page in page_text[7:]:assert all(normalize(h) in page for h in tables[1][0])
    pdf_text=''.join(page_text);position=0
    for matrix in tables:
        for row in matrix[1:]:
            value=normalize(''.join(row));found=pdf_text.find(value,position)
            assert found>=0, 'Actual PDF body-row text missing or out of order'
            position=found+len(value)
    pimages=[image_evidence(p) for p in pdoc['pageImages']]
    assert len(pimages)==10
    partitions=pdoc['tablePartitions']
    assert len(partitions)==2
    for matrix,record in zip(tables,partitions,strict=True):
        assert record['bodyRowOrderAndHtmlEqual'] and record['bodyRows']==len(matrix)-1
        assert record['parts'][0]['firstOriginalBodyRow']==1
        assert record['parts'][-1]['lastOriginalBodyRow']==len(matrix)-1
        assert all(p['headerDuplicatedExactly'] and p['columnDefinitionEqual'] for p in record['parts'])
        assert all(a['lastOriginalBodyRow']+1==b['firstOriginalBodyRow'] for a,b in zip(record['parts'],record['parts'][1:]))

    html_qa_path=ROOT/'html-m-code-category-r04/qa.before-visual-review.json';html_qa=read(html_qa_path)
    original_png=Path(entry['renderDirectory'])/'document.png'
    crops=[]
    with Image.open(original_png) as original:
        end=0
        for item in html_qa['crops']:
            assert digest(original_png)==item['sourcePngSha256']
            with Image.open(item['path']) as tile:
                assert ImageChops.difference(original.crop(tuple(item['sourceRectangle'])),tile).getbbox() is None
            left,top,right,bottom=item['sourceRectangle'];assert left==0 and right==original.width and top<=end
            end=max(end,bottom);crops.append(image_evidence(item))
        assert end==original.height
        dimensions=list(original.size)
    assert len(crops)==5

    excel_path=ROOT/'excel-literal-application-r01/result.json';excel=read(excel_path)
    assert excel['status']=='PASS_LITERAL_VALUE_AND_DISPLAY' and excel['text']==excel['value2']=='1.0'
    assert excel['readOnly'] and not excel['saved'] and excel['workbookBytesUnchanged']
    assert excel['beforeSha256']==excel['afterSha256']==digest(excel['workbook'])
    assert not excel['baselineExcelProcessIds'] and excel['macrosDisabled'] and excel['updateLinks']==0

    record={'schema':'reverse-agent-table-delivery-qa/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS_DERIVATIVE_FORMAT_CANDIDATE_ONLY','published':False,'formalQualityGatePassed':False,
        'formalScoring':'PENDING_ROOT_PROCESS','bodyReview':'ROOT_REPORTED_INDEPENDENTLY_APPROVED',
        'documentId':entry['documentId'],'canonicalDocumentPath':entry['canonicalDocumentPath'],
        'markdownSha256':EXPECTED_MD,'bindingSha256':binding_info['bindingSha256'],
        'sourceSnapshotManifestSha256':bound['sourceSnapshotManifestSha256'],
        'originalMarkdownBytesUnchanged':True,'sourceApplicationExecuted':False,'specAndSpecEvalRead':False,
        'rendererR10':{'qa':str(html_qa_path),'qaInputSha256':digest(html_qa_path),
             'visibleTextSequenceUnchanged':html_qa['fullVisibleTextSequenceEqual'],
             'tableCellSequenceUnchanged':html_qa['tableCellValuesAndOrderEqual'],
             'coreSha256':html_qa['rendererCoreSha256'],'originalPngDimensions':dimensions,
             'cropPixelEquality':True,'cropFullCanvasCoverage':True,'actuallyViewedCrops':crops},
        'losslessProjection':{'sourceHtmlToCellLiteralAndBlankSequenceEqual':True,'orderedValuesIncludingBlanks':len(actual),
             'nonemptyLiteralCells':142,'sourceMetadataExact':document['sourceMetadata'],
             'originalTitlePreambleAndSectionHeadingsPresentInOrder':True,'itemKeys':list(map(str,range(1,12))),
             'headerRecords':len(tables[0])-1,'detailRecords':len(tables[1])-1,
             'allCellCoordinatesReadbackEqual':True,'sheetCount':1,'declaredSheetName':sheet['name'],
             'columns':9,'xmlColumnWidthsEqualModel':widths,'printArea':sheet['printArea'],
             'preambleRange':'A3:I3','sectionHeadingRanges':[o['range'] for o in sheet['operations'] if o['style']=='heading'],
             'r04PriorCandidateLostSectionHeadings':True,'r05AddedOriginalHeadingsOnly':headings,
             'allOtherPriorCellStringsStylesAndProvenanceEqual':True,'coordinateMoves':moved},
        'html':{'path':pdoc['html'],'sha256':pdoc['htmlSha256'],'sameCanonicalRenderBytes':True},
        'pdf':{'path':pdoc['pdf'],'sha256':pdoc['pdfSha256'],'pages':10,'checkedVisibleStrings':142,
             'allActualPdfBodyRowsPresentInOriginalOrder':True,'allTenPagesHaveFullTableColumnHeaders':True,
             'tablePartitionRows':4,'tablePartitions':partitions,'printProjectionSha256':pdoc['printProjectionSha256'],
             'safeExecution':{'javascriptEnabled':False,'networkRequestsAborted':True,'originalApplicationExecuted':False},
             'actuallyViewedPages':list(range(1,11)),'visualReview':'PASS_DERIVATIVE_LAYOUT','pageImages':pimages,
             'r04PriorCandidateVisualReview':'FAIL_REPEATED_TABLE_HEADER_CLIPPED'},
        'xlsx':{'path':xdoc['xlsx'],'sha256':xdoc['xlsxSha256'],'author':'@oai/artifact-tool',
             'authoringMarkerReexecuted':False,'independentReadbackChecks':xdoc['readbackChecks'],
             'printMetadataConnection':xdoc['printMetadataConnection'],'actuallyViewedTiles':5,'previewRangesComplete':True,
             'visualReview':'PASS_NATIVE_DERIVATIVE_LAYOUT','previews':ximages,
             'nativePreviewsGeneratedBeforePrintMetadataConnection':True,
             'actualExcelPrintOrCompleteWorkbookDisplayQa':'NOT_EXECUTED'},
        'searchBasicLiteralFollowup':{'evidence':str(excel_path),'evidenceSha256':digest(excel_path),
             'cell':excel['cell'],'actualExcelValue2':excel['value2'],'value2Type':excel['value2Type'],
             'actualExcelText':excel['text'],'numberFormat':excel['numberFormat'],
             'excelVersion':excel['excelVersion'],'excelBuild':excel['excelBuild'],
             'workbookSha256Unchanged':excel['afterSha256'],'ownedExcelProcessId':excel['ownedExcelProcessId'],
             'ownedProcessAbsentAfterExitConfirmed':True,
             'scope':'ONE_READ_ONLY_CELL_ONLY; native Artifact preview discrepancy remains renderer-specific',
             'wholeWorkbookDisplayAndPrintQa':'NOT_EXECUTED'},
        'tests':{'path':str(ROOT/'tests-table-delivery-r05-fixed.raw.log'),
             'sha256':digest(ROOT/'tests-table-delivery-r05-fixed.raw.log'),'passed':20,
             'scope':'connection/literal/XML/table-preamble/table-partition; not formal business specification score'},
        'helpers':[{'path':str(ROOT/name),'sha256':digest(ROOT/name)} for name in
             ['delivery_model.py','build_xlsx.mjs','verify_xlsx.py','export_pdf.py','audit_m_code_category.py',
              'excel_literal_readonly.ps1','run_excel_literal_readonly.py']],
        'remaining':['Formal rubric scoring and final publication are parent-controlled.',
             'Links to referenced planned documents were preserved literally; target publication completeness not assessed.',
             'No live application/DB tests or actual Excel printing were performed.']}
    out=ROOT/'m-code-category-delivery-r05-qa.json';write(out,record)
    print(json.dumps({'report':str(out),'sha256':digest(out),'status':record['status'],
                     'pdfPagesActuallyViewed':10,'xlsxTilesActuallyViewed':5,'literalCells':142},ensure_ascii=False))

if __name__=='__main__':main()
