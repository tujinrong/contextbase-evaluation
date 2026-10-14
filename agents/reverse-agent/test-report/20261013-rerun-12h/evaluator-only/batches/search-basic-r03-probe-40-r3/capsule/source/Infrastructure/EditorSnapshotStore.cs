using System.Collections.Concurrent;
using System.Text.Json;
using StudentManagement.Core;
namespace StudentManagement.Web;
public sealed class EditorSnapshotStore
{
    public sealed record Snapshot(string Owner,string Session,long? StudentId,StudentDetail? Detail,StudentSaveInput Original,DateTimeOffset Expires,string? ReturnRevision);
    private readonly ConcurrentDictionary<string,Snapshot> snapshots=new();
    public string Create(CurrentUser user,long? id,StudentDetail? detail,StudentSaveInput original,string? returnRevision=null) {foreach(var old in snapshots.Where(s=>s.Value.Expires<DateTimeOffset.UtcNow))snapshots.TryRemove(old.Key,out _);var token=SearchContextStore.Token();snapshots[token]=new(user.Principal,user.SessionId,id,detail,Copy(original),DateTimeOffset.UtcNow.AddMinutes(30),returnRevision);return token;}
    public Snapshot Get(string token,CurrentUser user,long? id) {if(!snapshots.TryGetValue(token,out var s)||s.Expires<DateTimeOffset.UtcNow)throw new WebFault(409,"編集状態の期限が切れました。再読込してください。");if(s.Owner!=user.Principal||s.Session!=user.SessionId||s.StudentId!=id)throw new WebFault(403,"他の編集状態は使用できません。");return s;}
    public static StudentSaveInput Copy(StudentSaveInput input)=>JsonSerializer.Deserialize<StudentSaveInput>(JsonSerializer.Serialize(input))!;
}
