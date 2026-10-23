using System.Buffers.Binary;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Options;
using StudentManagement.Core;

namespace StudentManagement.Web;

// Small, explicitly enabled deployment adapter for a single server-configured owner.
public sealed class LocalLogin(IConfiguration configuration, TimeProvider clock)
{
    public sealed record Settings(string Username, string PasswordHash, Role Role, string Fingerprint);
    private readonly object gate = new();
    private readonly PasswordHasher<string> hasher = new(Options.Create(new PasswordHasherOptions { IterationCount = 210000 }));
    private int failures;
    private DateTimeOffset windowStarted;
    private DateTimeOffset lockedUntil;
    private static readonly TimeSpan Window = TimeSpan.FromMinutes(5);

    public Settings? ReadSettings()
    {
        if (!configuration.GetValue<bool>("LocalLogin:Enabled")) return null;
        var username = configuration["LocalLogin:Username"];
        var hash = configuration["LocalLogin:PasswordHash"];
        var roleText = configuration["LocalLogin:Role"];
        if (string.IsNullOrWhiteSpace(username) || username.Length > 64 || username.Any(char.IsControl))
            throw new InvalidOperationException("LocalLogin:Username must contain 1 to 64 characters without control characters.");
        if (!ValidHash(hash)) throw new InvalidOperationException("LocalLogin:PasswordHash must be a valid IdentityV3 password hash.");
        if (!Enum.TryParse<Role>(roleText, out var role) || !Enum.IsDefined(role) || roleText != role.ToString())
            throw new InvalidOperationException("LocalLogin:Role must be Viewer, Staff or Administrator.");
        var fingerprint = Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(username + "\0" + hash + "\0" + roleText)));
        return new(username, hash!, role, fingerprint);
    }

    private static bool ValidHash(string? hash)
    {
        if (hash is null || hash.Length > 512) return false;
        try
        {
            var bytes = Convert.FromBase64String(hash);
            if (bytes.Length != 61 || bytes[0] != 1) return false;
            var prf = BinaryPrimitives.ReadUInt32BigEndian(bytes.AsSpan(1, 4));
            var iterations = BinaryPrimitives.ReadUInt32BigEndian(bytes.AsSpan(5, 4));
            var saltLength = BinaryPrimitives.ReadUInt32BigEndian(bytes.AsSpan(9, 4));
            return prf == 2 && iterations is >= 100000 and <= 1000000 && saltLength == 16;
        }
        catch (FormatException) { return false; }
    }

    public ClaimsPrincipal? Authenticate(string? username, string? password)
    {
        // Serialize verification and the shared failure budget; parallel attempts cannot pass the limit.
        lock (gate)
        {
            var settings = ReadSettings();
            if (settings is null) return null;
            var now = clock.GetUtcNow();
            if (now < lockedUntil) return null;
            if (now - windowStarted >= Window) { failures = 0; windowStarted = now; }
            // Every username consumes the same budget, and bounded inputs receive the same hash work.
            var validInput = username is { Length: > 0 and <= 64 } && password is { Length: > 0 and <= 1024 };
            var verified = hasher.VerifyHashedPassword(settings.Username, settings.PasswordHash, validInput ? password! : "invalid-input");
            if (!validInput || !string.Equals(username, settings.Username, StringComparison.Ordinal) || verified == PasswordVerificationResult.Failed)
            {
                if (failures++ == 0) windowStarted = now;
                if (failures >= 5) lockedUntil = now + Window;
                return null;
            }
            failures = 0;
            return new ClaimsPrincipal(new ClaimsIdentity([
                new Claim(ClaimTypes.NameIdentifier, settings.Username),
                new Claim(ClaimTypes.Name, settings.Username),
                new Claim(ClaimTypes.Role, settings.Role.ToString()),
                new Claim("login_session", SearchContextStore.Token()),
                new Claim("login_source", "local"),
                new Claim("login_config", settings.Fingerprint)
            ], CookieAuthenticationDefaults.AuthenticationScheme));
        }
    }

    public bool AcceptsCookie(ClaimsPrincipal principal)
    {
        if (!principal.HasClaim("login_source", "local")) return true;
        var settings = ReadSettings();
        return settings is not null && principal.FindFirstValue("login_config") == settings.Fingerprint;
    }
}
