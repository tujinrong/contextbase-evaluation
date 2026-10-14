"""Offline print of pinned reviewed renderer HTML. Preparation only until marker ack.
No source application/code execution, prose reconstruction or semantic qualification.
Actual all-page PNG review is mandatory; text/geometry checks alone never approve.
"""
from __future__ import annotations
import argparse,ctypes,faulthandler,hashlib,io,json,os,queue,subprocess,sys,threading,time
from datetime import datetime,timezone
from pathlib import Path
from pypdf import PdfReader
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from delivery_model_v2_62_r06 import load_bound,document_model,safe_path,canonical,OWN_RUN_ROOTS
from pdf_projection_r04 import project_html,text_coverage,canonical_text_order,GEOMETRY_JS,CONTENT_WIDTH_PX

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError('HOLD: '+message)
def owned(path):
    p=safe_path(path);require(any(p.is_relative_to(r) for r in OWN_RUN_ROOTS),'output outside this run');return p
def fresh_write(path,data):
    p=owned(path);safe_path(p.parent).mkdir(parents=True,exist_ok=True)
    with safe_path(p).open('xb') as h:h.write(data)
    require(safe_path(p).read_bytes()==data,'fresh output changed');return p
def json_write(path,value):return fresh_write(path,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def stage(destination,name,**details):
    event={'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'stage':name,**details}
    with owned(destination/'stages.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(event,ensure_ascii=False)+'\n');h.flush()
    print(json.dumps(event,ensure_ascii=False),flush=True)

def creation_time(kernel,handle):
    from ctypes import wintypes as W
    kernel.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)];kernel.GetProcessTimes.restype=W.BOOL
    created,exit,kernel_time,user_time=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
    require(kernel.GetProcessTimes(handle,ctypes.byref(created),ctypes.byref(exit),ctypes.byref(kernel_time),ctypes.byref(user_time)),'owned process creation time failed')
    return (created.dwHighDateTime<<32)|created.dwLowDateTime

def worker_ready():
    from ctypes import wintypes as W
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=W.HANDLE
    print(json.dumps({'stage':'OWNED_WORKER_READY','pid':os.getpid(),'creationTime':creation_time(kernel,kernel.GetCurrentProcess())}),flush=True)


class OwnedWindowsJob:
    """Public Windows Job API; the worker waits for GO before spawning its browser."""
    def __init__(self,pid,expected_creation_time):
        require(os.name=='nt','this bounded helper requires Windows owned-job supervision')
        from ctypes import wintypes as W
        class BASIC(ctypes.Structure):
            _fields_=[('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),('LimitFlags',W.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',W.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]
        class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
        class EXT(ctypes.Structure):_fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];self.k.CreateJobObjectW.restype=W.HANDLE
        self.k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];self.k.SetInformationJobObject.restype=W.BOOL
        self.k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];self.k.OpenProcess.restype=W.HANDLE
        self.k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];self.k.AssignProcessToJobObject.restype=W.BOOL
        self.k.CloseHandle.argtypes=[W.HANDLE];self.k.CloseHandle.restype=W.BOOL
        self.handle=self.k.CreateJobObjectW(None,None);require(bool(self.handle),'CreateJobObject failed')
        info=EXT();info.BasicLimitInformation.LimitFlags=0x2000
        require(self.k.SetInformationJobObject(self.handle,9,ctypes.byref(info),ctypes.sizeof(info)),'job kill-on-close configuration failed')
        process=self.k.OpenProcess(0x0100|0x0001|0x1000,False,pid);require(bool(process),'owned worker process handle failed')
        try:
            require(creation_time(self.k,process)==expected_creation_time,'worker PID creation-time mismatch')
            require(self.k.AssignProcessToJobObject(self.handle,process),'owned worker job assignment failed')
        finally:self.k.CloseHandle(process)
    def close(self):
        if getattr(self,'handle',None):self.k.CloseHandle(self.handle);self.handle=None

