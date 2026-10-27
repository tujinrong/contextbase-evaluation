using System.Net;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.Data.SqlClient;
using StudentManagement.Core;

namespace StudentManagement.Web;

/// <summary>
/// Explicit local-only shared-database sample profile. Roles come from the
/// selected database; neither request fields nor the server process are users.
/// </summary>
public sealed class SharedDatabaseTraining(IConfiguration configuration, IHostEnvironment environment, TimeProvider clock)
{
    public const string EnvironmentName = "SharedDatabaseTraining";
    private const string LoginSource = "shared-database-training";
    public sealed record Settings(string ConnectionString, string Principal, string Scope);

    public Settings? ReadSettings()
    {
        if (!configuration.GetValue<bool>("SharedDatabaseTraining:Enabled")) return null;
        if (!environment.IsEnvironment(EnvironmentName))
            throw new InvalidOperationException("SharedDatabaseTraining is allowed only in its explicit environment.");
        if (configuration.GetValue<bool>("LocalLogin:Enabled"))
            throw new InvalidOperationException("SharedDatabaseTraining and LocalLogin must not be enabled together.");
        if (configuration["StudentDatabase:Profile"] != "SharedAccess")
            throw new InvalidOperationException("SharedDatabaseTraining requires the SharedAccess database profile.");
        var principal = configuration["SharedDatabaseTraining:Principal"];
        if (string.IsNullOrWhiteSpace(principal) || principal.EnumerateRunes().Count() > 64 || principal.Any(char.IsControl))
            throw new InvalidOperationException("SharedDatabaseTraining:Principal must identify an explicit database user.");
        var raw = configuration.GetConnectionString("StudentDb");
        if (string.IsNullOrWhiteSpace(raw)) throw new InvalidOperationException("SharedDatabaseTraining requires StudentDb.");
        var connection = new SqlConnectionStringBuilder(raw) { Encrypt = true };
        if (!IsLocalSqlExpress(connection.DataSource) || string.IsNullOrWhiteSpace(connection.InitialCatalog))
            throw new InvalidOperationException("SharedDatabaseTraining requires an explicit local SQLEXPRESS database.");
        var scope = Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(
            connection.DataSource.ToUpperInvariant() + "\0" + connection.InitialCatalog + "\0" + principal)));
        return new(connection.ConnectionString, principal, scope);
    }

    public static bool IsLocalSqlExpress(string server) => server.Equals(@".\SQLEXPRESS", StringComparison.OrdinalIgnoreCase)
        || server.Equals(@"localhost\SQLEXPRESS", StringComparison.OrdinalIgnoreCase)
        || server.Equals(@"127.0.0.1\SQLEXPRESS", StringComparison.OrdinalIgnoreCase);

    public static Role DatabaseRole(string? role) => role switch
    {
        "Reader" => Role.Viewer,
        "Staff" => Role.Staff,
        "Admin" => Role.Administrator,
        _ => throw new WebFault(403, "共有DBの利用権限が設定されていません。", messageId: "E-COM-002")
    };

    public bool AcceptsCookie(ClaimsPrincipal principal)
    {
        if (!principal.HasClaim("login_source", LoginSource)) return true;
        var settings = ReadSettings();
        return settings is not null && principal.FindFirstValue("training_scope") == settings.Scope
            && principal.FindFirstValue(ClaimTypes.NameIdentifier) == settings.Principal;
    }

    public async Task ApplyAsync(HttpContext context)
    {
        var settings = ReadSettings();
        if (settings is null) return;
        if (!context.Request.IsHttps || context.Connection.RemoteIpAddress is not { } address || !IPAddress.IsLoopback(address))
            throw new WebFault(403, "共有DBの確認用モードはローカルHTTPS接続に限定されています。", messageId: "E-COM-002");

        await using var connection = new SqlConnection(settings.ConnectionString);
        await connection.OpenAsync(context.RequestAborted);
        await using var command = new SqlCommand("SELECT role_name FROM dbo.t_app_role WHERE user_id=@user_id", connection);
        command.Parameters.Add("@user_id", System.Data.SqlDbType.NVarChar, 128).Value = settings.Principal;
        var value = await command.ExecuteScalarAsync(context.RequestAborted);
        var role = DatabaseRole(value as string);

        var existing = context.User;
        var existingSession = existing.FindFirstValue("login_session");
        var reusable = existing.Identity?.IsAuthenticated == true && existing.HasClaim("login_source", LoginSource)
            && AcceptsCookie(existing) && existingSession is { Length: 64 } && existingSession.All(Uri.IsHexDigit);
        var session = reusable ? existingSession! : SearchContextStore.Token();
        var identity = new ClaimsPrincipal(new ClaimsIdentity([
            new Claim(ClaimTypes.NameIdentifier, settings.Principal), new Claim(ClaimTypes.Name, settings.Principal),
            new Claim(ClaimTypes.Role, role.ToString()), new Claim("login_session", session),
            new Claim("login_source", LoginSource), new Claim("training_scope", settings.Scope)
        ], CookieAuthenticationDefaults.AuthenticationScheme));
        if (!reusable || existing.FindFirstValue(ClaimTypes.Role) != role.ToString())
            await context.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, identity,
                new AuthenticationProperties { IsPersistent = false, AllowRefresh = false, ExpiresUtc = clock.GetUtcNow().AddMinutes(30) });
        context.User = identity;
        context.Items["SharedDatabaseTraining"] = true;
    }
}
