using System.Collections.Concurrent;
using StudentManagement.Core;
namespace StudentManagement.Web;
public sealed class FlashMessageStore
{
    private readonly ConcurrentDictionary<string,(string Message,DateTimeOffset Expires)> messages=new();
    private static string Key(CurrentUser user,string context)=>user.Principal+"\0"+user.SessionId+"\0"+context;
    public void Put(CurrentUser user,string context,string message)=>messages[Key(user,context)]=(message,DateTimeOffset.UtcNow.AddMinutes(10));
    public string Take(CurrentUser user,string context)=>messages.TryRemove(Key(user,context),out var value)&&value.Expires>=DateTimeOffset.UtcNow?value.Message:"";
}
