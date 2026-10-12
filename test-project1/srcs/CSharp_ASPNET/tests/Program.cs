using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using StudentManagement.Core;
using StudentManagement.Web;

int checks=0;
void Check(bool condition,string name){if(!condition)throw new Exception("FAILED: "+name);checks++;}
string ErrorSummary(string html){var match=System.Text.RegularExpressions.Regex.Match(html,"<div\\b[^>]*class=\"[^\"]*\\bmessage\\s+error\\b[^\"]*\"[^>]*>([\\s\\S]*?)</div>");return match.Success?match.Value:"";}
bool EmptySummaryBullet(string html)=>System.Text.RegularExpressions.Regex.IsMatch(html,"<li[^>]*style=\"[^\"]*display\\s*:\\s*none[^\"]*\"[^>]*>\\s*</li>");
async Task Fault(Func<Task> action,int status,string name){try{await action();throw new Exception("EXPECTED: "+name);}catch(WebFault f){Check(f.Status==status,name);}}
var unknown=JsonSerializer.SerializeToElement(WebPresentation.Save(new SaveResult(Outcome.Unknown,null,null,[])));Check(unknown.GetProperty("retryBySearch").GetBoolean()&&!unknown.GetProperty("message").GetString()!.Contains("保存しました"),"unknown save never reports success");
var user=new CurrentUser("alice","session",Role.Staff);var store=new SearchContextStore();var entry=store.Create(user,"tab");Check(entry.Id.Length==64&&entry.Id.All(Uri.IsHexDigit),"256bit hex context");
await Fault(()=>Task.Run(()=>store.Get(entry.Id,new("bob","session",Role.Staff),"tab")),403,"other principal rejected");
await Fault(()=>Task.Run(()=>store.Get(entry.Id,new("alice","other",Role.Staff),"tab")),403,"other session rejected");
await Fault(()=>Task.Run(()=>store.Get(entry.Id,user,"other")),403,"other tab rejected");
entry.Expires=DateTimeOffset.UtcNow.AddSeconds(-1);await Fault(()=>Task.Run(()=>store.Get(entry.Id,user)),409,"expired context rejected");entry.Expires=DateTimeOffset.UtcNow.AddMinutes(30);
await Fault(()=>store.Use(new(){ContextId=entry.Id,ContextRevision="0"},user,"tab",e=>Task.FromResult(0),default),409,"stale revision rejected");
var first=new ContextRequest{ContextId=entry.Id,ContextRevision="1"};await store.Use(first,user,"tab",e=>{e.Revision++;return Task.FromResult(0);},default);await Fault(()=>store.Use(first,user,"tab",e=>Task.FromResult(0),default),409,"reused revision rejected");
await Fault(()=>store.Use(new(){ContextId=entry.Id},user,"tab",e=>Task.FromResult(0),default),409,"R74-13 missing revision rejected");
var parallelEntry=store.Create(user,"parallel-tab");
async Task<int> ConcurrentUse(){try{return await store.Use(new(){ContextId=parallelEntry.Id,ContextRevision="1"},user,"parallel-tab",async e=>{await Task.Yield();e.Revision++;return 200;},default);}catch(WebFault f){return f.Status;}}
var parallel=await Task.WhenAll(ConcurrentUse(),ConcurrentUse());Check(parallel.Count(v=>v==200)==1&&parallel.Count(v=>v==409)==1,"R74-13 exactly one concurrent revision mutation");
Check(IdParser.Required("9007199254740993","id")==9007199254740993L,"ID beyond JS safe integer");Check(IdParser.Required(long.MaxValue.ToString(),"id")==long.MaxValue,"max bigint");await Fault(()=>Task.Run(()=>IdParser.Required("9223372036854775808","id")),422,"bigint overflow rejected");await Fault(()=>Task.Run(()=>IdParser.Required("1e3","id")),422,"exponent ID rejected");

