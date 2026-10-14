using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text.Json;
using StudentManagement.Core;
namespace StudentManagement.Web;
// 共通12: Single-node, server-held criteria; no personal information in cookies or URLs.
public sealed class SearchContextStore
{
    public sealed class Entry(string owner,string session,string tab) { public string Id {get;}=Token(); public string Owner {get;}=owner; public string Session {get;}=session; public string Tab {get;}=tab; public DateTimeOffset Expires {get;set;}=DateTimeOffset.UtcNow.AddMinutes(30); public long Revision {get;set;}=1; public SearchCriteria? Applied {get;set;} public SearchResult? LastResult {get;set;} public SemaphoreSlim Gate {get;}=new(1,1); }
    private readonly ConcurrentDictionary<string,Entry> entries=new();
    public static string Token()=>Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32));
    public Entry Create(CurrentUser user,string? tab=null) { foreach(var old in entries.Where(e=>e.Value.Expires<DateTimeOffset.UtcNow)) entries.TryRemove(old.Key,out _); var entry=new Entry(user.Principal,user.SessionId,string.IsNullOrEmpty(tab)?Token():tab); entries[entry.Id]=entry; return entry; }
    public Entry Get(string? id,CurrentUser user,string? tab=null) { if(id is null||!entries.TryGetValue(id,out var e)||e.Expires<DateTimeOffset.UtcNow) throw new WebFault(409,"検索状態の期限が切れました。検索画面を開き直してください。",messageId:"W-SRC-002"); if(e.Owner!=user.Principal||e.Session!=user.SessionId||(!string.IsNullOrEmpty(tab)&&e.Tab!=tab)) throw new WebFault(403,"他の利用者・画面の検索状態は使用できません。"); return e; }
    public async Task<T> Use<T>(ContextRequest request,CurrentUser user,string? tab,Func<Entry,Task<T>> operation,CancellationToken ct) { var e=Get(request.ContextId,user,tab); await e.Gate.WaitAsync(ct); try { Get(e.Id,user,tab); if(request.ContextRevision!=e.Revision.ToString(System.Globalization.CultureInfo.InvariantCulture)) throw new WebFault(409,"検索状態が更新されています。画面を開き直してください。"); if(e.Revision==long.MaxValue) throw new WebFault(409,"検索状態の版上限です。画面を開き直してください。"); var result=await operation(e); e.Expires=DateTimeOffset.UtcNow.AddMinutes(30); return result; } finally { e.Gate.Release(); } }
    public static SearchCriteria Copy(SearchCriteria value)=>JsonSerializer.Deserialize<SearchCriteria>(JsonSerializer.Serialize(value))!;
}
