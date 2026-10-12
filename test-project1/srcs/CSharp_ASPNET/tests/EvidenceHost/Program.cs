using System.Globalization;
using System.Net;
using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
using StudentManagement.Core;
using StudentManagement.Web;

const string profile="CSharp_ASPNET";
string FindRoot() {
    for(var d=new DirectoryInfo(AppContext.BaseDirectory);d is not null;d=d.Parent)
        if(File.Exists(Path.Combine(d.FullName,"StudentManagement.Web.csproj")))return d.FullName;
    throw new DirectoryNotFoundException("The own-project production root was not found.");
}
var root=FindRoot();var fixturePath=Path.Combine(root,"tests","EvidenceHost","fixture-data.json");
var fixture=new EvidenceFixture(fixturePath);
if(args.Contains("--self-check")) { var passed=await fixture.Smoke();Console.WriteLine($"PASS fixture {profile}: {passed} checks; 3 synthetic students, 2 classes, 70 codes; no SQL Server connection or UI tests.");return; }
var port=7441;var lifetime=60;
foreach(var arg in args) {if(arg.StartsWith("--port="))port=int.Parse(arg[7..],CultureInfo.InvariantCulture);if(arg.StartsWith("--minutes="))lifetime=int.Parse(arg[10..],CultureInfo.InvariantCulture);}
if(port is <1024 or >65535||lifetime is <1 or >60)throw new ArgumentException("Loopback port 1024..65535 and lifetime 1..60 minutes required.");
var contentRoot=Path.Combine(root,".");
var builder=WebApplication.CreateBuilder(new WebApplicationOptions { EnvironmentName="Development",ApplicationName=typeof(StudentsController).Assembly.GetName().Name,ContentRootPath=contentRoot,WebRootPath=Path.Combine(contentRoot,"wwwroot") });
builder.WebHost.UseUrls($"https://localhost:{port}");
builder.Configuration["ConnectionStrings:StudentDb"]=null;
builder.Configuration["EvaluationSession:Secret"]=null;
builder.Logging.ClearProviders();builder.Logging.AddConsole();builder.Logging.SetMinimumLevel(LogLevel.Warning);
WebHostSetup.Add(builder);
builder.Services.RemoveAll<IStudentService>();builder.Services.AddSingleton<IStudentService>(fixture);
builder.Services.Configure<CookieAuthenticationOptions>(CookieAuthenticationDefaults.AuthenticationScheme,o=>o.Cookie.Name="__Host-Evidence-MVC");
builder.Services.Configure<Microsoft.AspNetCore.Antiforgery.AntiforgeryOptions>(o=>o.Cookie.Name="__Host-Evidence-MVC-CSRF");

var app=builder.Build();WebHostSetup.Use(app);
app.Use(async(ctx,next)=>{ctx.Response.Headers["X-Evidence-Fixture"]=profile;ctx.Response.Headers["X-SQL-Integration"]="not-tested";await next();});
app.MapControllers();
app.MapGet("/",()=>Results.Redirect("/students"));
app.MapGet("/__evidence",()=>Results.Content("<!doctype html><html lang=ja><meta charset=utf-8><title>撮影専用fixture</title><h1>"+profile+" 撮影専用fixture</h1><p>合成3学生・2クラス・70コード。SQL Server未接続。保存・削除は拒否します。</p><p><a href='/__evidence/login?role=Staff'>担当者として撮影画面を開く</a></p><p><a href='/__evidence/login?role=Viewer'>閲覧者として開く</a></p><p><a href='/__evidence/login?role=Administrator'>管理者表示として開く</a></p></html>","text/html; charset=utf-8")).AllowAnonymous();
app.MapGet("/__evidence/login",async(HttpContext ctx,string? role)=>{
    if(!IPAddress.IsLoopback(ctx.Connection.RemoteIpAddress??IPAddress.None))return Results.Forbid();
    if(!Enum.TryParse<Role>(role??"Staff",out var parsed))return Results.BadRequest();
    var session=SearchContextStore.Token();var principal="fixture-MVC";
    await ctx.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme,new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier,principal),new Claim(ClaimTypes.Name,principal),new Claim(ClaimTypes.Role,parsed.ToString()),new Claim("login_session",session)],CookieAuthenticationDefaults.AuthenticationScheme)));
    return Results.Redirect("/students");
}).AllowAnonymous();
app.MapGet("/__evidence/status",()=>Results.Json(new {fixture=profile,synthetic=true,students=3,classes=2,codes=70,sqlConnected=false,mutations="rejected",minutes=lifetime})).AllowAnonymous();
app.MapPost("/__evidence/stop",()=>{_ =Task.Run(async()=>{await Task.Delay(250);app.Lifetime.StopApplication();});return Results.Ok(new {stopping=true});}).AllowAnonymous();
using var timer=new CancellationTokenSource(TimeSpan.FromMinutes(lifetime));using var registration=timer.Token.Register(app.Lifetime.StopApplication);
Console.WriteLine($"EVIDENCE_HOST profile={profile} url=https://localhost:{port}/__evidence lifetime={lifetime}m fixture-only sql=not-connected");
await app.RunAsync();