var builder=WebApplication.CreateBuilder(new WebApplicationOptions{EnvironmentName="Development",ApplicationName=typeof(StudentsController).Assembly.FullName});
builder.WebHost.UseUrls("https://127.0.0.1:0");builder.Logging.ClearProviders();builder.Configuration.AddInMemoryCollection(new Dictionary<string,string?>{{"AllowedHosts","127.0.0.1"},{"EvaluationSession:Secret","mvc-contract-key"},{"EvaluationSession:Role","Staff"}});
WebHostSetup.Add(builder);var fake=new FakeService();builder.Services.AddSingleton<IStudentService>(fake);var app=builder.Build();WebHostSetup.Use(app);app.MapControllers();await app.StartAsync();
try{
 using var client=new HttpClient(new HttpClientHandler{UseCookies=false,UseProxy=false,AllowAutoRedirect=false,ServerCertificateCustomValidationCallback=HttpClientHandler.DangerousAcceptAnyServerCertificateValidator}){BaseAddress=new Uri(app.Urls.Single())};var cookies=new Dictionary<string,string>();
 void Collect(HttpResponseMessage r){if(r.Headers.TryGetValues("Set-Cookie",out var vs))foreach(var v in vs){var p=v.Split(';')[0].Split('=',2);cookies[p[0]]=p[1];}client.DefaultRequestHeaders.Remove("Cookie");if(cookies.Count>0)client.DefaultRequestHeaders.Add("Cookie",string.Join("; ",cookies.Select(p=>p.Key+"="+p.Value)));}
 string Field(string html,string name){var m=System.Text.RegularExpressions.Regex.Match(html,"<input[^>]*name=\""+System.Text.RegularExpressions.Regex.Escape(name)+"\"[^>]*value=\"([^\"]*)\"");if(!m.Success)throw new Exception("Missing rendered field "+name);return WebUtility.HtmlDecode(m.Groups[1].Value);}
 async Task<(HttpResponseMessage Response,string Html)> Get(string url){var r=await client.GetAsync(url);Collect(r);return(r,await r.Content.ReadAsStringAsync());}
 async Task<(HttpResponseMessage Response,string Html)> Post(string url,Dictionary<string,string> values){var r=await client.PostAsync(url,new FormUrlEncodedContent(values.Concat(values.ContainsKey("__Invariant")?[new KeyValuePair<string,string>("__Invariant","Criteria.AdmissionTo")]:[])));Collect(r);return(r,await r.Content.ReadAsStringAsync());}
 var anonymous=await Get("/students");Check(anonymous.Response.StatusCode==HttpStatusCode.Unauthorized,"anonymous MVC denied");
 client.DefaultRequestHeaders.Add("X-Evaluation-Secret","mvc-contract-key");var login=await client.PostAsync("/_evaluation/session",null);Collect(login);Check(login.StatusCode==HttpStatusCode.OK,"server evaluation identity");client.DefaultRequestHeaders.Remove("X-Evaluation-Secret");
 var screen=await Get("/students");Check(screen.Response.StatusCode==HttpStatusCode.OK,"Razor search renders");Check(screen.Html.Contains("SRC-012")&&screen.Html.Contains("検索条件"),"all search filters render");
 Check(ErrorSummary(screen.Html)=="","UI-OBS-MVC-001 initial search has no empty error panel");Check(!EmptySummaryBullet(screen.Html),"initial search has no empty summary bullet");
 var context=Field(screen.Html,"ContextId");var revision=Field(screen.Html,"ContextRevision");var tab=Field(screen.Html,"TabId");var csrf=Field(screen.Html,"__RequestVerificationToken");
 Dictionary<string,string> Values(string rev)=>new(){{"ContextId",context},{"ContextRevision",rev},{"TabId",tab},{"PageSize","20"},{"SortKey","studentNo"},{"SortDirection","asc"},{"Criteria.StudentNo",""},{"Criteria.Name",""},{"Criteria.Kana",""},{"__Invariant","Criteria.AdmissionFrom"}};
 var noCsrf=await Post("/students/search",Values(revision));Check(noCsrf.Response.StatusCode==HttpStatusCode.BadRequest,"MVC CSRF enforced");
 var values=Values(revision);values["__RequestVerificationToken"]=csrf;var searched=await Post("/students/search",values);Check(searched.Response.StatusCode==HttpStatusCode.OK,"MVC search submits actual="+searched.Response.StatusCode+" body="+searched.Html);Check(fake.LastCriteria!.EnrollmentStatusCodes.Length==0,"all-off statuses stay all-off");Check(searched.Html.Contains("9007199254740993")&&WebUtility.HtmlDecode(searched.Html).Contains("平成20年05月15日"),"big ID and wareki render");Check(searched.Response.Headers.CacheControl?.NoStore==true&&searched.Response.Headers.Contains("Content-Security-Policy"),"cache and CSP headers");
 var stale=await Post("/students/search",values);Check(stale.Response.StatusCode==HttpStatusCode.Conflict,"stale search revision rejected");
 Check(WebUtility.HtmlDecode(ErrorSummary(stale.Html)).Contains("検索状態が更新されています。"),"actual global validation message remains visible");
 var missingValues=Values(revision);missingValues.Remove("ContextRevision");missingValues["__RequestVerificationToken"]=csrf;var missing=await Post("/students/search",missingValues);Check(missing.Response.StatusCode==HttpStatusCode.Conflict,"missing search revision rejected");
 var missingReturn=await Get("/students?contextId="+context);Check(missingReturn.Response.StatusCode==HttpStatusCode.Conflict,"return never substitutes latest revision");
 var current=Field(searched.Html,"ContextRevision");var resumed=await Get("/students?contextId="+context+"&contextRevision="+current);Check(resumed.Response.StatusCode==HttpStatusCode.OK,"return uses received revision");
 var clearValues=new Dictionary<string,string>{{"ContextId",context},{"ContextRevision",Field(resumed.Html,"ContextRevision")},{"TabId",tab},{"__RequestVerificationToken",Field(resumed.Html,"__RequestVerificationToken")}};
 var clear=await Post("/students/clear",clearValues);Check(clear.Response.StatusCode==HttpStatusCode.OK&&clear.Html.Contains("未検索"),"clear returns unsearched");
 var edit=await Get("/students/new?returnContextId="+context);Check(edit.Response.StatusCode==HttpStatusCode.OK,"Razor registration renders");Check(edit.Html.Contains("REG-023")&&edit.Html.Contains("REG-024")&&edit.Html.Contains("BirthDateInput.Era"),"full registration fields and raw wareki");
 Check(ErrorSummary(edit.Html)=="","new screen has no empty error panel");Check(!EmptySummaryBullet(edit.Html),"new screen has no empty summary bullet");
 var existingEdit=await Get("/students/9007199254740993?returnContextId="+context);Check(existingEdit.Response.StatusCode==HttpStatusCode.OK&&ErrorSummary(existingEdit.Html)=="","existing edit has no empty error panel");Check(!EmptySummaryBullet(existingEdit.Html),"existing edit has no empty summary bullet");
 var invalidCriteria=Values(Field(clear.Html,"ContextRevision"));invalidCriteria["Criteria.SchoolYear"]="invalid-year";invalidCriteria["__RequestVerificationToken"]=Field(clear.Html,"__RequestVerificationToken");var invalidBound=await Post("/students/search",invalidCriteria);Check((int)invalidBound.Response.StatusCode==422&&WebUtility.HtmlDecode(ErrorSummary(invalidBound.Html)).Contains("invalid-year"),"real model binding validation remains visible");
 fake.NextSave=new SaveResult(Outcome.ValidationFailed,null,null,[new("REG-002","E-STU-001","撮影契約テストの入力エラーです。")]);
 var validation=await Post("/students/create",new(){{"SnapshotId",Field(edit.Html,"SnapshotId")},{"Input.ReturnContextId",context},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}});Check((int)validation.Response.StatusCode==422&&WebUtility.HtmlDecode(ErrorSummary(validation.Html)).Contains("撮影契約テストの入力エラーです。"),"service field validation remains visible in the actual Razor summary");fake.NextSave=null;
 var reset=await Post("/students/reset",new(){{"SnapshotId",Field(edit.Html,"SnapshotId")},{"StudentId",""},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}});Check(reset.Response.StatusCode==HttpStatusCode.OK&&WebUtility.HtmlDecode(reset.Html).Contains("入力を読込時の値へ戻しました。")&&reset.Html.Contains("class=\"message info\""),"normal reset information remains visible");Check(ErrorSummary(reset.Html)=="","reset information does not create an empty error panel");
 var other=await Get("/students");var forged=new Dictionary<string,string>{{"SnapshotId",Field(edit.Html,"SnapshotId")},{"Input.ReturnContextId",Field(other.Html,"ContextId")},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}};var tamper=await Post("/students/create",forged);Check(tamper.Response.StatusCode==HttpStatusCode.Forbidden,"editor return context cannot be replaced");
}finally{await app.StopAsync();await app.DisposeAsync();}
Console.WriteLine($"MVC contract checks: {checks} passed (fake service; no SQL Server integration).");

