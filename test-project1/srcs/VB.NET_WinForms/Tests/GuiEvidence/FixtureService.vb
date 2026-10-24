Imports System.Globalization
Imports System.IO
Imports System.Text.Json
Imports System.Threading
Imports System.Threading.Tasks
Imports StudentManagement.WinForms.Domain

Namespace GuiEvidence
    ' Test-only backend. No SQL connection or persistence.
    Public NotInheritable Class FixtureService
        Implements IStudentService
        Private ReadOnly data As JsonDocument
        Public Sub New(path As String)
            data=JsonDocument.Parse(File.ReadAllText(path))
            If data.RootElement.GetProperty("profile").GetString() <> "VB.NET_WinForms" OrElse data.RootElement.GetProperty("databaseConnected").GetBoolean() Then Throw New InvalidDataException("Expected isolated VB fixture.")
        End Sub
        Private Function Students() As IEnumerable(Of JsonElement)
            Return data.RootElement.GetProperty("students").EnumerateArray().ToArray()
        End Function
        Private Shared Function Values(s As JsonElement) As Dictionary(Of String,String)
            Return s.GetProperty("values").EnumerateObject().ToDictionary(Function(p) p.Name,Function(p) p.Value.GetString())
        End Function
        Private Shared Function Draft(s As JsonElement) As StudentDraft
            Dim v=Values(s)
            Dim result As New StudentDraft
            For Each prop In GetType(StudentDraft).GetProperties().Where(Function(p) p.PropertyType Is GetType(String))
                prop.SetValue(result,If(v.ContainsKey(prop.Name),v(prop.Name),Nothing))
            Next
            result.BirthDateInput=New BirthDateInput(v("BirthEra"),v("BirthYear"),v("BirthMonth"),v("BirthDay"))
            result.ClassId=If(v("ClassId")="",CType(Nothing,Long?),Long.Parse(v("ClassId"),CultureInfo.InvariantCulture))
            Return result
        End Function
        Public Function LookupAsync(Optional ct As CancellationToken=Nothing) As Task(Of LookupSet) Implements IStudentService.LookupAsync
            Return LookupAsync(True,ct)
        End Function
        Public Function LookupAsync(includeOccupancy As Boolean,Optional ct As CancellationToken=Nothing) As Task(Of LookupSet) Implements IStudentService.LookupAsync
            ct.ThrowIfCancellationRequested()
            Dim codes=data.RootElement.GetProperty("codes").EnumerateArray().Select(Function(c) New CodeEntry(c.GetProperty("category").GetString(),c.GetProperty("value").GetString(),c.GetProperty("name").GetString(),0,True,New DateOnly(1900,1,1),Nothing,False)).ToArray()
            Dim classes=data.RootElement.GetProperty("classes").EnumerateArray().Select(Function(c) New SchoolClass(c.GetProperty("id").GetInt64(),c.GetProperty("year").GetInt32(),c.GetProperty("grade").GetString(),c.GetProperty("code").GetString(),c.GetProperty("name").GetString(),New DateOnly(2026,4,1),New DateOnly(2027,3,31),c.GetProperty("capacity").GetInt32(),If(includeOccupancy,c.GetProperty("occupancy").GetInt32(),0),True)).ToArray()
            Return Task.FromResult(New LookupSet(codes,classes))
        End Function
        Private Shared Function Matches(v As Dictionary(Of String,String),c As SearchCriteria) As Boolean
            Return (String.IsNullOrEmpty(c.StudentNo) OrElse StudentNormalizer.Identifier(v("StudentNo"),15,"StudentNo").StartsWith(StudentNormalizer.Identifier(c.StudentNo,15,"StudentNo"),StringComparison.Ordinal)) AndAlso
                (String.IsNullOrEmpty(c.StudentName) OrElse StudentNormalizer.NameKey(v("StudentName")).Contains(StudentNormalizer.NameKey(c.StudentName),StringComparison.Ordinal)) AndAlso
                (c.EnrollmentStatusCodes.Length=0 OrElse c.EnrollmentStatusCodes.Contains(v("EnrollmentStatusCode"))) AndAlso
                (Not c.ClassId.HasValue OrElse v("ClassId")=c.ClassId.Value.ToString(CultureInfo.InvariantCulture))
        End Function
        Private Shared Function SortKey(s As JsonElement,c As SearchCriteria) As String
            Dim v=Values(s)
            Select Case c.SortKey
                Case "name" : Return v("StudentName")
                Case "admissionDate" : Return v("AdmissionDate")
                Case "updatedAt" : Return s.GetProperty("updatedAt").GetString()
                Case Else : Return v("StudentNo")
            End Select
        End Function
        Public Function SearchAsync(criteria As SearchCriteria,Optional ct As CancellationToken=Nothing) As Task(Of SearchResult) Implements IStudentService.SearchAsync
            ct.ThrowIfCancellationRequested()
            Dim selected=Students().Where(Function(s) Matches(Values(s),criteria))
            Dim ordered=If(criteria.SortDirection="desc",selected.OrderByDescending(Function(s) SortKey(s,criteria),StringComparer.Ordinal),selected.OrderBy(Function(s) SortKey(s,criteria),StringComparer.Ordinal)).ThenBy(Function(s) s.GetProperty("id").GetInt64()).ToArray()
            Dim rows=ordered.Skip((criteria.Page-1)*criteria.PageSize).Take(criteria.PageSize).Select(Function(s) ToRow(s)).ToArray()
            Return Task.FromResult(New SearchResult(Outcome.NoChange,ordered.Length,rows,DateTimeOffset.Parse(data.RootElement.GetProperty("searchedAt").GetString(),CultureInfo.InvariantCulture),False,Array.Empty(Of FieldError)()))
        End Function
        Private Function ToRow(s As JsonElement) As StudentRow
            Dim v=Values(s)
            Dim cls=data.RootElement.GetProperty("classes").EnumerateArray().Single(Function(c) c.GetProperty("id").GetInt64().ToString(CultureInfo.InvariantCulture)=v("ClassId"))
            Dim state=data.RootElement.GetProperty("codes").EnumerateArray().Single(Function(c) c.GetProperty("category").GetString()="ENROLLMENT_STATUS" AndAlso c.GetProperty("value").GetString()=v("EnrollmentStatusCode")).GetProperty("name").GetString()
            Return New StudentRow(s.GetProperty("id").GetInt64(),v("StudentNo"),v("StudentName"),v("StudentNameKana"),DateOnly.Parse(s.GetProperty("birthDate").GetString(),CultureInfo.InvariantCulture),2026,"1年",cls.GetProperty("code").GetString(),cls.GetProperty("name").GetString(),state)
        End Function
        Public Function GetAsync(id As Long,Optional ct As CancellationToken=Nothing) As Task(Of StudentDetail) Implements IStudentService.GetAsync
            ct.ThrowIfCancellationRequested()
            Dim s=Students().Where(Function(x) x.GetProperty("id").GetInt64()=id).ToArray()
            If s.Length=0 Then Return Task.FromResult(Of StudentDetail)(Nothing)
            Return Task.FromResult(New StudentDetail(id,s(0).GetProperty("version").GetInt64(),Draft(s(0)),DateOnly.Parse(s(0).GetProperty("birthDate").GetString(),CultureInfo.InvariantCulture),DateTimeOffset.Parse(s(0).GetProperty("updatedAt").GetString(),CultureInfo.InvariantCulture),"FIXTURE-NOT-DB"))
        End Function
        Public Function SaveAsync(request As SaveRequest,Optional ct As CancellationToken=Nothing) As Task(Of SaveResult) Implements IStudentService.SaveAsync
            Return Task.FromResult(New SaveResult(Outcome.SystemError,Nothing,Nothing,{New FieldError("","FIXTURE-NO-WRITE","撮影fixtureでは保存を実施しません。入力を保持しています。DB未接続。" )}))
        End Function
        Public Function DeleteAsync(id As Long,version As Long,reason As String,Optional ct As CancellationToken=Nothing) As Task(Of SaveResult) Implements IStudentService.DeleteAsync
            Return Task.FromResult(New SaveResult(Outcome.SystemError,Nothing,Nothing,{New FieldError("","FIXTURE-NO-WRITE","撮影fixtureでは削除を実施しません。DB未接続。" )}))
        End Function
    End Class
End Namespace
