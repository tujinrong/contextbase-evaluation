using System.Text.Json.Serialization;
namespace StudentManagement.Web;
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed class StudentDeleteInput { public string ExpectedVersion {get;set;}=""; public string Reason {get;set;}=""; public bool Confirmed {get;set;} public string? ReturnContextId {get;set;} }
