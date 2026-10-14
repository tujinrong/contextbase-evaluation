"""Print only hash-bound safe renderer HTML; text checks are not visual approval."""
from __future__ import annotations
import argparse
import base64
import copy
import faulthandler
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from pypdf import PdfReader
from PIL import Image
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from delivery_model import load_bound, document_model, safe_path, canonical, sha

PRINT_CSS = '''
@page { margin: 12mm; }
html body,html body * { font-family: "MS Gothic", monospace !important; font-variant-ligatures:none !important; }
body { font-size: 9pt; line-height: 1.5; }
h1,h2,h3,h4 { break-after: avoid; }
table { min-width:0 !important; width:100% !important; table-layout:fixed !important; font-size:8pt !important; }
th,td { white-space:normal; overflow-wrap:anywhere; vertical-align:top; }
thead { display:table-header-group; } tr { break-inside:avoid; }
pre { white-space:pre-wrap; overflow-wrap:anywhere; font-size:8pt; }
img { max-width:100%; height:auto; } p { orphans:3; widows:3; }
img[data-renderer-diagram] { display:block !important; max-height:160mm; width:auto; height:auto; object-fit:contain; break-inside:avoid; }
.delivery-image-tile { break-before:page; break-inside:avoid; background:white; padding:0; margin:0; }
.delivery-image-tile figcaption { font-size:8pt; margin:0 0 2mm; }
.delivery-image-tile img { display:block; max-width:100%; max-height:160mm; width:auto; height:auto; }
'''

TABLE_PAGE_CSS='''
table[data-delivery-table-page] { break-inside:avoid !important; }
body > table[data-delivery-table-page] ~ h2 { break-before:page !important; }
table[data-delivery-table-page] thead { display:table-row-group !important; }
table[data-delivery-table-page][data-delivery-table-continued] { break-before:page !important; }
'''

def partition_markdown_tables(html_text, max_rows):
    """Print projection only: duplicate parser-owned headers, preserve body rows."""
    if not 1<=max_rows<=12:raise ValueError('Table page row limit must be 1..12')
    soup=BeautifulSoup(html_text,'html.parser');records=[];projected=html_text
    for ordinal,table in enumerate(soup.select('table[data-renderer-markdown]'),1):
        if table.find('tfoot',recursive=False) is not None:raise ValueError('Table footer partition unsupported')
        if any(cell.get('rowspan','1')!='1' or cell.get('colspan','1')!='1' for cell in table.find_all(['th','td'])):
            raise ValueError('Spanning table cells require separate explicit print QA')
        head=table.find('thead',recursive=False);body=table.find('tbody',recursive=False)
        columns=table.find('colgroup',recursive=False)
        if head is None or body is None or columns is None:raise ValueError('Pinned renderer table structure required')
        rows=body.find_all('tr',recursive=False)
        original=str(table)
        if original not in projected:raise ValueError('Cannot locate exact immutable table fragment')
        parts=[];part_records=[];copied_rows=[]
        for begin in range(0,len(rows),max_rows):
            end=min(begin+max_rows,len(rows));piece=copy.deepcopy(table)
            output_body=piece.find('tbody',recursive=False);output_body.clear()
            for row in rows[begin:end]:output_body.append(copy.deepcopy(row))
            piece['data-delivery-table-page']=str(len(parts)+1)
            if begin:piece['data-delivery-table-continued']=''
            assert str(piece.find('thead',recursive=False))==str(head)
            assert str(piece.find('colgroup',recursive=False))==str(columns)
            copied_rows.extend(str(row) for row in output_body.find_all('tr',recursive=False))
            parts.append(str(piece))
            part_records.append({'part':len(parts),'firstOriginalBodyRow':begin+1,'lastOriginalBodyRow':end,
                                 'headerDuplicatedExactly':True,'columnDefinitionEqual':True})
        assert copied_rows==[str(row) for row in rows]
        projected=projected.replace(original,'\n'.join(parts),1)
        records.append({'originalTable':ordinal,'originalTableSha256':sha(original.encode('utf-8')),
                        'bodyRows':len(rows),'columnCount':int(table['data-renderer-columns']),
                        'bodyRowOrderAndHtmlEqual':True,'parts':part_records})
    if not records:raise ValueError('No parser-owned Markdown table to partition')
    return projected,records