sealed record FixtureStudent(long StudentId,long RowVersion,DateOnly BirthDate,StudentDraft Draft);
sealed class FixtureData {
    public bool Synthetic{get;set;} public string FixtureId{get;set;}="";public DateTimeOffset UpdatedAt{get;set;}
    public FixtureStudent[] Students{get;set;}=[];public SchoolClass[] Classes{get;set;}=[];public CodeEntry[] Codes{get;set;}=[];
}
sealed class EvidenceFixture : IStudentService {
    readonly FixtureData data;readonly JsonSerializerOptions json=new(JsonSerializerDefaults.Web);
    public EvidenceFixture(string path){data=JsonSerializer.Deserialize<FixtureData>(File.ReadAllText(path),json)??throw new InvalidDataException("Missing own fixture.");Check();}
    public void Check(){
        if(!data.Synthetic||data.Students.Length!=3||data.Classes.Length!=2||data.Codes.Length!=70)throw new InvalidDataException("Unexpected fixture cardinality.");
        if(data.Students.Select(x=>x.StudentId).Distinct().Count()!=3||data.Codes.Select(x=>(x.CategoryId,x.CodeValue)).Distinct().Count()!=70)throw new InvalidDataException("Duplicate fixture keys.");
        foreach(var s in data.Students){
            if(!s.Draft.StudentNo.StartsWith("TEST",StringComparison.Ordinal))throw new InvalidDataException("Synthetic student number must be explicit.");
            if(StudentNormalizer.Identifier(s.Draft.StudentNo,15,"StudentNo")!=s.Draft.StudentNo||JapaneseDateService.Parse(s.Draft.BirthDateInput,new DateOnly(2026,10,12))!=s.BirthDate)throw new InvalidDataException("Fixture boundary check failed.");
            if(s.Draft.ClassId is long id&&!data.Classes.Any(c=>c.ClassId==id))throw new InvalidDataException("Fixture class reference missing.");
        }
    }
    public async Task<int> Smoke(){
        var passed=0;void Assert(bool condition,string name){if(!condition)throw new InvalidDataException("Fixture smoke failed: "+name);passed++;}
        var found=await SearchAsync(new());Assert(found.Count==2&&found.Items.Count==2,"default status rows");Assert(found.Items.All(x=>x.StudentNo.StartsWith("TEST")),"synthetic numbers");
        Assert((await SearchAsync(new(){StudentNo="TEST2026-0002"})).Count==1,"literal prefix filter");
        Assert((await SearchAsync(new(){EnrollmentStatusCodes=[]})).Count==3,"unfiltered statuses");
        Assert((await SearchAsync(new(){UnassignedOnly=true,EnrollmentStatusCodes=[]})).Count==1,"unassigned terminal row");
        Assert((await SearchAsync(new(){GradeCode="01"})).Count==1,"grade reference");
        Assert((await SearchAsync(new(){PhoneNumber="000000"})).Count==2,"phone substring");
        Assert((await SearchAsync(new(){StudentNo="MISSING"})).Count==0,"empty result");
        var detail=await GetAsync(9007199254740993);Assert(detail?.Draft.StudentNo=="TEST2026-0001"&&detail.StudentId>9007199254740991,"exact Int64 detail");
        Assert(await GetAsync(1) is null,"missing detail");
        var lookup=await LookupAsync();Assert(lookup.Codes.Count==70&&lookup.Classes.Count==2,"complete lookups");
        Assert((await LookupAsync(false)).Classes.All(x=>x.Occupied==0),"search omits occupancy");
        Assert((await SaveAsync(new(new StudentDraft()))).Outcome==Outcome.Forbidden,"fixture save blocked");
        Assert((await DeleteAsync(9007199254740993,2,"test")).Outcome==Outcome.Forbidden,"fixture delete blocked");
        detail!.Draft.StudentName="改変テスト";Assert((await GetAsync(9007199254740993))!.Draft.StudentName=="テスト 太郎","detail clone isolation");
        Assert((await SearchAsync(new())).Items[0].StudentNo=="TEST2026-0001","immutable fixture after rejected mutations");
        return passed;
    }
    StudentDraft Copy(StudentDraft value)=>JsonSerializer.Deserialize<StudentDraft>(JsonSerializer.Serialize(value,json),json)!;
    StudentRow Row(FixtureStudent s){
        var c=data.Classes.SingleOrDefault(x=>x.ClassId==s.Draft.ClassId);
        string? Code(string category,string value)=>data.Codes.FirstOrDefault(x=>x.CategoryId==category&&x.CodeValue==value)?.CodeName;
        return new(s.StudentId,s.Draft.StudentNo,s.Draft.StudentName,s.Draft.StudentNameKana,s.BirthDate,c?.SchoolYear,c is null?null:Code("GRADE",c.GradeCode),c?.ClassCode,c?.ClassName,Code("ENROLLMENT_STATUS",s.Draft.EnrollmentStatusCode),s.Draft.AddressLine1,s.Draft.PhoneNumber,DateOnly.Parse(s.Draft.AdmissionDate,CultureInfo.InvariantCulture),data.UpdatedAt,s.RowVersion);
    }
    public Task<SearchResult> SearchAsync(SearchCriteria c,CancellationToken ct=default){
        ct.ThrowIfCancellationRequested();IEnumerable<FixtureStudent> q=data.Students;
        if(!string.IsNullOrEmpty(c.StudentNo))q=q.Where(x=>x.Draft.StudentNo.StartsWith(c.StudentNo,StringComparison.OrdinalIgnoreCase));
        if(!string.IsNullOrEmpty(c.StudentName))q=q.Where(x=>StudentNormalizer.NameKey(x.Draft.StudentName).Contains(StudentNormalizer.NameKey(c.StudentName),StringComparison.Ordinal));
        if(!string.IsNullOrEmpty(c.StudentNameKana))q=q.Where(x=>StudentNormalizer.Kana(x.Draft.StudentNameKana).Contains(StudentNormalizer.Kana(c.StudentNameKana),StringComparison.Ordinal));
        if(c.EnrollmentStatusCodes.Length>0)q=q.Where(x=>c.EnrollmentStatusCodes.Contains(x.Draft.EnrollmentStatusCode));
        if(c.ClassId is long id)q=q.Where(x=>x.Draft.ClassId==id);
        if(c.UnassignedOnly)q=q.Where(x=>x.Draft.ClassId is null);
        if(c.SchoolYear is int y)q=q.Where(x=>data.Classes.Any(k=>k.ClassId==x.Draft.ClassId&&k.SchoolYear==y));
        if(!string.IsNullOrEmpty(c.GradeCode))q=q.Where(x=>data.Classes.Any(k=>k.ClassId==x.Draft.ClassId&&k.GradeCode==c.GradeCode));
        if(!string.IsNullOrEmpty(c.PrefectureCode))q=q.Where(x=>x.Draft.PrefectureCode==c.PrefectureCode);
        if(!string.IsNullOrEmpty(c.PhoneNumber))q=q.Where(x=>(x.Draft.PhoneNumber??"").Contains(c.PhoneNumber,StringComparison.Ordinal)||(x.Draft.EmergencyPhoneNumber??"").Contains(c.PhoneNumber,StringComparison.Ordinal));
        if(!string.IsNullOrEmpty(c.AdmissionFrom))q=q.Where(x=>string.CompareOrdinal(x.Draft.AdmissionDate,c.AdmissionFrom)>=0);
        if(!string.IsNullOrEmpty(c.AdmissionTo))q=q.Where(x=>string.CompareOrdinal(x.Draft.AdmissionDate,c.AdmissionTo)<=0);
        var count=q.Count();Func<FixtureStudent,string> key=c.SortKey switch {"name"=>x=>StudentNormalizer.NameKey(x.Draft.StudentName),"admissionDate"=>x=>x.Draft.AdmissionDate,"updatedAt"=>x=>data.UpdatedAt.ToString("O"),_=>x=>x.Draft.StudentNo};
        q=c.SortDirection=="desc"?q.OrderByDescending(key,StringComparer.Ordinal).ThenBy(x=>x.StudentId):q.OrderBy(key,StringComparer.Ordinal).ThenBy(x=>x.StudentId);
        return Task.FromResult(new SearchResult(Outcome.NoChange,count,q.Skip((Math.Max(1,c.Page)-1)*c.PageSize).Take(c.PageSize).Select(Row).ToArray(),DateTimeOffset.UtcNow,false,[]));
    }
    public Task<StudentDetail?> GetAsync(long id,CancellationToken ct=default){var s=data.Students.SingleOrDefault(x=>x.StudentId==id);return Task.FromResult(s is null?null:new StudentDetail(s.StudentId,s.RowVersion,Copy(s.Draft),s.BirthDate,data.UpdatedAt,"fixture-operator"));}
    public Task<LookupSet> LookupAsync(CancellationToken ct=default)=>LookupAsync(true,ct);
    public Task<LookupSet> LookupAsync(bool includeOccupancy,CancellationToken ct=default)=>Task.FromResult(new LookupSet(data.Codes,data.Classes.Select(x=>includeOccupancy?x:x with{Occupied=0}).ToArray()));
    static SaveResult Refuse()=>new(Outcome.Forbidden,null,null,[new("","EVIDENCE-READONLY","撮影fixtureは読取り専用です。SQL Serverへの保存・削除は実施していません。")]);
    public Task<SaveResult> SaveAsync(SaveRequest r,CancellationToken ct=default)=>Task.FromResult(Refuse());
    public Task<SaveResult> DeleteAsync(long id,long version,string reason,CancellationToken ct=default)=>Task.FromResult(Refuse());
}

