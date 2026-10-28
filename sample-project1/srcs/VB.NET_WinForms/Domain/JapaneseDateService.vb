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
    Public Module JapaneseDateService
        Private NotInheritable Class Era
            Public ReadOnly Property Id As String
            Public ReadOnly Property Name As String
            Public ReadOnly Property Offset As Integer
            Public ReadOnly Property Start As DateOnly
            Public ReadOnly Property [End] As DateOnly

            Public Sub New(Id As String, Name As String, Offset As Integer, Start As DateOnly, [End] As DateOnly)
                Me.Id = Id
                Me.Name = Name
                Me.Offset = Offset
                Me.Start = Start
                Me.End = [End]
            End Sub
        End Class

        Private ReadOnly Eras As Era() = New Global.StudentManagement.WinForms.Domain.JapaneseDateService.Era() {New Global.StudentManagement.WinForms.Domain.JapaneseDateService.Era("REIWA", "令和", 2018, New Global.System.DateOnly(2019, 5, 1), DateOnly.MaxValue), New Global.StudentManagement.WinForms.Domain.JapaneseDateService.Era("HEISEI", "平成", 1988, New Global.System.DateOnly(1989, 1, 8), New Global.System.DateOnly(2019, 4, 30)), New Global.StudentManagement.WinForms.Domain.JapaneseDateService.Era("SHOWA", "昭和", 1925, New Global.System.DateOnly(1926, 12, 25), New Global.System.DateOnly(1989, 1, 7)), New Global.StudentManagement.WinForms.Domain.JapaneseDateService.Era("TAISHO", "大正", 1911, New Global.System.DateOnly(1912, 7, 30), New Global.System.DateOnly(1926, 12, 24)), New Global.StudentManagement.WinForms.Domain.JapaneseDateService.Era("MEIJI", "明治", 1867, New Global.System.DateOnly(1900, 1, 1), New Global.System.DateOnly(1912, 7, 29))}
        Public Function Parse(input As BirthDateInput, businessDay As DateOnly) As DateOnly
            Dim era = Eras.SingleOrDefault(Function(entry) Equals(entry.Id, input.Era))
            If era Is Nothing Then Throw New ArgumentException("E-DATE-001: 生年月日の元号を確認してください。")
            Dim yearText = input.Year.Normalize(NormalizationForm.FormKC)
            Dim year = If(Equals(yearText, "元"), 1, Number(yearText, 4))
            Dim month = Number(input.Month.Normalize(NormalizationForm.FormKC), 2)
            Dim day = Number(input.Day.Normalize(NormalizationForm.FormKC), 2)
            Dim [date] As DateOnly
            Try
                [date] = New Global.System.DateOnly(era.Offset + year, month, day)
            Catch __unusedArgumentOutOfRangeException1__ As ArgumentOutOfRangeException
                Throw New ArgumentException("E-STU-005: 生年月日に正しい日付を入力してください。")
            End Try

            If [date] < era.Start OrElse [date] > era.End OrElse [date] > businessDay Then Throw New ArgumentException("E-DATE-001: 生年月日の元号・年・月・日を確認してください。")
            Dim reverse = ToInput([date])
            If Not Equals(reverse.Era, input.Era) OrElse Integer.Parse(reverse.Year, CultureInfo.InvariantCulture) <> year Then Throw New ArgumentException("E-DATE-001: 元号境界が一致しません。")
            Return [date]
        End Function

        Private Function Number(text As String, maximum As Integer) As Integer
            Dim value As Integer = Nothing
            If text.Length = 0 OrElse text.Length > maximum OrElse text.Any(Function(c) c < "0"c OrElse c > "9"c) OrElse Not Integer.TryParse(text, value) OrElse value <= 0 Then Throw New ArgumentException("E-DATE-001: 正の整数を入力してください。")
            Return value
        End Function

        Public Function ToInput([date] As DateOnly) As BirthDateInput
            Dim era = If(Eras.FirstOrDefault(Function(entry) [date] >= entry.Start AndAlso [date] <= entry.End), ConversionSupport.__Throw(Of Era)(New ArgumentOutOfRangeException(NameOf([date]), "DATE-R01下限外です。")))
            Return New Global.StudentManagement.WinForms.Domain.BirthDateInput(era.Id, ([date].Year - era.Offset).ToString(CultureInfo.InvariantCulture), [date].Month.ToString("00"), [date].Day.ToString("00"))
        End Function

        Public Function ToWareki([date] As DateOnly) As String
            Dim input = ToInput([date])
            Return $"{Enumerable.Single(Eras, Function(entry) Equals(entry.Id, input.Era)).Name}{If(Equals(input.Year, "1"), "元", input.Year)}年{input.Month}月{input.Day}日"
        End Function

        Public Function ParseIso(raw As String, businessDay As DateOnly, Optional historical As Boolean = True) As DateOnly
            Dim text = raw.Normalize(NormalizationForm.FormKC)
            Dim [date] As DateOnly = Nothing
            If text.Length <> 10 OrElse Not DateOnly.TryParseExact(text, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, [date]) Then Throw New ArgumentException("E-STU-005: 正しい西暦日付を入力してください。")
            If [date] < New DateOnly(1900, 1, 1) OrElse historical AndAlso [date] > businessDay Then Throw New ArgumentException("E-DATE-002: 日付が許容範囲外です。")
            Return [date]
        End Function

        Public Function SchoolYear(day As DateOnly) As Integer
            Return If(day.Month < 4, day.Year - 1, day.Year)
        End Function

        Private Class ConversionSupport
            
            Shared Function __Throw(Of T)(ByVal e As Exception) As T
                Throw e
            End Function
        End Class
    End Module

End Namespace
