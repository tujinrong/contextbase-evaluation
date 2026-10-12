Imports System.Text.Json
Imports System.Text.Json.Serialization
Imports StudentManagement.WinForms.Domain
Module Program
 Function Main(args As String()) As Integer
  Return RunAsync(args).GetAwaiter().GetResult()
 End Function
 Private Async Function RunAsync(args As String()) As Task(Of Integer)
  If args.Length<>2 OrElse (args(0)<>"class" AndAlso args(0)<>"code") Then
   Console.Error.WriteLine("Usage: StudentMaintenance class|code approved-input.json") : Return 2
  End If
  Dim connection=Environment.GetEnvironmentVariable("STUDENT_DB_CONNECTION")
  If String.IsNullOrWhiteSpace(connection) Then
   Console.Error.WriteLine("STUDENT_DB_CONNECTIONを設定してください。") : Return 2
  End If
  Try
   Dim bytes=Await System.IO.File.ReadAllBytesAsync(args(1))
   Using document=JsonDocument.Parse(bytes)
    If document.RootElement.ValueKind<>JsonValueKind.Object Then Throw New ArgumentException("JSONはオブジェクト必須です。")
    Dim names As New HashSet(Of String)(StringComparer.Ordinal)
    For Each item In document.RootElement.EnumerateObject()
     If Not names.Add(item.Name) Then Throw New ArgumentException("JSONの項目が重複しています。")
    Next
   End Using
   Dim options As New JsonSerializerOptions With {.PropertyNamingPolicy=JsonNamingPolicy.CamelCase, .UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow}
   Dim service As New MasterMaintenanceService(connection)
   Dim result As MaintenanceResult
   If args(0)="class" Then
    Dim input=JsonSerializer.Deserialize(Of ClassChange)(bytes,options)
    If input Is Nothing Then Throw New ArgumentException("入力なし")
    result=Await service.SaveClassAsync(input)
   Else
    Dim input=JsonSerializer.Deserialize(Of CodeChange)(bytes,options)
    If input Is Nothing Then Throw New ArgumentException("入力なし")
    result=Await service.SaveCodeAsync(input)
   End If
   Console.WriteLine(JsonSerializer.Serialize(result,options))
   Return If(result.Outcome=Outcome.Saved OrElse result.Outcome=Outcome.NoChange,0,1)
  Catch ex As InputValidationException
   Console.Error.WriteLine(String.Join(vbLf,ex.Errors.Select(Function(e) e.Message))) : Return 1
  Catch ex As ArgumentException
   Console.Error.WriteLine(ex.Message) : Return 1
  Catch ex As JsonException
   Console.Error.WriteLine("JSON入力を確認してください。") : Return 1
  Catch ex As UnauthorizedAccessException
   Console.Error.WriteLine("管理者権限がありません。") : Return 1
  Catch ex As Exception
   Console.Error.WriteLine("処理結果を確認できません。再実行前にマスタを照会してください。") : Return 1
  End Try
 End Function
End Module
