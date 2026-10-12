Option Strict On
Imports System
Imports System.Collections.Generic
Imports System.Globalization
Imports System.Linq
Imports System.Text.Json

' Test doubles return supplied rows and record interactions, without business calculations.
Public Class SelectionChangedEventArgs
    Inherits EventArgs
End Class
Public Class DummyButton
    Public Property IsEnabled As Boolean
End Class
Public Class DummySelection
    Public Property SelectedItem As Object
End Class
Public Class Application
    Public Shared ReadOnly Current As New Application()
    Public ReadOnly Resources As New Dictionary(Of String,Object) From {{"txt--money","txt--money"},{"txt--money_minus","txt--money_minus"}}
End Class
Public Class EventPorts
    Public Shared SourceUpdates As Integer
    Public Shared Calls As New List(Of String)()
    Public Shared AddressResult As String=""
    Public Shared Sub Reset()
        SourceUpdates=0 : Calls.Clear() : AddressResult=""
    End Sub
    Public Shared Sub ObserveQuery(sql As String, parameters As List(Of NpgsqlParameter))
        Dim tier=If(sql.Contains("m206_magazine_price"),"conditional","base")
        Dim value As Func(Of String,String)=Function(n) Convert.ToString(parameters.Single(Function(p) p.ParameterName=n).Value,CultureInfo.InvariantCulture)
        Calls.Add(tier & "|" & value("prBOOK_CD") & "|" & value("prCS_KBN") & "|" & value("prHAISO_KBN"))
    End Sub
    Public Shared Function PriceRow(tier As String, book As String, customer As Integer, delivery As Integer) As Dictionary(Of String,Object)
        MyNpg.Queries+=1
        Calls.Add(tier & "|" & book & "|" & customer.ToString() & "|" & delivery.ToString())
        Return If(tier="conditional",MyNpg.Primary,MyNpg.Fallback)
    End Function
    Public Shared Function ReadPostal(leftValue As String,rightValue As String) As String
        Calls.Add("postal|" & leftValue & "|" & rightValue)
        Return AddressResult
    End Function
End Class

Public Module EventCases
    Private Function Price(value As Object) As Dictionary(Of String,Object)
        Return New Dictionary(Of String,Object) From {{"booknm","見本"},{"sell_kbn",2},{"kbnmei","試験"},{"fixedprice",value},{"discount",123},{"reducepercent",15}}
    End Function
    Private Function Model(scenarioIndex As Integer) As SpecialModel
        Return New SpecialModel With {.BookCd=If(scenarioIndex=0,"","B001"),.ReducePercent=CSng(10.5+scenarioIndex),.FixedPrice=1001,.Discounts=210,.SeikyuTanka=777,.SeikyuPrice=-432,.SendCopies=scenarioIndex-2,.UriageKbn=3,.SagawaAddress="元の住所"}
    End Function
    Private Sub Setup(scenarioIndex As Integer)
        MyNpg.Reset(False) : EventPorts.Reset()
        MyNpg.Primary=If(scenarioIndex=1 OrElse scenarioIndex=2,Nothing,Price(If(scenarioIndex=3,DirectCast(DBNull.Value,Object),1000)))
        MyNpg.Fallback=If(scenarioIndex=2,Nothing,Price(800))
    End Sub
    Public Function Snapshot(model As SpecialModel, enabled As Boolean, maximum As Integer, style As String, failure As String) As String
        Return JsonSerializer.Serialize(New With {.model=model,.priceEnabled=enabled,.maximum=maximum,.style=style,.sourceUpdates=EventPorts.SourceUpdates,.calls=EventPorts.Calls,.dbWrites=MyNpg.Executions,.failure=failure})
    End Function
    Private Function Observe(original As Boolean,eventName As String,active As Boolean,mode As String,minus As Boolean,scenarioIndex As Integer,Optional postalLeft As String="100",Optional postalRight As String="0001",Optional address As String="") As String
        Setup(scenarioIndex) : EventPorts.AddressResult=address
        Dim m=Model(scenarioIndex) : m.SagawaPostalno1=postalLeft : m.SagawaPostalno3=postalRight
        If original Then
            Dim o=New OriginalFeature()
            Return o.RunEvent(eventName,m,active,mode,minus,scenarioIndex<>1)
        Else
            Dim o=New RebuiltEvents(m,active,mode,minus,scenarioIndex<>1),failure=""
            Try
                o.Dispatch(eventName)
            Catch ex As Exception
                failure=ex.GetType().FullName
            End Try
            Return Snapshot(m,o.PriceEnabled,o.MaxLength,o.Style,failure)
        End If
    End Function
    Public Function Run() As List(Of Dictionary(Of String,Object))
        Dim results=New List(Of Dictionary(Of String,Object))(),number=0
        For Each eventName In {"rate","discount","calculate","minus","book","price"}
            For Each active In {False,True}
                For Each mode In {"ADD","EDT"}
                    For Each minus In {False,True}
                        For scenarioIndex As Integer=0 To 4
                            number+=1
                            Dim expected=Observe(True,eventName,active,mode,minus,scenarioIndex), actual=Observe(False,eventName,active,mode,minus,scenarioIndex)
                            Dim expectedFailure=(scenarioIndex=3 AndAlso (eventName="price" OrElse eventName="book" AndAlso active))
                            Dim parsed=JsonDocument.Parse(expected), failure=parsed.RootElement.GetProperty("failure").GetString()
                            Dim passed=expected=actual AndAlso (If(expectedFailure,failure="System.InvalidCastException",failure=""))
                            results.Add(New Dictionary(Of String,Object) From {{"case","EVENT-" & number},{"family","event_" & eventName},{"passed",passed},{"original",expected},{"reimplemented",actual},{"model_injection",True}})
                        Next
                    Next
                Next
            Next
        Next
        For Each active In {False,True}
            For Each values In {Tuple.Create("100","0001"),Tuple.Create(" 100 "," 0001 "),Tuple.Create("10","0001"),Tuple.Create("100","001"),Tuple.Create(DirectCast(Nothing,String),"0001"),Tuple.Create("100",DirectCast(Nothing,String))}
                For Each address In {"","補完した住所"}
                    number+=1
                    Dim expected=Observe(True,"postal",active,"ADD",False,0,values.Item1,values.Item2,address), actual=Observe(False,"postal",active,"ADD",False,0,values.Item1,values.Item2,address)
                    Dim failure=JsonDocument.Parse(expected).RootElement.GetProperty("failure").GetString()
                    results.Add(New Dictionary(Of String,Object) From {{"case","EVENT-" & number},{"family","event_postal"},{"passed",expected=actual AndAlso failure=""},{"original",expected},{"reimplemented",actual},{"model_injection",True}})
                Next
            Next
        Next
        Return results
    End Function
End Module
