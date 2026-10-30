using System.Globalization;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using CareerManagement.Application;

namespace CareerManagement.Web.Filters;
public static class HttpJson
{
    public static JsonSerializerOptions Options {get;}=Create();
    private static JsonSerializerOptions Create(){var o=new JsonSerializerOptions(JsonSerializerDefaults.Web);Configure(o);return o;}
    public static void Configure(JsonSerializerOptions o)
    {
        o.UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow;o.PropertyNameCaseInsensitive=false;o.MaxDepth=16;
        o.Converters.Add(new JsonStringEnumConverter(allowIntegerValues:false));o.Converters.Add(new DecimalIdConverter());
    }
    public static async Task<T> ReadAsync<T>(HttpRequest request,CancellationToken ct)
    {
        if(!request.HasJsonContentType())throw new BadHttpRequestException("JSON required.",415);
        using var doc=await JsonDocument.ParseAsync(request.Body,new JsonDocumentOptions{MaxDepth=16},ct);
        Shape(doc.RootElement,typeof(T));return doc.RootElement.Deserialize<T>(Options)??throw new JsonException("Null request.");
    }
    private static void Shape(JsonElement element,Type type)
    {
        var nullable=Nullable.GetUnderlyingType(type);if(nullable is not null){if(element.ValueKind==JsonValueKind.Null)return;type=nullable;}
        if(type.IsArray)
        {
            if(element.ValueKind!=JsonValueKind.Array)throw new JsonException("Array required.");
            if(element.GetArrayLength()>1024)throw new JsonException("Array limit.");
            foreach(var item in element.EnumerateArray())Shape(item,type.GetElementType()!);return;
        }
        if(type==typeof(string))
        {
            if(element.ValueKind==JsonValueKind.String)
            {
                try{Validation.TechnicalRaw(element.GetString());}catch(ArgumentException){throw new JsonException("Raw transport bounds.");}
            }
            return;
        }
        if(type.IsPrimitive)
        {
            if(element.ValueKind==JsonValueKind.Number&&(element.GetRawText().Contains('e')||element.GetRawText().Contains('E')))
                throw new JsonException("Exponent notation refused.");
            return;
        }
        if(type.IsEnum||type==typeof(Guid)||type==typeof(DateOnly))return;
        if(element.ValueKind==JsonValueKind.Null)return;
        if(element.ValueKind!=JsonValueKind.Object)throw new JsonException("Object required.");
        var properties=type.GetProperties(BindingFlags.Instance|BindingFlags.Public).Where(p=>p.GetCustomAttribute<JsonIgnoreAttribute>() is null).ToDictionary(p=>JsonNamingPolicy.CamelCase.ConvertName(p.Name),StringComparer.Ordinal);
        var seen=new HashSet<string>(StringComparer.Ordinal);var nullability=new NullabilityInfoContext();
        foreach(var property in element.EnumerateObject())
        {
            if(!seen.Add(property.Name)||!properties.TryGetValue(property.Name,out var info))throw new JsonException("Unknown or duplicate field.");
            if(property.Value.ValueKind==JsonValueKind.Null&&nullability.Create(info).ReadState==NullabilityState.NotNull&&Nullable.GetUnderlyingType(info.PropertyType)is null)throw new JsonException("Required value.");
            Shape(property.Value,info.PropertyType);
        }
        if(seen.Count!=properties.Count)throw new JsonException("Missing field.");
    }
    public static int Status(Outcome o)=>o.Kind switch {"Expired"=>401,"Forbidden"=>403,"NotFound"=>404,"Conflict"=>409,"UiExpired"=>409,"Busy"=>503,"RolledBack"=>503,"ResultUnknown"=>503,"Corrupt"=>503,"Validation"=>422,_=>200};
}
public sealed class DecimalIdConverter:JsonConverter<long>
{
    public override long Read(ref Utf8JsonReader reader,Type type,JsonSerializerOptions options)
    {
        if(reader.TokenType!=JsonTokenType.String)throw new JsonException("Decimal string ID required.");var value=reader.GetString();
        if(string.IsNullOrEmpty(value)||value.Any(x=>x is <'0' or >'9')||!long.TryParse(value,NumberStyles.None,CultureInfo.InvariantCulture,out var id)||id<=0)throw new JsonException("Invalid ID.");return id;
    }
    public override void Write(Utf8JsonWriter writer,long value,JsonSerializerOptions options)=>writer.WriteStringValue(value.ToString(CultureInfo.InvariantCulture));
}
