"""Fresh synthetic audit adaptation; previous failed probe is preserved byte-for-byte."""
import ast,hashlib,json
from pathlib import Path
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
source=A/'probe_pdf_metadata_and_projection_r01.py'
before=hashlib.sha256(source.read_bytes()).hexdigest()
text=source.read_text(encoding='utf-8')
for old,new in (
    ('pdf_projection_r02.py','pdf_projection_r04.py'),
    ('660e8f5731d14c5415d43b4ebf3a750e81bcbc6df5082778403d7af56375fbe1','7bcd51255ceddc0e07e03ff4e26102a9b8689246aab8408f119c89cdf6f13394'),
    ('export_pdf_bound_r03.py','export_pdf_bound_r05.py'),
    ('88540ccd8cc70cf81ea5d7dd6c52a0ec871254e5feaa59141f531af0dd4f35f6','03a6fb7f445b52211c07d50cbd1a07bff413e5a1f91b1b5bfd38fb7d924d84e3'),
    ('independent_pdf_projection_r02','independent_pdf_projection_r04'),
    ('pdf-runtime-deps-metadata-r01.json','pdf-runtime-deps-metadata-r02.json'),
    ('pdf-projection-r02-driver-r03-independent-probes-r01.json','pdf-projection-r04-driver-r05-independent-probes-r01.json'),
    ("'status':'HOLD_COMPLETE_NATIVE_IMAGE_COVERAGE_CONTRACT'","'status':'CODE_AND_SYNTHETIC_PASS_ACTUAL_PDF_REVIEW_PENDING'"),
):
    assert old in text,old
    text=text.replace(old,new)
start=text.index('def small_missing():')
end=text.index('def css_network_accepted():',start)
text=text[:start]+'''def small_missing():
    from PIL import Image
    projected,receipt,tiles=m.project_html(html('<p>synthetic</p>'),[{**small,'kind':'layout'}])
    assert len(tiles)==1 and len(receipt['nativeTiles'])==1 and 'data:image/png' in projected
    assert tiles[0]['cropBox']==[0,0,20,10] and tiles[0]['sourceTileCount']==1
    decoded=Image.open(io.BytesIO(tiles[0]['bytes']));decoded.load()
    assert decoded.convert('RGBA').tobytes()==small_image.tobytes()
    assert receipt['allNativeAssetsEitherInlineOrAnnexed']
    assert receipt['nativeAssetIdsRetained']==['SYNTHETIC-PNG']
case('small-noninline-layout-bound-image-annex-1of1-all-pixels',small_missing)

def diagram_missing():
    rejects(lambda:m.project_html(html(),[{**small,'kind':'diagram'}]))
case('reject-missing-canonical-inline-diagram',diagram_missing)

def diagram_duplicate():
    pictures=[{**small,'id':'DIAGRAM-1','kind':'diagram'},{**small,'id':'DIAGRAM-2','kind':'diagram'}]
    rejects(lambda:m.project_html(html('<img src="'+src+'">'),pictures))
    projected,receipt,tiles=m.project_html(html('<img src="'+src+'"><img src="'+src+'">'),pictures)
    assert not tiles and receipt['canonicalInlineNativeImageCount']==2
    assert receipt['nativeAssetIdsRetained']==['DIAGRAM-1','DIAGRAM-2']
case('duplicate-SHA-diagrams-minimum-two-inline-occurrences',diagram_duplicate)

def both_comment_boundaries():
    raw=html('<p>合成 001</p><!-- </body> -->','<!-- </head> -->')
    projected,receipt,tiles=m.project_html(raw,[])
    assert receipt['inverseRestoresCanonicalHtmlBytes'] and not tiles
    assert projected.encode().replace(('<style data-spec-agent-pdf="1">'+m.PRINT_CSS+'</style>').encode(),b'',1)==raw
case('head-and-body-comment-close-literals-do-not-anchor-insertions',both_comment_boundaries)

def offset_delta_exact():
    old=(DEL/'pdf_projection_r03.py').read_bytes()
    current=(DEL/'pdf_projection_r04.py').read_bytes()
    assert sha(old)=='1f97920494cade5b41f6047607c495662b3dc965368529b4040ef69ba60b66d5'
    assert old.replace(b'def offset(',b'def source_offset(').replace(b'self.offset()',b'self.source_offset()')==current
    old_driver=(DEL/'export_pdf_bound_r04.py').read_bytes()
    current_driver=(DEL/'export_pdf_bound_r05.py').read_bytes()
    assert sha(old_driver)=='91d10a2ffaf523febaa2e3acb5be125a2d0682339aa173dfebbf1d20a0fa7642'
    assert old_driver.replace(b'from pdf_projection_r03 import',b'from pdf_projection_r04 import')==current_driver
    for p in (DEL/'pdf_projection_r03.py',DEL/'export_pdf_bound_r04.py'):
        pins[str(p)]=hash_file(p)
case('fresh-offset-rename-three-points-and-driver-import-only-byte-exact-deltas',offset_delta_exact)

'''+text[end:]
ast.parse(text)
target=A/'probe_pdf_metadata_and_projection_r02.py'
assert not target.exists()
with target.open('x',encoding='utf-8') as h:h.write(text)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'oldProbeSha256':before,'oldProbeUnchanged':True},ensure_ascii=False))
