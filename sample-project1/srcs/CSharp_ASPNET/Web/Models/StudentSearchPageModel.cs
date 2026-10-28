using System.Text.Json;
using StudentManagement.Core;
namespace StudentManagement.Web;
public sealed class StudentSearchPageModel
{
    public StudentSearchInput Criteria {get;set;}=new();
    public required LookupSet Lookups {get;set;}
    public required SearchContextStore.Entry Context {get;set;}
    public required CurrentUser User {get;set;}
    public JsonElement Data {get;set;}
    public string Message {get;set;}="";
    public int PageSize {get;set;}=20;
    public string SortKey {get;set;}="studentNo";
    public string SortDirection {get;set;}="asc";
    public static JsonElement Json(object value)=>JsonSerializer.SerializeToElement(value,new JsonSerializerOptions(JsonSerializerDefaults.Web));
}
