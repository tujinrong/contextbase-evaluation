using StudentManagement.Core;
namespace StudentManagement.Web;
public sealed class WebStudentCoordinator(IStudentService service,RequestIdentity identity,SearchContextStore contexts)
{
    public SearchContextStore.Entry NewContext(string? tab=null)=>contexts.Create(identity.CurrentUser,tab);
    public void CheckReturn(string? id) { if(!string.IsNullOrEmpty(id)) contexts.Get(id,identity.CurrentUser); }
    public async Task<object> Search(SearchRequest request,string? tab,CancellationToken ct) {
        identity.Read();
        return await contexts.Use(request,identity.CurrentUser,tab,async entry=>{
            if(ResetLegacy(entry))return Present(entry,null);
            SearchCriteria criteria;
            try{criteria=request.Criteria.ToCriteria(request.PageSize,request.SortKey,request.SortDirection);}
            catch(InputValidationException e){var first=e.Errors[0];throw new WebFault(422,first.Message,first.Field,first.Code);}
            var result=await service.SearchAsync(criteria,ct);EnsureSearch(result);
            entry.Raw=SearchContextStore.CopyInput(request.Criteria);entry.Applied=SearchContextStore.Copy(criteria);entry.LastResult=result;entry.Revision++;
            return Present(entry,result);
        },ct);
    }
    public async Task<object> Page(PageRequest request,string? tab,CancellationToken ct){
        identity.Read();return await contexts.Use(request,identity.CurrentUser,tab,async entry=>{
            if(ResetLegacy(entry))return Present(entry,null);
            if(entry.Applied is null)throw new WebFault(409,"先に検索してください。");
            if(request.Page<1||request.PageSize is not (20 or 50 or 100)||request.SortKey is not ("studentNo" or "name" or "admissionDate" or "updatedAt")||request.SortDirection is not ("asc" or "desc"))throw new WebFault(422,"ページと並び順を確認してください。",messageId:"E-COM-003");
            var c=SearchContextStore.Copy(entry.Applied);
            c.Page=c.PageSize!=request.PageSize||c.SortKey!=request.SortKey||c.SortDirection!=request.SortDirection?1:request.Page;
            c.PageSize=request.PageSize;c.SortKey=request.SortKey;c.SortDirection=request.SortDirection;
            return await ReadPage(entry,c,ct);
        },ct);
    }
    public async Task<object> Resume(ContextRequest request,string? tab,CancellationToken ct){
        identity.Read();return await contexts.Use(request,identity.CurrentUser,tab,async entry=>{
            if(ResetLegacy(entry)||entry.Applied is null)return Present(entry,null);
            return await ReadPage(entry,SearchContextStore.Copy(entry.Applied),ct);
        },ct);
    }
    private async Task<object> ReadPage(SearchContextStore.Entry entry,SearchCriteria criteria,CancellationToken ct){
        var result=await service.SearchAsync(criteria,ct);EnsureSearch(result);
        var last=Math.Max(1,(result.Count+criteria.PageSize-1)/criteria.PageSize);
        if(!result.LimitExceeded&&criteria.Page>last){criteria.Page=last;result=await service.SearchAsync(criteria,ct);EnsureSearch(result);}
        entry.Applied=SearchContextStore.Copy(criteria);entry.LastResult=result;entry.Revision++;return Present(entry,result);
    }
    public Task<object> Clear(ContextRequest request,string? tab,CancellationToken ct){
        identity.Read();return contexts.Use(request,identity.CurrentUser,tab,entry=>{
            if(!ResetLegacy(entry)){entry.Raw=new();entry.Applied=null;entry.LastResult=null;entry.Revision++;}
            return Task.FromResult(Present(entry,null));
        },ct);
    }
    private static bool ResetLegacy(SearchContextStore.Entry entry){
        entry.FormatReset=false;if(entry.FormatVersion==SearchContextStore.CurrentFormat)return false;
        entry.Raw=new();entry.Applied=null;entry.LastResult=null;entry.FormatVersion=SearchContextStore.CurrentFormat;entry.FormatReset=true;entry.Revision++;return true;
    }
    public async Task<object> Options(OptionsRequest request,CancellationToken ct) { identity.Read(); if(request.Usage=="register") identity.CreateOrUpdate(); StudentDetail? existing=null; if(!string.IsNullOrEmpty(request.StudentId)) existing=await service.GetAsync(IdParser.Required(request.StudentId,"REG-INT-012"),ct) ?? throw new WebFault(404,"学生情報が見つかりません。",messageId:"E-STU-103"); return WebPresentation.Lookups(await service.LookupAsync(request.Usage=="register",ct),request.Usage,existing,request.SchoolYear,request.GradeCode,request.EnrollmentStatusCode,request.AdmissionDate,request.EnrollmentEndDate); }
    public async Task<(StudentDetail? Detail,StudentSaveInput Form,LookupSet Lookups)> Edit(long? id,string? contextId,CancellationToken ct) { identity.Read();CheckReturn(contextId); if(id is null) identity.CreateOrUpdate(); var detail=id is null?null:await service.GetAsync(id.Value,ct)??throw new WebFault(404,"学生情報が見つかりません。",messageId:"E-STU-103");var lookup=await service.LookupAsync(ct);return(detail,StudentSaveInput.From(detail,contextId,lookup),lookup); }
    public async Task<SaveResult> Save(long? id,StudentSaveInput input,CancellationToken ct) { identity.CreateOrUpdate();CheckReturn(input.ReturnContextId); return await service.SaveAsync(input.ToRequest(id),ct); }
    public async Task<SaveResult> Delete(long id,StudentDeleteInput input,CancellationToken ct) { identity.Administrator(); CheckReturn(input.ReturnContextId);if(!input.Confirmed) throw new WebFault(422,"削除対象と理由を確認してください。","REG-026");return await service.DeleteAsync(id,IdParser.Required(input.ExpectedVersion,"REG-INT-013"),input.Reason,ct); }
    private static void EnsureSearch(SearchResult result) { if(result.Outcome is not (Outcome.Saved or Outcome.NoChange)) { var error=result.Errors.FirstOrDefault();throw new WebFault(WebPresentation.Status(result.Outcome),error?.Message??"検索できませんでした。",error?.Field,error?.Code??"E-COM-004"); } }
    public static object Present(SearchContextStore.Entry entry,SearchResult? result) { var c=entry.Applied??new SearchCriteria(); return new { outcome=result is null?"unsearched":result.LimitExceeded?"tooMany":result.Count==0?"empty":"found",totalCount=result is null||result.LimitExceeded?(int?)null:result.Count,items=(result?.Items??[]).Select(WebPresentation.Row),page=c.Page,pageSize=c.PageSize,sortKey=c.SortKey,sortDirection=c.SortDirection,searchedAt=result is null?null:WebPresentation.Time(result.SearchedAt),contextId=entry.Id,contextRevision=entry.Revision.ToString(System.Globalization.CultureInfo.InvariantCulture),formatVersion=entry.FormatVersion,messageId=entry.FormatReset?"W-SRC-002":null,message=entry.FormatReset?"検索条件の形式が更新されました。条件を再指定して検索してください。":null,criteria=entry.Raw }; }
}
