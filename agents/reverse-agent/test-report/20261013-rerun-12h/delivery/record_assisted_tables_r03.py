"""Final format-only QA for immutable assisted TABLE derivatives; never authors body."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile
from PIL import Image
from delivery_model_tables_r03 import load_bound, safe_path, sha

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
EXPECTED_RENDERER='0c87df73032d812a3e646ff2846c5daa6b3053472a52dc2b1f78d0c13d41f902'
def digest(path):return sha(safe_path(path).read_bytes())
def read(path):return json.loads(safe_path(path).read_bytes())
def fresh(path,record):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')

def runtime_record(path,expected):
    receipt_path=path
    assert digest(path)==expected
    record=read(path);directory=safe_path(record['destination'])
    actual={}
    for path in directory.rglob('*'):
        if '__pycache__' in path.parts or path.suffix in {'.pyc','.pyo'}:continue
        safe_path(path)
        if path.is_file():actual[path.relative_to(directory).as_posix()]=digest(path)
    assert actual==record['files'] and len(actual)==record['fileCount']==124
    return {'path':str(receipt_path),'receiptSha256':expected,'destination':str(directory),'verifiedFileCount':len(actual),'inventoryExact':True,'inventory':actual}

def main():
    qa_path=ROOT/'assisted-tables-r03-mechanical-qa.json';qa=copy.deepcopy(read(qa_path))
    inventory_path=ROOT/'assisted-tables-r03-native-crops/inventory.json';inventory=read(inventory_path)
    seen_path=ROOT/'assisted-tables-r03-actually-viewed.json';seen=read(seen_path)
    assert inventory['mechanicalQaSha256']==digest(qa_path) and inventory['allOriginalPixelsCovered']
    assert len(seen['actuallyViewed'])==len(inventory['images'])==105
    index={item['path']:item for item in seen['actuallyViewed']}
    assert len(index)==105 and set(index)=={item['path'] for item in inventory['images']}
    for item in inventory['images']:
        checked=index[item['path']]
        assert checked['actuallyViewed'] and checked['visualReview']=='PASS_DERIVATIVE_LAYOUT'
        assert checked['sha256']==item['sha256']==digest(item['path'])
        with Image.open(item['path']) as image:assert list(image.size)==item['dimensions']
        if item.get('sourcePng'):assert digest(item['sourcePng'])==item['sourcePngSha256']
    old=read(ROOT/'model-assisted-tables-r02.json');new=read(ROOT/'model-assisted-tables-r03.json')
    layout_delta=[]
    for before,after in zip(old['documents'],new['documents'],strict=True):
        for first,second in zip(before['sheets'],after['sheets'],strict=True):
            h1=first.pop('rowHeights');h2=second.pop('rowHeights')
            assert set(h1)==set(h2)
            headers={re.search(r'\d+',op['range']).group(0) for op in second['operations'] if op.get('style')=='table-header'}
            for row in h1:
                if h1[row]!=h2[row]:
                    assert row in headers and h1[row]==24 and h2[row]==36
                    layout_delta.append({'documentId':after['documentId'],'sheet':second['name'],'row':int(row),'beforePoints':24,'afterPoints':36})
    assert old==new and len(layout_delta)==4
    xml_delta=[];relationship_delta=[]
    for doc in qa['documents']:
        stem=Path(doc['canonicalDocumentPath']).with_suffix('.xlsx')
        old_x=ROOT/'xlsx-assisted-tables-r02/Excel'/stem;new_x=Path(doc['xlsx']['path'])
        with zipfile.ZipFile(old_x) as z1,zipfile.ZipFile(new_x) as z2:
            assert z1.read('xl/styles.xml')==z2.read('xl/styles.xml')
            assert z1.read('xl/sharedStrings.xml')==z2.read('xl/sharedStrings.xml')
            t1=ET.fromstring(z1.read('xl/worksheets/sheet1.xml'));t2=ET.fromstring(z2.read('xl/worksheets/sheet1.xml'))
            attr='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
            rels1={r.attrib['Id']:r.attrib for r in ET.fromstring(z1.read('xl/worksheets/_rels/sheet1.xml.rels'))}
            rels2={r.attrib['Id']:r.attrib for r in ET.fromstring(z2.read('xl/worksheets/_rels/sheet1.xml.rels'))}
            for part1,part2 in zip(t1.findall(f'{NS}tableParts/{NS}tablePart'),t2.findall(f'{NS}tableParts/{NS}tablePart'),strict=True):
                id1=part1.attrib[attr];id2=part2.attrib[attr];r1=rels1[id1];r2=rels2[id2]
                assert {k:v for k,v in r1.items() if k!='Id'}=={k:v for k,v in r2.items() if k!='Id'}
                assert r1['Target']=='/xl/tables/table1.xml' and r1['Type'].endswith('/table') and 'TargetMode' not in r1
                assert z1.read('xl/tables/table1.xml')==z2.read('xl/tables/table1.xml')
                relationship_delta.append({'documentId':doc['documentId'],'beforeRelationshipId':id1,'afterRelationshipId':id2,
                    'sameTarget':r1['Target'],'targetBytesExactEqual':True,'targetSha256':sha(z1.read('xl/tables/table1.xml'))})
                part1.attrib[attr]='IDENTICAL_TABLE_TARGET';part2.attrib[attr]='IDENTICAL_TABLE_TARGET'
            rows1=t1.findall(f'{NS}sheetData/{NS}row');rows2=t2.findall(f'{NS}sheetData/{NS}row')
            for r1,r2 in zip(rows1,rows2,strict=True):
                if r1.attrib.get('ht')!=r2.attrib.get('ht'):
                    assert float(r1.attrib['ht'])==24 and float(r2.attrib['ht'])==36
                    xml_delta.append({'documentId':doc['documentId'],'row':int(r2.attrib['r']),'beforePoints':24,'afterPoints':36})
                r1.attrib.pop('ht',None);r2.attrib.pop('ht',None)
            assert ET.tostring(t1)==ET.tostring(t2)
    assert {(x['documentId'],x['row']) for x in xml_delta}=={(x['documentId'],x['row']) for x in layout_delta}
    html_qa=read(ROOT/'html-assisted-tables-r02b/qa.json')
    assert all(digest(path)==expected for path,expected in html_qa['allInputHashes'].items())
    _,entries,_=load_bound(ROOT/'binding-assisted-tables-r02.json')
    runtimes={}
    for entry in entries:
        pin=read(entry['rootReviewedPin'])
        for key in ['generationRuntime','reviewRuntime','structureRuntime']:
            role=pin[key];path=role['record']
            if path not in runtimes:runtimes[path]=runtime_record(path,role['recordSha256'])
    frozen=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/runtime-code/assisted-05/src/contextbase/ai/rendering.py'
    assert digest(frozen)==EXPECTED_RENDERER
    current=REPO/'agents/reverse-agent/src/contextbase/ai/rendering.py'
    main_sha=digest(current)
    for doc in qa['documents']:
        did=doc['documentId']
        for fmt in ['html','pdf','xlsx']:
            assert digest(doc[fmt]['path'])==doc[fmt]['sha256']
            images=[item for item in seen['actuallyViewed'] if item['documentId']==did and item['format']==fmt]
            doc[fmt].update(visualReview='PASS_DERIVATIVE_LAYOUT',actuallyViewedImageCount=len(images))
        for fmt,key in [('html','crops'),('pdf','pageImages')]:
            for image in doc[fmt][key]:image.update(actuallyViewed=True,visualReview='PASS_DERIVATIVE_LAYOUT',resolution='original')
        doc['xlsx']['actuallyViewedOriginalResolutionCrops']=[item for item in seen['actuallyViewed'] if item['documentId']==did and item['format']=='xlsx']
        for preview in doc['xlsx']['previews']:
            preview.update(allPixelsActuallyViewedInCrops=True,visualReview='PASS_DERIVATIVE_LAYOUT')
        doc['pdf']['actuallyViewedPages']=list(range(1,doc['pdf']['pages']+1))
        doc['visualObservation']='All source pixel extents viewed at original resolution. No clipped header/value, overlapping rows, missing header, or unintended border observed. Narrow cells wrap long strings visually; exact cell/XML/PDF literals are checked separately.'
    assert sum(d['pdf']['pages'] for d in qa['documents'])==68
    qa.update(status='PASS_DERIVATIVE_FORMAT_CANDIDATE_ONLY',published=False,formalQualityGatePassed=False,
        formalScoring='PENDING_PARENT_DECISION',visualReview='PASS_ALL_105_ACTUALLY_VIEWED_IMAGES',
        visualReviewCompletedUtc=datetime.now(timezone.utc).isoformat(),
        mechanicalInput={'path':str(qa_path),'sha256':digest(qa_path)},
        visualInventory={'path':str(inventory_path),'sha256':digest(inventory_path),'allOriginalPixelsCovered':True},
        actuallyViewedRecord={'path':str(seen_path),'sha256':digest(seen_path)},
        actuallyViewedImages=seen['actuallyViewed'],actuallyViewedPdfPages=68,actuallyViewedXlsxCrops=19,actuallyViewedHtmlCrops=18,
        allPreparationInputPinsUnchanged=True,runtimeReceiptsAndFullInventory=list(runtimes.values()),
        layoutCorrection={'scope':'row-height only','sourceCellsMetadataWidthsBordersImagesPrintAreasEqual':True,
            'beforeModelSha256':digest(ROOT/'model-assisted-tables-r02.json'),'afterModelSha256':digest(ROOT/'model-assisted-tables-r03.json'),
            'changes':layout_delta,'actualXlsxXmlRowChanges':xml_delta,'stylesXmlAndSharedStringsExactEqual':True,
            'artifactToolGeneratedRelationshipIds':relationship_delta,
            'sheetXmlEqualExceptRowHeightsAndEquivalentTableRelationshipIds':True,
            'preservedFailedCandidate':str(ROOT/'xlsx-assisted-tables-r02'),
            'reason':'Native NOT NULL two-line header lower edge clipped at 24pt; header minimum36pt resolves it.'},
        rendererBoundary={'renderCreationRevision':'r12','renderCreationSha256':EXPECTED_RENDERER,
            'frozenSameRenderer':str(frozen),'frozenRendererSha256':digest(frozen),
            'mainRendererAtFinalReview':str(current),'mainRendererSha256AtFinalReview':main_sha,
            'mainChangedDuringTask':main_sha!=EXPECTED_RENDERER,
            'reason':'Parent changed current main wrappingWidth in r14. Existing r12 canonical HTML/PNG derivatives retained byte-identically; no new main test result is asserted for these outputs.'},
        preservedFailures=[{'path':str(ROOT/'pdf-assisted-tables-r02'),'reason':'4-row partitions overflowed actual student pages; strict audit rejected'},
            {'path':str(ROOT/'pdf-assisted-tables-r03'),'reason':'Code second-table heading shared prior page; strict page/header audit rejected'},
            {'path':str(ROOT/'assisted-tables-r02-render-worker.json'),'reason':'Post-render wrapper assumed documentCapture instead of documentPng; completed renders reused read-only in fresh QA'}],
        derivedPdfPrintLayout={'dataRowsPerPartition':2,'secondTableHeadingStartsFreshPage':True,'all68ActualPageHeadersVerified':True,
            'canonicalHtmlUntouched':True,'JS':False,'network':'abort','ownedWorkerStageTimeoutSeconds':90,
            'limitation':'Two-row conservative paging retains readable text and leaves substantial white space.'},
        remaining=['Formal rubric score and final publication remain parent-controlled.',
            'Whole-workbook live Excel display/printing not executed; native Artifact Tool previews were viewed.',
            'No original app/DB execution; linked planned documents were not published/validated by this QA.'])
    for item in qa['manifests']:assert digest(item['path'])==item['sha256']
    qa['helpers'].extend({'path':str(ROOT/name),'sha256':digest(ROOT/name)} for name in ['record_assisted_tables_r03.py','delivery_model_tables_r03.py','export_pdf_tables_r02.py','audit_assisted_tables_r03.py','prepare_table_r03_visual_inventory.py'])
    final=ROOT/'assisted-tables-r03-final-qa.json';fresh(final,qa)
    manifest={'schema':'reverse-agent-final-format-candidate-manifest/1','status':qa['status'],'published':False,'formalQualityGatePassed':False,
        'qa':str(final),'qaSha256':digest(final),'sourceSnapshotManifestSha256':qa['documents'][0]['sourceSnapshotManifestSha256'],
        'documents':[{'documentId':d['documentId'],'markdown':d['markdown'],'markdownSha256':d['markdownSha256'],
            'canonicalDocumentPath':d['canonicalDocumentPath'],'sourceMetadataExact':d['sourceMetadataExact'],
            'formats':{fmt:{'path':d[fmt]['path'],'sha256':d[fmt]['sha256'],'visualReview':d[fmt]['visualReview']} for fmt in ['html','pdf','xlsx']}} for d in qa['documents']]}
    final_manifest=ROOT/'assisted-tables-r03-final-manifest.json';fresh(final_manifest,manifest)
    lines=['# Assistedテーブル2件の派生形式QA','',
        'm_studentとm_codeの同名HTML・PDF・Excel候補を作成し、全セル・空欄・行順・書式の機械検査と全105画像の原寸レビューを完了した。正式採点と公開はrootの判断に残す。','',
        '| 原名 | 版 | PDF全頁 | 非空literal／空欄 | 原寸画像 HTML／PDF／XLSX |',
        '| --- | --- | --- | --- | --- |']
    for d in qa['documents']:lines.append(f"| {Path(d['canonicalDocumentPath']).name} | {d['sourceMetadataExact']['version']} | {d['pdf']['pages']} | {d['nonemptyLiteralCells']}／{d['blankValues']} | {d['html']['actuallyViewedImageCount']}／{d['pdf']['actuallyViewedImageCount']}／{d['xlsx']['actuallyViewedImageCount']} |")
    lines.extend(['','ExcelはArtifact Tool公開APIで著作。各原宣言の単一9列sheet、原順序の全文preamble・節見出し・表セル・空欄・キーを保持し、521非空literalと122空欄、数式0、結合・列幅・印刷範囲・枠外無罫線を独立検査した。24ptのNOT NULL見出しが下端で切れた旧候補を保存し、4見出し行の高さだけ36ptへ変更したfresh r03で解消した。変更前後のモデルは行高以外完全一致、実XLSXのstyles/sharedStringsも一致し、sheet XMLは4行の高さ以外一致した。native全4範囲を原寸19切出しで全画素実見。print metadata接続前のnative描画であり、実Excel全体表示・印刷は未実施。','',
        'PDFは同一canonical HTMLを元にJS無効・通信拒否・90秒stage timeoutで生成。元表の2データ行ごとに同一列見出し/colgroupを印刷投影へ複製し、2表目は新頁から開始する。全135本文行の値と順序、全68頁の列見出しを機械照合し、Poppler全頁を原寸実見した。切れ・行重なり・列見出し欠落は見つからなかった。安全側の2行単位のため頁内余白は多い。','',
        'HTML全キャンバスは18切出しで原画素一致・80px重複・全coverageを確認し、今回実見した。rootが現main rendererをr14へ変更したため、r12の不変を現mainに対しては主張しない。生成時renderer0c87…と同byteの凍結assisted05 rendererを基準に既存HTML/PNGのSHAを再確認し、生成・別review・構造検査runtime receipt各124ファイルの完全inventoryも再確認した。原稿・source・元spec/evalを変更せず、元アプリ/DB・開始markerを実行していない。',''])
    lines=[line.replace('実XLSXのstyles/sharedStringsも一致し、sheet XMLは4行の高さ以外一致した。','実XLSXのstyles/sharedStrings/table bytesも一致した。sheet XML差分は4行の高さとArtifact Toolが生成するtable relationship IDであり、同一targetとtarget bytesを解決照合した上で他の全XML一致を検査した。') for line in lines]
    for d in qa['documents']:
        lines.extend([f"`{Path(d['canonicalDocumentPath']).name}` — 原MD SHA256 `{d['markdownSha256']}`。",''])
        for fmt in ['html','pdf','xlsx']:lines.append(f"- [{fmt.upper()}](<{d[fmt]['path']}>) — `{d[fmt]['sha256']}`")
        lines.append('')
    lines.extend([f"[詳細QA](<{final}>) SHA256 `{digest(final)}`。",f"[候補manifest](<{final_manifest}>) SHA256 `{digest(final_manifest)}`。",''])
    report=ROOT/'ASSISTED-TABLES-DELIVERY-R03.md'
    with report.open('x',encoding='utf-8') as stream:stream.write('\n'.join(lines))
    print(json.dumps({'qa':str(final),'qaSha256':digest(final),'manifest':str(final_manifest),'manifestSha256':digest(final_manifest),'report':str(report),'reportSha256':digest(report),
        'documents':[{'id':d['documentId'],'htmlSha256':d['html']['sha256'],'pdfSha256':d['pdf']['sha256'],'xlsxSha256':d['xlsx']['sha256']} for d in qa['documents']]},ensure_ascii=False))

if __name__=='__main__':main()
