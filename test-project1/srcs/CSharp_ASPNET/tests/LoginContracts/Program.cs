using System.Net;
using System.Security.Claims;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using StudentManagement.Core;
using StudentManagement.Web;

int checks = 0;
void Check(bool condition, string name) { if (!condition) throw new Exception("FAILED: " + name); Interlocked.Increment(ref checks); }
const string password = "contract-only-unique-password";
var hasher = new PasswordHasher<string>(Options.Create(new PasswordHasherOptions { IterationCount = 210000 }));
var hash = hasher.HashPassword("owner", password);
Dictionary<string, string?> Values(bool enabled = true) => new() {
    ["LocalLogin:Enabled"] = enabled.ToString(), ["LocalLogin:Username"] = "owner",
    ["LocalLogin:PasswordHash"] = hash, ["LocalLogin:Role"] = "Staff", ["AllowedHosts"] = "127.0.0.1"
};
ConfigurationManager Config(bool enabled = true) { var config = new ConfigurationManager(); config.AddInMemoryCollection(Values(enabled)); return config; }
var config = Config();
var clock = new TestClock();
var login = new LocalLogin(config, clock);
var first = login.Authenticate("owner", password)!;
Check(first.Identity?.IsAuthenticated == true && first.FindFirstValue(ClaimTypes.Role) == "Staff", "server configured identity and role");
var second = login.Authenticate("owner", password)!;
Check(first.FindFirstValue("login_session") != second.FindFirstValue("login_session"), "fresh random session every success");
var contexts = new SearchContextStore();
CurrentUser User(ClaimsPrincipal p) => new(p.FindFirstValue(ClaimTypes.NameIdentifier)!, p.FindFirstValue("login_session")!, Role.Staff);
var old = contexts.Create(User(first));
try { contexts.Get(old.Id, User(second)); Check(false, "old session denied"); } catch (WebFault e) { Check(e.Status == 403, "old search session inaccessible after relogin"); }
Check(login.AcceptsCookie(first), "current configuration accepts cookie");
config["LocalLogin:Role"] = "Viewer";
Check(!login.AcceptsCookie(first), "role rotation invalidates cookie");
config["LocalLogin:Role"] = "Staff";
config["LocalLogin:PasswordHash"] = hasher.HashPassword("owner", "changed-contract-password");
Check(!login.AcceptsCookie(first), "password rotation invalidates cookie");
config["LocalLogin:PasswordHash"] = hash;
config["LocalLogin:Username"] = "changed-owner";
Check(!login.AcceptsCookie(first), "username rotation invalidates cookie");
config["LocalLogin:Enabled"] = "false";
Check(!login.AcceptsCookie(first) && login.Authenticate("owner", password) is null, "disabled local adapter rejects local cookie and login");
Check(login.AcceptsCookie(new ClaimsPrincipal(new ClaimsIdentity([new Claim("evaluation", "true")], "Cookies"))), "evaluation identity unaffected");
foreach (var bad in new[] { ("Username", ""), ("Username", new string('u', 65)), ("PasswordHash", "not-base64"), ("PasswordHash", Convert.ToBase64String(new byte[61])), ("Role", "9"), ("Role", "administrator"), ("Role", "") }) {
    var invalid = Config(); invalid["LocalLogin:" + bad.Item1] = bad.Item2;
    try { new LocalLogin(invalid, clock).ReadSettings(); Check(false, "invalid configuration rejected"); }
    catch (InvalidOperationException) { Check(true, "invalid " + bad.Item1 + " rejected"); }
}
var disabled = Config(false); disabled["LocalLogin:PasswordHash"] = "";
Check(new LocalLogin(disabled, clock).ReadSettings() is null, "disabled does not require credentials");
var limited = new LocalLogin(Config(), clock);
Parallel.For(0, 8, i => Check(limited.Authenticate("other-" + i, "wrong") is null, "parallel invalid credentials"));
Check(limited.Authenticate("owner", password) is null, "concurrent attempts exhaust shared budget");
clock.Advance(TimeSpan.FromMinutes(4));
Check(limited.Authenticate("owner", password) is null, "locked correct password denied");
clock.Advance(TimeSpan.FromSeconds(61));
Check(limited.Authenticate("owner", password) is not null, "lock expires and blocked attempts do not extend it");

