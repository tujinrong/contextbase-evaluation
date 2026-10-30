"""New owned fixture + unchanged-publish observer host. No production application writes."""
from pathlib import Path
import json,hashlib,os,subprocess,threading,queue,time,urllib.request,ssl
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2];DB='SP2_WebFixture_ADDITIONAL_R20261030';URL='https://localhost:5184'
PROFILE=ROOT/'.tmp/additional-ui-runtime/profile.json';profile=json.loads(PROFILE.read_text(encoding='utf-8-sig'));assert profile['database']==DB and profile['url']==URL
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def artifact():
    return json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {hashArtifact} from './agents/builds/build-agent/scripts/ui-conformance.mjs';console.log(JSON.stringify(hashArtifact('sample-project2/srcs/CSharp_ASPNET/build/publish')));"],cwd=REPO,text=True))
def sql(query):
    guard="SET NOCOUNT ON; IF DB_NAME()<>N'"+DB+"' THROW 51000,'Wrong additional fixture',1; IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Wrong owner',1; "
    r=subprocess.run(['sqlcmd','-S',r'.\SQLEXPRESS','-E','-C','-b','-d',DB,'-f','65001','-y','0','-Q',guard+query],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf8',errors='replace') or r.stdout.decode('utf8',errors='replace'))
    return r.stdout.decode('utf-8-sig').strip()
def rows(query):return json.loads(''.join(sql(query+' FOR JSON PATH,INCLUDE_NULL_VALUES;').splitlines()))
def counter():
    return rows("SELECT q.execution_count,CONVERT(varchar(130),q.plan_handle,1) AS plan_token,q.statement_start_offset,q.statement_end_offset,CONVERT(varchar(33),q.creation_time,126) AS creation_time FROM sys.dm_exec_query_stats q CROSS APPLY sys.dm_exec_sql_text(q.sql_handle)t CROSS APPLY sys.dm_exec_plan_attributes(q.plan_handle)a WHERE a.attribute='dbid' AND CONVERT(int,a.value)=DB_ID() AND t.text LIKE '%SELECT e.employee_id,e.employee_no%' AND t.text LIKE '%ORDER BY e.employee_no;%' AND t.text NOT LIKE '%sys.dm_exec_query_stats%'")
def delta(before,after):
    key=lambda r:(r['plan_token'],r['statement_start_offset'],r['statement_end_offset'],r['creation_time'])
    b={key(r):r['execution_count'] for r in before};a={key(r):r['execution_count'] for r in after}
    if not b or not b.keys()<=a.keys() or any(a[k]<v for k,v in b.items()):raise AssertionError('SQL cache unavailable/recreated: no zero/one claim')
    return sum(a.values())-sum(b.values())
class Observer:
    def __init__(self):
        env=os.environ.copy();env.update(SP2_DATABASE=DB,SP2_FIXTURE='true',SP2_CONNECTION_STRING=profile['connectionString'],SP2_DATA_KEYS=profile['keys'],ASPNETCORE_URLS=URL,ASPNETCORE_ENVIRONMENT='Production',DOTNET_ENVIRONMENT='Production',ASPNETCORE_APPLICATIONNAME='CareerManagement.Web',ASPNETCORE_CONTENTROOT=str(ROOT/'build/publish'),ASPNETCORE_Kestrel__Certificates__Default__Path=profile['certificate'],ASPNETCORE_Kestrel__Certificates__Default__Password=profile['certificatePassword'])
        self.dll=ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll';self.events=queue.Queue();self.lines=[]
        self.process=subprocess.Popen(['dotnet',str(self.dll),str(ROOT/'build/publish')],cwd=ROOT/'build/publish',env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8')
        def read():
            for line in self.process.stdout:
                self.lines.append(line)
                if line.startswith('OBSERVER:'):self.events.put(json.loads(line[len('OBSERVER:'):]))
        self.thread=threading.Thread(target=read,daemon=True);self.thread.start()
        try:
            self.ready=self.events.get(timeout=35);assert self.ready['kind']=='ready',self.ready
            started=subprocess.check_output(['powershell','-NoProfile','-NonInteractive','-Command',f"(Get-Process -Id {self.process.pid}).StartTime.ToUniversalTime().ToString('o')"],text=True).strip()
            self.ownership={'pid':self.process.pid,'startedAt':started,'database':DB,'productFile':str(self.dll),'productSha256':sha(self.dll),'measuredProductFile':self.ready['productFile'],'measuredProductSha256':self.ready['productSha256'],'profileSha256':sha(PROFILE),'url':URL}
            (PROFILE.parent/'owned-host.json').write_text(json.dumps(self.ownership,indent=2)+'\n',encoding='utf8')
            for _ in range(50):
                try:
                    with urllib.request.urlopen(URL+'/account/login',context=ssl._create_unverified_context(),timeout=1) as r:assert r.status==200
                    break
                except Exception:
                    if self.process.poll() is not None:raise RuntimeError('Observer host exited: '+''.join(self.lines))
                    time.sleep(.1)
            else:raise RuntimeError('Observer HTTPS listener did not become ready')
        except BaseException:
            if self.process.poll() is None:self.process.kill();self.process.wait(timeout=10)
            raise
    def snapshot(self,id):
        self.process.stdin.write(json.dumps({'command':'snapshot','stateId':id})+'\n');self.process.stdin.flush();r=self.events.get(timeout=10);assert r['kind']=='snapshot' and r['found'] and r['stateId']==id,r;return r
    def sql_counters(self):
        self.process.stdin.write('{"command":"sqlCounters"}\n');self.process.stdin.flush();r=self.events.get(timeout=10);assert r['kind']=='sqlCounters',r;assert r['snapshot']['callbackFailures']==0,r;return r['snapshot']
    def stop(self):
        if self.process.poll() is None:
            self.process.stdin.write('{"command":"stop"}\n');self.process.stdin.flush();r=self.events.get(timeout=10);assert r['kind']=='stopping',r;self.process.wait(timeout=20)
        (PROFILE.parent/'observer-stdout.log').write_text(''.join(self.lines),encoding='utf8');return {'pid':self.process.pid,'exitCode':self.process.returncode,'stopped':self.process.poll() is not None,'databaseDroppedOrReset':False}
