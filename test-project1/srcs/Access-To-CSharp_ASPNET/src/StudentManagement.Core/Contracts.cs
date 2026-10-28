namespace StudentManagement.Core;

public enum Role { Reader, Staff, Admin }

/// <summary>The request's authenticated subject and database-resolved role.</summary>
public sealed record Actor(string UserId, Role Role);

/// <summary>A stable domain outcome suitable for HTML and HTTP adapters.</summary>
public sealed class BusinessException(string code, string message, string? field = null) : Exception(message)
{
    public string Code { get; } = code;
    public string? Field { get; } = field;
}
