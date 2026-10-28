using System.Security.Claims;
using StudentManagement.Core;
namespace StudentManagement.Web;
public sealed class RequestIdentity(IHttpContextAccessor accessor)
{
    private HttpContext Context => accessor.HttpContext ?? throw new InvalidOperationException("HTTP要求がありません。");
    public CurrentUser CurrentUser {
        get { var p=Context.User; if(p.Identity?.IsAuthenticated!=true) throw new WebFault(401,"認証が失効しました。再認証してください。");
            var id=p.FindFirstValue(ClaimTypes.NameIdentifier); var session=p.FindFirstValue("login_session"); var role=p.FindFirstValue(ClaimTypes.Role);
            if(string.IsNullOrWhiteSpace(id)||id.EnumerateRunes().Count()>64||string.IsNullOrWhiteSpace(session)||session.Length>64||!Enum.TryParse<Role>(role,out var r)) throw new WebFault(401,"認証情報を確認できません。"); return new(id,session,r); }
    }
    public string TabId => Context.Request.Headers["X-Tab-Id"].FirstOrDefault() ?? Context.Request.Query["tabId"].FirstOrDefault() ?? "";
    public void Read() { _=CurrentUser; }
    public void CreateOrUpdate() { if(CurrentUser.Role==Role.Viewer) throw new WebFault(403,"この操作を実行する権限がありません。"); }
    public void Administrator() { if(CurrentUser.Role!=Role.Administrator) throw new WebFault(403,"管理者権限が必要です。"); }
    public object Permissions => new { read=true,create=CurrentUser.Role!=Role.Viewer,update=CurrentUser.Role!=Role.Viewer,@delete=CurrentUser.Role==Role.Administrator,maintain=CurrentUser.Role==Role.Administrator };
}
public sealed class WebFault(int status,string message,string? field=null,string messageId="E-COM-004") : Exception(message) { public int Status {get;}=status; public string? Field {get;}=field; public string MessageId {get;}=messageId; }
