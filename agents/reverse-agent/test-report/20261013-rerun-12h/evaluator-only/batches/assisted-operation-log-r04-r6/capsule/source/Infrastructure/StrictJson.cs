using System.Text.Json;
using System.Text.Json.Serialization;
namespace StudentManagement.Web;
public static class StrictJson
{
    private static readonly JsonSerializerOptions options=new(JsonSerializerDefaults.Web) { UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow,PropertyNameCaseInsensitive=false,MaxDepth=16 };
    public static async Task<T> Read<T>(HttpRequest request,CancellationToken ct) {
        if(request.ContentType?.StartsWith("application/json",StringComparison.OrdinalIgnoreCase)!=true) throw new WebFault(400,"JSON要求を指定してください。");
        if(request.ContentLength>65536) throw new WebFault(400,"要求本文は64KiB以内で指定してください。");
        using var buffer=new MemoryStream(); var part=new byte[4096]; int count; while((count=await request.Body.ReadAsync(part,ct))>0) { if(buffer.Length+count>65536) throw new WebFault(400,"要求本文は64KiB以内で指定してください。"); buffer.Write(part,0,count); }
        try { using var document=JsonDocument.Parse(buffer.ToArray(),new() { MaxDepth=16 }); Check(document.RootElement); return document.RootElement.Deserialize<T>(options) ?? throw new JsonException(); }
        catch(JsonException) { throw new WebFault(400,"要求の項目名・型・構造が不正です。"); }
    }
    private static void Check(JsonElement value) { if(value.ValueKind==JsonValueKind.Object) { var seen=new HashSet<string>(StringComparer.Ordinal); foreach(var property in value.EnumerateObject()) { if(!seen.Add(property.Name)) throw new JsonException("同名項目"); Check(property.Value); } } else if(value.ValueKind==JsonValueKind.Array) foreach(var item in value.EnumerateArray()) Check(item); }
}
