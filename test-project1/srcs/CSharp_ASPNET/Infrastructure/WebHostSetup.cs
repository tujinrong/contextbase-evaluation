using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Mvc;
using StudentManagement.Core;
namespace StudentManagement.Web;
public static class WebHostSetup
{
    public static void Add(WebApplicationBuilder builder) {
        builder.Services.AddHttpContextAccessor();builder.Services.AddScoped<RequestIdentity>();builder.Services.AddSingleton<SearchContextStore>();builder.Services.AddSingleton<FlashMessageStore>();builder.Services.AddSingleton<EditorSnapshotStore>();builder.Services.AddScoped<WebStudentCoordinator>();
        builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme).AddCookie(options=> { options.Cookie.Name="__Host-StudentManagement";options.Cookie.SecurePolicy=CookieSecurePolicy.Always;options.Cookie.HttpOnly=true;options.Cookie.SameSite=SameSiteMode.Strict;options.ExpireTimeSpan=TimeSpan.FromMinutes(30);options.SlidingExpiration=true;options.Events.OnRedirectToLogin=ctx=> { ctx.Response.StatusCode=401;return ctx.Request.Path.StartsWithSegments("/api")?ctx.Response.WriteAsJsonAsync(WebPresentation.Error("unauthenticated","認証が失効しました。再認証してください。")):Task.CompletedTask; };options.Events.OnRedirectToAccessDenied=ctx=> { ctx.Response.StatusCode=403;return ctx.Request.Path.StartsWithSegments("/api")?ctx.Response.WriteAsJsonAsync(WebPresentation.Error("forbidden","この操作を実行する権限がありません。")):Task.CompletedTask; }; });
        builder.Services.AddAuthorization();builder.Services.AddAntiforgery(o=> { o.HeaderName="RequestVerificationToken";o.Cookie.Name="__Host-StudentManagement-CSRF";o.Cookie.SecurePolicy=CookieSecurePolicy.Always;o.Cookie.HttpOnly=true;o.Cookie.SameSite=SameSiteMode.Strict; });
        builder.Services.AddControllersWithViews(o=> { o.Filters.Add(new AutoValidateAntiforgeryTokenAttribute());o.Filters.Add(new AntiforgeryResultFilter());o.MaxModelValidationErrors=100; });
        builder.Services.Configure<Microsoft.AspNetCore.Http.Features.FormOptions>(o=> { o.MultipartBodyLengthLimit=65536;o.ValueLengthLimit=65536;o.ValueCountLimit=128; });
        builder.WebHost.ConfigureKestrel(o=>o.Limits.MaxRequestBodySize=65536);
        builder.Services.AddScoped<IStudentService>(sp=> { var connection=builder.Configuration.GetConnectionString("StudentDb"); if(string.IsNullOrWhiteSpace(connection)) throw new WebFault(503,"データベース接続が設定されていません。"); var identity=sp.GetRequiredService<RequestIdentity>(); return new SqlServerStudentService(connection,()=>identity.CurrentUser,webTokens:true); });
    }
    public static void Use(WebApplication app) {
        app.Use(async (ctx,next)=> { ctx.Response.Headers.CacheControl="no-store";ctx.Response.Headers["X-Content-Type-Options"]="nosniff";ctx.Response.Headers["Referrer-Policy"]="no-referrer";ctx.Response.Headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'";
            try { await next(); } catch(Exception e) when(!ctx.Response.HasStarted) { var fault=e as WebFault;ctx.Response.StatusCode=fault?.Status??503; if(ctx.Request.Path.StartsWithSegments("/api")) await ctx.Response.WriteAsJsonAsync(WebPresentation.Error(ctx.Response.StatusCode==401?"unauthenticated":ctx.Response.StatusCode==403?"forbidden":ctx.Response.StatusCode==409?"conflict":ctx.Response.StatusCode==422?"validationFailed":"systemError",fault?.Message??"処理結果を確認できません。保存の場合は検索で確認してください。",fault?.MessageId??"E-COM-004",fault?.Field is string field?[new FieldError(field,fault.MessageId,fault.Message)]:[],retry:fault is null)); else { ctx.Response.ContentType="text/html; charset=utf-8";await ctx.Response.WriteAsync("<!doctype html><html lang=ja><meta charset=utf-8><title>学生管理 エラー</title><p>"+System.Net.WebUtility.HtmlEncode(fault?.Message??"処理結果を確認できません。検索で確認してください。")+"</p><a href=/students>検索画面を開く</a></html>"); } }
        });
        app.UseHttpsRedirection();app.UseStaticFiles();app.UseRouting();app.UseAuthentication();app.UseAuthorization();
        // QA-AUTH evaluation adapter: disabled outside Development and when the server-side secret is absent.
        app.MapPost("/_evaluation/session",async (HttpContext ctx,IConfiguration config)=> { var secret=config["EvaluationSession:Secret"]; if(!app.Environment.IsDevelopment()||string.IsNullOrEmpty(secret)) return Results.NotFound(); var provided=ctx.Request.Headers["X-Evaluation-Secret"].ToString();if(!CryptographicOperations.FixedTimeEquals(SHA256.HashData(Encoding.UTF8.GetBytes(secret)),SHA256.HashData(Encoding.UTF8.GetBytes(provided))))return Results.Unauthorized();var user=config["EvaluationSession:Principal"]??"evaluation-user";if(!Enum.TryParse<Role>(config["EvaluationSession:Role"]??"Viewer",out var role))return Results.BadRequest();var session=SearchContextStore.Token();await ctx.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme,new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier,user),new Claim(ClaimTypes.Name,user),new Claim(ClaimTypes.Role,role.ToString()),new Claim("login_session",session)],CookieAuthenticationDefaults.AuthenticationScheme)));return Results.Ok(new { authenticated=true }); }).AllowAnonymous();
        app.MapGet("/health",()=>Results.Ok(new { status="running",database="not-tested" }));
    }
}
