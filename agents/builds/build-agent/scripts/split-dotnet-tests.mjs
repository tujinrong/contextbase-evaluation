// LEGACY one-time migration resource. Current generation uses build/ and .tmp/.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
const base=path.join(root,'test-project1/srcs');
const mvc=path.join(base,'CSharp_ASPNET/tests');
const original=fs.readFileSync(path.join(mvc,'Program.cs'),'utf8');
if(!original.includes('using StudentManagement.Api;'))throw new Error('One-time migration already completed; the MVC-only tests must not be overwritten.');
const fake=original.slice(original.indexOf('sealed class FakeService'));
let api=original.replace('using StudentManagement.Web;','using StudentManagement.Web;').replace('ApplicationName=typeof(StudentsController).Assembly.FullName','ApplicationName=typeof(StudentsApiController).Assembly.FullName');
api=api.split(/\r?\n/).filter(line=>!line.includes('omittedMvcResume')&&!line.includes('validMvcReturn')&&!line.includes('var mvc=await')&&!line.includes('var edit=await')).join('\n');
fs.writeFileSync(path.join(base,'Vue_CSharpAPI/tests/ApiContracts.cs'),api);
fs.writeFileSync(path.join(base,'Vue_CSharpAPI/tests/ApiContracts.csproj'),`<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings><EnableDefaultCompileItems>false</EnableDefaultCompileItems></PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App"/><ProjectReference Include="../backend/StudentManagement.Api.csproj"/><Compile Include="ApiContracts.cs"/></ItemGroup></Project>\n`);
const prefix=original.slice(0,original.indexOf('async Task Parse')).replace('using StudentManagement.Api;','');
const body=String.raw`
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
 var screen=await Get("/students");Check(screen.Response.StatusCode==HttpStatusCode.OK,"Razor search renders");Check(screen.Html.Contains("SRC-012")&&screen.Html.Contains("検索条件"),"all search filters render");
 var context=Field(screen.Html,"ContextId");var revision=Field(screen.Html,"ContextRevision");var tab=Field(screen.Html,"TabId");var csrf=Field(screen.Html,"__RequestVerificationToken");
 Dictionary<string,string> Values(string rev)=>new(){{"ContextId",context},{"ContextRevision",rev},{"TabId",tab},{"PageSize","20"},{"SortKey","studentNo"},{"SortDirection","asc"},{"Criteria.StudentNo",""},{"Criteria.Name",""},{"Criteria.Kana",""}};
 var noCsrf=await Post("/students/search",Values(revision));Check(noCsrf.Response.StatusCode==HttpStatusCode.BadRequest,"MVC CSRF enforced");
 var values=Values(revision);values["__RequestVerificationToken"]=csrf;var searched=await Post("/students/search",values);Check(searched.Response.StatusCode==HttpStatusCode.OK,"MVC search submits");Check(fake.LastCriteria!.EnrollmentStatusCodes.Length==0,"all-off statuses stay all-off");Check(searched.Html.Contains("9007199254740993")&&searched.Html.Contains("平成20年05月15日"),"big ID and wareki render");Check(searched.Response.Headers.CacheControl?.NoStore==true&&searched.Response.Headers.Contains("Content-Security-Policy"),"cache and CSP headers");
 var stale=await Post("/students/search",values);Check(stale.Response.StatusCode==HttpStatusCode.Conflict,"stale search revision rejected");
 var missingValues=Values(revision);missingValues.Remove("ContextRevision");missingValues["__RequestVerificationToken"]=csrf;var missing=await Post("/students/search",missingValues);Check(missing.Response.StatusCode==HttpStatusCode.Conflict,"missing search revision rejected");
 var missingReturn=await Get("/students?contextId="+context);Check(missingReturn.Response.StatusCode==HttpStatusCode.Conflict,"return never substitutes latest revision");
 var current=Field(searched.Html,"ContextRevision");var resumed=await Get("/students?contextId="+context+"&contextRevision="+current);Check(resumed.Response.StatusCode==HttpStatusCode.OK,"return uses received revision");
 var clearValues=new Dictionary<string,string>{{"ContextId",context},{"ContextRevision",Field(resumed.Html,"ContextRevision")},{"TabId",tab},{"__RequestVerificationToken",Field(resumed.Html,"__RequestVerificationToken")}};
 var clear=await Post("/students/clear",clearValues);Check(clear.Response.StatusCode==HttpStatusCode.OK&&clear.Html.Contains("未検索"),"clear returns unsearched");
 var edit=await Get("/students/new?returnContextId="+context);Check(edit.Response.StatusCode==HttpStatusCode.OK,"Razor registration renders");Check(edit.Html.Contains("REG-023")&&edit.Html.Contains("REG-024")&&edit.Html.Contains("BirthDateInput.Era"),"full registration fields and raw wareki");
 var other=await Get("/students");var forged=new Dictionary<string,string>{{"SnapshotId",Field(edit.Html,"SnapshotId")},{"Input.ReturnContextId",Field(other.Html,"ContextId")},{"__RequestVerificationToken",Field(edit.Html,"__RequestVerificationToken")}};var tamper=await Post("/students/create",forged);Check(tamper.Response.StatusCode==HttpStatusCode.Forbidden,"editor return context cannot be replaced");
}finally{await app.StopAsync();await app.DisposeAsync();}
Console.WriteLine($"MVC contract checks: {checks} passed (fake service; no SQL Server integration).");
`;
fs.writeFileSync(path.join(mvc,'Program.cs'),prefix+body+'\n'+fake);
fs.writeFileSync(path.join(mvc,'WebContracts.csproj'),`<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings><EnableDefaultCompileItems>false</EnableDefaultCompileItems></PropertyGroup><ItemGroup><FrameworkReference Include="Microsoft.AspNetCore.App"/><ProjectReference Include="../StudentManagement.Web.csproj"/><Compile Include="Program.cs"/></ItemGroup></Project>\n`);
let smoke=fs.readFileSync(path.join(base,'VB.NET_WinForms/Tests/NativeSmoke.cs'),'utf8').replace('using VB = StudentManagement.WinForms;','');
const start=smoke.indexOf('        using (var date');const end=smoke.indexOf('        var app =');smoke=smoke.slice(0,start)+smoke.slice(end);smoke=smoke.replace('Native smoke:','WPF smoke:');
const smokeDir=path.join(base,'CSharp_WPF/tests/Smoke');fs.mkdirSync(smokeDir,{recursive:true});fs.writeFileSync(path.join(smokeDir,'Program.cs'),smoke);
fs.writeFileSync(path.join(smokeDir,'NativeSmoke.csproj'),`<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0-windows</TargetFramework><UseWPF>true</UseWPF><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><EnableDefaultApplicationDefinition>false</EnableDefaultApplicationDefinition></PropertyGroup><ItemGroup><ProjectReference Include="../../StudentManagement.Wpf.csproj"/></ItemGroup></Project>\n`);
console.log('Independent MVC/API/WPF test projects created.');
