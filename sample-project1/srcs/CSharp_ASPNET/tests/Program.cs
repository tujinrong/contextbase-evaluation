using System.Net;
using System.Security.Claims;
using Microsoft.AspNetCore.Http;
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
string ErrorSummary(string html){var match=System.Text.RegularExpressions.Regex.Match(html,"<div\\b[^>]*class=\"[^\"]*(?:\\bmessage\\s+error\\b|\\berror-summary\\b)[^\"]*\"[^>]*>([\\s\\S]*?)</div>");return match.Success?match.Value:"";}
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

// Reject every incompatible state before any operation can invoke the repository or mutate state.
var http=new DefaultHttpContext();http.User=new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier,"alice"),new Claim("login_session","session"),new Claim(ClaimTypes.Role,"Staff")],"test"));
var schemaService=new FakeService();var coordinator=new WebStudentCoordinator(schemaService,new RequestIdentity(new HttpContextAccessor{HttpContext=http}),store);
foreach(var schema in new string?[]{null,"8.0","unknown"}) foreach(var operation in new[]{"search","page","clear","resume"}) {
 var old=store.Create(user,"schema-tab");old.SchemaVersion=schema;old.Applied=SearchCriteria.FromRaw("OLD",null,null,[]);old.Draft=new(){StudentNo="OLD"};old.LastResult=new(Outcome.NoChange,0,[],DateTimeOffset.UtcNow,false,[]);
 var applied=old.Applied;var raw=old.Draft;var last=old.LastResult;var expires=old.Expires;var calls=schemaService.SearchCalls;
 var request=new ContextRequest{ContextId=old.Id,ContextRevision="1"};
 try {
  _=operation switch {"search"=>await coordinator.Search(new(){ContextId=old.Id,ContextRevision="1",Criteria=new(){StudentNo="NEW"}},"schema-tab",default),"page"=>await coordinator.Page(new(){ContextId=old.Id,ContextRevision="1"},"schema-tab",default),"clear"=>await coordinator.Clear(request,"schema-tab",default),_=>await coordinator.Resume(request,"schema-tab",default)};
  throw new Exception("incompatible schema accepted");
 } catch(WebFault f) {Check(f.Status==409&&f.MessageId=="E-SRC-002"&&f.Message=="検索仕様が更新されました。条件を再指定して検索してください。","schema rejected: "+schema+"/"+operation);}
 Check(old.Revision==1&&ReferenceEquals(old.Applied,applied)&&ReferenceEquals(old.Draft,raw)&&ReferenceEquals(old.LastResult,last)&&old.Expires==expires&&schemaService.SearchCalls==calls,"schema rejection leaves all state untouched: "+schema+"/"+operation);
 var fresh=store.Create(user,"schema-tab");Check(fresh.Id!=old.Id&&fresh.SchemaVersion=="8.1"&&fresh.Revision==1&&fresh.Applied is null&&fresh.Draft.StatusCodes.SequenceEqual(new[]{"01","02"}),"fresh state resets incompatible schema");
 await Fault(()=>Task.Run(()=>store.Get(old.Id,user,"schema-tab")),409,"fresh initialization invalidates old context");
}
var shrink=store.Create(user,"shrink-tab");shrink.Applied=new(){Page=3,PageSize=20,StatusCodes=[]};shrink.Draft=new(){Name="原入力"};
var shrunk=StudentSearchPageModel.Json(await coordinator.Resume(new(){ContextId=shrink.Id,ContextRevision="1"},"shrink-tab",default));
Check(shrunk.GetProperty("page").GetInt32()==1&&shrink.Applied.Page==1&&schemaService.LastCriteria!.Page==1&&shrink.Draft.Name=="原入力","resume clamps reduced result page and preserves raw input");
var dto=StudentSearchPageModel.Json(WebStudentCoordinator.Present(store.Create(user),new(Outcome.NoChange,1,[new(9007199254740993,"S1","氏名","カナ",new(2008,5,15),2026,"1年","A","A組","在学")],DateTimeOffset.UtcNow,false,[])));
var row=dto.GetProperty("items")[0];Check(row.GetProperty("studentId").GetString()=="9007199254740993","search DTO preserves exact bigint");
foreach(var forbidden in new[]{"addressDisplay","address","phoneNumber","admissionDate","updatedAt","rowVersion","emailAddress","remarks"})Check(!row.TryGetProperty(forbidden,out _),"search DTO excludes "+forbidden);
Check(dto.GetProperty("schemaVersion").GetString()=="8.1"&&dto.GetProperty("criteria").EnumerateObject().Select(p=>p.Name).Order().SequenceEqual(new[]{"classId","nameKey","statusCodes","studentNoPrefix"}),"presented normalized criteria has only four conditions");

