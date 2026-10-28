Option Strict On
Imports System.Globalization
Imports System.Text.Json.Serialization

Namespace Global.StudentManagement.WinForms.Domain
    ' SRC-001/002/006/008: preserve raw input independently of the four validated query values.
    <JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)>
    Public NotInheritable Class SearchDraft
        Public Property StudentNo As String = ""
        Public Property StudentName As String = ""
        Public Property ClassId As String = ""
        Public Property EnrollmentStatusCodes As String() = {"01", "02"}
        Public Function Normalize() As SearchCriteria
            Dim no = StudentNormalizer.Text(StudentNo, 15, 15, "StudentNo")
            Dim name = StudentNormalizer.Text(StudentName, 8, 8, "StudentName")
            Dim cls As Long? = Nothing
            If Not String.IsNullOrEmpty(ClassId) Then
                Dim value As Long
                If Not Long.TryParse(ClassId, NumberStyles.None, CultureInfo.InvariantCulture, value) OrElse value <= 0 Then Throw New InvalidOperationException("E-COM-003 クラス識別番号が不正です。")
                cls = value
            End If
            If EnrollmentStatusCodes Is Nothing OrElse EnrollmentStatusCodes.Length > 4 OrElse EnrollmentStatusCodes.Distinct(StringComparer.Ordinal).Count() <> EnrollmentStatusCodes.Length OrElse EnrollmentStatusCodes.Any(Function(x) Not {"01", "02", "03", "04"}.Contains(x, StringComparer.Ordinal)) Then Throw New InvalidOperationException("E-COM-003 在籍区分が不正です。")
            Return New SearchCriteria With {.StudentNo = If(no Is Nothing, Nothing, StudentNormalizer.Identifier(StudentNo, 15, "StudentNo")), .StudentName = If(name Is Nothing, Nothing, StudentNormalizer.NameKey(name)), .ClassId = cls, .EnrollmentStatusCodes = EnrollmentStatusCodes.ToArray()}
        End Function
    End Class
End Namespace
