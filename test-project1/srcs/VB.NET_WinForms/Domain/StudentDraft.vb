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
    Public NotInheritable Class StudentDraft
        Public Property StudentNo As String = ""
        Public Property StudentName As String = ""
        Public Property StudentNameKana As String = ""
        Public Property BirthDateInput As BirthDateInput = New Global.StudentManagement.WinForms.Domain.BirthDateInput()
        Public Property GenderCode As String = "0"
        Public Property PostalCode As String = ""
        Public Property PrefectureCode As String = ""
        Public Property AddressLine1 As String = ""
        Public Property AddressLine2 As String
        Public Property PhoneNumber As String
        Public Property EmailAddress As String
        Public Property AdmissionDate As String = ""
        Public Property EnrollmentStatusCode As String = "01"
        Public Property EnrollmentEndDate As String
        Public Property ClassId As Long?
        Public Property EmergencyContactName As String
        Public Property RelationshipCode As String
        Public Property EmergencyPhoneNumber As String
        Public Property Remarks As String
    End Class

End Namespace
