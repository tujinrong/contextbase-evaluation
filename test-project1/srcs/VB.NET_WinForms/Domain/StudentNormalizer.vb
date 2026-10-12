Option Strict On
Option Explicit On
Option Infer On
Option Compare Binary
Imports System
Imports System.Collections.Generic
Imports System.Linq
Imports System.Threading
Imports System.Threading.Tasks
Imports System.Globalization
Imports System.Text
Imports System.Data
Imports Microsoft.Data.SqlClient
Imports StudentManagement.WinForms.Domain.SqlServerStudentService
Imports System.Xml
Imports System.Text.RegularExpressions

Namespace Global.StudentManagement.WinForms.Domain
    Public Module StudentNormalizer
        Private ReadOnly Labels As Dictionary(Of String, String) = New Global.System.Collections.Generic.Dictionary(Of String, String)() From {
    {"StudentNo", "学籍番号"},
    {"StudentName", "氏名"},
    {"StudentNameKana", "氏名カナ"},
    {"BirthDateInput", "生年月日"},
    {"GenderCode", "性別"},
    {"PostalCode", "郵便番号"},
    {"PrefectureCode", "都道府県"},
    {"AddressLine1", "住所1"},
    {"AddressLine2", "住所2"},
    {"PhoneNumber", "本人電話"},
    {"EmailAddress", "本人メール"},
    {"AdmissionDate", "入学日"},
    {"EnrollmentStatusCode", "在籍区分"},
    {"EnrollmentEndDate", "卒業・退学日"},
    {"ClassId", "クラス"},
    {"EmergencyContactName", "緊急連絡先氏名"},
    {"RelationshipCode", "緊急連絡先続柄"},
    {"EmergencyPhoneNumber", "緊急連絡先電話"},
    {"Remarks", "備考"},
    {"Reason", "確認・変更理由"},
    {"DeleteReason", "削除理由"},
    {"ClassCode", "クラスコード"},
    {"ClassName", "クラス名"},
    {"CodeName", "コード名称"},
    {"GradeCode", "学年"},
    {"Principal", "認証主体"}
}
        Friend ReadOnly PropertyNames As Dictionary(Of String, String) = New Global.System.Collections.Generic.Dictionary(Of String, String)() From {
    {"student_no", "StudentNo"},
    {"student_name", "StudentName"},
    {"student_name_kana", "StudentNameKana"},
    {"birth_date", "BirthDateInput"},
    {"gender_code", "GenderCode"},
    {"postal_code", "PostalCode"},
    {"prefecture_code", "PrefectureCode"},
    {"address_line1", "AddressLine1"},
    {"address_line2", "AddressLine2"},
    {"phone_number", "PhoneNumber"},
    {"email_address", "EmailAddress"},
    {"admission_date", "AdmissionDate"},
    {"enrollment_status_code", "EnrollmentStatusCode"},
    {"enrollment_end_date", "EnrollmentEndDate"},
    {"class_id", "ClassId"},
    {"emergency_contact_name", "EmergencyContactName"},
    {"relationship_code", "RelationshipCode"},
    {"emergency_phone_number", "EmergencyPhoneNumber"},
    {"remarks", "Remarks"}
}
        Private Function Label(field As String) As String
            Return Labels.GetValueOrDefault(field, "入力項目")
        End Function
        Public Function ScalarCount(text As String) As Integer
            Dim count = 0
            Dim i = 0

            While i < text.Length
                If Char.IsHighSurrogate(text(i)) Then
                    If Interlocked.Increment(i) >= text.Length OrElse Not Char.IsLowSurrogate(text(i)) Then Throw New ArgumentException("不正なUnicodeです。")
                ElseIf Char.IsLowSurrogate(text(i)) Then
                    Throw New ArgumentException("不正なUnicodeです。")
                End If

                i += 1
                count += 1
            End While

            Return count
        End Function

        Public Function Text(raw As String, rawMax As Integer, savedMax As Integer, field As String, Optional required As Boolean = False, Optional multiline As Boolean = False) As String
            raw = If(raw, "")
            If ScalarCount(raw) > rawMax Then Fail(field, "E-STU-002", $"{Label(field)}は{rawMax}文字以内で入力してください。")
            Dim value = If(multiline, raw.Replace(vbCrLf, vbLf).Replace(ChrW(13), ChrW(10)), raw)
            If value.EnumerateRunes().Any(Function(rune) Rune.GetUnicodeCategory(rune) = UnicodeCategory.Control AndAlso Not (multiline AndAlso rune.Value = 10)) Then Fail(field, "E-STU-002", $"{Label(field)}に使用できない制御文字があります。")
            value = value.Trim()
            If value.Length = 0 Then
                If required Then Fail(field, "E-STU-001", $"{Label(field)}を入力してください。")
                Return Nothing
            End If

            If ScalarCount(value) > savedMax Then Fail(field, "E-STU-002", $"{Label(field)}は{savedMax}文字以内で入力してください。")
            Return value
        End Function

        Public Function Identifier(raw As String, max As Integer, field As String) As String
            Dim value = Text(raw, max, max, field, True).Normalize(NormalizationForm.FormKC).ToUpperInvariant()
            If ScalarCount(value) > max OrElse Not Regex.IsMatch(value, "^[A-Z0-9][A-Z0-9-]*$", RegexOptions.CultureInvariant) Then Fail(field, "E-STU-003", $"{Label(field)}は英数字・ハイフンで{max}文字以内にしてください。")
            Return value
        End Function

        Public Function NameKey(name As String) As String
            Dim key = String.Concat(name.Normalize(NormalizationForm.FormKC).ToUpperInvariant().EnumerateRunes().Where(Function(rune) Not Rune.IsWhiteSpace(rune)))
            If ScalarCount(key) > 160 Then Fail("StudentName", "E-STU-002", "氏名照合値が上限を超えています。")
            Return key
        End Function

        Public Function Kana(raw As String, Optional required As Boolean = True) As String
            Dim value = If(Text(raw, 36, 36, "StudentNameKana", required)?.Normalize(NormalizationForm.FormKC), "")
            Dim output = New StringBuilder()
            Dim space = False
            For Each rune In value.EnumerateRunes()
                If Rune.IsWhiteSpace(rune) Then
                    space = output.Length > 0
                    Continue For
                End If

                If space Then
                    output.Append(" "c)
                    space = False
                End If

                Dim c = If(rune.Value >= &H3041 AndAlso rune.Value <= &H3096 OrElse rune.Value = &H309D OrElse rune.Value = &H309E, rune.Value + &H60, rune.Value)
                If Not (c >= &H30A1 AndAlso c <= &H30FA OrElse c = &H30FC OrElse c = &H30FB OrElse c = &H30FD OrElse c = &H30FE) Then Fail("StudentNameKana", "E-STU-004", "氏名カナはカタカナで入力してください。")
                output.Append(New Rune(c).ToString())
            Next

            Dim result = output.ToString()
            If ScalarCount(result) > 18 Then Fail("StudentNameKana", "E-STU-002", "氏名カナは18文字以内です。")
            Return result
        End Function

        Public Function Phone(raw As String, field As String) As String
            Dim text = StudentNormalizer.Text(raw, 20, 20, field)?.Normalize(NormalizationForm.FormKC)
            If Equals(text, Nothing) Then Return Nothing
            Dim value = String.Concat(text.EnumerateRunes().Where(Function(rune) Not Rune.IsWhiteSpace(rune) AndAlso Not (rune.Value = 45 OrElse rune.Value = &H2010 OrElse rune.Value = &H2011 OrElse rune.Value = &H2212 OrElse rune.Value = 40 OrElse rune.Value = 41)))
            If Not Regex.IsMatch(value, "^(0[0-9]{9,10}|\+[1-9][0-9]{6,14})$", RegexOptions.CultureInvariant) Then Fail(field, "E-STU-016", "電話番号の形式を確認してください。")
            Return value
        End Function

        Public Function Postal(raw As String) As String
            Dim text = StudentNormalizer.Text(raw, 10, 10, "PostalCode", True).Normalize(NormalizationForm.FormKC)
            Dim value = String.Concat(text.EnumerateRunes().Where(Function(rune) Not Rune.IsWhiteSpace(rune) AndAlso Not (rune.Value = 45 OrElse rune.Value = &H2010 OrElse rune.Value = &H2011 OrElse rune.Value = &H2212)))
            If Not Regex.IsMatch(value, "^[0-9]{7}$", RegexOptions.CultureInvariant) Then Fail("PostalCode", "E-STU-015", "郵便番号は7桁で入力してください。")
            Return value
        End Function

        Public Function Email(raw As String) As String
            Dim value = Text(raw, 60, 60, "EmailAddress")
            If Equals(value, Nothing) Then Return Nothing
            Dim parts = value.Split("@"c)
            If parts.Length <> 2 OrElse parts(0).Length = 0 OrElse parts(0).Length > 64 OrElse parts(0).StartsWith("."c) OrElse parts(0).EndsWith("."c) OrElse parts(0).Contains("..") OrElse Not Regex.IsMatch(parts(0), "^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$", RegexOptions.CultureInvariant) Then Fail("EmailAddress", "E-STU-017", "メールアドレスの形式を確認してください。")
            Dim labels = parts(1).Split("."c)
            If labels.Length < 2 OrElse labels.Any(Function(label) label.Length < 1 OrElse label.Length > 63 OrElse Not Regex.IsMatch(label, "^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$", RegexOptions.CultureInvariant)) Then Fail("EmailAddress", "E-STU-017", "メールアドレスの形式を確認してください。")
            Return parts(0) & "@" & parts(1).ToLowerInvariant()
        End Function

        Public Function Code(raw As String, width As Integer, field As String, Optional required As Boolean = True) As String
            Dim text = StudentNormalizer.Text(raw, width, width, field, required)?.Normalize(NormalizationForm.FormKC)
            If Not Equals(text, Nothing) AndAlso (text.Length <> width OrElse text.Any(Function(c) c < "0"c OrElse c > "9"c)) Then Fail(field, "E-STU-009", "コードを選択し直してください。")
            Return text
        End Function

        Friend Function Normalize(raw As StudentDraft, businessDay As DateOnly) As NormalizedStudent
            Dim values = New Dictionary(Of String, Object)()
            Dim errors = New List(Of FieldError)()
            Dim [Set] As Action(Of String, Func(Of Object)) = Sub(column, [get])
                                                                  Try
                                                                      values(column) = [get]()
                                                                  Catch e As InputValidationException
                                                                      errors.AddRange(e.Errors)
                                                                  Catch e As ArgumentException
                                                                      errors.Add(ArgumentError(PropertyNames(column), e))
                                                                  End Try
                                                              End Sub
            [Set]("student_no", Function() Identifier(raw.StudentNo, 15, "StudentNo"))
            [Set]("student_name", Function() Text(raw.StudentName, 8, 8, "StudentName", True))
            [Set]("student_name_kana", Function() Kana(raw.StudentNameKana))
            [Set]("birth_date", Function() Parse(raw.BirthDateInput, businessDay))
            [Set]("gender_code", Function() Code(raw.GenderCode, 1, "GenderCode"))
            [Set]("postal_code", Function() Postal(raw.PostalCode))
            [Set]("prefecture_code", Function() Code(raw.PrefectureCode, 2, "PrefectureCode"))
            [Set]("address_line1", Function() Text(raw.AddressLine1, 45, 45, "AddressLine1", True))
            [Set]("address_line2", Function() Text(raw.AddressLine2, 45, 45, "AddressLine2"))
            [Set]("phone_number", Function() Phone(raw.PhoneNumber, "PhoneNumber"))
            [Set]("email_address", Function() Email(raw.EmailAddress))
            [Set]("admission_date", Function() ParseIso(raw.AdmissionDate, businessDay))
            [Set]("enrollment_status_code", Function() Code(raw.EnrollmentStatusCode, 2, "EnrollmentStatusCode"))
            [Set]("enrollment_end_date", Function() If(String.IsNullOrEmpty(raw.EnrollmentEndDate), Nothing, CObj(ParseIso(raw.EnrollmentEndDate, businessDay))))
            [Set]("class_id", Function() If(raw.ClassId <= 0, ConversionSupport.__Throw(Of Object)(New ArgumentException("E-STU-010: クラスIDが不正です。")), raw.ClassId))
            [Set]("emergency_contact_name", Function() Text(raw.EmergencyContactName, 8, 8, "EmergencyContactName"))
            [Set]("relationship_code", Function() Code(raw.RelationshipCode, 2, "RelationshipCode", False))
            [Set]("emergency_phone_number", Function() Phone(raw.EmergencyPhoneNumber, "EmergencyPhoneNumber"))
            [Set]("remarks", Function() Text(raw.Remarks, 120, 120, "Remarks", multiline:=True))
            If errors.Count > 0 Then Throw New InputValidationException(errors)
            values("name_key") = NameKey(CStr(values("student_name")))
            values("kana_key") = CStr(values("student_name_kana")).Replace(" ", "")
            ' COM-STU-008 7.4: this category is derived; it is never a client input.
            values("relationship_category") = If(values("relationship_code") Is Nothing, Nothing, "RELATIONSHIP")
            Dim birth = CType(values("birth_date"), DateOnly)
            Dim admission = CType(values("admission_date"), DateOnly)
            Dim [end] = CType(values("enrollment_end_date"), DateOnly?)
            Dim status = CStr(values("enrollment_status_code"))
            If birth > admission Then errors.Add(New Global.StudentManagement.WinForms.Domain.FieldError("AdmissionDate", "E-STU-007", "生年月日≦入学日となるよう入力してください。"))
            If Not (Equals(status, "01") OrElse Equals(status, "02") OrElse Equals(status, "03") OrElse Equals(status, "04")) Then errors.Add(New Global.StudentManagement.WinForms.Domain.FieldError("EnrollmentStatusCode", "E-STU-009", "在籍区分が不正です。"))
            If If(Equals(status, "01") OrElse Equals(status, "02"), Not [end] Is Nothing, [end] Is Nothing OrElse [end] < admission) Then errors.Add(New Global.StudentManagement.WinForms.Domain.FieldError("EnrollmentEndDate", "E-STU-008", "在籍区分に対応する終了日を設定してください。"))
            If (Equals(status, "01") OrElse Equals(status, "02")) AndAlso raw.ClassId Is Nothing Then errors.Add(New Global.StudentManagement.WinForms.Domain.FieldError("ClassId", "E-STU-012", "在学・休学はクラス必須です。"))
            If values("phone_number") Is Nothing AndAlso values("email_address") Is Nothing AndAlso values("emergency_phone_number") Is Nothing Then errors.Add(New Global.StudentManagement.WinForms.Domain.FieldError("PhoneNumber", "E-STU-018", "連絡先を1つ以上入力してください。"))
            Dim emergency = {values("emergency_contact_name"), values("relationship_code"), values("emergency_phone_number")}.Count(Function(value) Not value Is Nothing)
            If Not (emergency = 0 OrElse emergency = 3) Then errors.Add(New Global.StudentManagement.WinForms.Domain.FieldError("EmergencyContactName", "E-STU-019", "緊急連絡先は3項目すべて入力してください。"))
            If errors.Count > 0 Then Throw New InputValidationException(errors)
            Return New Global.StudentManagement.WinForms.Domain.NormalizedStudent(values)
        End Function

        Public Function EscapeLike(input As String) As String
            Return input.Replace("!", "!!").Replace("%", "!%").Replace("_", "!_").Replace("[", "![")
        End Function
        Friend Function ArgumentError(field As String, [error] As ArgumentException) As FieldError
            Dim code = [error].Message.Split(":"c)(0)
            Return If(Regex.IsMatch(code, "^E-(?:STU|DATE|COM|SRC|MST)-[0-9]{3}$", RegexOptions.CultureInvariant), New Global.StudentManagement.WinForms.Domain.FieldError(field, code, [error].Message), New Global.StudentManagement.WinForms.Domain.FieldError(field, "E-STU-002", $"{Label(field)}の文字を確認してください。"))
        End Function

        Private Sub Fail(field As String, code As String, message As String)
            ConversionSupport.__Throw(Of Object)(New InputValidationException(New Global.StudentManagement.WinForms.Domain.FieldError() {New Global.StudentManagement.WinForms.Domain.FieldError(field, code, message)}))
        End Sub

        Private Class ConversionSupport
            
            Shared Function __Throw(Of T)(ByVal e As Exception) As T
                Throw e
            End Function
        End Class
    End Module
End Namespace
