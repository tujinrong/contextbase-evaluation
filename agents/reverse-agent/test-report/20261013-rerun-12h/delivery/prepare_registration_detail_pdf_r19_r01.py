"""Prepare metadata binding and a generic CSS-only print-projection exporter."""
from pathlib import Path
import hashlib
import json

P = Path(__file__).resolve().parent
R = P.parent
AGENT = P.parents[2]
REPO = P.parents[4]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
pinpath = R / 'training-assisted/reviewed-registration-detail-r05-r11-pin.json'
assert sha(pinpath) == '016746beaab58be3a3ab2406b662c63c0df9cb4824cc929b87e701c6fc975bcb'
pin = read(pinpath)
assert pin['sha256'] == 'ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd'
assert pin['independentReviewApproved'] is True
render = R / 'render/assisted-registration-detail-r01-delivery-r19'
pins = read(render / 'render-pins.json')
assert sha(render / 'render-pins.json') == '1684f46d512528883842d65d6fc7ebb464c63062a3649efa639a5f6ea0cdc9e1'
reviewpath = P / 'registration-detail-columns-probe-r03-actual-native-review.json'
assert sha(reviewpath) == '2a894762d39e2ef4543ab3746c13f20e3560b52f0c41503238c6d9ad0bf598c4'
review = read(reviewpath)
assert review['status'] == 'PASS_WITH_NOTES_DERIVED_CSS_NATIVE_GEOMETRY_ONLY' and review['blocking'] == []
assert review['actualTileCount'] == 76 and review['actuallyViewedZeroBasedIndices'] == list(range(76))
assert all(sha(path) == value for path, value in review['afterHashes'].items())
handoff = Path(pin['independentReview']).with_name('review-handoff.json')
assert read(handoff)['approved'] is True
binding = {
 'schema':'reverse-agent-delivery-binding/1', 'referenceMode':'training-assisted',
 'permittedMarkdownRoot':str(REPO / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'),
 'permittedRenderRoot':str(R / 'render'),
 'sourceSnapshotManifestSha256':'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cb09b85a0e7',
 'formalQualityGatePassed':False, 'wholeQualityApproved':False, 'published':False,
 'documents':[{
  'documentId':pin['documentId'], 'canonicalDocumentPath':pin['path'],
  'markdown':pins['source'], 'markdownSha256':pin['sha256'],
  'renderDirectory':str(render), 'renderPinsSha256':sha(render / 'render-pins.json'),
  'renderManifestSha256':sha(render / 'manifest.json'),
  'draftResult':pin['draftResult'], 'draftResultSha256':pin['draftResultSha256'],
  'nativeGeometryReview':str(reviewpath), 'nativeGeometryReviewSha256':sha(reviewpath),
  'nativeGeometryReviewScope':'CSS_ONLY_2400PX_VIEW_PROJECTION; original body viewport HOLD preserved',
  'separateApprovedReview':{
   'handoff':str(handoff), 'handoffSha256':sha(handoff),
   'review':pin['independentReview'], 'reviewSha256':pin['independentReviewSha256'],
   'approved':True, 'scope':'text-source-and-structure'},
  'stateProjectionIncluded':False
 }]
}
# Fixed capsule hash is copied exactly from the source binding.
binding['sourceSnapshotManifestSha256'] = pins['sourceSnapshotManifestSha256']
assert binding['sourceSnapshotManifestSha256'] == 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
output = P / 'binding-assisted-registration-detail-r19-r01.json'
assert not output.exists()
output.write_text(json.dumps(binding, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
base = P / 'export_pdf_r18.py'
assert sha(base) == '29c8d125034bf73c0739e2b594c2b179955f07639529b30a56a58e23a88e25bb'
code = base.read_text(encoding='utf8')
needle = "    parser.add_argument('--table-page-rows',type=int,default=0)"
assert code.count(needle) == 1
code = code.replace(needle, needle + "\n    parser.add_argument('--minimum-content-width',type=int,default=1440)\n    parser.add_argument('--marked-cell-min-em',type=int,default=0)\n    parser.add_argument('--marked-first-cell-min-em',type=int,default=0)")
needle = "    args=parser.parse_args()"
assert code.count(needle) == 1
code = code.replace(needle, needle + "\n    if not 1440<=args.minimum_content_width<=6000 or not 0<=args.marked_cell_min_em<=40 or not 0<=args.marked_first_cell_min_em<=40:raise ValueError('Bounded CSS-only print geometry required')")
needle = "                    table_records=[];print_css=PRINT_CSS"
assert code.count(needle) == 1
extra = "\n                    eligible='table[data-renderer-markdown]:not([data-renderer-columns=\"1\"]):not([data-renderer-columns=\"2\"])'\n                    if args.marked_cell_min_em:print_css+='\\n'+eligible+' th,'+eligible+' td{min-width:'+str(args.marked_cell_min_em)+'em}'\n                    if args.marked_first_cell_min_em:print_css+='\\n'+eligible+' th:first-child,'+eligible+' td:first-child{min-width:'+str(args.marked_first_cell_min_em)+'em}'"
code = code.replace(needle, needle + extra)
needle = "width_px=max(1440,max((image['width'] for image in entry['images']),default=0))+96"
assert code.count(needle) == 1
code = code.replace(needle, "width_px=max(args.minimum_content_width,max((image['width'] for image in entry['images']),default=0))+96")
needle = "'marginCssPixels':48,'popplerDpi':96}"
assert code.count(needle) == 1
code = code.replace(needle, "'marginCssPixels':48,'popplerDpi':96,'minimumContentWidth':args.minimum_content_width,'markedCellMinEm':args.marked_cell_min_em,'markedFirstCellMinEm':args.marked_first_cell_min_em}")
helper = P / 'export_pdf_minimum_columns_r19.py'
assert not helper.exists()
compile(code, str(helper), 'exec')
helper.write_text(code, encoding='utf8')
print(json.dumps({'binding':str(output),'bindingSha256':sha(output),'helper':str(helper),'helperSha256':sha(helper),'baseHelperSha256':sha(base)}, ensure_ascii=False))
