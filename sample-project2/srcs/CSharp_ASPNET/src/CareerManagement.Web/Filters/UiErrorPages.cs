using CareerManagement.Application;
using CareerManagement.Infrastructure.State;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using Microsoft.AspNetCore.Mvc.ViewFeatures;

namespace CareerManagement.Web.Filters;
public static class UiErrorPages
{
    public static bool IsDocument(HttpRequest request)=>HttpMethods.IsGet(request.Method)&&
        (request.Path.StartsWithSegments("/employees")||request.Path.StartsWithSegments("/codes")||request.Path.StartsWithSegments("/menu"));
    public static ViewResult Create(HttpContext context,Outcome outcome,ScreenStateStore states)
    {
        var path=context.Request.Path.Value??"/menu";
        var screen=path.StartsWith("/codes",StringComparison.Ordinal)?"F06":path.Contains("/edit",StringComparison.Ordinal)||path=="/employees/new"?"F04":path.StartsWith("/employees",StringComparison.Ordinal)?"F03":"F02";
        var actor=context.Items["Actor"] as Actor;
        var ui=actor is null?null:states.Info(states.Add(new NavigationState(actor.SessionId)),path);
        var data=new ViewDataDictionary(new EmptyModelMetadataProvider(),new ModelStateDictionary())
        {
            Model=new UiErrorVm(outcome,ui),["ScreenId"]=screen,["Title"]=outcome.CommitState==CommitState.Committed?"保存後の表示を確認できません":"画面を表示できません",
            ["NoUiBootstrap"]=ui is null,["IsUiError"]=true
        };
        return new ViewResult{ViewName="~/Views/Shared/UiError.cshtml",ViewData=data,
            StatusCode=outcome.MessageId=="MSG-041"&&context.Request.Query.ContainsKey("nav")?410:HttpJson.Status(outcome)};
    }
}
