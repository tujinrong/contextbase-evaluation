using StudentManagement.Core;
namespace StudentManagement.Web;
public static class WebPresentation
{
    public static DateOnly BusinessDate=>DateOnly.FromDateTime(DateTimeOffset.UtcNow.ToOffset(TimeSpan.FromHours(9)).DateTime);
    public static int SchoolYear=>BusinessDate.Month<4 ? BusinessDate.Year-1 : BusinessDate.Year;
    public static string Time(DateTimeOffset value)=>value.ToOffset(TimeSpan.FromHours(9)).ToString("yyyy/MM/dd HH:mm:ss",System.Globalization.CultureInfo.InvariantCulture);
    public static object Lookups(LookupSet set,string usage="search",StudentDetail? existing=null,int? year=null,string? grade=null,string? status=null,string? admission=null,string? end=null)
    {
        if(usage is not ("search" or "register")) throw new WebFault(400,"候補用途が不正です。");
        var today=BusinessDate; bool search=usage=="search"; var draft=existing?.Draft;
        var codes=set.Codes.Select(c=>new { categoryId=c.CategoryId,value=c.CodeValue,name=c.CodeName,selectable=search||(c.IsActive&&c.ValidFrom<=today&&(c.ValidTo is null||today<=c.ValidTo)),note=c.IsActive?"":"停止" });
        var classes=set.Classes.Where(c=>(year is null||c.SchoolYear==year)&&(string.IsNullOrEmpty(grade)||c.GradeCode==grade)).Select(c=> {
            bool terminal=status is "03" or "04"; bool overlap=DateOnly.TryParse(admission,out var a)&&DateOnly.TryParse(end,out var e)&&c.ValidFrom<=e&&a<=c.ValidTo;
            bool active=c.IsActive&&c.ValidFrom<=today&&today<=c.ValidTo; bool same=draft?.ClassId==c.ClassId;
            return new { classId=c.ClassId.ToString(System.Globalization.CultureInfo.InvariantCulture),c.SchoolYear,c.GradeCode,gradeName=set.Codes.FirstOrDefault(x=>x.CategoryId=="GRADE"&&x.CodeValue==c.GradeCode)?.CodeName??"不整合",c.ClassCode,c.ClassName,selectable=search||same||(terminal?overlap:active),note=!c.IsActive?"停止":today<c.ValidFrom||today>c.ValidTo?"期間外":"",occupancy=(int?)c.Occupied,c.Capacity };
        });
        return new { codes,classes,years=set.Classes.Select(c=>c.SchoolYear).Distinct().OrderDescending() };
    }
    public static object Row(StudentRow r)=>new { studentId=r.StudentId.ToString(System.Globalization.CultureInfo.InvariantCulture),r.StudentNo,r.StudentName,r.StudentNameKana,r.BirthDateWareki,r.SchoolYear,r.GradeName,r.ClassCode,r.ClassName,enrollmentName=r.EnrollmentStatusName,addressDisplay=r.Address,r.PhoneNumber,updatedAt=Time(r.UpdatedAt) };
    public static Dictionary<string,string[]> Errors(IEnumerable<FieldError> errors)=>errors.GroupBy(e=>e.Field).ToDictionary(g=>g.Key,g=>g.Select(e=>e.Message).ToArray());
    public static object Error(string outcome,string message,string id="E-COM-004",IEnumerable<FieldError>? errors=null,string? requestId=null,bool retry=false)=>new { outcome,messageId=id,message,fieldErrors=Errors(errors??[]),correlationId=requestId??Guid.NewGuid().ToString(),retryBySearch=retry };
    public static int Status(Outcome outcome)=>outcome switch { Outcome.Saved=>200,Outcome.NoChange=>200,Outcome.ValidationFailed=>422,Outcome.Forbidden=>403,Outcome.NotFound=>404,Outcome.Conflict or Outcome.ConfirmationRequired=>409,_=>503 };
    private static (string Id,string Message) SaveMessage(Outcome outcome)=>outcome switch {
        Outcome.Saved=>("I-STU-001","保存しました。"), Outcome.NoChange=>("I-STU-004","変更はありません。"),
        Outcome.ConfirmationRequired=>("W-STU-101","同一人物の候補があります。確認してください。"),
        Outcome.ValidationFailed=>("E-COM-004","入力を確認してください。"),Outcome.Forbidden=>("E-COM-004","この操作を実行する権限がありません。"),
        Outcome.NotFound=>("E-COM-004","対象は存在しません。"),Outcome.Conflict=>("E-COM-004","データが変更されています。再読込してください。"),
        Outcome.Unknown=>("E-COM-004","処理結果が不明です。再送せず検索して確認してください。"),_=>("E-COM-004","処理を完了できませんでした。") };
    public static object Save(SaveResult r)=>new { outcome=char.ToLowerInvariant(r.Outcome.ToString()[0])+r.Outcome.ToString()[1..],studentId=r.StudentId?.ToString(System.Globalization.CultureInfo.InvariantCulture),rowVersion=r.RowVersion?.ToString(System.Globalization.CultureInfo.InvariantCulture),messageId=r.Errors.FirstOrDefault()?.Code??SaveMessage(r.Outcome).Id,message=r.Errors.FirstOrDefault()?.Message??SaveMessage(r.Outcome).Message,fieldErrors=Errors(r.Errors),correlationId=r.RequestId??Guid.NewGuid().ToString(),retryBySearch=r.Outcome==Outcome.Unknown,duplicateToken=r.ConfirmationToken,candidateCount=r.CandidateCount,candidates=(r.Candidates??[]).Take(20).Select(c=>new { studentId=c.StudentId.ToString(System.Globalization.CultureInfo.InvariantCulture),c.StudentNo,c.StudentName,birthDate=c.BirthDate.ToString("yyyy-MM-dd"),c.BirthDateWareki,classLabel=c.ClassName??"未所属" }) };
}
