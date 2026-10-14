"""Record the 45 images actually inspected; keep mechanical evidence immutable."""
from __future__ import annotations
from datetime import datetime, timezone
import copy
import json
from pathlib import Path
from PIL import Image
from delivery_model import load_bound, sha

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
def digest(path):return sha(Path(path).read_bytes())
def read(path):return json.loads(Path(path).read_bytes())
def fresh(path,record):
    if path.exists():raise FileExistsError('Fresh visual record required')
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    original=ROOT/'assisted-tables-r01-mechanical-qa.json';record=copy.deepcopy(read(original));seen=[]
    expected_counts={'03_m_code_category':{'html':4,'pdf':10,'xlsx':4},'02_m_class':{'html':6,'pdf':15,'xlsx':6}}
    for doc in record['documents']:
        stem=Path(doc['canonicalDocumentPath']).stem
        for kind,key in [('html','crops'),('pdf','pageImages'),('xlsx','previews')]:
            images=doc[kind][key];assert len(images)==expected_counts[stem][kind]
            for image in images:
                assert digest(image['path'])==image['sha256']
                with Image.open(image['path']) as im:assert list(im.size)==image['dimensions']
                image.update(actuallyViewed=True,visualReview='PASS_DERIVATIVE_LAYOUT',resolution='original',reviewer='delivery_tools')
                seen.append({'documentId':doc['documentId'],'format':kind,'path':image['path'],'sha256':image['sha256']})
            doc[kind]['visualReview']='PASS_DERIVATIVE_LAYOUT'
            doc[kind]['actuallyViewedImageCount']=len(images)
        doc['pdf']['actuallyViewedPages']=list(range(1,doc['pdf']['pages']+1))
        doc['visualObservation']='All image extents inspected at original resolution; complete labels/values, no clipped text, overlapping rows, missing column headers or unintended frames were observed. Literal strings and row order are separately proved mechanically.'
        for key in ['markdown','draftResult']:assert digest(doc[key])==doc[key+'Sha256']
        for fmt,key in [('pdf','pdf'),('xlsx','xlsx')]:assert digest(doc[fmt]['path'])==doc[fmt]['sha256']
    assert len(seen)==45 and len({x['path'] for x in seen})==45
    load_bound(ROOT/'binding-assisted-tables-r01.json')
    record.update(status='PASS_DERIVATIVE_FORMAT_CANDIDATE_ONLY',published=False,formalQualityGatePassed=False,
        visualReview='PASS_ALL_45_ACTUALLY_VIEWED_IMAGES',visualReviewCompletedUtc=datetime.now(timezone.utc).isoformat(),
        mechanicalInput={'path':str(original),'sha256':digest(original)},actuallyViewedImages=seen,
        actuallyViewedPdfPages=25,actuallyViewedXlsxTiles=10,actuallyViewedHtmlCrops=10,
        rendererCoreSha256AfterReview=digest(REPO/'agents/reverse-agent/src/contextbase/ai/rendering.py'),
        remaining=['Formal rubric scoring and final publication remain parent-controlled; this is a derivative-format candidate.',
                   'Reference links/text were retained; existence/publication of every linked planned document is outside this QA.',
                   'No original app/DB execution, actual Excel printing or whole-workbook live Excel display QA was performed.'],
        auditorCorrection={'beforeCode':str(ROOT/'audit_assisted_tables-before-exact-version.py'),'beforeCodeSha256':digest(ROOT/'audit_assisted_tables-before-exact-version.py'),
                           'issue':'Auditor incorrectly assumed both versions were 1.0; class original is 1.1.',
                           'fix':'Compare every source metadata field with the exact original spec-meta JSON instead of a hard-coded version. No manuscript/output bytes were changed.'})
    final_manifests=[]
    for name in ['pdf-assisted-tables-r01','xlsx-assisted-tables-r01']:
        path=ROOT/name/'delivery-manifest.json';prior=path.read_bytes();backup=path.with_name('delivery-manifest.before-visual-review.json')
        if backup.exists():raise FileExistsError('Fresh manifest QA required')
        backup.write_bytes(prior);manifest=json.loads(prior)
        for doc in manifest['documents']:
            doc.update(visualReview='PASS_DERIVATIVE_LAYOUT',formalQualityGatePassed=False,sourceFidelity='NOT_ASSESSED_BY_FORMAL_RUBRIC')
        manifest.update(status='PASS_DERIVATIVE_FORMAT_CANDIDATE_ONLY',visualReview='PASS_DERIVATIVE_LAYOUT',published=False,formalQualityGatePassed=False,
                        formalScoring='PENDING_ROOT_PROCESS',beforeVisualReviewManifestSha256=sha(prior),
                        visualEvidence='assisted-tables-r01-final-qa.json')
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        final_manifests.append({'path':str(path),'sha256':digest(path),'beforeVisualReview':str(backup),'beforeVisualReviewSha256':sha(prior)})
    record['finalManifests']=final_manifests
    record['recordHelper']={'path':str(Path(__file__)),'sha256':digest(Path(__file__))}
    output=ROOT/'assisted-tables-r01-final-qa.json';fresh(output,record)
    lines=['# Assistedテーブル2件の派生形式QA','','2件の同名HTML・PDF・Excel候補を作成し、文字・順序・空欄・罫線の機械検査と全45画像の原寸レビューを完了した。正式採点・最終公開の合格は本記録に含めない。','',
           '対象はtraining-assistedの固定manifest `e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7`。原稿・固定描画・AI receipt・別承認レビューのSHAを文書ごとに独立して記録した。原仕様/spec-evalは読まず、元アプリ/DBを実行せず、本文を編集していない。','',
           '| 原名 | 版 | MD SHA256 | PDF全ページ | Excel literal/空欄 | 原寸画像 |','| --- | --- | --- | --- | --- | --- |']
    for doc in record['documents']:
        lines.append(f"| {Path(doc['canonicalDocumentPath']).name} | {doc['sourceMetadataExact']['version']} | `{doc['markdownSha256']}` | {doc['pdf']['pages']} | {doc['nonemptyLiteralCells']}/{doc['blankValues']} | HTML {doc['html']['actuallyViewedImageCount']}・PDF {doc['pdf']['actuallyViewedImageCount']}・XLSX {doc['xlsx']['actuallyViewedImageCount']} |")
    lines.extend(['','Excelはbundled `@oai/artifact-tool`で著作し、開始markerは再実行していない。各原宣言の単一sheet、9列、原順序の全文preamble/節見出し/表セル・空欄・11件と17件の項目キー、正本IDと版を保持した。全350非空セルはliteralで数式0。枠外無罫線、結合・列幅・印刷範囲を独立XML検査した。printメタ情報だけを既存接続器で追加し、セル・罫線のOOXML著作はしていない。native画像はprint接続前のArtifact Tool描画であり、実Excel全体表示・印刷は未実施。','',
        'PDFは信頼済ChromiumでJS無効・通信拒否、所有worker 90秒stage timeoutのまま作成した。同一canonical HTML bytesを同名で保存し、印刷投影だけ4データ行ごとに元の見出し/colgroupを複製した。全95本文行はHTML bytesと原順序が一致し、pypdfで全文と全25ページの列見出しを確認した。Poppler全25ページを原寸で実見し、切れ・行重なり・見出し欠落は見つからなかった。','',
        'HTMLの元PNGは1440×4464と1440×6412。計10個の原寸切出しは全画素一致・80px重複・全キャンバスcoverageを確認した。XLSX native全10tilesも9列・全行を覆い、日本語・長文折返し・罫線・節見出しを確認した。単語の折返しは元文字列を変更せず表示上で行われる。','',
        '監査コードの一律版1.0仮定で初回検査を停止した。classの原版は1.1であり、原spec-meta JSON全項目と厳密照合する検査へ修正した。旧監査コードを保存した。この修正で稿や生成物の文字を変更していない。',''])
    for doc in record['documents']:
        lines.append(f"`{Path(doc['canonicalDocumentPath']).stem}` の成果とSHA：")
        lines.append('')
        for fmt in ['html','pdf','xlsx']:
            artifact=doc[fmt];lines.append(f"- [{fmt.upper()}](<{artifact['path']}>) — `{artifact['sha256']}`")
        lines.append('')
    lines.extend([f"詳細証跡は [assisted-tables-r01-final-qa.json](<{output}>)、SHA256 `{digest(output)}`。正式採点と公開の判断はrootに残す。リンク先計画文書の公開状態は本QAの対象外。",''])
    report=ROOT/'ASSISTED-TABLES-DELIVERY-R01.md'
    if report.exists():raise FileExistsError('Fresh report required')
    report.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'qa':str(output),'qaSha256':digest(output),'report':str(report),'reportSha256':digest(report),
        'documents':[{'id':d['documentId'],'markdownSha256':d['markdownSha256'],'htmlSha256':d['html']['sha256'],'pdfSha256':d['pdf']['sha256'],'xlsxSha256':d['xlsx']['sha256']} for d in record['documents']]},ensure_ascii=False))

if __name__=='__main__':main()
