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
using StudentManagement.Api;
int checks=0;
void Check(bool condition,string name){if(!condition)throw new Exception("FAILED: "+name);checks++;}
async Task Fault(Func<Task> action,int status,string name){try{await action();throw new Exception("EXPECTED: "+name);}catch(WebFault f){Check(f.Status==status,name);}}
var unknown=JsonSerializer.SerializeToElement(WebPresentation.Save(new SaveResult(Outcome.Unknown,null,null,[])));Check(unknown.GetProperty("retryBySearch").GetBoolean()&&!unknown.GetProperty("message").GetString()!.Contains("保存しました"),"unknown save never reports success");
var user=new CurrentUser("alice","session",Role.Staff);var store=new SearchContextStore();var entry=store.Create(user,"tab");Check(entry.Id.Length==64&&entry.Id.All(Uri.IsHexDigit),"256bit hex context");
await Fault(()=>Task.Run(()=>store.Get(entry.Id,new("bob","session",Role.Staff),"tab")),403,"other principal rejected");
await Fault(()=>Task.Run(()=>store.Get(entry.Id,new("alice","other",Role.Staff),"tab")),403,"other session rejected");
await Fault(()=>Task.Run(()=>store.Get(entry.Id,user,"other")),403,"other tab rejected");
entry.Expires=DateTimeOffset.UtcNow.AddSeconds(-1);await Fault(()=>Task.Run(()=>store.Get(entry.Id,user)),409,"expired context rejected");entry.Expires=DateTimeOffset.UtcNow.AddMinutes(30);
await Fault(()=>store.Use(new(){ContextId=entry.Id,ContextRevision="0"},user,"tab",e=>Task.FromResult(0),default),409,"stale revision rejected");
var first=new ContextRequest{ContextId=entry.Id,ContextRevision="1"};await store.Use(first,user,"tab",e=>{e.Revision++;return Task.FromResult(0);},default);await Fault(()=>store.Use(first,user,"tab",e=>Task.FromResult(0),default),409,"reused revision rejected");
Check(IdParser.Required("9007199254740993","id")==9007199254740993L,"ID beyond JS safe integer");Check(IdParser.Required(long.MaxValue.ToString(),"id")==long.MaxValue,"max bigint");await Fault(()=>Task.Run(()=>IdParser.Required("9223372036854775808","id")),422,"bigint overflow rejected");await Fault(()=>Task.Run(()=>IdParser.Required("1e3","id")),422,"exponent ID rejected");
async Task Parse(string body){var ctx=new Microsoft.AspNetCore.Http.DefaultHttpContext();ctx.Request.ContentType="application/json";ctx.Request.Body=new MemoryStream(Encoding.UTF8.GetBytes(body));await StrictJson.Read<StudentSaveInput>(ctx.Request,default);}
await Fault(()=>Parse("{\"studentName\":\"a\",\"studentName\":\"b\"}"),400,"duplicate JSON rejected");await Fault(()=>Parse("{\"createdBy\":\"forged\"}"),400,"management JSON rejected");await Fault(()=>Parse("{\"studentName\":42}"),400,"string coercion rejected");await Fault(()=>Parse("{\"birthDateInput\":{\"era\":\"MEIJI\",\"era\":\"REIWA\"}}"),400,"nested duplicate rejected");await Fault(()=>Parse("{\"remarks\":\""+new string('x',65536)+"\"}"),400,"64KiB enforced");
var builder=WebApplication.CreateBuilder(new WebApplicationOptions{EnvironmentName="Development",ApplicationName=typeof(StudentsController).Assembly.FullName});builder.WebHost.UseUrls("https://127.0.0.1:0");builder.Logging.ClearProviders();builder.Configuration.AddInMemoryCollection(new Dictionary<string,string?>{{"AllowedHosts","127.0.0.1"},{"EvaluationSession:Secret","contract-test-key"},{"EvaluationSession:Role","Staff"}});WebHostSetup.Add(builder);var fake=new FakeService();builder.Services.AddSingleton<IStudentService>(fake);builder.Services.AddControllersWithViews().AddApplicationPart(typeof(StudentsApiController).Assembly);var app=builder.Build();WebHostSetup.Use(app);app.MapControllers();await app.StartAsync();
try {
    using var client=new HttpClient(new HttpClientHandler{UseCookies=false,UseProxy=false,AllowAutoRedirect=false,ServerCertificateCustomValidationCallback=HttpClientHandler.DangerousAcceptAnyServerCertificateValidator}){BaseAddress=new Uri(app.Urls.Single())};var cookies=new Dictionary<string,string>();
    void Collect(HttpResponseMessage response){if(response.Headers.TryGetValues("Set-Cookie",out var values))foreach(var value in values){var pair=value.Split(';')[0].Split('=',2);cookies[pair[0]]=pair[1];}client.DefaultRequestHeaders.Remove("Cookie");if(cookies.Count>0)client.DefaultRequestHeaders.Add("Cookie",string.Join("; ",cookies.Select(p=>p.Key+"="+p.Value)));}
    var anonymous=await client.GetAsync("/api/students/bootstrap");Check(anonymous.StatusCode==HttpStatusCode.Unauthorized,"anonymous API 401 actual="+anonymous.StatusCode+" body="+await anonymous.Content.ReadAsStringAsync());Check((await anonymous.Content.ReadFromJsonAsync<JsonElement>()).GetProperty("outcome").GetString()=="unauthenticated","401 JSON contract");
    client.DefaultRequestHeaders.Add("X-Evaluation-Secret","contract-test-key");var login=await client.PostAsync("/_evaluation/session",null);Check(login.StatusCode==HttpStatusCode.OK,"evaluation adapter login");Collect(login);client.DefaultRequestHeaders.Remove("X-Evaluation-Secret");client.DefaultRequestHeaders.Add("X-Tab-Id","contract-tab");
    var bootstrap=await client.GetAsync("/api/students/bootstrap");Check(bootstrap.StatusCode==HttpStatusCode.OK,"bootstrap authenticated actual="+bootstrap.StatusCode+" body="+await bootstrap.Content.ReadAsStringAsync());Collect(bootstrap);var b=await bootstrap.Content.ReadFromJsonAsync<JsonElement>();string context=b.GetProperty("contextId").GetString()!,revision=b.GetProperty("contextRevision").GetString()!,csrf=b.GetProperty("csrfToken").GetString()!;
    var payload=new {contextId=context,contextRevision=revision,criteria=new StudentSearchInput{StatusCodes=[]},pageSize=20,sortKey="studentNo",sortDirection="asc"};var noCsrf=await client.PostAsJsonAsync("/api/students/search",payload);Check(noCsrf.StatusCode==HttpStatusCode.BadRequest,"missing CSRF rejected");Check((await noCsrf.Content.ReadFromJsonAsync<JsonElement>()).GetProperty("outcome").GetString()=="badRequest","CSRF JSON contract");
    client.DefaultRequestHeaders.Add("RequestVerificationToken",csrf);var searched=await client.PostAsJsonAsync("/api/students/search",payload);Check(searched.StatusCode==HttpStatusCode.OK,"search HTTP contract");var s=await searched.Content.ReadFromJsonAsync<JsonElement>();Check(s.GetProperty("items")[0].GetProperty("studentId").GetString()=="9007199254740993","API ID decimal string");Check(s.GetProperty("items")[0].GetProperty("birthDateWareki").GetString()=="平成20年05月15日","API wareki output");Check(!s.GetProperty("items")[0].TryGetProperty("rowVersion",out _),"list excludes version");Check(!s.GetProperty("items")[0].TryGetProperty("emailAddress",out _),"list excludes private extra fields");Check(fake.LastCriteria!.EnrollmentStatusCodes.Length==0,"all-off statuses preserved");
    var stale=await client.PostAsJsonAsync("/api/students/search",payload);Check(stale.StatusCode==HttpStatusCode.Conflict,"HTTP stale revision");
    var invalid=await client.PostAsync("/api/students",new StringContent("{\"createdBy\":\"forged\"}",Encoding.UTF8,"application/json"));Check(invalid.StatusCode==HttpStatusCode.BadRequest,"HTTP unknown management property");
    var duplicate=await client.PostAsync("/api/students",new StringContent("{\"studentName\":\"a\",\"studentName\":\"b\"}",Encoding.UTF8,"application/json"));Check(duplicate.StatusCode==HttpStatusCode.BadRequest,"HTTP duplicate properties");
    var delete=await client.PostAsJsonAsync("/api/students/9007199254740993/soft-delete",new{expectedVersion="2",reason="test",confirmed=true,returnContextId=context});Check(delete.StatusCode==HttpStatusCode.Forbidden,"Staff delete denied");
    Check(searched.Headers.CacheControl?.NoStore==true,"no-store response");Check(searched.Headers.Contains("Content-Security-Policy"),"CSP response");
    var mvc=await client.GetAsync("/students");Check(mvc.StatusCode==HttpStatusCode.OK,"Razor search renders");var html=await mvc.Content.ReadAsStringAsync();Check(html.Contains("SRC-012")&&html.Contains("検索条件"),"Razor search all filters");
    var edit=await client.GetAsync("/students/new?returnContextId="+context);Check(edit.StatusCode==HttpStatusCode.OK,"Razor registration renders");var editHtml=await edit.Content.ReadAsStringAsync();Check(editHtml.Contains("REG-023")&&editHtml.Contains("REG-024")&&editHtml.Contains("BirthDateInput.Era"),"Razor registration full input and wareki");
} finally {await app.StopAsync();await app.DisposeAsync();}
Console.WriteLine($"Web contract checks: {checks} passed (fake service; no SQL Server integration).");
sealed class FakeService:IStudentService
{
    public SearchCriteria? LastCriteria;
    private static StudentRow Row=>new(9007199254740993,"S2026-0001","見本 太郎","ミホン タロウ",new(2008,5,15),2026,"学年なし","C-A","Aクラス","在学","東京都見本町","0300000000",new(2026,4,1),DateTimeOffset.UtcNow,2);
    public Task<SearchResult> SearchAsync(SearchCriteria c,CancellationToken ct=default){LastCriteria=c;return Task.FromResult(new SearchResult(Outcome.Saved,1,[Row],DateTimeOffset.UtcNow,false,[]));}
    public Task<StudentDetail?> GetAsync(long id,CancellationToken ct=default)=>Task.FromResult<StudentDetail?>(new(id,2,new StudentDraft(),new(2008,5,15),DateTimeOffset.UtcNow,"alice"));
    public Task<LookupSet> LookupAsync(CancellationToken ct=default)=>Task.FromResult(new LookupSet([new("GENDER","0","未回答",0,true,new(1900,1,1),null,true),new("GRADE","00","学年なし",0,true,new(1900,1,1),null,true),new("ENROLLMENT_STATUS","01","在学",0,true,new(1900,1,1),null,true)], [new(1,2026,"00","C-A","Aクラス",new(2026,4,1),new(2027,3,31),40,1,true)]));
    public Task<SaveResult> SaveAsync(SaveRequest r,CancellationToken ct=default)=>Task.FromResult(new SaveResult(Outcome.Saved,9007199254740993,2,[]));
    public Task<SaveResult> DeleteAsync(long id,long version,string reason,CancellationToken ct=default)=>Task.FromResult(new SaveResult(Outcome.Saved,id,version+1,[]));
}