var builder=WebApplication.CreateBuilder(new WebApplicationOptions{EnvironmentName="Development",ApplicationName=typeof(StudentsController).Assembly.FullName});
builder.WebHost.UseUrls("https://127.0.0.1:0");builder.Logging.ClearProviders();builder.Configuration.AddInMemoryCollection(new Dictionary<string,string?>{{"AllowedHosts","127.0.0.1"},{"EvaluationSession:Secret","mvc-contract-key"},{"EvaluationSession:Role","Staff"}});
WebHostSetup.Add(builder);var fake=new FakeService();builder.Services.AddSingleton<IStudentService>(fake);var app=builder.Build();WebHostSetup.Use(app);app.MapControllers();await app.StartAsync();
try{
 using var client=new HttpClient(new HttpClientHandler{UseCookies=false,UseProxy=false,AllowAutoRedirect=false,ServerCertificateCustomValidationCallback=HttpClientHandler.DangerousAcceptAnyServerCertificateValidator}){BaseAddress=new Uri(app.Urls.Single())};var cookies=new Dictionary<string,string>();
 void Collect(HttpResponseMessage r){if(r.Headers.TryGetValues("Set-Cookie",out var vs))foreach(var v in vs){var p=v.Split(';')[0].Split('=',2);cookies[p[0]]=p[1];}client.DefaultRequestHeaders.Remove("Cookie");if(cookies.Count>0)client.DefaultRequestHeaders.Add("Cookie",string.Join("; ",cookies.Select(p=>p.Key+"="+p.Value)));}
 string Field(string html,string name){var m=System.Text.RegularExpressions.Regex.Match(html,"<input[^>]*name=\""+System.Text.RegularExpressions.Regex.Escape(name)+"\"[^>]*value=\"([^\"]*)\"");if(!m.Success)throw new Exception("Missing rendered field "+name);return WebUtility.HtmlDecode(m.Groups[1].Value);}
 async Task<(HttpResponseMessage Response,string Html)> Get(string url){var r=await client.GetAsync(url);Collect(r);return(r,await r.Content.ReadAsStringAsync());}
 async Task<(HttpResponseMessage Response,string Html)> Post(string url,Dictionary<string,string> values){var r=await client.PostAsync(url,new FormUrlEncodedContent(values));Collect(r);return(r,await r.Content.ReadAsStringAsync());}
 var anonymous=await Get("/students");Check(anonymous.Response.StatusCode==HttpStatusCode.Unauthorized,"anonymous MVC denied");
 client.DefaultRequestHeaders.Add("X-Evaluation-Secret","mvc-contract-key");var login=await client.PostAsync("/_evaluation/session",null);Collect(login);Check(login.StatusCode==HttpStatusCode.OK,"server evaluation identity");client.DefaultRequestHeaders.Remove("X-Evaluation-Secret");
 var screen=await Get("/students");Check(screen.Response.StatusCode==HttpStatusCode.OK,"Razor search renders");Check(screen.Html.Contains("SRC-006")&&screen.Html.Contains("検索条件")&&!screen.Html.Contains("Criteria.Kana")&&!screen.Html.Contains("Criteria.SchoolYear"),"four search filters render");
 Check(ErrorSummary(screen.Html)=="","UI-OBS-MVC-001 initial search has no empty error panel");Check(!EmptySummaryBullet(screen.Html),"initial search has no empty summary bullet");
 var context=Field(screen.Html,"ContextId");var revision=Field(screen.Html,"ContextRevision");var tab=Field(screen.Html,"TabId");var csrf=Field(screen.Html,"__RequestVerificationToken");
 Dictionary<string,string> Values(string rev)=>new(){{"ContextId",context},{"ContextRevision",rev},{"TabId",tab},{"PageSize","20"},{"SortKey","studentNo"},{"SortDirection","asc"},{"Criteria.StudentNo",""},{"Criteria.Name",""}};
 var noCsrf=await Post("/students/search",Values(revision));Check(noCsrf.Response.StatusCode==HttpStatusCode.BadRequest,"MVC CSRF enforced");
 var values=Values(revision);values["__RequestVerificationToken"]=csrf;var searched=await Post("/students/search",values);Check(searched.Response.StatusCode==HttpStatusCode.OK,"MVC search submits actual="+searched.Response.StatusCode+" body="+searched.Html);Check(fake.LastCriteria!.StatusCodes.Length==0,"all-off statuses stay all-off");Check(searched.Html.Contains("9007199254740993")&&WebUtility.HtmlDecode(searched.Html).Contains("平成20年05月15日"),"big ID and wareki render");Check(searched.Response.Headers.CacheControl?.NoStore==true&&searched.Response.Headers.Contains("Content-Security-Policy"),"cache and CSP headers");
 var stale=await Post("/students/search",values);Check(stale.Response.StatusCode==HttpStatusCode.Conflict,"stale search revision rejected");
 Check(WebUtility.HtmlDecode(ErrorSummary(stale.Html)).Contains("検索状態が更新されています。"),"actual global validation message remains visible");
 var missingValues=Values(revision);missingValues.Remove("ContextRevision");missingValues["__RequestVerificationToken"]=csrf;var missing=await Post("/students/search",missingValues);Check(missing.Response.StatusCode==HttpStatusCode.Conflict,"missing search revision rejected");
 var missingReturn=await Get("/students?contextId="+context);Check(missingReturn.Response.StatusCode==HttpStatusCode.Conflict,"return never substitutes latest revision");
 var current=Field(searched.Html,"ContextRevision");var resumed=await Get("/students?contextId="+context+"&contextRevision="+current);Check(resumed.Response.StatusCode==HttpStatusCode.OK,"return uses received revision");
 var clearValues=new Dictionary<string,string>{{"ContextId",context},{"ContextRevision",Field(resumed.Html,"ContextRevision")},{"TabId",tab},{"__RequestVerificationToken",Field(resumed.Html,"__RequestVerificationToken")}};
 var clear=await Post("/students/clear",clearValues);Check(clear.Response.StatusCode==HttpStatusCode.OK&&clear.Html.Contains("未検索"),"clear returns unsearched");
 var edit=await Get("/students/new?returnContextId="+context);Check(edit.Response.StatusCode==HttpStatusCode.OK,"Razor registration renders actual="+edit.Response.StatusCode+" body="+edit.Html);Check(edit.Html.Contains("REG-023")&&edit.Html.Contains("REG-024")&&edit.Html.Contains("BirthDateInput.Era"),"full registration fields and raw wareki");
 Check(ErrorSummary(edit.Html)=="","new screen has no empty error panel");Check(!EmptySummaryBullet(edit.Html),"new screen has no empty summary bullet");
 var existingEdit=await Get("/students/9007199254740993?returnContextId="+context);Check(existingEdit.Response.StatusCode==HttpStatusCode.OK&&ErrorSummary(existingEdit.Html)=="","existing edit has no empty error panel");Check(!EmptySummaryBullet(existingEdit.Html),"existing edit has no empty summary bullet");
 foreach(var size in new[]{"0","-1","21"}) {
  var badSize=Values(Field(clear.Html,"ContextRevision"));badSize["PageSize"]=size;badSize["Criteria.Name"]="保持確認";badSize["__RequestVerificationToken"]=Field(clear.Html,"__RequestVerificationToken");var calls=fake.SearchCalls;var rejectedSize=await Post("/students/search",badSize);Check((int)rejectedSize.Response.StatusCode==422&&fake.SearchCalls==calls&&WebUtility.HtmlDecode(ErrorSummary(rejectedSize.Html)).Contains("表示件数")&&WebUtility.HtmlDecode(rejectedSize.Html).Contains("保持確認"),"invalid page size re-renders raw input safely: "+size);
 }
 var invalidCriteria=Values(Field(clear.Html,"ContextRevision"));invalidCriteria["Criteria.ClassId"]="invalid-class";invalidCriteria["__RequestVerificationToken"]=Field(clear.Html,"__RequestVerificationToken");var invalidBound=await Post("/students/search",invalidCriteria);Check((int)invalidBound.Response.StatusCode==422&&invalidBound.Html.Contains("invalid-class"),"invalid class raw input remains visible");
 foreach(var removed in new[]{"Kana","SchoolYear","GradeCode","UnassignedOnly","PrefectureCode","PhoneNumber","AdmissionFrom","AdmissionTo","Unexpected"}) {
  var bad=Values(Field(clear.Html,"ContextRevision"));bad["Criteria."+removed]="";bad["Criteria.Name"]="入力保持";bad["__RequestVerificationToken"]=Field(clear.Html,"__RequestVerificationToken");var calls=fake.SearchCalls;var rejected=await Post("/students/search",bad);
  Check((int)rejected.Response.StatusCode==422&&WebUtility.HtmlDecode(ErrorSummary(rejected.Html)).Contains("E-SRC-002"),"removed/unknown empty field rejected: "+removed);Check(fake.SearchCalls==calls&&WebUtility.HtmlDecode(rejected.Html).Contains("入力保持"),"rejected field preserves raw input without query: "+removed);
 }
 var obsolete=await Post("/students/options",new(){{"__RequestVerificationToken",Field(clear.Html,"__RequestVerificationToken")}});Check(obsolete.Response.StatusCode==HttpStatusCode.NotFound,"obsolete search options route is 404 actual="+obsolete.Response.StatusCode+" body="+obsolete.Html);
 var normalizedValues=Values(Field(clear.Html,"ContextRevision"));normalizedValues["Criteria.StudentNo"]="ａｂ-１";normalizedValues["Criteria.Name"]="㍿";normalizedValues["__RequestVerificationToken"]=Field(clear.Html,"__RequestVerificationToken");var normalized=await Post("/students/search",normalizedValues);Check(normalized.Response.StatusCode==HttpStatusCode.OK&&fake.LastCriteria!.StudentNoPrefix=="AB-1"&&fake.LastCriteria.NameKey=="株式会社","raw input normalized before typed search");Check(WebUtility.HtmlDecode(normalized.Html).Contains("ａｂ-１")&&WebUtility.HtmlDecode(normalized.Html).Contains("㍿"),"raw text preserved after normalized search");
 var normalizedRevision=Field(normalized.Html,"ContextRevision");
 var pageCalls=fake.SearchCalls;var invalidPage=await Post("/students/page",new(){{"ContextId",context},{"ContextRevision",normalizedRevision},{"TabId",tab},{"Page","invalid-page"},{"PageSize","20"},{"SortKey","studentNo"},{"SortDirection","asc"},{"__RequestVerificationToken",Field(normalized.Html,"__RequestVerificationToken")}});Check((int)invalidPage.Response.StatusCode==422&&fake.SearchCalls==pageCalls,"page type binding failure never queries or advances revision");
 var paged=await Post("/students/page",new(){{"ContextId",context},{"ContextRevision",normalizedRevision},{"TabId",tab},{"Page","2"},{"PageSize","50"},{"SortKey","name"},{"SortDirection","desc"},{"__RequestVerificationToken",Field(normalized.Html,"__RequestVerificationToken")}});Check(paged.Response.StatusCode==HttpStatusCode.OK&&fake.LastCriteria!.StudentNoPrefix=="AB-1"&&fake.LastCriteria.Page==1&&fake.LastCriteria.PageSize==50,"sort/size uses applied normalized criteria and resets page");
 var resumedRaw=await Get("/students?contextId="+context+"&contextRevision="+Field(paged.Html,"ContextRevision"));Check(resumedRaw.Response.StatusCode==HttpStatusCode.OK&&WebUtility.HtmlDecode(resumedRaw.Html).Contains("ａｂ-１")&&WebUtility.HtmlDecode(resumedRaw.Html).Contains("㍿"),"resume restores raw input separately from normalized conditions");
 Check(!searched.Html.Contains("東京都見本町")&&!searched.Html.Contains("0300000000"),"search page has no address or phone values");
 fake.NextSave=new SaveResult(Outcome.ValidationFailed,null,null,[new("REG-002","E-STU-001","撮影契約テストの入力エラーです。")]);
 var validation=await Post("/students/create",new(){{"SnapshotId",Field(edit.Html,"SnapshotId")},{"Input.ReturnContextId",context},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}});Check((int)validation.Response.StatusCode==422&&WebUtility.HtmlDecode(ErrorSummary(validation.Html)).Contains("撮影契約テストの入力エラーです。"),"service field validation remains visible in the actual Razor summary");fake.NextSave=null;
 var reset=await Post("/students/reset",new(){{"SnapshotId",Field(edit.Html,"SnapshotId")},{"StudentId",""},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}});Check(reset.Response.StatusCode==HttpStatusCode.OK&&WebUtility.HtmlDecode(reset.Html).Contains("入力を読込時の値へ戻しました。")&&reset.Html.Contains("class=\"notice\""),"normal reset information remains visible");Check(ErrorSummary(reset.Html)=="","reset information does not create an empty error panel");
 var other=await Get("/students");var forged=new Dictionary<string,string>{{"SnapshotId",Field(edit.Html,"SnapshotId")},{"Input.ReturnContextId",Field(other.Html,"ContextId")},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}};var tamper=await Post("/students/create",forged);Check(tamper.Response.StatusCode==HttpStatusCode.Forbidden,"editor return context cannot be replaced");
}finally{await app.StopAsync();await app.DisposeAsync();}
Console.WriteLine($"MVC contract checks: {checks} passed (fake service; no SQL Server integration).");

