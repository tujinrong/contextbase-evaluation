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
    Public Module NativeStoredProcedureClient
        Public Const PrepareProcedure As String = "student_api.prepare_save"
        Public Const PersistProcedure As String = "student_api.persist_student"
        Public Const DeleteProcedure As String = "student_api.delete_student"
        Private NotInheritable Class Response
            Public ReadOnly Property State As String
            Public ReadOnly Property Result As SaveResult

            Public Sub New(State As String, Result As SaveResult)
                Me.State = State
                Me.Result = Result
            End Sub
        End Class

        Public Function SaveClassAsync(c As SqlConnection, tx As SqlTransaction, change As ClassChange, requestId As Guid, Optional rawReason As String = Nothing, Optional ct As CancellationToken = Nothing) As Task(Of MaintenanceResult)
            Dim raw As String
            Try
                raw = SerializeClass(change, rawReason)
            Catch ex As ArgumentException
                Return Task.FromResult(New MaintenanceResult(Outcome.ValidationFailed, Nothing, NativeMessages.Resolve("E-STU-002", "ClassName", requestId:=requestId)))
            Catch ex As XmlException
                Return Task.FromResult(New MaintenanceResult(Outcome.ValidationFailed, Nothing, NativeMessages.Resolve("E-STU-002", "ClassName", requestId:=requestId)))
            End Try
            Return Master(c, tx, "student_api.save_class", raw, change.ClassId, change.ExpectedVersion, requestId, ct)
        End Function
        Public Function SaveCodeAsync(c As SqlConnection, tx As SqlTransaction, change As CodeChange, requestId As Guid, Optional rawReason As String = Nothing, Optional ct As CancellationToken = Nothing) As Task(Of MaintenanceResult)
            Dim raw As String
            Try
                raw = SerializeCode(change, rawReason)
            Catch ex As ArgumentException
                Return Task.FromResult(New MaintenanceResult(Outcome.ValidationFailed, Nothing, NativeMessages.Resolve("E-STU-002", "CodeName", requestId:=requestId)))
            Catch ex As XmlException
                Return Task.FromResult(New MaintenanceResult(Outcome.ValidationFailed, Nothing, NativeMessages.Resolve("E-STU-002", "CodeName", requestId:=requestId)))
            End Try
            Return Master(c, tx, "student_api.save_code", raw, Nothing, change.ExpectedVersion, requestId, ct)
        End Function
        Private Async Function Master(c As SqlConnection, tx As SqlTransaction, procedure As String, raw As String, id As Long?, version As Long?, requestId As Guid, ct As CancellationToken) As Task(Of MaintenanceResult)
            ValidateTransaction(c, tx)
            Dim parsed As Outcome = Nothing
            Using command = Stored(c, tx, procedure)
                Parameter(command, "@raw", SqlDbType.NVarChar, raw, -1)
                If Equals(procedure, "student_api.save_class") Then Parameter(command, "@target_id", SqlDbType.BigInt, id)
                Parameter(command, "@expected_version", SqlDbType.BigInt, version)
                Parameter(command, "@request_id", SqlDbType.UniqueIdentifier, requestId)
                Try
                    Using reader = Await command.ExecuteReaderAsync(ct)
                        If Not Await reader.ReadAsync(ct) Then Throw New InvalidOperationException("Native master procedure returned no status.")
                        Dim state = reader.GetString(reader.GetOrdinal("outcome"))
                        Dim outcome = If([Enum].TryParse(state, parsed), parsed, Global.StudentManagement.WinForms.Domain.Outcome.SystemError)
                        Dim code = If(Text(reader, "code"), "E-COM-004")
                        Dim field = If(Text(reader, "field"), "")
                        Dim after = [Long](reader, "row_version")
                        Dim same = reader.GetBoolean(reader.GetOrdinal("same_name_warning"))
                        Dim message = If(outcome = Outcome.Saved AndAlso Not same, If(Equals(procedure, "student_api.save_class"), "クラスを保存しました。", "コードを保存しました。"), NativeMessages.Resolve(code, field, requestId:=requestId))
                        Return New Global.StudentManagement.WinForms.Domain.MaintenanceResult(outcome, after, message, same)
                    End Using
                Catch e As SqlException When e.Number = 2601 OrElse e.Number = 2627 OrElse e.Number = 547 OrElse e.Number = 1205 OrElse e.Number = 1222 OrElse e.Number = 3960 OrElse e.Number = 51001 OrElse e.Number = 51005 OrElse e.Number = 229
                    Dim code = If(e.Number = 2601 OrElse e.Number = 2627, "E-MST-002", If(e.Number = 547, "E-STU-009", If(e.Number = 229, "E-COM-002", "E-STU-105")))
                    Return New Global.StudentManagement.WinForms.Domain.MaintenanceResult(If(e.Number = 229, Outcome.Forbidden, If(e.Number = 1205 OrElse e.Number = 1222 OrElse e.Number = 3960 OrElse e.Number = 51001 OrElse e.Number = 51005, Outcome.Conflict, Outcome.ValidationFailed)), Nothing, NativeMessages.Resolve(code, requestId:=requestId))
                End Try
            End Using
        End Function

        Public Async Function SaveAsync(c As SqlConnection, tx As SqlTransaction, request As SaveRequest, sessionId As Guid, requestId As Guid, Optional ct As CancellationToken = Nothing) As Task(Of SaveResult)
            ValidateTransaction(c, tx)
            Dim token As Guid? = Nothing
            Dim parsed As Guid = Nothing, text As String = Nothing

            If ConversionSupport.__Assign(text, TryCast(request.ConfirmationToken, String)) IsNot Nothing Then
                If Not Guid.TryParse(text, parsed) Then Return Failure(Outcome.ValidationFailed, "E-COM-003", "ConfirmationToken", requestId)
                token = parsed
            End If

            Dim raw As String
            Try
                raw = SerializeRaw(request)
            Catch __unusedArgumentException1__ As ArgumentException
                Return Failure(Outcome.ValidationFailed, "E-STU-002", "Save", requestId)
            Catch __unusedXmlException2__ As XmlException
                Return Failure(Outcome.ValidationFailed, "E-STU-002", "Save", requestId)
            End Try

            Try
                Dim prepared = Await SaveProcedure(c, tx, PrepareProcedure, raw, request, sessionId, token, requestId, ct)
                If Not Equals(prepared.State, "Ready") Then Return prepared.Result
                ' Persist repeats normalization/role/gate/latest rules and full confirmation comparison.
                Return (Await SaveProcedure(c, tx, PersistProcedure, raw, request, sessionId, token, requestId, ct)).Result
            Catch e As SqlException When Not KnownFailure(e, requestId) Is Nothing
                Return KnownFailure(e, requestId)
            End Try
        End Function

        Public Async Function DeleteAsync(c As SqlConnection, tx As SqlTransaction, id As Long, version As Long, rawReason As String, sessionId As Guid, requestId As Guid, Optional ct As CancellationToken = Nothing) As Task(Of SaveResult)
            ValidateTransaction(c, tx)
            Using command = Stored(c, tx, DeleteProcedure)
                Parameter(command, "@target_id", SqlDbType.BigInt, id)
                Parameter(command, "@expected_version", SqlDbType.BigInt, version)
                Parameter(command, "@raw_reason", SqlDbType.NVarChar, rawReason, -1)
                Parameter(command, "@session_id", SqlDbType.UniqueIdentifier, sessionId)
                Parameter(command, "@request_id", SqlDbType.UniqueIdentifier, requestId)
                Try
                    Return (Await Read(command, requestId, ct)).Result
                Catch e As SqlException When Not KnownFailure(e, requestId) Is Nothing
                    Return KnownFailure(e, requestId)
                End Try
            End Using
        End Function

        Private Sub ValidateTransaction(c As SqlConnection, tx As SqlTransaction)
            If c.State <> ConnectionState.Open OrElse Not ReferenceEquals(tx.Connection, c) Then Throw New InvalidOperationException("Native procedure requires caller's open connection/transaction.")
            If tx.IsolationLevel <> IsolationLevel.ReadCommitted Then Throw New InvalidOperationException("Native caller transaction must be READ COMMITTED.")
        End Sub

        Private Function Stored(c As SqlConnection, tx As SqlTransaction, name As String) As SqlCommand
            Return New Global.Microsoft.Data.SqlClient.SqlCommand(name, c, tx) With {
                .CommandType = CommandType.StoredProcedure,
                .CommandTimeout = 30
            }
        End Function
        Private Sub Parameter(cmd As SqlCommand, name As String, type As SqlDbType, value As Object, Optional size As Integer = 0)
            Dim p = cmd.Parameters.Add(name, type)
            If size <> 0 Then p.Size = size
            p.Value = If(value, DBNull.Value)
        End Sub

        Private Async Function SaveProcedure(c As SqlConnection, tx As SqlTransaction, name As String, raw As String, request As SaveRequest, sessionId As Guid, token As Guid?, requestId As Guid, ct As CancellationToken) As Task(Of Response)
            Using command = Stored(c, tx, name)
                Parameter(command, "@raw", SqlDbType.NVarChar, raw, -1)
                Parameter(command, "@target_id", SqlDbType.BigInt, request.StudentId)
                Parameter(command, "@expected_version", SqlDbType.BigInt, request.ExpectedVersion)
                Parameter(command, "@session_id", SqlDbType.UniqueIdentifier, sessionId)
                Parameter(command, "@confirmation_token", SqlDbType.UniqueIdentifier, token)
                Parameter(command, "@request_id", SqlDbType.UniqueIdentifier, requestId)
                Return Await Read(command, requestId, ct)
            End Using
        End Function

        Private Function Text(reader As SqlDataReader, key As String) As String
            Return If(reader.IsDBNull(reader.GetOrdinal(key)), Nothing, reader.GetString(reader.GetOrdinal(key)))
        End Function
        Private Function [Long](reader As SqlDataReader, key As String) As Long?
            Return If(reader.IsDBNull(reader.GetOrdinal(key)), CType(Nothing,Long?), CType(reader.GetInt64(reader.GetOrdinal(key)),Long?))
        End Function
        Private Async Function Read(command As SqlCommand, requestId As Guid, ct As CancellationToken) As Task(Of Response)
            Dim parsed As Outcome = Nothing, [property] As String = Nothing
            Using reader = Await command.ExecuteReaderAsync(ct)
                If Not Await reader.ReadAsync(ct) Then Throw New InvalidOperationException("Native procedure returned no status.")
                Dim state = reader.GetString(reader.GetOrdinal("outcome"))
                Dim outcome = If(Equals(state, "Ready"), Global.StudentManagement.WinForms.Domain.Outcome.NoChange, If([Enum].TryParse(state, parsed), parsed, Global.StudentManagement.WinForms.Domain.Outcome.SystemError))
                Dim id = [Long](reader, "student_id")
                Dim version = [Long](reader, "row_version")
                Dim token = If(reader.IsDBNull(reader.GetOrdinal("confirmation_token")), Nothing, reader.GetGuid(reader.GetOrdinal("confirmation_token")).ToString())
                Dim count = reader.GetInt32(reader.GetOrdinal("candidate_count"))
                Dim code = Text(reader, "code")
                Dim field = If(Text(reader, "field"), "")

                If PropertyNames.TryGetValue(field, [property]) Then
                    field = [property]
                Else
                    field = If(Equals(field, "reason"), "Reason", If(Equals(field, "school_year"), "SchoolYear", If(Equals(field, "grade_code"), "GradeCode", field)))
                End If

                Dim errors = If(code?.StartsWith("E-", StringComparison.Ordinal) = True, {New FieldError(field, code, NativeMessages.Resolve(code, field, requestId:=requestId))}, New Global.StudentManagement.WinForms.Domain.FieldError() {})
                Dim candidates = New List(Of StudentRow)()
                If Await reader.NextResultAsync(ct) Then
                    While Await reader.ReadAsync(ct)
                        ' Confirmation exposes only the four permitted display categories.
                        candidates.Add(New Global.StudentManagement.WinForms.Domain.StudentRow(0, Text(reader, "student_no"), Text(reader, "student_name"), "", DateOnly.FromDateTime(reader.GetDateTime(reader.GetOrdinal("birth_date"))), Nothing, Nothing, Nothing, Text(reader, "class_name"), Nothing, "", Nothing, DateOnly.MinValue, DateTimeOffset.MinValue, 0))
                    End While
                End If

                Return New Global.StudentManagement.WinForms.Domain.NativeStoredProcedureClient.Response(state, New Global.StudentManagement.WinForms.Domain.SaveResult(outcome, id, version, errors, token, count, candidates, requestId.ToString()))
            End Using
        End Function

        Private Function KnownFailure([error] As SqlException, requestId As Guid) As SaveResult
            Return If([error].Number = 2601 OrElse [error].Number = 2627, Failure(Outcome.ValidationFailed, "E-STU-101", "StudentNo", requestId), If([error].Number = 547, Failure(Outcome.ValidationFailed, "E-STU-009", "Save", requestId), If([error].Number = 1205 OrElse [error].Number = 1222 OrElse [error].Number = 3960 OrElse [error].Number = 51001 OrElse [error].Number = 51005, Failure(Outcome.Conflict, "E-STU-105", "Save", requestId), If([error].Number = 229, Failure(Outcome.Forbidden, "E-COM-002", "Save", requestId), Nothing))))
        End Function
        Private Function Failure(outcome As Outcome, code As String, field As String, requestId As Guid) As SaveResult
            Return New Global.StudentManagement.WinForms.Domain.SaveResult(outcome, Nothing, Nothing, New Global.StudentManagement.WinForms.Domain.FieldError() {New Global.StudentManagement.WinForms.Domain.FieldError(field, code, NativeMessages.Resolve(code, field, requestId:=requestId))}, RequestId:=requestId.ToString())
        End Function
        ' Raw strings are deliberately unnormalized. Character entities preserve CR before raw scalar checks.
        Public Function SerializeRaw(request As SaveRequest) As String
            Dim d = request.Draft
            Dim birth = d.BirthDateInput
            Dim buffer = New StringBuilder()
            Using xml = XmlWriter.Create(buffer, New XmlWriterSettings With {
                .OmitXmlDeclaration = True,
                .NewLineHandling = NewLineHandling.Entitize,
                .CheckCharacters = True
            })
                xml.WriteStartElement("raw")
                Dim Field As Action(Of String, Object) = Sub(key, value)
                                                             xml.WriteStartElement(key)
                                                             If value Is Nothing Then
                                                                 xml.WriteAttributeString("null", "true")
                                                             Else
                                                                 xml.WriteString(If(Convert.ToString(value, CultureInfo.InvariantCulture), ""))
                                                             End If
                                                             xml.WriteEndElement()
                                                         End Sub
                Field("student_no", d.StudentNo)
                Field("student_name", d.StudentName)
                Field("student_name_kana", d.StudentNameKana)
                Field("birth_era", birth.Era)
                Field("birth_year", birth.Year)
                Field("birth_month", birth.Month)
                Field("birth_day", birth.Day)
                Field("gender_code", d.GenderCode)
                Field("postal_code", d.PostalCode)
                Field("prefecture_code", d.PrefectureCode)
                Field("address_line1", d.AddressLine1)
                Field("address_line2", d.AddressLine2)
                Field("phone_number", d.PhoneNumber)
                Field("email_address", d.EmailAddress)
                Field("admission_date", d.AdmissionDate)
                Field("enrollment_status_code", d.EnrollmentStatusCode)
                Field("enrollment_end_date", d.EnrollmentEndDate)
                Field("class_id", d.ClassId)
                Field("emergency_contact_name", d.EmergencyContactName)
                Field("relationship_code", d.RelationshipCode)
                Field("emergency_phone_number", d.EmergencyPhoneNumber)
                Field("remarks", d.Remarks)
                Field("school_year", request.SchoolYear)
                Field("grade_code", request.GradeCode)
                Field("reason", request.Reason)
                xml.WriteEndElement()
            End Using

            Return buffer.ToString()
        End Function

        Public Function SerializeClass(c As ClassChange, Optional reason As String = Nothing) As String
            Return SerializeFields(New Dictionary(Of String, Object) From {
                {"school_year", c.SchoolYear},
                {"grade_code", c.GradeCode},
                {"class_code", c.ClassCode},
                {"class_name", c.ClassName},
                {"valid_from", c.ValidFrom},
                {"valid_to", c.ValidTo},
                {"capacity", c.Capacity},
                {"display_order", c.DisplayOrder},
                {"is_active", c.IsActive},
                {"remarks", c.Remarks},
                {"reason", reason}
            })
        End Function
        Public Function SerializeCode(c As CodeChange, Optional reason As String = Nothing) As String
            Return SerializeFields(New Dictionary(Of String, Object) From {
                {"category_id", c.CategoryId},
                {"code_value", c.CodeValue},
                {"code_name", c.CodeName},
                {"display_order", c.DisplayOrder},
                {"is_active", c.IsActive},
                {"valid_from", c.ValidFrom},
                {"valid_to", c.ValidTo},
                {"remarks", c.Remarks},
                {"reason", reason}
            })
        End Function
        Private Function SerializeFields(values As Dictionary(Of String, Object)) As String
            Dim buffer = New StringBuilder()
            Dim b As Boolean = Nothing
            Using xml = XmlWriter.Create(buffer, New XmlWriterSettings With {
                .OmitXmlDeclaration = True,
                .NewLineHandling = NewLineHandling.Entitize,
                .CheckCharacters = True
            })
                xml.WriteStartElement("raw")
                For Each pair In values
                    xml.WriteStartElement(pair.Key)
                    If pair.Value Is Nothing Then
                        xml.WriteAttributeString("null", "true")
                    Else
                        xml.WriteString(If(TypeOf pair.Value Is Boolean, If(CBool(pair.Value), "true", "false"), If(Convert.ToString(pair.Value, CultureInfo.InvariantCulture), "")))
                    End If
                    xml.WriteEndElement()
                Next

                xml.WriteEndElement()
            End Using

            Return buffer.ToString()
        End Function

        Private Class ConversionSupport
            
            Shared Function __Assign(Of T)(ByRef target As T, value As T) As T
                target = value
                Return value
            End Function
        End Class
    End Module

End Namespace
