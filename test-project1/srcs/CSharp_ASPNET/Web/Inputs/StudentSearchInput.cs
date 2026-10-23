using System.Text.Json.Serialization;
using StudentManagement.Core;
namespace StudentManagement.Web;
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed class StudentSearchInput
{
    public string StudentNo { get; set; } = "";
    public string Name { get; set; } = "";
    public string? ClassId { get; set; }
    public string[] StatusCodes { get; set; } = ["01","02"];
    public SearchCriteria ToCriteria(int size,string key,string direction) => SearchCriteria.FromRaw(
        StudentNo,Name,IdParser.Optional(ClassId,"Criteria.ClassId"),StatusCodes,size,key,direction);
}
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public class ContextRequest { public string ContextId {get;set;}=""; public string ContextRevision {get;set;}=""; }
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed class SearchRequest : ContextRequest { public StudentSearchInput Criteria {get;set;}=new(); public int PageSize {get;set;}=20; public string SortKey {get;set;}="studentNo"; public string SortDirection {get;set;}="asc"; }
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed class PageRequest : ContextRequest { public int Page {get;set;}=1; public int PageSize {get;set;}=20; public string SortKey {get;set;}="studentNo"; public string SortDirection {get;set;}="asc"; }
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed class OptionsRequest { public string Usage {get;set;}="search"; public int? SchoolYear {get;set;} public string? GradeCode {get;set;} public string? StudentId {get;set;} public string? EnrollmentStatusCode {get;set;} public string? AdmissionDate {get;set;} public string? EnrollmentEndDate {get;set;} }
