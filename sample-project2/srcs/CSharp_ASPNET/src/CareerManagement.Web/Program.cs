using System.Text.Json.Serialization;
using CareerManagement.Application;
using CareerManagement.Infrastructure.Authentication;
using CareerManagement.Infrastructure.Reports;
using CareerManagement.Infrastructure.Sql;
using CareerManagement.Infrastructure.State;
using CareerManagement.Web.Filters;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Http.Features;

var builder=WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();builder.Logging.AddConsole();
builder.Logging.AddFilter("Microsoft.AspNetCore",LogLevel.Warning);
builder.WebHost.ConfigureKestrel(k=>k.Limits.MaxRequestBodySize=2*1024*1024);
var database=Environment.GetEnvironmentVariable("SP2_DATABASE")??"SampleProject2_Career";
var fixture=Environment.GetEnvironmentVariable("SP2_FIXTURE")=="true";
var connection=Environment.GetEnvironmentVariable("SP2_CONNECTION_STRING")??"Server=.\\SQLEXPRESS;Database=SampleProject2_Career;Integrated Security=True;Encrypt=True;TrustServerCertificate=False";
var dbOptions=new DatabaseOptions{ConnectionString=connection,AllowedDatabase=database,Fixture=fixture};dbOptions.Validate();
builder.Services.AddSingleton(dbOptions);builder.Services.AddSingleton<TimeProvider>(TimeProvider.System);
builder.Services.AddSingleton<BusinessClock>();builder.Services.AddSingleton<IDbFaults,NoDbFaults>();
builder.Services.AddSingleton<Database>();builder.Services.AddSingleton<Repository>();
builder.Services.AddSingleton<SessionRegistry>();builder.Services.AddSingleton<ScreenStateStore>();builder.Services.AddSingleton<ExportOperationRegistry>();
builder.Services.AddSingleton<AuthService>();builder.Services.AddSingleton<CurrentUserService>();builder.Services.AddSingleton<EmployeeService>();builder.Services.AddSingleton<CodeService>();
builder.Services.AddSingleton<ITextWidthMeasurer,GdiTextWidthMeasurer>();builder.Services.AddTransient<ReportService>();
builder.Services.Configure<FormOptions>(o=>{o.ValueCountLimit=1024;o.ValueLengthLimit=16384;o.MultipartBodyLengthLimit=2*1024*1024;});
var keys=Environment.GetEnvironmentVariable("SP2_DATA_KEYS")??Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"CareerManagement","keys");
if(!OperatingSystem.IsWindows())throw new PlatformNotSupportedException("This profile requires Windows GDI and DPAPI.");
builder.Services.AddDataProtection().SetApplicationName("SP2.CareerManagement").PersistKeysToFileSystem(new DirectoryInfo(keys)).ProtectKeysWithDpapi();
builder.Services.AddAuthentication("SP2").AddCookie("SP2",o=>
{
    o.Cookie.Name="__Host-SP2Auth";o.Cookie.Path="/";o.Cookie.Domain=null;o.Cookie.SecurePolicy=CookieSecurePolicy.Always;o.Cookie.HttpOnly=true;o.Cookie.SameSite=SameSiteMode.Lax;
    o.ExpireTimeSpan=TimeSpan.FromMinutes(30);o.SlidingExpiration=false;o.LoginPath="/account/login";
    o.Events=new CookieAuthenticationEvents{OnRedirectToLogin=c=>{c.Response.StatusCode=401;return Task.CompletedTask;},OnRedirectToAccessDenied=c=>{c.Response.StatusCode=403;return Task.CompletedTask;}};
});
builder.Services.AddAntiforgery(o=>{o.HeaderName="X-SP2-CSRF";o.FormFieldName="__RequestVerificationToken";o.Cookie.SecurePolicy=CookieSecurePolicy.Always;o.Cookie.HttpOnly=true;o.Cookie.SameSite=SameSiteMode.Strict;});
builder.Services.AddControllersWithViews(o=>{o.Filters.Add<CurrentActorFilter>();o.Filters.Add(new Microsoft.AspNetCore.Mvc.AutoValidateAntiforgeryTokenAttribute());})
    .AddJsonOptions(o=>HttpJson.Configure(o.JsonSerializerOptions));
var app=builder.Build();
app.Use(async(context,next)=>
{
    context.Response.Headers.CacheControl="no-store";context.Response.Headers.Pragma="no-cache";
    context.Response.Headers["X-Content-Type-Options"]="nosniff";context.Response.Headers["Referrer-Policy"]="no-referrer";
    context.Response.Headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'";
    try{await next();}
    catch(Exception exception) when(!context.Response.HasStarted&&exception is not OutOfMemoryException)
    {
        var outcome=SqlErrors.Map(exception,40);
        app.Logger.LogWarning("Request failed {CorrelationId} {MessageId} {CommitState}",outcome.CorrelationId,outcome.MessageId,outcome.CommitState);
        context.Response.StatusCode=exception is System.Text.Json.JsonException or BadHttpRequestException?400:HttpJson.Status(outcome);await context.Response.WriteAsJsonAsync(new{outcome},HttpJson.Options);
    }
});
app.UseHttpsRedirection();app.UseStaticFiles();app.UseAuthentication();app.UseAuthorization();
app.MapControllers();app.MapGet("/",()=>Results.Redirect("/menu"));
app.Run();
public partial class Program;
