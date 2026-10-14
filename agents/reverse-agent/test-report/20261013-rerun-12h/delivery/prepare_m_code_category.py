"""Pin the existing canonical manuscript and audit renderer-only changes."""
import json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
from delivery_model import sha

repo=Path('D:/開発/contextbase-evaluation')
report=repo/'agents/reverse-agent/test-report/20261013-rerun-12h'
delivery=report/'delivery'
md=repo/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/remaining-batch-03/基本設計書/テーブル/03_m_code_category.md'
draft=repo/'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/jobs/remaining-batch-03/2152d5f7e821bc29/draft-result.json'
old,new=report/'render/source-m-code-category-r03',report/'render/source-m-code-category-r04'
expected_md='c43b8c5de33de810413b9b5cf306f1fd60ae4a9d054fd2be7c1a7bd6f6adab46'
snapshot_sha='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
assert sha(md.read_bytes())==expected_md
pins=json.loads((new/'render-pins.json').read_bytes())
assert pins['sourceSha256']==expected_md and pins['sourceSnapshotManifestSha256']==snapshot_sha
assert pins['canonicalDocumentPath']=='基本設計書/テーブル/03_m_code_category.md'
assert pins['draftResultSha256']==sha(draft.read_bytes())
old_soup,new_soup=[BeautifulSoup((folder/'document.html').read_bytes(),'html.parser') for folder in [old,new]]
assert list(old_soup.body.stripped_strings)==list(new_soup.body.stripped_strings)
table_cells=lambda soup:[[cell.get_text('\n',strip=False) for row in table.select('tr') for cell in row.find_all(['th','td'],recursive=False)] for table in soup.select('table')]
assert table_cells(old_soup)==table_cells(new_soup)
assert [len(t.select('thead th')) for t in new_soup.select('table')]==[2,9]
assert all(t.has_attr('data-renderer-markdown') for t in new_soup.select('table'))
assert [(t['data-renderer-columns'],len(t.select('colgroup col'))) for t in new_soup.select('table')]==[('2',2),('9',9)]
binding={'schema':'reverse-agent-delivery-binding/1','referenceMode':'source-only',
         'permittedMarkdownRoot':str(md.parents[2]),'permittedRenderRoot':str(report/'render'),
         'sourceSnapshotManifestSha256':snapshot_sha,'formalQualityGatePassed':False,
         'documents':[{'documentId':pins['documentId'],'canonicalDocumentPath':pins['canonicalDocumentPath'],
            'markdown':str(md),'markdownSha256':expected_md,'renderDirectory':str(new),
            'renderPinsSha256':sha((new/'render-pins.json').read_bytes()),
            'renderManifestSha256':sha((new/'manifest.json').read_bytes()),
            'draftResult':str(draft),'draftResultSha256':sha(draft.read_bytes())}]}
binding_path=delivery/'binding-m-code-category-r04.json'
if binding_path.exists():raise FileExistsError('Fresh binding required')
binding_path.write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
qa=delivery/'html-m-code-category-r04'
qa.mkdir()
raw_image=new/'document.png'
with Image.open(raw_image) as image:
    crops=[]
    for ordinal,y in enumerate(range(0,image.height,1120),1):
        box=(0,y,image.width,min(y+1200,image.height))
        path=qa/f'document-{ordinal:03d}.png'
        image.crop(box).save(path)
        crops.append({'path':str(path),'sha256':sha(path.read_bytes()),'sourceRectangle':list(box),
                      'sourcePngSha256':sha(raw_image.read_bytes()),'actuallyViewed':False})
record={'schema':'reverse-agent-render-table-qa/1','documentId':pins['documentId'],'markdownSha256':expected_md,
        'rendererCoreSha256':sha((repo/'agents/reverse-agent/src/contextbase/ai/rendering.py').read_bytes()),
        'r10Verification':str(report/'engine/all-ai-r10-result.json'),
        'r10VerificationSha256':sha((report/'engine/all-ai-r10-result.json').read_bytes()),
        'oldHtmlSha256':sha((old/'document.html').read_bytes()),'newHtmlSha256':sha((new/'document.html').read_bytes()),
        'fullVisibleTextSequenceEqual':True,'tableCellValuesAndOrderEqual':True,
        'tableColumnCounts':[2,9],'preambleRetained':True,'originalMarkdownUnchanged':True,
        'visualReview':'PENDING','formalRubricPassed':False,'published':False,'crops':crops}
(qa/'qa.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'binding':str(binding_path),'bindingSha256':sha(binding_path.read_bytes()),
                  'tableCellOrder':'PASS','fullVisibleSequence':'PASS','imageQaCrops':len(crops)},ensure_ascii=False))