sealed class FakeService:IStudentService
{
    public SearchCriteria? LastCriteria;
    public SaveResult? NextSave;
    private static StudentRow Row=>new(9007199254740993,"S2026-0001","見本 太郎","ミホン タロウ",new(2008,5,15),2026,"学年なし","C-A","Aクラス","在学","東京都見本町","0300000000",new(2026,4,1),DateTimeOffset.UtcNow,2);
    public Task<SearchResult> SearchAsync(SearchCriteria c,CancellationToken ct=default){LastCriteria=c;return Task.FromResult(new SearchResult(Outcome.Saved,1,[Row],DateTimeOffset.UtcNow,false,[]));}
    public Task<StudentDetail?> GetAsync(long id,CancellationToken ct=default)=>Task.FromResult<StudentDetail?>(new(id,2,new StudentDraft(),new(2008,5,15),DateTimeOffset.UtcNow,"alice"));
    public Task<LookupSet> LookupAsync(CancellationToken ct=default)=>Task.FromResult(new LookupSet([new("GENDER","0","未回答",0,true,new(1900,1,1),null,true),new("GRADE","00","学年なし",0,true,new(1900,1,1),null,true),new("ENROLLMENT_STATUS","01","在学",0,true,new(1900,1,1),null,true)], [new(1,2026,"00","C-A","Aクラス",new(2026,4,1),new(2027,3,31),40,1,true)]));
    public Task<SaveResult> SaveAsync(SaveRequest r,CancellationToken ct=default)=>Task.FromResult(NextSave??new SaveResult(Outcome.Saved,9007199254740993,2,[]));
    public Task<SaveResult> DeleteAsync(long id,long version,string reason,CancellationToken ct=default)=>Task.FromResult(new SaveResult(Outcome.Saved,id,version+1,[]));
}
