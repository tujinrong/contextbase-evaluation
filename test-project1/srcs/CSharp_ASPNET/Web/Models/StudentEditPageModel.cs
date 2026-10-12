using StudentManagement.Core;
namespace StudentManagement.Web;
public sealed class StudentEditPageModel
{
    public long? StudentId {get;set;}
    public StudentSaveInput Input {get;set;}=new();
    public required LookupSet Lookups {get;set;}
    public required CurrentUser User {get;set;}
    public StudentDetail? Detail {get;set;}
    public SaveResult? Result {get;set;}
    public string Message {get;set;}="";
    public string SnapshotId {get;set;}="";
    public bool CanEdit=>User.Role!=Role.Viewer;
}
