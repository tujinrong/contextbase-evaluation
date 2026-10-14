"""Fresh print-only exporter; canonical HTML/MD and historical helpers stay fixed."""
from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
source=HERE/'export_pdf.py';target=HERE/'export_pdf_r18.py'
assert not target.exists()
text=source.read_text(encoding='utf8')
text=text.replace('from delivery_model import load_bound, document_model, safe_path, canonical, sha','from delivery_model_r18 import load_bound, document_model, safe_path, canonical, sha')
needle="TABLE_PAGE_CSS='''"
assert text.count(needle)==1
addition='''# Append only the frozen r18 eligible Markdown-table projection. Existing
# one/two-column and unmarked embedded table rules are untouched.
PRINT_CSS += '\\n' + 'table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]){table-layout:auto!important;font-size:9pt!important}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) col{width:auto!important}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td{overflow-wrap:normal!important;word-break:normal!important;white-space:normal!important}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) code{white-space:nowrap!important}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th:last-child,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td:last-child{min-width:20em}'
# Native-size graph pages are a viewing projection; PNG text/edges never change.
PRINT_CSS += '\\nbody{margin:0!important}img[data-renderer-diagram]{max-height:none!important;width:auto!important;height:auto!important;break-before:page;break-after:page;break-inside:avoid}'

'''
text=text.replace(needle,addition+needle)
old="""                        data=page.pdf(format='A4',landscape=landscape,print_background=True,display_header_footer=True,"""
new="""                        width_px=max(1440,max((image['width'] for image in entry['images']),default=0))+96
                        height_px=max(2000,max((image['height']+48 for image in entry['images']),default=0))+96
                        page.set_viewport_size({'width':width_px-96,'height':1000})
                        log_stage(destination,'native-size-paper-projection',widthPixels=width_px,heightPixels=height_px)
                        page_geometry=page.locator('table[data-renderer-markdown]').evaluate_all('''tables=>tables.map(t=>({columns:t.dataset.rendererColumns,width:t.getBoundingClientRect().width,rows:t.rows.length,cells:[...t.querySelectorAll('th,td')].map(c=>({text:c.textContent,width:c.getBoundingClientRect().width,scroll:c.scrollWidth,client:c.clientWidth})),code:[...t.querySelectorAll('code')].map(c=>({text:c.textContent,width:c.getBoundingClientRect().width}))}))''')
                        if any(t['width']>width_px-96+1 for t in page_geometry):raise ValueError('Print table exceeds native-size paper width')
                        data=page.pdf(width=str(width_px)+'px',height=str(height_px)+'px',print_background=True,display_header_footer=True,"""
assert text.count(old)==1;text=text.replace(old,new)
oldmargin="margin={'top':'12mm','bottom':'15mm','left':'12mm','right':'12mm'})"
assert text.count(oldmargin)==1;text=text.replace(oldmargin,"margin={'top':'48px','bottom':'48px','left':'48px','right':'48px'})")
text=text.replace("'-r','110'","'-r','96'")
entryneedle="'renderManifestSha256':entry['renderManifestSha256'],**checks,"
assert text.count(entryneedle)==1
text=text.replace(entryneedle,"'renderManifestSha256':entry['renderManifestSha256'],'paperGeometry':{'widthCssPixels':width_px,'heightCssPixels':height_px,'marginCssPixels':48,'popplerDpi':96},'printTableGeometry':page_geometry,**checks,")
domneedle="                    annex_records=[]\n"
assert text.count(domneedle)==1
domproof="""                    original_dom=BeautifulSoup(html_bytes.decode('utf-8'),'html.parser')
                    projected_dom=BeautifulSoup(print_html,'html.parser')
                    injected=projected_dom.select('style[data-delivery-print]')
                    assert len(injected)==1
                    injected[0].decompose()
                    assert str(original_dom)==str(projected_dom),'Print CSS changed non-style DOM'
                    (qa_dir/'print-projection.html').write_text(print_html,encoding='utf8')
                    annex_records=[]
"""
text=text.replace(domneedle,domproof)
target.write_text(text,encoding='utf8')
verifier=(HERE/'verify_xlsx.py').read_text(encoding='utf8').replace('from delivery_model import safe_path, sha, col, load_bound, document_model','from delivery_model_r18 import safe_path, sha, col, load_bound, document_model')
(HERE/'verify_xlsx_r18.py').write_text(verifier,encoding='utf8')
print({'originalExporterSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'freshExporterSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'path':str(target)})
