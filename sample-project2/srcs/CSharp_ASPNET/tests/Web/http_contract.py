"""Real HTTPS contracts against a newly created private fixture. Never prints credentials or bodies."""
import html, http.cookiejar, io, json, pathlib, re, ssl, sys, urllib.error, urllib.parse, urllib.request, uuid, zipfile
from datetime import datetime, timezone

root=pathlib.Path.cwd()
profile=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
base=profile["url"]
assert base=="https://localhost:7444"
assert re.fullmatch(r"SP2_WebFixture_Http_[a-f0-9]{12}",profile["database"])
results=[]

class Client:
    def __init__(self):
        self.cookies=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies),urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
        self.token=""
    def request(self,path,data=None,token=True,raw=None):
        headers={"Sec-Fetch-Mode":"navigate" if data is None and raw is None else "cors"}
        if data is not None or raw is not None:
            headers.update({"Content-Type":"application/json","X-SP2-User-Action":"true"})
            if token: headers["X-SP2-CSRF"]=self.token
        body=raw.encode() if raw is not None else json.dumps(data,ensure_ascii=True).encode() if data is not None else None
        try:
            with self.opener.open(urllib.request.Request(base+path,body,headers),timeout=40) as r: return r.status,r.read(),dict(r.headers)
        except urllib.error.HTTPError as e: return e.code,e.read(),dict(e.headers)
    def page(self,path):
        status,body,_=self.request(path);assert status==200
        text=body.decode()
        token=re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',text)
        if token:self.token=html.unescape(token.group(1))
        initial=re.search(r'data-initial="([^"]+)"',text)
        return json.loads(html.unescape(initial.group(1))) if initial else text
    def login(self):
        self.page("/account/login")
        data=urllib.parse.urlencode({"LoginId":"demostaff","Password":profile["staffPassword"],"__RequestVerificationToken":self.token}).encode()
        with self.opener.open(urllib.request.Request(base+"/account/login",data,{"Content-Type":"application/x-www-form-urlencoded","Sec-Fetch-Mode":"navigate"}),timeout=30) as r:assert r.status==200 and r.url.endswith("/menu")
        return self.page("/employees")

def check(name,call):
    try:call();results.append({"id":name,"status":"PASS"});print("PASS",name)
    except Exception as e:results.append({"id":name,"status":"FAIL","error":type(e).__name__});print("FAIL",name,type(e).__name__)
def expect(value,expected):assert value==expected,(value,expected)

c=Client();vm=c.login()
command={"stateId":vm["stateId"],"stateRevision":vm["stateRevision"]}
check("HTTP-01-missing-csrf",lambda:expect(c.request("/employees/clear",command,False)[0],400))
check("HTTP-02-unknown-field",lambda:expect(c.request("/employees/clear",{**command,"userId":"SP2ADMIN"})[0],400))
check("HTTP-03-missing-field",lambda:expect(c.request("/employees/clear",{"stateId":vm["stateId"]})[0],400))
check("HTTP-04-duplicate-field",lambda:expect(c.request("/employees/clear",raw=json.dumps(command)[:-1]+',"stateRevision":1}')[0],400))
check("HTTP-05-enum-unknown",lambda:expect(c.request("/employees/open",{"searchStateId":vm["stateId"],"stateRevision":vm["stateRevision"],"employeeId":None,"mode":"Administrator"})[0],400))
other=Client();other.login()
check("HTTP-06-session-ownership",lambda:expect(other.request("/employees/clear",command)[0],403))
check("HTTP-07-old-revision-no-mutation",lambda:(expect(c.request("/employees/clear",{**command,"stateRevision":999})[0],409),expect(c.request("/employees/clear",command)[0],200)))
vm=c.page("/employees")
status,body,_=c.request("/employees/open",{"searchStateId":vm["stateId"],"stateRevision":vm["stateRevision"],"employeeId":None,"mode":"New"});assert status==200
edit=json.loads(body)["edit"]
emoji="😀"
employee={"employeeNo":"007777","name":emoji*40,"kana":"カ"*80,"departmentCode":"01","employmentStatus":"01","joinDateRaw":"2024-04-01","careerSummary":emoji*1000,"skills":emoji*1000,"qualifications":emoji*1000,"selfPr":emoji*1000}
careers=[]
for i in range(20):
    careers.append({"careerId":None,"clientRowKey":str(uuid.uuid4()),"startMonthRaw":"2024-04","endMonthRaw":None,"companyName":emoji*100,"projectName":f"{i:02}"+emoji*98,"description":emoji*1000,"duties":emoji*1000,"achievements":emoji*1000,"technologies":emoji*500,"phases":emoji*200,"roleCode":"01","teamSizeRaw":"999"})
save={"editStateId":edit["editStateId"],"stateRevision":edit["stateRevision"],"employee":employee,"careers":careers,"removedCareerIds":[]}
assert len(json.dumps(save,ensure_ascii=True).encode())<2*1024*1024
status,body,_=c.request("/employees/save",save)
check("HTTP-08-escaped-maximum20-save",lambda:expect(status,200))
redirect=json.loads(body).get("redirect")
if redirect:
    saved=c.page(redirect)
    status,body,_=c.request("/employees/search",{"stateId":saved["stateId"],"stateRevision":saved["stateRevision"],"employeeNo":"007777","name":None,"department":None,"employmentStatus":None})
    found=json.loads(body)
    check("HTTP-09-maximum-saved-search",lambda:(expect(status,200),expect(len(found["rows"]),1)))
    export={"searchStateId":found["stateId"],"stateRevision":found["stateRevision"],"employeeId":found["rows"][0]["employeeId"],"operationId":str(uuid.uuid4())}
    check("HTTP-10-id-must-be-string",lambda:expect(c.request("/employees/export",{**export,"employeeId":int(export["employeeId"])})[0],400))
    status,book,headers=c.request("/employees/export",export)
    def workbook():
        expect(status,200);assert headers.get("Content-Type","").startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with zipfile.ZipFile(io.BytesIO(book)) as z:
            workbook_xml=z.read("xl/workbook.xml").decode();assert "職務経歴書" in workbook_xml and "案件経歴" in workbook_xml
            assert not any("externalLinks" in n or "vbaProject" in n for n in z.namelist())
        (root/".tmp"/"http-maximum.xlsx").write_bytes(book)
    check("HTTP-11-maximum20-response-xlsx",workbook)
    status,body,_=c.request("/employees/invalidate",{"stateId":found["stateId"],"stateRevision":found["stateRevision"]})
    invalid=json.loads(body)
    check("HTTP-12-old-result-disabled",lambda:expect(c.request("/employees/export",{**export,"stateRevision":invalid["stateRevision"]})[0],422))

out=root/"build"/"test-results"/"http-contract.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"executedUtc":datetime.now(timezone.utc).isoformat(),"passed":all(x["status"]=="PASS" for x in results),"tests":results,"scope":"real HTTPS, CSRF, strict body shape/IDs, owned state/revision, maximum JSON scalar aggregate and downloadable workbook; new isolated owned fixture only","unperformed":["terminal save success","SQL Server 2022 physical host","formal acceptance"]},ensure_ascii=False,indent=2),encoding="utf-8")
sys.exit(0 if all(x["status"]=="PASS" for x in results) else 1)
