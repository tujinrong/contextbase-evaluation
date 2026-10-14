"""Bind the five actual-viewed synthetic PNGs to independent native QA."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from PIL import Image

HERE=Path(__file__).resolve().parent
RUN=HERE.parent/'engine/all-ai-r18-root-r01'
LOG=HERE.parent/'engine/all-ai-r18-root-r01.log'
NAMES=['table-css-readable','table-css-baseline','table-css-protected',
       'table-css-protected-baseline','table-css-authored-break']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    integration=HERE/'core-r18-independent-integration-qa.json'
    assert sha(integration)=='997e9c4e80e15a16e292eb75b9e265f8148e55f6a4524a1a10b8f9d9f0d16f98'
    seen=[];states={}
    for name in NAMES:
        path=RUN/name/'document.png';metadata=RUN/name/'measurement.json'
        state=json.loads(metadata.read_text(encoding='utf8'));states[name]=state
        with Image.open(path) as image: size=image.size
        assert tuple(size)==(state['width'],state['height'])
        assert state['capture']['documentPng']['sha256']==sha(path)
        assert state['blockedRequests']==[]
        seen.append({'name':name,'path':str(path),'sha256':sha(path),'size':size,
                     'measurement':str(metadata),'measurementSha256':sha(metadata),
                     'actuallyViewed':True,'viewMethod':'view_image original detail',
                     'fullOriginalPixelExtentReviewed':True,
                     'candidateFindings':[] if name!='table-css-baseline' else
                         ['Known fixed-width baseline fractures identifiers; retained as comparison, not candidate approval.']})
    baseline=states['table-css-baseline'];candidate=states['table-css-readable']
    assert [table['html'] for table in baseline['tables']]==[table['html'] for table in candidate['tables']]
    assert [table['columns'] for table in candidate['tables']]==['9','3','6']
    assert all(len(token['rows'])==1 and token['withinCell'] for token in candidate['tokens'])
    assert candidate['overflows']==[] and all(style=='nowrap' for style in candidate['inlineCodeWhitespace'])
    assert states['table-css-protected']['tables']==states['table-css-protected-baseline']['tables']
    with Image.open(RUN/'table-css-protected/document.png') as current, Image.open(RUN/'table-css-protected-baseline/document.png') as old:
        assert current.convert('RGBA').tobytes()==old.convert('RGBA').tobytes()
    authored=states['table-css-authored-break']
    assert 'AuthoredAtomic<br>Token' in authored['tables'][0]['html']
    assert len({token['rows'][0] for token in authored['tokens']})==2
    assert not list((RUN/'table-css-excessive').glob('*.png'))
    log=LOG.read_text(encoding='utf-8-sig')
    tests=['test_table_css_keeps_nine_non_no_three_and_long_six_column_tokens_whole',
           'test_table_css_one_two_column_and_embedded_geometry_and_pixels_are_unchanged',
           'test_table_css_preserves_authored_identifier_break_without_content_repair',
           'test_table_css_excessive_atomic_width_is_display_error_with_no_partial_png']
    lines=[next(line for line in log.splitlines() if line.startswith(test+' ') and line.endswith(' ... ok')) for test in tests]
    result={'schema':'core-r18-native-synthetic-actual-review/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS_SYNTHETIC_NATIVE_GEOMETRY_ONLY','integrationReview':str(integration),
        'integrationReviewSha256':sha(integration),'actuallyViewedImageCount':5,'images':seen,
        'candidateFindings':[],'originalCellsAndOrderExact':True,
        'allSyntheticIdentifiersAndNumbersWholeInsideCells':True,
        'oneTwoColumnAndEmbeddedGeometryAndExactRgbaUnchanged':True,
        'authoredBreakRetainedWithoutRepair':True,'widthBoundNegativeFinalImageAbsent':True,
        'widthBoundNegativeFixtureSha256':sha(RUN/'table-css-excessive.md'),
        'observedFourNativeTestPassLines':lines,'fullSuiteStillSeparate':True,
        'scope':{'businessMaterialsRead':False,'canonicalBodyEdited':False,'mainEdited':False,
                 'providerCalls':0,'applicationExecuted':False,'wholeSpecificationQualityApproved':False,'published':False},
        'limits':['These are synthetic fixture images, not production draft qualification.',
                  'Candidate width increases to preserve atomic text; PDF scaling must be reviewed separately.',
                  'Historical baseline wrapping is intentionally preserved as comparison evidence.']}
    out=HERE/'core-r18-independent-native-qa.json';assert not out.exists()
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'path':str(out),'sha256':sha(out),'status':result['status']},ensure_ascii=False))

if __name__=='__main__':main()
