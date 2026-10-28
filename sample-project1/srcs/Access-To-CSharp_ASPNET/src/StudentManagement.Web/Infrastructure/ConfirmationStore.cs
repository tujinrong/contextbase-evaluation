using System.Collections.Concurrent;
using System.Security.Cryptography;

namespace StudentManagement.Web.Infrastructure;

/// <summary>
/// One-use confirmation state stays on the server, bound to the browser session
/// and authenticated subject. Hidden fields cannot authorize a different draft.
/// This single-node store intentionally expires across application restarts.
/// </summary>
public sealed class ConfirmationStore
{
    private sealed record Entry(string SessionId, string UserId, object Payload, DateTimeOffset Expires);
    private readonly ConcurrentDictionary<string, Entry> _entries = new();
    private static readonly TimeSpan Lifetime = TimeSpan.FromMinutes(10);

    public string Create<T>(string sessionId, string userId, T payload) where T : class
    {
        foreach (var pair in _entries)
            if (pair.Value.Expires <= DateTimeOffset.UtcNow) _entries.TryRemove(pair.Key, out _);
        var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(24));
        _entries[token] = new(sessionId, userId, payload, DateTimeOffset.UtcNow.Add(Lifetime));
        return token;
    }

    public T? Peek<T>(string token, string sessionId, string userId) where T : class =>
        _entries.TryGetValue(token, out var entry) && IsValid(entry, sessionId, userId) ? entry.Payload as T : null;

    public T? Consume<T>(string token, string sessionId, string userId) where T : class
    {
        if (!_entries.TryGetValue(token, out var existing) || existing.Payload is not T || !IsValid(existing, sessionId, userId)) return null;
        return _entries.TryRemove(token, out var entry) && IsValid(entry, sessionId, userId) ? entry.Payload as T : null;
    }

    public void Cancel(string token, string sessionId, string userId)
    {
        if (_entries.TryGetValue(token, out var entry) && IsValid(entry, sessionId, userId)) _entries.TryRemove(token, out _);
    }

    public IReadOnlyList<T> CancelWhere<T>(string sessionId, string userId, Predicate<T> predicate) where T : class
    {
        var removed = new List<T>();
        foreach (var pair in _entries)
            if (IsValid(pair.Value, sessionId, userId) && pair.Value.Payload is T payload && predicate(payload) &&
                _entries.TryRemove(pair.Key, out _)) removed.Add(payload);
        return removed;
    }

    private static bool IsValid(Entry entry, string sessionId, string userId) =>
        entry.Expires > DateTimeOffset.UtcNow && entry.SessionId == sessionId &&
        string.Equals(entry.UserId, userId, StringComparison.OrdinalIgnoreCase);
}