def image_annex(entry,directory):
    """Pixel-only viewport cuts; all graph words and edges come from pinned PNGs."""
    sections=[];records=[];directory.mkdir()
    def origins(length,limit,overlap):
        return list(range(0,max(1,length-overlap),limit-overlap))
    for picture in entry['images']:
        if not picture['id'].startswith('diagram-') or (picture['width']<=1100 and picture['height']<=2000):continue
        raw=Path(picture['path']).read_bytes()
        if sha(raw)!=picture['sha256']:raise ValueError('Changed source diagram PNG')
        source=Image.open(io.BytesIO(raw));source.load();boxes=[]
        for y in origins(source.height,600,60):
            for x in origins(source.width,900,60):boxes.append((x,y,min(x+900,source.width),min(y+600,source.height)))
        for ordinal,box in enumerate(boxes,1):
            crop=source.crop(box)
            # Exact pixel test only: preserve the white viewport in the coverage
            # audit, but avoid printing a page containing no graph pixel.
            all_white=crop.convert('RGB').getextrema()==((255,255),(255,255),(255,255))
            buffer=io.BytesIO();crop.save(buffer,format='PNG');tile=buffer.getvalue()
            name=f'{picture["id"]}-{ordinal:03d}.png';target=directory/name;target.write_bytes(tile)
            records.append({'id':picture['id'],'sourceSha256':picture['sha256'],'sourcePath':picture['path'],'cropBox':box,'path':str(target),'sha256':sha(tile),
                            'printed':not all_white,'omissionReason':'ALL_RGB_PIXELS_255' if all_white else None,'tileOrdinal':ordinal,'sourceTileCount':len(boxes),'overlapPixels':60})
            if all_white:continue
            label=picture['id']+f' {ordinal}/{len(boxes)}'
            sections.append('<figure class="delivery-image-tile"><figcaption>'+label+'</figcaption><img src="data:image/png;base64,'+base64.b64encode(tile).decode('ascii')+'"></figure>')
    return ''.join(sections),records