sealed class FakeService:IStudentService
{
    public SearchCriteria? LastCriteria;
    public int SearchCalls;
    public SaveResult? NextSave;
    private static StudentListItem Row=>new(9007199254740993,"S2026-0001","見本 太郎","ミホン タロウ",new(2008,5,15),2026,"学年なし","C-A","Aクラス","在学");
    public Task<SearchResult> SearchAsync(SearchCriteria c,CancellationToken ct=default){SearchCalls++;LastCriteria=c;return Task.FromResult(new SearchResult(Outcome.Saved,1,[Row],DateTimeOffset.UtcNow,false,[]));}
    public Task<StudentDetail?> GetAsync(long id,CancellationToken ct=default)=>Task.FromResult<StudentDetail?>(new(id,2,new StudentDraft(),new(2008,5,15),DateTimeOffset.UtcNow,"alice"));
    public Task<LookupSet> LookupAsync(CancellationToken ct=default)=>Task.FromResult(new LookupSet([new("GENDER","0","未回答",0,true,new(1900,1,1),null,true),new("GRADE","00","学年なし",0,true,new(1900,1,1),null,true),new("ENROLLMENT_STATUS","01","在学",0,true,new(1900,1,1),null,true)], [new(1,2026,"00","C-A","Aクラス",new(2026,4,1),new(2027,3,31),40,1,true)]));
    public Task<SaveResult> SaveAsync(SaveRequest r,CancellationToken ct=default)=>Task.FromResult(NextSave??new SaveResult(Outcome.Saved,9007199254740993,2,[]));
    public Task<SaveResult> DeleteAsync(long id,long version,string reason,CancellationToken ct=default)=>Task.FromResult(new SaveResult(Outcome.Saved,id,version+1,[]));
}