def supervise(args):
    destination=owned(args.output_root);require(not destination.exists(),'fresh PDF root required')
    destination.mkdir(parents=True);job=None;process=None
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    process=subprocess.Popen([sys.executable,'-B','-X','utf8','-u',str(Path(__file__)),*sys.argv[1:],'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    start=time.monotonic();progress=start;last=-1
    try:
        lines=queue.Queue()
        def relay():
            for line in iter(process.stdout.readline,b''):lines.put(line);sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
            lines.put(None)
        threading.Thread(target=relay,daemon=True).start()
        ready_raw=lines.get(timeout=args.stage_timeout);require(bool(ready_raw),'worker exited without READY')
        ready=json.loads(ready_raw.decode('utf-8'))
        require(ready.get('stage')=='OWNED_WORKER_READY' and ready.get('pid')==process.pid and type(ready.get('creationTime')) is int,'invalid owned worker READY')
        require(process.poll() is None,'worker exited before ownership handshake')
        job=OwnedWindowsJob(process.pid,ready['creationTime']);require(process.poll() is None,'worker exited after job assignment')
        process.stdin.write(b'GO\n');process.stdin.flush();process.stdin.close()
        json_write(destination/'owned-worker.json',{'pid':process.pid,'processCreationTime':ready['creationTime'],'windowsJobKillOnClose':True,'goAfterJobAssignment':True,'onlyOwnedTreeStopped':True,'stageTimeoutSeconds':args.stage_timeout,'totalTimeoutSeconds':args.total_timeout})
        while process.poll() is None:
            log=owned(destination/'stages.jsonl');size=log.stat().st_size if log.exists() else 0
            if size!=last:last=size;progress=time.monotonic()
            if time.monotonic()-progress>args.stage_timeout or time.monotonic()-start>args.total_timeout:
                json_write(destination/'timeout.json',{'status':'FAILED_TIMEOUT','elapsedSeconds':time.monotonic()-start,'ownedJobOnly':True,'visualQualified':False});raise TimeoutError('Owned PDF worker exceeded bounded timeout')
            time.sleep(0.2)
        require(process.returncode==0,'PDF worker failed: '+str(process.returncode))
    finally:
        if job:job.close()
        if process.poll() is None:process.terminate()
        process.wait(timeout=20)

def tool(path,expected):
    p=safe_path(path);require(p.is_file() and sha(p.read_bytes())==expected,'tool path/SHA mismatch');return p

def worker(args):
    worker_ready()
    require(sys.stdin.buffer.readline(4)==b'GO\n','owned supervisor handshake required')
    bound,entries,provenance=load_bound(args.binding,args.binding_sha256)
    require(bound.get('referenceMode')=='source-only','AG-SPEC PDF requires this source-only binding')
    destination=owned(args.output_root)
    for root in (Path(bound['permittedMarkdownRoot']),Path(bound['permittedRenderRoot']),args.binding):
        root=safe_path(root);require(not(destination==root or destination.is_relative_to(root) or root.is_relative_to(destination)),'PDF output overlaps input roots')
    chromium=tool(args.chromium,args.chromium_sha256);poppler=tool(args.poppler,args.poppler_sha256)
    runtime=owned(destination/'.runtime');runtime.mkdir();oldenv={k:os.environ.get(k) for k in ('TEMP','TMP','TMPDIR')};os.environ.update({k:str(runtime) for k in oldenv})
    record={'schema':'spec-agent-offline-pdf-delivery/1',**provenance,'sourceSnapshotManifestSha256':bound['sourceSnapshotManifestSha256'],'referenceMode':bound['referenceMode'],'documents':[],'status':'RUNNING','inputJavaScriptEnabled':False,'businessProseReauthored':False,'originalApplicationExecuted':False,'formalQualityAssessed':False,'sourceUnknownsResolved':False,'visualReview':'PENDING','adoption':False,'published':False,'pdfMarkerAcknowledged':True}
    fault=owned(destination/'faulthandler.log').open('x',encoding='utf-8');faulthandler.enable(file=fault,all_threads=True);faulthandler.dump_traceback_later(max(15,args.stage_timeout-15),repeat=True,file=fault)
    try:
        stage(destination,'pinned-inputs',documents=len(entries))
        with sync_playwright() as pw:
            stage(destination,'trusted-chromium-launch');browser=pw.chromium.launch(executable_path=str(chromium),headless=True,timeout=45000)
            context=browser.new_context(java_script_enabled=False,service_workers='block',locale='ja-JP',accept_downloads=False);context.set_default_timeout(45000)
            blocked=[];context.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()))
            try:
                for entry in entries:
                    relative=canonical(entry['canonicalDocumentPath']);qa=owned(destination/'qa'/relative.with_suffix(''));qa.mkdir(parents=True)
                    html=safe_path(entry['canonicalHtml']).read_bytes();pictures=[]
                    for image in entry['images']:
                        raw=safe_path(image['path']).read_bytes();require(sha(raw)==image['sha256'],'native source PNG drift')
                        fresh_write(destination/'native-assets'/relative.with_suffix('')/(image['id']+'.png'),raw);pictures.append({**image,'bytes':raw})
                    print_html,projection,tiles=project_html(html,pictures)
                    source_md=safe_path(entry['markdown']).read_bytes();require(sha(source_md)==entry['markdownSha256'],'source Markdown changed before exact copy')
                    fresh_write(destination/'HTML'/relative.with_suffix('.html'),html);fresh_write(destination/'Markdown'/relative,source_md)
                    fresh_write(qa/'print-projection.html',print_html.encode('utf-8'))
                    for tile in tiles:fresh_write(qa/'native-tiles'/(tile['sourceId']+'-'+str(tile['tileOrdinal']).zfill(3)+'.png'),tile['bytes'])
                    stage(destination,'set-content',documentId=entry['documentId']);page=context.new_page()
                    try:
                        page.set_viewport_size({'width':CONTENT_WIDTH_PX,'height':1000});page.set_content(print_html,wait_until='domcontentloaded',timeout=45000);page.emulate_media(media='print')
                        stage(destination,'trusted-geometry-measure');geometry=page.evaluate(GEOMETRY_JS);json_write(qa/'print-geometry.json',geometry)
                        require(not geometry['issues'],'print geometry clips or splits a whole token')
                        stage(destination,'print-pdf');data=page.pdf(format='A3',landscape=True,scale=1,print_background=True,prefer_css_page_size=True,margin={'top':'12mm','bottom':'12mm','left':'12mm','right':'12mm'})
                    finally:page.close()
                    require(not blocked,'unexpected external resource request')
                    pdf=fresh_write(destination/'PDF'/relative.with_suffix('.pdf'),data)
                    stage(destination,'complete-text-coverage');reader=PdfReader(io.BytesIO(data),strict=True);require(bool(reader.pages),'PDF has no pages')
                    extracted='\n'.join(p.extract_text() or '' for p in reader.pages);model=document_model(entry);coverage=text_coverage(extracted,model)
                    soup=BeautifulSoup(html.decode('utf-8'),'html.parser')
                    for element in soup.select('style,script'):element.decompose()
                    canonical_strings=list(soup.body.stripped_strings)
                    normalized=''.join(extracted.split());missing=[s for s in canonical_strings if ''.join(s.split()) not in normalized]
                    coverage.update(canonicalDomStrings=len(canonical_strings),missingCanonicalStrings=missing,canonicalDomIncludesRawMermaidCode=True,canonicalTextOrder=canonical_text_order(extracted,canonical_strings))
                    fresh_write(qa/'pypdf-extracted.txt',extracted.encode('utf-8'));json_write(qa/'text-coverage.json',coverage)
                    require(not coverage['missing'] and not coverage['multiplicityFailures'] and not missing and not coverage['canonicalTextOrder']['orderFailures'],'PDF incomplete or reordered literal text')
                    root=reader.trailer['/Root'];require(not any(k in root for k in ('/OpenAction','/AA','/AcroForm')),'active PDF catalog unsupported')
                    stage(destination,'poppler-all-pages',pages=len(reader.pages))
                    proc=subprocess.run([str(poppler),'-png','-r','110','-f','1','-l',str(len(reader.pages)),str(pdf),str(qa/'page')],capture_output=True,text=True,timeout=args.stage_timeout-5)
                    require(proc.returncode==0,'Poppler capture failed: '+proc.stderr[:1000])
                    images=sorted(qa.glob('page-*.png'));require(len(images)==len(reader.pages),'native PDF page count mismatch')
                    load_bound(args.binding,args.binding_sha256);tool(args.chromium,args.chromium_sha256);tool(args.poppler,args.poppler_sha256)
                    record['documents'].append({'documentId':entry['documentId'],'canonicalDocumentPath':entry['canonicalDocumentPath'],'markdownSha256':entry['markdownSha256'],'canonicalHtmlSha256':sha(html),'renderPinsSha256':entry['renderPinsSha256'],'renderManifestSha256':entry['renderManifestSha256'],'pdfPath':str(pdf),'pdfSha256':sha(data),'pages':len(reader.pages),'projection':projection,'geometry':geometry,'textCoverage':coverage,'pageImages':[{'path':str(p),'sha256':sha(safe_path(p).read_bytes())} for p in images],'allActualPagesViewed':False,'visualReview':'PENDING','formalQualityAssessed':False,'adoption':False})
                    stage(destination,'document-written',pages=len(reader.pages))
            finally:context.close();browser.close()
        record['status']='TEXT_CHECKED_ALL_NATIVE_PAGES_REVIEW_REQUIRED'
    except BaseException as exc:record.update(status='FAILED',error=str(exc));raise
    finally:
        faulthandler.cancel_dump_traceback_later();faulthandler.disable();fault.close()
        for k,v in oldenv.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        json_write(destination/'delivery-manifest.json',record)

def main():
    p=argparse.ArgumentParser();p.add_argument('--binding',type=Path,required=True);p.add_argument('--binding-sha256',required=True);p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--chromium',type=Path,required=True);p.add_argument('--chromium-sha256',required=True);p.add_argument('--poppler',type=Path,required=True);p.add_argument('--poppler-sha256',required=True)
    p.add_argument('--stage-timeout',type=int,default=90);p.add_argument('--total-timeout',type=int,default=900);p.add_argument('--pdf-marker-completed',action='store_true');p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args();require(args.pdf_marker_completed,'one-time root PDF marker must already have completed');require(30<=args.stage_timeout<=300 and args.stage_timeout<=args.total_timeout<=3600,'bounded timeout required')
    if args.worker:worker(args)
    else:supervise(args)
if __name__=='__main__':main()