def log_stage(destination, stage, **details):
    event={'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'stage':stage,**details}
    with (destination/'stages.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(event,ensure_ascii=False)+'\n');stream.flush()
    print(json.dumps(event,ensure_ascii=False),flush=True)

def run_bounded():
    """Own one worker tree; stop a stalled stage rather than waiting indefinitely."""
    argv=sys.argv[1:]
    output=Path(argv[argv.index('--output-root')+1])
    if output.exists():raise ValueError('Fresh PDF delivery root required')
    stage_limit=int(argv[argv.index('--stage-timeout')+1]) if '--stage-timeout' in argv else 90
    command=[sys.executable,'-u',str(Path(__file__).resolve()),*argv,'--worker']
    start=time.monotonic();last_progress=start;previous_size=-1
    process=subprocess.Popen(command)
    print(json.dumps({'event':'owned-worker-started','pid':process.pid,'stageTimeoutSeconds':stage_limit}),flush=True)
    try:
        while process.poll() is None:
            progress=output/'stages.jsonl'
            size=progress.stat().st_size if progress.exists() else 0
            if size!=previous_size:previous_size=size;last_progress=time.monotonic()
            if time.monotonic()-last_progress>stage_limit or time.monotonic()-start>900:
                failure={'event':'owned-worker-timeout','pid':process.pid,'stageTimeoutSeconds':stage_limit,'elapsedSeconds':time.monotonic()-start}
                if os.name=='nt':
                    stopped=subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,text=True,timeout=20)
                    failure['ownedTreeStopReturnCode']=stopped.returncode
                else:process.kill()
                process.wait(timeout=20)
                if output.exists():
                    (output/'timeout.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
                    manifest=output/'delivery-manifest.json'
                    record=json.loads(manifest.read_bytes()) if manifest.exists() else {'documents':[]}
                    record.update(status='FAILED_TIMEOUT',published=False,timeout=failure)
                    manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                raise TimeoutError(json.dumps(failure))
            time.sleep(0.2)
    except BaseException:
        if process.poll() is None:
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20)
            else:process.kill()
        raise
    if process.returncode:raise SystemExit(process.returncode)

def verify_text(data, model, diagnostic_directory=None):
    reader=PdfReader(io.BytesIO(data),strict=True)
    if not reader.pages: raise ValueError('PDF has no pages')
    text='\n'.join(page.extract_text() or '' for page in reader.pages)
    normalize=lambda value: ''.join(value.replace('\u00ad','').split())
    expected=[model['title'],*[d['heading'] for d in model['sourceMetadata'].get('sections',model['sourceMetadata'].get('sheets',[]))],*model['visibleCoverage']]
    expected=[value for value in expected if normalize(value)]
    missing=[value for value in expected if normalize(value) not in normalize(text)]
    if diagnostic_directory:
        (diagnostic_directory/'pypdf-extracted.txt').write_text(text,encoding='utf-8')
        (diagnostic_directory/'text-coverage.json').write_text(json.dumps({'pages':len(reader.pages),'expectedCount':len(expected),'missingCount':len(missing),'missing':missing},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if missing: raise ValueError('PDF visible text coverage failed: '+repr(missing[:8]))
    return {'pages':len(reader.pages),'checkedVisibleStrings':len(expected),'textCharacters':len(text), 'textCoverage':'PASS'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--binding',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    parser.add_argument('--chromium',type=Path,required=True)
    parser.add_argument('--poppler',type=Path,default=None)
    parser.add_argument('--deadline',default='2026-10-13T20:15:58Z')
    parser.add_argument('--stage-timeout',type=int,default=90)
    parser.add_argument('--diagram-tiles',action='store_true')
    parser.add_argument('--table-page-rows',type=int,default=0)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if datetime.now(timezone.utc)>=datetime.fromisoformat(args.deadline.replace('Z','+00:00')):
        raise ValueError('Deadline reached')
    bound, entries, provenance=load_bound(args.binding)
    destination=safe_path(args.output_root)
    origins=[safe_path(bound['permittedMarkdownRoot']),safe_path(bound['permittedRenderRoot']),safe_path(args.binding)]
    if any(destination==p or destination.is_relative_to(p) or p.is_relative_to(destination) for p in origins):
        raise ValueError('Output must be disjoint from pinned inputs')
    if destination.exists(): raise ValueError('Fresh PDF delivery root required')
    chromium=safe_path(args.chromium)
    if not chromium.is_file(): raise ValueError('Existing trusted Chromium executable required')
    poppler=safe_path(args.poppler or shutil.which('pdftoppm') or '')
    if not poppler.is_file(): raise ValueError('Existing Poppler executable required')
    destination.mkdir(parents=True)
    fault=(destination/'faulthandler.log').open('w',encoding='utf-8')
    faulthandler.enable(file=fault,all_threads=True)
    faulthandler.dump_traceback_later(max(10,args.stage_timeout-15),repeat=True,file=fault)
    log_stage(destination,'bound-inputs-validated',documents=len(entries))
    record={'schema':'reverse-agent-pdf-delivery/1',**provenance,'sourceSnapshotManifestSha256':bound['sourceSnapshotManifestSha256'],
            'referenceMode':bound.get('referenceMode'),
            'documents':[],'originalApplicationExecuted':False,'inputJavaScriptEnabled':False,'businessContentAuthored':False,
            'status':'RUNNING','visualReview':'PENDING'}
    previous={key:os.environ.get(key) for key in ('TEMP','TMP','TMPDIR')}
    runtime=destination/'.runtime';runtime.mkdir()
    os.environ.update({key:str(runtime) for key in previous})
    try:
        log_stage(destination,'playwright-start')
        with sync_playwright() as playwright:
            log_stage(destination,'chromium-launch')
            browser=playwright.chromium.launch(executable_path=str(chromium),headless=True,timeout=45000)
            log_stage(destination,'context-create')
            context=browser.new_context(java_script_enabled=False,service_workers='block',locale='ja-JP',accept_downloads=False)
            context.set_default_timeout(45000)
            blocked=[]
            context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()))
            try:
                for entry in entries:
                    if datetime.now(timezone.utc)>=datetime.fromisoformat(args.deadline.replace('Z','+00:00')):
                        raise ValueError('Deadline reached during publication')
                    model=document_model(entry);relative=canonical(entry['canonicalDocumentPath'])
                    html_path=destination/'html'/relative.with_suffix('.html')
                    pdf_path=destination/'PDF'/relative.with_suffix('.pdf')
                    qa_dir=destination/'qa'/relative.with_suffix('')
                    html_path.parent.mkdir(parents=True,exist_ok=True);pdf_path.parent.mkdir(parents=True,exist_ok=True);qa_dir.mkdir(parents=True)
                    html_bytes=Path(entry['canonicalHtml']).read_bytes();html_path.write_bytes(html_bytes)
                    # Trusted print CSS is connected without DOM evaluation. The
                    # bound renderer HTML is preserved byte-for-byte separately.
                    html_text=html_bytes.decode('utf-8')
                    if not html_text.startswith('<!doctype html><html ') or '</head>' not in html_text:
                        raise ValueError('Expected pinned safe renderer document head')
                    table_records=[];print_css=PRINT_CSS
                    if args.table_page_rows:
                        html_text,table_records=partition_markdown_tables(html_text,args.table_page_rows)
                        print_css+=TABLE_PAGE_CSS
                        log_stage(destination,'table-row-partition',tables=len(table_records),maxBodyRows=args.table_page_rows)
                    print_html=html_text.replace('</head>','<style data-delivery-print="1">'+print_css+'</style></head>',1)
                    annex_records=[]
                    if args.diagram_tiles:
                        annex,annex_records=image_annex(entry,qa_dir/'diagram-tiles')
                        closing=print_html.rfind('</body>')
                        if closing<0:raise ValueError('Safe renderer body closure missing')
                        print_html=print_html[:closing]+annex+print_html[closing:]
                        log_stage(destination,'diagram-pixel-tiles',tiles=len(annex_records))
                    log_stage(destination,'page-create',documentId=entry['documentId'])
                    page=context.new_page()
                    try:
                        log_stage(destination,'set-content',bytes=len(print_html.encode('utf-8')))
                        page.set_content(print_html,wait_until='domcontentloaded',timeout=45000)
                        log_stage(destination,'emulate-print')
                        page.emulate_media(media='print')
                        landscape=any(s['columns']>=8 for s in model['sheets'] if s['role']!='cover')
                        log_stage(destination,'print-pdf',landscape=landscape)
                        data=page.pdf(format='A4',landscape=landscape,print_background=True,display_header_footer=True,
                                      header_template='<div></div>',footer_template='<div style="font-size:8px;width:100%;text-align:center"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
                                      margin={'top':'12mm','bottom':'15mm','left':'12mm','right':'12mm'})
                        log_stage(destination,'print-pdf-complete',bytes=len(data))
                    finally:
                        log_stage(destination,'page-close');page.close()
                    if blocked: raise ValueError('Unexpected external resource request')
                    log_stage(destination,'pypdf-text-coverage')
                    pdf_path.write_bytes(data)
                    checks=verify_text(data,model,qa_dir)
                    time_left=(datetime.fromisoformat(args.deadline.replace('Z','+00:00'))-datetime.now(timezone.utc)).total_seconds()
                    if time_left<=0: raise ValueError('Deadline reached before Poppler capture')
                    log_stage(destination,'poppler-all-pages',pages=checks['pages'])
                    process=subprocess.run([str(poppler),'-png','-r','110','-f','1','-l',str(checks['pages']),str(pdf_path),str(qa_dir/'page')],capture_output=True,text=True,timeout=min(args.stage_timeout-5,time_left))
                    if process.returncode: raise ValueError('Poppler failed: '+process.stderr[:2000])
                    pictures=sorted(qa_dir.glob('page-*.png'))
                    if len(pictures)!=checks['pages']: raise ValueError('PDF page PNG coverage mismatch')
                    record['documents'].append({'documentId':entry['documentId'],'canonicalDocumentPath':entry['canonicalDocumentPath'],
                        'markdownSha256':entry['markdownSha256'],'html':str(html_path),'htmlSha256':sha(html_bytes),
                        'printProjectionSha256':sha(print_html.encode('utf-8')),'printProjection':'TRUSTED_CSS'+('_TABLE_PARTITION' if table_records else '')+('_PIXEL_ANNEX' if annex_records else ''),
                        'printCssSha256':sha(print_css.encode('utf-8')),'cssInsertion':'FIRST_OUTER_HEAD_CLOSE','annexInsertion':'LAST_OUTER_BODY_CLOSE' if annex_records else None,'diagramTiles':annex_records,'tablePartitions':table_records,
                        'pdf':str(pdf_path),'pdfSha256':sha(data),'renderPinsSha256':entry['renderPinsSha256'],
                        'renderManifestSha256':entry['renderManifestSha256'],**checks,
                        'pageImages':[{'path':str(p),'sha256':sha(p.read_bytes())} for p in pictures],
                        'visualReview':'PENDING','sourceFidelity':'NOT_ASSESSED'})
                    (destination/'delivery-manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                    log_stage(destination,'document-complete',pages=checks['pages'],pngCount=len(pictures))
            finally:
                log_stage(destination,'context-close');context.close()
                log_stage(destination,'browser-close');browser.close()
        load_bound(args.binding)
        record['status']='TEXT_VERIFIED_VISUAL_REVIEW_PENDING'
    except Exception as exc:
        record.update(status='FAILED',error=str(exc),published=False)
        raise
    finally:
        faulthandler.cancel_dump_traceback_later();faulthandler.disable();fault.close()
        for key,value in previous.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key]=value
        (destination/'delivery-manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'documents':len(record['documents']),'status':record['status']}))

if __name__=='__main__':
    if '--worker' in sys.argv:main()
    else:run_bounded()