var root = new DirectoryInfo(AppContext.BaseDirectory);
while (root is not null && !File.Exists(Path.Combine(root.FullName, "StudentManagement.Web.csproj"))) root = root.Parent;
if (root is null) throw new Exception("Application root not found");
async Task<(WebApplication App, ConfigurationManager Config, HttpClient Client)> Start(bool enabled) {
    var builder = WebApplication.CreateBuilder(new WebApplicationOptions { EnvironmentName = "Production", ApplicationName = typeof(AccountController).Assembly.FullName, ContentRootPath = root.FullName });
    builder.Configuration.AddInMemoryCollection(Values(enabled)); builder.Logging.ClearProviders(); builder.WebHost.UseUrls("https://127.0.0.1:0");
    WebHostSetup.Add(builder);
    var app = builder.Build(); WebHostSetup.Use(app); app.MapControllers();
    app.MapGet("/api/probe", () => Results.Ok()).RequireAuthorization();
    app.MapGet("/probe", (HttpContext context, IAntiforgery csrf) => Results.Json(new { role = context.User.FindFirstValue(ClaimTypes.Role), session = context.User.FindFirstValue("login_session"), csrf = csrf.GetAndStoreTokens(context).RequestToken })).RequireAuthorization();
    await app.StartAsync();
    var client = new HttpClient(new HttpClientHandler { UseCookies = false, UseProxy = false, AllowAutoRedirect = false, ServerCertificateCustomValidationCallback = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator }) { BaseAddress = new Uri(app.Urls.Single()) };
    return (app, builder.Configuration, client);
}
var host = await Start(true);
var cookieOptions = host.App.Services.GetRequiredService<IOptionsMonitor<CookieAuthenticationOptions>>().Get(CookieAuthenticationDefaults.AuthenticationScheme);
Check(cookieOptions.ExpireTimeSpan == TimeSpan.FromMinutes(30) && cookieOptions.SlidingExpiration, "30 minute sliding authentication lifetime");
var cookies = new Dictionary<string, string>();
void Collect(HttpResponseMessage response) {
    if (response.Headers.TryGetValues("Set-Cookie", out var values)) foreach (var value in values) { var pair = value.Split(';')[0].Split('=', 2); cookies[pair[0]] = pair[1]; }
    host.Client.DefaultRequestHeaders.Remove("Cookie");
    if (cookies.Count > 0) host.Client.DefaultRequestHeaders.Add("Cookie", string.Join("; ", cookies.Select(pair => pair.Key + "=" + pair.Value)));
}
string Csrf(string html) => WebUtility.HtmlDecode(Regex.Match(html, "name=\"__RequestVerificationToken\"[^>]*value=\"([^\"]+)\"").Groups[1].Value);
async Task<HttpResponseMessage> Post(string path, string? token, string suppliedPassword = password, string username = "owner") {
    var values = new Dictionary<string, string> { ["Username"] = username, ["Password"] = suppliedPassword, ["Role"] = "Administrator", ["returnUrl"] = "https://example.invalid" };
    if (token is not null) values["__RequestVerificationToken"] = token;
    return await host.Client.PostAsync(path, new FormUrlEncodedContent(values));
}
try {
    var anonymous = await host.Client.GetAsync("/students"); Check(anonymous.StatusCode == HttpStatusCode.Found && anonymous.Headers.Location?.ToString() == "/login", "interactive page redirects to login");
    var api = await host.Client.GetAsync("/api/probe"); Check(api.StatusCode == HttpStatusCode.Unauthorized && (await api.Content.ReadAsStringAsync()).Contains("unauthenticated"), "API keeps JSON 401");
    Check((await Post("/students/search", null)).StatusCode == HttpStatusCode.Unauthorized, "unsafe anonymous request stays 401");
    Check((await Post("/_evaluation/session", null)).StatusCode == HttpStatusCode.NotFound, "production evaluation endpoint unavailable");
    var form = await host.Client.GetAsync("/login"); Collect(form); var html = await form.Content.ReadAsStringAsync(); var token = Csrf(html);
    Check(form.StatusCode == HttpStatusCode.OK && token.Length > 0 && html.Contains("autocomplete=\"current-password\"") && !html.Contains("利用者 </span>"), "Japanese login form and antiforgery rendered without empty identity");
    Check((await Post("/login", null)).StatusCode == HttpStatusCode.BadRequest, "login requires csrf");
    const string wrong = "never-render-this-password";
    var rejected = await Post("/login", token, wrong); var error = await rejected.Content.ReadAsStringAsync();
    Check(rejected.StatusCode == HttpStatusCode.Unauthorized && error.Contains("role=\"alert\"") && !error.Contains(wrong), "generic failure never renders password");
    var other = await Post("/login", token, wrong, "other");
    Check(Regex.Match(error, "<p class=\"message error\"[^>]*>(.*?)</p>").Value == Regex.Match(await other.Content.ReadAsStringAsync(), "<p class=\"message error\"[^>]*>(.*?)</p>").Value, "unknown username gets same error");
    var accepted = await Post("/login", token); Collect(accepted);
    Check(accepted.StatusCode == HttpStatusCode.Found && accepted.Headers.Location?.ToString() == "/students", "successful login fixed local redirect");
    var authCookie = accepted.Headers.GetValues("Set-Cookie").Single(v => v.StartsWith("__Host-StudentManagement="));
    Check(authCookie.Contains("secure", StringComparison.OrdinalIgnoreCase) && authCookie.Contains("httponly", StringComparison.OrdinalIgnoreCase) && authCookie.Contains("samesite=strict", StringComparison.OrdinalIgnoreCase) && !authCookie.Contains("expires=", StringComparison.OrdinalIgnoreCase) && !authCookie.Contains("max-age=", StringComparison.OrdinalIgnoreCase), "secure strict HttpOnly session cookie");
    var probe = await host.Client.GetAsync("/probe"); Collect(probe); var identity = JsonDocument.Parse(await probe.Content.ReadAsStringAsync()).RootElement;
    Check(identity.GetProperty("role").GetString() == "Staff", "posted Administrator role ignored");
    var session = identity.GetProperty("session").GetString(); var logoutToken = identity.GetProperty("csrf").GetString();
    Check((await Post("/logout", null)).StatusCode == HttpStatusCode.BadRequest, "logout requires csrf");
    var logout = await Post("/logout", logoutToken); Collect(logout); Check(logout.StatusCode == HttpStatusCode.Found && logout.Headers.Location?.ToString() == "/login", "logout signs out and redirects");
    Check((await host.Client.GetAsync("/probe")).StatusCode == HttpStatusCode.Found, "signed out cookie cannot access protected page");
    var reloginForm = await host.Client.GetAsync("/login"); Collect(reloginForm); var relogin = await Post("/login", Csrf(await reloginForm.Content.ReadAsStringAsync())); Collect(relogin);
    var secondProbe = await host.Client.GetAsync("/probe");
    Check(JsonDocument.Parse(await secondProbe.Content.ReadAsStringAsync()).RootElement.GetProperty("session").GetString() != session, "HTTP relogin rotates session");
    host.Config["LocalLogin:PasswordHash"] = hasher.HashPassword("owner", "rotated-secret");
    var rotated = await host.Client.GetAsync("/probe"); Collect(rotated); Check(rotated.StatusCode == HttpStatusCode.Found, "rotated hash rejects existing cookie at middleware");
    host.Config["LocalLogin:PasswordHash"] = hash;
    var newForm = await host.Client.GetAsync("/login"); Collect(newForm); var newLogin = await Post("/login", Csrf(await newForm.Content.ReadAsStringAsync())); Collect(newLogin);
    host.Config["LocalLogin:Enabled"] = "false";
    Check((await host.Client.GetAsync("/probe")).StatusCode == HttpStatusCode.Unauthorized && (await host.Client.GetAsync("/login")).StatusCode == HttpStatusCode.NotFound, "disabling adapter invalidates cookie and hides form");
}
finally { host.Client.Dispose(); await host.App.StopAsync(); await host.App.DisposeAsync(); }
var off = await Start(false);
try { Check((await off.Client.GetAsync("/students")).StatusCode == HttpStatusCode.Unauthorized && (await off.Client.GetAsync("/login")).StatusCode == HttpStatusCode.NotFound, "disabled deployment preserves original unauthenticated behavior"); }
finally { off.Client.Dispose(); await off.App.StopAsync(); await off.App.DisposeAsync(); }
Console.WriteLine($"Login contract checks passed: {checks}");

sealed class TestClock : TimeProvider
{
    private DateTimeOffset now = new(2026, 10, 23, 0, 0, 0, TimeSpan.Zero);
    public override DateTimeOffset GetUtcNow() => now;
    public void Advance(TimeSpan duration) => now += duration;
}
