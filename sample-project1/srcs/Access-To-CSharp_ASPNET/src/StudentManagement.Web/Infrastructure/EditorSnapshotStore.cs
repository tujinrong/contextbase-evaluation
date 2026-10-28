using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text.Json;
using StudentManagement.Web.Models;

namespace StudentManagement.Web.Infrastructure;

/// <summary>
/// Immutable original raw values and optimistic version for one editor, bound
/// to the session and subject. Reset never reads newer database values; reload
/// replaces a snapshot only after the explicit reload action.
/// </summary>
public sealed class EditorSnapshotStore
{
    private sealed record Snapshot(string SessionId, string UserId, string Json, DateTimeOffset Expires);
    private readonly ConcurrentDictionary<string, Snapshot> _snapshots = new();

    public string Capture(StudentInput input, string sessionId, string userId)
    {
        foreach (var pair in _snapshots)
            if (pair.Value.Expires <= DateTimeOffset.UtcNow) _snapshots.TryRemove(pair.Key, out _);
        var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(24));
        var original = Clone(input);
        original.SnapshotToken = token;
        _snapshots[token] = new(sessionId, userId, JsonSerializer.Serialize(original), DateTimeOffset.UtcNow.AddMinutes(30));
        return token;
    }

    public StudentInput? Get(string? token, string sessionId, string userId)
    {
        if (token is null || !_snapshots.TryGetValue(token, out var snapshot) || snapshot.Expires <= DateTimeOffset.UtcNow ||
            snapshot.SessionId != sessionId || !string.Equals(snapshot.UserId, userId, StringComparison.OrdinalIgnoreCase)) return null;
        return JsonSerializer.Deserialize<StudentInput>(snapshot.Json);
    }

    public void Remove(string? token, string sessionId, string userId)
    {
        if (Get(token, sessionId, userId) is not null) _snapshots.TryRemove(token!, out _);
    }

    public static StudentInput Clone(StudentInput input) => JsonSerializer.Deserialize<StudentInput>(JsonSerializer.Serialize(input))!;

    public static IReadOnlyDictionary<string, string> RawValues(StudentInput input)
    {
        var values = new Dictionary<string, string>
        {
        ["Input.StudentNo"] = input.StudentNo ?? "", ["Input.StudentName"] = input.StudentName ?? "",
        ["Input.StudentNameKana"] = input.StudentNameKana ?? "", ["Input.BirthDate"] = input.BirthDate ?? "", ["Input.BirthEra"] = input.BirthEra ?? "",
        ["Input.BirthYear"] = input.BirthYear ?? "", ["Input.BirthMonth"] = input.BirthMonth ?? "", ["Input.BirthDay"] = input.BirthDay ?? "",
        ["Input.GenderCode"] = input.GenderCode ?? "", ["Input.PostalCode"] = input.PostalCode ?? "",
        ["Input.PrefectureCode"] = input.PrefectureCode ?? "", ["Input.AddressLine1"] = input.AddressLine1 ?? "",
        ["Input.AddressLine2"] = input.AddressLine2 ?? "", ["Input.PhoneNumber"] = input.PhoneNumber ?? "",
        ["Input.EmailAddress"] = input.EmailAddress ?? "", ["Input.AdmissionDate"] = input.AdmissionDate ?? "",
        ["Input.EnrollmentStatusCode"] = input.EnrollmentStatusCode ?? "", ["Input.EnrollmentEndDate"] = input.EnrollmentEndDate ?? "",
        ["Input.SchoolYear"] = input.SchoolYear ?? "", ["Input.GradeCode"] = input.GradeCode ?? "", ["Input.ClassId"] = input.ClassId ?? "",
        ["Input.EmergencyContactName"] = input.EmergencyContactName ?? "", ["Input.RelationshipCode"] = input.RelationshipCode ?? "",
        ["Input.EmergencyPhoneNumber"] = input.EmergencyPhoneNumber ?? "", ["Input.Remarks"] = input.Remarks ?? "",
        ["Input.OperationReason"] = input.OperationReason ?? ""
        };
        // The Web editor renders one ISO date input. Legacy era components stay
        // as an adapter compatibility input, not invisible dirty-form fields.
        if (input.BirthDate is not null)
            foreach (var component in new[] { "BirthEra", "BirthYear", "BirthMonth", "BirthDay" }) values.Remove("Input." + component);
        return values;
    }
}
