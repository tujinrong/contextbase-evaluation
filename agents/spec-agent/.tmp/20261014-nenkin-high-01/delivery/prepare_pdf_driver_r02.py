"""Fresh code candidate only; no writer/browser/process supervisor is executed."""
import ast,hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
p=D/'export_pdf_bound_r01.py';raw=p.read_bytes();text=raw.decode().replace('\r\n','\n')
text=text.replace('import argparse,ctypes,faulthandler,hashlib,io,json,os,subprocess,sys,time','import argparse,ctypes,faulthandler,hashlib,io,json,os,queue,subprocess,sys,threading,time',1)
helper='''
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

'''
text=text.replace('\nclass OwnedWindowsJob:',helper+'\nclass OwnedWindowsJob:',1)
text=text.replace('def __init__(self,pid):','def __init__(self,pid,expected_creation_time):',1)
old="        process=self.k.OpenProcess(0x0100|0x0001,False,pid);require(bool(process),'owned worker process handle failed')\n        try:require(self.k.AssignProcessToJobObject(self.handle,process),'owned worker job assignment failed')\n"
new="        process=self.k.OpenProcess(0x0100|0x0001|0x1000,False,pid);require(bool(process),'owned worker process handle failed')\n        try:\n            require(creation_time(self.k,process)==expected_creation_time,'worker PID creation-time mismatch')\n            require(self.k.AssignProcessToJobObject(self.handle,process),'owned worker job assignment failed')\n"
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('stdin=subprocess.PIPE,env=env)','stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=env)',1)
old="        job=OwnedWindowsJob(process.pid);require(process.poll() is None,'worker exited before ownership handshake')\n"
new="""        lines=queue.Queue()
        def relay():
            for line in iter(process.stdout.readline,b''):lines.put(line);sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
            lines.put(None)
        threading.Thread(target=relay,daemon=True).start()
        ready_raw=lines.get(timeout=args.stage_timeout);require(bool(ready_raw),'worker exited without READY')
        ready=json.loads(ready_raw.decode('utf-8'))
        require(ready.get('stage')=='OWNED_WORKER_READY' and ready.get('pid')==process.pid and type(ready.get('creationTime')) is int,'invalid owned worker READY')
        require(process.poll() is None,'worker exited before ownership handshake')
        job=OwnedWindowsJob(process.pid,ready['creationTime']);require(process.poll() is None,'worker exited after job assignment')
"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("'pid':process.pid,'windowsJobKillOnClose':True","'pid':process.pid,'processCreationTime':ready['creationTime'],'windowsJobKillOnClose':True",1)
text=text.replace("def worker(args):\n    require(sys.stdin.buffer.readline(4)==b'GO\\n'","def worker(args):\n    worker_ready()\n    require(sys.stdin.buffer.readline(4)==b'GO\\n'",1)
old="fresh_write(destination/'HTML'/relative.with_suffix('.html'),html);fresh_write(destination/'Markdown'/relative,entry['rawMarkdown'].encode('utf-8'))"
new="source_md=safe_path(entry['markdown']).read_bytes();require(sha(source_md)==entry['markdownSha256'],'source Markdown changed before exact copy')\n                    fresh_write(destination/'HTML'/relative.with_suffix('.html'),html);fresh_write(destination/'Markdown'/relative,source_md)"
assert text.count(old)==1;text=text.replace(old,new)
ast.parse(text);out=D/'export_pdf_bound_r02.py'
with out.open('xb') as h:h.write(text.encode('utf-8'))
assert p.read_bytes()==raw
result={'scope':'PDF_DRIVER_CODE_PREPARATION_ONLY','source':{'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()},'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'corrections':['exact source Markdown bytes, including BOM','READY pid+public GetProcessTimes creation-time match before owned job assignment','GO only after confirmed owned job; no browser descendants before GO'],'actualPdfCreated':0,'browserStarted':0,'workerStarted':0,'providerExecuted':0,'markerExecuted':0,'status':'PREPARED_PENDING_INDEPENDENT_REVIEW_AND_SYNTHETIC_CHECKS','limitations':['Actual job assignment/browser ancestry and native page output remain unexecuted.','Package/module input dependencies must be pinned independently before use.']}
record=O/'pdf-driver-r02-preparation.json'
with record.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'driver':str(out),'sha256':result['candidate']['sha256'],'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest()}))
