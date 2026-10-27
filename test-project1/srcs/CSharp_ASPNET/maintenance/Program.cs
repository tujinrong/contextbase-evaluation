using System.Text.Json;
using System.Text.Json.Serialization;
using StudentManagement.Core;
if(args.Length!=2||args[0] is not ("class" or "code")) { Console.Error.WriteLine("Usage: StudentMaintenance class|code approved-input.json");return 2; }
var connection=Environment.GetEnvironmentVariable("STUDENT_DB_CONNECTION");
if(string.IsNullOrEmpty(connection)) { Console.Error.WriteLine("STUDENT_DB_CONNECTIONを設定してください。");return 2; }
try {
    var data=await File.ReadAllBytesAsync(args[1]); if(data.Length>65536) throw new ArgumentException("入力サイズが上限を超えています。");
    using var document=JsonDocument.Parse(data); if(document.RootElement.ValueKind!=JsonValueKind.Object||document.RootElement.EnumerateObject().GroupBy(property=>property.Name,StringComparer.Ordinal).Any(group=>group.Count()>1)) throw new ArgumentException("JSON項目が不正または重複しています。");
    var options=new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase,UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow};
    var profileText=Environment.GetEnvironmentVariable("STUDENT_DATABASE_PROFILE")??"Native";
    if(!Enum.TryParse<StudentDatabaseProfile>(profileText,false,out var profile)||!Enum.IsDefined(profile))throw new ArgumentException("STUDENT_DATABASE_PROFILEはNativeまたはSharedAccessを指定してください。");
    var service=new MasterMaintenanceService(connection,profile);
    var result=args[0]=="class"?await service.SaveClassAsync(JsonSerializer.Deserialize<ClassChange>(data,options)??throw new ArgumentException("入力なし")):await service.SaveCodeAsync(JsonSerializer.Deserialize<CodeChange>(data,options)??throw new ArgumentException("入力なし"));
    Console.WriteLine(JsonSerializer.Serialize(result,options));return result.Outcome is Outcome.Saved or Outcome.NoChange?0:1;
} catch(InputValidationException e) { Console.Error.WriteLine(string.Join('\n',e.Errors.Select(error=>error.Message)));return 1; }
catch(ArgumentException e) { Console.Error.WriteLine(e.Message);return 1; }
catch(UnauthorizedAccessException) { Console.Error.WriteLine("管理者権限がありません。");return 1; }
catch(Exception) { Console.Error.WriteLine("処理結果を確認できません。再実行前にマスタを照会してください。");return 1; }
