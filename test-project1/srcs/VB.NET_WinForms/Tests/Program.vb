Imports StudentManagement.WinForms.Domain
Imports VB = StudentManagement.WinForms
Imports System.Linq
Imports System.Collections.Generic

Module Program
    Private count As Integer
    Private ReadOnly outcomes As New List(Of Object)
    Private Sub Same(Of T)(expected As T, actual As T, id As String)
        If Not EqualityComparer(Of T).Default.Equals(expected, actual) Then Throw New Exception(id & ": expected " & Convert.ToString(expected) & ", actual " & Convert.ToString(actual))
        count += 1
        outcomes.Add(New With {.id=id, .passed=True})
    End Sub
    Private Sub Reject(action As Action, id As String)
        Try
            action()
        Catch ex As ArgumentException
            count += 1 : outcomes.Add(New With {.id=id, .passed=True}) : Return
        Catch ex As InputValidationException
            count += 1 : outcomes.Add(New With {.id=id, .passed=True}) : Return
        End Try
        Throw New Exception(id & ": invalid input accepted")
    End Sub
    Private Function Parse(era As String, year As String, month As String, day As String) As DateOnly
        Return JapaneseDateService.Parse(New BirthDateInput(era,year,month,day), New DateOnly(2026,10,10))
    End Function
    Private Function Draft() As StudentDraft
        Return New StudentDraft With {.StudentNo="S2026-0001", .StudentName="見本 太郎", .StudentNameKana="ミホン タロウ", .BirthDateInput=New BirthDateInput("HEISEI","20","05","15"), .GenderCode="0", .PostalCode="1000001", .PrefectureCode="13", .AddressLine1="見本町1", .PhoneNumber="0312345678", .AdmissionDate="2026-04-01", .EnrollmentStatusCode="03", .EnrollmentEndDate="2026-10-10"}
    End Function
    Private Function Invalid(edit As Action(Of StudentDraft)) As IReadOnlyList(Of FieldError)
        Dim input=Draft() : edit(input)
        Try
            StudentNormalizer.Normalize(input,New DateOnly(2026,10,10))
        Catch ex As InputValidationException
            Same(True,ex.Errors.Count>0,"combined validation") : Return ex.Errors
        End Try
        Throw New Exception("invalid combined draft accepted")
    End Function
    <STAThread>
    Sub Main()
        Same("平成20年05月15日",JapaneseDateService.ToWareki(New DateOnly(2008,5,15)),"DATE-T01")
        Same(New DateOnly(1900,1,1),Parse("MEIJI","33","01","01"),"DATE-T02")
        Reject(Sub() Parse("MEIJI","32","12","31"),"DATE-T02 below")
        For Each boundary In {("TAISHO","1","07","29","30"),("SHOWA","1","12","24","25"),("HEISEI","1","01","07","08"),("REIWA","1","05","00","01")}
            Dim value=boundary
            Reject(Sub() Parse(value.Item1,value.Item2,value.Item3,value.Item4),"boundary " & value.Item1)
            Same(value.Item1,JapaneseDateService.ToInput(Parse(value.Item1,value.Item2,value.Item3,value.Item5)).Era,"reverse " & value.Item1)
        Next
        For Each boundary In {("TAISHO","15","12","25"),("SHOWA","64","01","08"),("HEISEI","31","05","01"),("REIWA","元","04","30")}
            Dim value=boundary : Reject(Sub() Parse(value.Item1,value.Item2,value.Item3,value.Item4),"era end " & value.Item1)
        Next
        For Each yearText As String In {"0","-1","99999","1e2","1.5",""}
            Dim value=yearText : Reject(Sub() Parse("REIWA",value,"05","01"),"DATE-T10 " & value)
        Next
        Reject(Sub() Parse("UNKNOWN","1","01","01"),"unknown era")
        Same(New DateOnly(2000,2,29),Parse("HEISEI","12","02","29"),"leap")
        Reject(Sub() Parse("HEISEI","13","02","29"),"nonleap")
        Same(New DateOnly(2026,10,10),Parse("REIWA","8","10","10"),"today")
        Reject(Sub() Parse("REIWA","8","10","11"),"future")
        For Each dateText In {"2026-04-31","2026-13-01","26-04-01","1899-12-31","2026-10-11"}
            Dim value=dateText : Reject(Sub() JapaneseDateService.ParseIso(value,New DateOnly(2026,10,10)),"ISO " & value)
        Next
        Same(2025,JapaneseDateService.SchoolYear(New DateOnly(2026,3,31)),"fiscal before")
        Same(2026,JapaneseDateService.SchoolYear(New DateOnly(2026,4,1)),"fiscal after")
        Same(8,StudentNormalizer.ScalarCount(String.Concat(Enumerable.Repeat("𠮷",8))),"scalar8")
        Reject(Sub() StudentNormalizer.ScalarCount(ChrW(&HD800)),"invalid high surrogate")
        Reject(Sub() StudentNormalizer.ScalarCount(ChrW(&HDC00)),"invalid low surrogate")
        Reject(Sub() StudentNormalizer.Text("         ",8,8,"StudentName"),"raw before trim")
        Reject(Sub() StudentNormalizer.Text("123456789",8,8,"StudentName"),"raw9")
        Same(String.Concat(Enumerable.Repeat("𠮷",8)),StudentNormalizer.Text(String.Concat(Enumerable.Repeat("𠮷",8)),8,8,"StudentName"),"supplementary8")
        Same("見本 太郎",StudentNormalizer.Text("見本 太郎",8,8,"StudentName"),"internal space")
        Same("AB-01",StudentNormalizer.Identifier("ＡＢ-01",15,"StudentNo"),"N06")
        Reject(Sub() StudentNormalizer.Identifier("-A",15,"StudentNo"),"N06 initial")
        Same("AB",StudentNormalizer.NameKey("Ａ  ｂ"),"N03")
        Same("ミホン ガ",StudentNormalizer.Kana("みほん  ｶﾞ"),"N04")
        Reject(Sub() StudentNormalizer.Kana("ﾐ" & New String("ｱ"c,36)),"raw37")
        Reject(Sub() StudentNormalizer.Kana(New String("ア"c,19)),"saved19")
        Reject(Sub() StudentNormalizer.Kana("abc"),"kana latin")
        Same("1000001",StudentNormalizer.Postal("１００－０００１"),"N08")
        Same("0312345678",StudentNormalizer.Phone("(03)1234-5678","PhoneNumber"),"N09")
        Same("+81312345678",StudentNormalizer.Phone("+81 3 1234 5678","PhoneNumber"),"N09 intl")
        Reject(Sub() StudentNormalizer.Phone("+012345678","PhoneNumber"),"intl zero")
        Reject(Sub() StudentNormalizer.Phone("03/1234/5678","PhoneNumber"),"phone separator")
        Same("User@example.com",StudentNormalizer.Email(" User@EXAMPLE.COM "),"N10")
        For Each address In {".x@example.com","x..y@example.com","x@example","x@-example.com","x@example-.com","x@例.jp"}
            Dim value=address : Reject(Sub() StudentNormalizer.Email(value),"email " & value)
        Next
        Same("!%!_!!![",StudentNormalizer.EscapeLike("%_!["),"SQL LIKE escape")
        Reject(Sub() StudentNormalizer.Code("1",2,"GradeCode"),"no padding")
        Reject(Sub() StudentNormalizer.Text("a" & vbTab & "b",120,120,"Remarks",multiline:=True),"tab reject")
        Same("a" & vbLf & "b",StudentNormalizer.Text("a" & vbCrLf & "b",120,120,"Remarks",multiline:=True),"LF")
        Dim errors=Invalid(Sub(d) d.StudentName=ChrW(&HD800))
        Same(True,errors.Any(Function(e) e.Field="StudentName" AndAlso e.Code="E-STU-002"),"invalid Unicode field")
        errors=Invalid(Sub(d) d.AdmissionDate="2000-04-01")
        Same(True,errors.Any(Function(e) e.Code="E-STU-007"),"birth before admission")
        errors=Invalid(Sub(d) d.PhoneNumber=Nothing)
        Same(True,errors.Any(Function(e) e.Code="E-STU-018"),"contact required")
        errors=Invalid(Sub(d) d.EmergencyContactName="見本 花子")
        Same(True,errors.Any(Function(e) e.Code="E-STU-019"),"emergency all three")
        errors=Invalid(Sub(d) d.EnrollmentStatusCode="01")
        Same(True,errors.Any(Function(e) e.Code="E-STU-012"),"active class required")
        Same(True,errors.Any(Function(e) e.Code="E-STU-008"),"active end excluded")
        Dim normalized=StudentNormalizer.Normalize(Draft(),New DateOnly(2026,10,10))
        For Each column In {"emergency_contact_name","relationship_category","relationship_code","emergency_phone_number"}
            Same(Of Object)(Nothing,normalized.Values(column),"R74 empty " & column)
        Next
        Dim complete=Draft() : complete.EmergencyContactName="見本 花子" : complete.RelationshipCode="01" : complete.EmergencyPhoneNumber="0312345678"
        normalized=StudentNormalizer.Normalize(complete,New DateOnly(2026,10,10))
        Same("RELATIONSHIP",normalized.Text("relationship_category"),"R74 derived")
        Same("01",normalized.Text("relationship_code"),"R74 code")
        complete.EmergencyContactName=Nothing : complete.RelationshipCode=Nothing : complete.EmergencyPhoneNumber=Nothing
        normalized=StudentNormalizer.Normalize(complete,New DateOnly(2026,10,10))
        Same(Of Object)(Nothing,normalized.Values("relationship_category"),"R74 clear")
        For Each state In {(CType(Nothing,Boolean?),False,"CREATE"),(CType(Nothing,Boolean?),True,"CREATE"),(CType(False,Boolean?),False,"UPDATE"),(CType(True,Boolean?),True,"UPDATE"),(CType(True,Boolean?),False,"DISABLE"),(CType(False,Boolean?),True,"ENABLE")}
            Same(state.Item3,AuditOperation.ForMaster(state.Item1,state.Item2),"audit " & state.Item3)
        Next
        Using control As New VB.Controls.NullableDateControl
            control.RawText="2026-02-31" : Same("2026-02-31",control.RawText,"UI invalid raw date")
            control.RawText="" : Same("",control.RawText,"UI nullable date")
        End Using
        Using control As New VB.Controls.JapaneseBirthDateControl
            control.LoadRaw(New BirthDateInput("REIWA","元","2","31"))
            Dim raw=control.ReadRaw() : Same("元",raw.Year,"UI raw year") : Same("31",raw.Day,"UI raw invalid day")
        End Using
        Dim rawDraft=Draft() : rawDraft.StudentName=" Ａ  b " : rawDraft.Remarks="a" & vbCrLf & "b"
        Dim xml=System.Xml.Linq.XDocument.Parse(NativeStoredProcedureClient.SerializeRaw(New SaveRequest(rawDraft)))
        Same(" Ａ  b ",xml.Root.Element("student_name").Value,"wire preserves raw name")
        Same("a" & vbCrLf & "b",xml.Root.Element("remarks").Value,"wire preserves CRLF")
        Same("true",xml.Root.Element("class_id").Attribute("null").Value,"wire null class")
        Same(False,xml.Root.Elements("name_key").Any(),"wire excludes client key")
        Same(False,xml.Root.Elements("principal").Any(),"wire excludes client principal")
        Same(False,xml.Root.Elements("relationship_category").Any(),"wire excludes derived category")
        Dim classXml=System.Xml.Linq.XDocument.Parse(NativeStoredProcedureClient.SerializeClass(New ClassChange(Nothing,Nothing,2026,"01","A","試験", "2026-04-01","2027-03-31",Nothing,0,False,Nothing)))
        Same("false",classXml.Root.Element("is_active").Value,"wire Boolean false")
        Same("true",classXml.Root.Element("capacity").Attribute("null").Value,"wire nullable capacity")
        Same(True,NativeMessages.Resolve("E-STU-002","student_name").Contains("氏名"),"message field Japanese")
        Same(False,NativeMessages.Resolve("E-STU-002","student_name").Contains("{max}"),"message maximum substituted")
        normalized=StudentNormalizer.Normalize(New StudentDraft With {.StudentNo="S1",.StudentName="試験",.StudentNameKana="シケン",.BirthDateInput=New BirthDateInput("HEISEI","20","05","15"),.GenderCode="0",.PostalCode="1000001",.PrefectureCode="13",.AddressLine1="試験",.PhoneNumber="0312345678",.AdmissionDate="2026-04-01",.EnrollmentStatusCode="01",.ClassId=1,.EnrollmentEndDate=Nothing},New DateOnly(2026,10,10))
        Same(Of Object)(Nothing,normalized.Values("enrollment_end_date"),"optional date stays null")
        Using command=SqlServerStudentService.Command(Nothing,Nothing,"SELECT @value")
            SqlServerStudentService.Param(command,"@value",System.Data.SqlDbType.Date,New DateOnly(2026,10,10))
            Same(New DateTime(2026,10,10),CType(command.Parameters("@value").Value,DateTime),"typed date parameter")
        End Using
        Using command=SqlServerStudentService.Command(Nothing,Nothing,"SELECT @value")
            SqlServerStudentService.Param(command,"@value",System.Data.SqlDbType.BigInt,Nothing)
            Same(Of Object)(DBNull.Value,command.Parameters("@value").Value,"typed null parameter")
        End Using
        Dim malformedClass As New ClassChange(Nothing,Nothing,2026,"01","A",ChrW(&HD800),"2026-04-01","2027-03-31",Nothing,0,True,Nothing)
        Dim classFailure=NativeStoredProcedureClient.SaveClassAsync(Nothing,Nothing,malformedClass,Guid.NewGuid()).GetAwaiter().GetResult()
        Same(Outcome.ValidationFailed,classFailure.Outcome,"NATIVE-XML-R2-CLASS invalid surrogate rejected")
        Same(ChrW(&HD800),malformedClass.ClassName,"NATIVE-XML-R2-CLASS raw retained")
        Dim malformedCode As New CodeChange("GRADE","09",Nothing,ChrW(0),0,True,"2026-04-01",Nothing,Nothing)
        Dim codeFailure=NativeStoredProcedureClient.SaveCodeAsync(Nothing,Nothing,malformedCode,Guid.NewGuid()).GetAwaiter().GetResult()
        Same(Outcome.ValidationFailed,codeFailure.Outcome,"NATIVE-XML-R2-CODE invalid XML control rejected")
        Same(ChrW(0),malformedCode.CodeName,"NATIVE-XML-R2-CODE raw retained")
        Dim trueXml=System.Xml.Linq.XDocument.Parse(NativeStoredProcedureClient.SerializeCode(New CodeChange("GRADE","09",Nothing,"試験",0,True,"2026-04-01",Nothing,Nothing)))
        Same("true",trueXml.Root.Element("is_active").Value,"NATIVE-XML-R2-BOOL lower-case true")
        Dim appService As New VB.Application.StudentApplicationService("Server=unconnected.invalid;Database=none;Integrated Security=true;Encrypt=true")
        Using form As New VB.Forms.FrmStudentSearch(appService)
            Same(True,form.Controls.Count>0,"search construction")
        End Using
        Using form As New VB.Forms.FrmStudentEdit(appService,Nothing)
            Same(True,form.Controls.Count>0,"edit construction")
        End Using
        Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(New With {.profile="VB.NET_WinForms", .passed=count,.failed=0,.cases=outcomes,.database="NOT_RUN",.interactiveUI="NOT_RUN"}))
    End Sub
End Module
