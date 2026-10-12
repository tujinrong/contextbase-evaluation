Option Strict On
Imports System
Imports System.Collections.Generic
Imports System.Globalization
Imports System.Linq
Imports System.Text.Json
Imports System.Text.RegularExpressions

Module Program
    Private ReadOnly Results As New List(Of Dictionary(Of String,Object))()
    Private Function Observe(action As Func(Of String)) As String
        Try
            Return action()
        Catch ex As Exception
            Return "exception:" & ex.GetType().FullName
        End Try
    End Function
    Private Sub Check(name As String, group As String, expected As Func(Of String), actual As Func(Of String), Optional allowException As Boolean=False)
        Dim a=Observe(expected), b=Observe(actual)
        Dim passed=a=b AndAlso (allowException OrElse Not a.StartsWith("exception:"))
        Results.Add(New Dictionary(Of String,Object) From {{"case",name},{"family",group},{"passed",passed},{"original",a},{"reimplemented",b}})
    End Sub
    Private Function NormalSql(text As String) As String
        Return Regex.Replace(text,"\s+","").TrimEnd(";"c).ToUpperInvariant()
    End Function
    Private Function DbSnapshot() As String
        Dim parts=New List(Of String) From {MyNpg.Executions.ToString()}
        For i=0 To MyNpg.Sqls.Count-1
            parts.Add(NormalSql(MyNpg.Sqls(i)))
            parts.Add(String.Join(";",MyNpg.Batches(i).OrderBy(Function(p) p.ParameterName).Select(Function(p) p.ParameterName & "=" & Convert.ToString(p.Value,CultureInfo.InvariantCulture))))
        Next
        Return String.Join("|",parts)
    End Function
    Private Function OriginalUpdate(mode As String, bulk As Boolean, failure As Boolean, action As String, answer As MessageBoxResult, confirm As Boolean) As String
        MyNpg.Reset(failure) : MyMessage.Answer=answer : MyMessage.Confirm=confirm
        Dim o=New OriginalFeature()
        o.CommandMode=mode : o._Model=New SpecialModel With {.OrderNo=501,.SagawaBulkUpdate=bulk}
        o.Orders=New List(Of SpecialModel) From {New SpecialModel With {.SagawaBulkUpdate=bulk},New SpecialModel With {.SendCopies=-1}}
        Dim cancel=False
        Select Case action
            Case "confirm" : o.RunConfirm()
            Case "close" : cancel=o.RunClose()
            Case Else : o.RunPersist()
        End Select
        Return DbSnapshot() & "|" & String.Join(",",o.Orders.Select(Function(x) x.OrderNo)) & "|" & o.State() & "|" & cancel.ToString()
    End Function
    Private Function RebuiltUpdate(mode As String, bulk As Boolean, failure As Boolean, action As String, answer As MessageBoxResult, confirm As Boolean) As String
        MyNpg.Reset(failure) : MyMessage.Answer=answer : MyMessage.Confirm=confirm
        Dim o=New RebuiltFeature With {.Mode=mode,.Model=New SpecialModel With {.OrderNo=501,.SagawaBulkUpdate=bulk}}
        o.Orders=New List(Of SpecialModel) From {New SpecialModel With {.SagawaBulkUpdate=bulk},New SpecialModel With {.SendCopies=-1}}
        Dim cancel=False
        Select Case action
            Case "confirm" : o.Confirm()
            Case "close" : cancel=o.CloseRequest()
            Case Else : o.Persist()
        End Select
        Return DbSnapshot() & "|" & String.Join(",",o.Orders.Select(Function(x) x.OrderNo)) & "|" & String.Join(",",o.Changed,o.Updated,o.Dialog,o.Closed) & "|" & cancel.ToString()
    End Function
    Private Function OriginalLookup(p As Dictionary(Of String,Object), b As Dictionary(Of String,Object)) As String
        MyNpg.Reset(False) : MyNpg.Primary=p : MyNpg.Fallback=b
        Dim o=New MasterBookModel()
        o.FindPrice("B001",1,2)
        Return String.Join("|",o.FixedPrice,o.Discount,o.ReducePercent,MyNpg.Queries)
    End Function
    Sub Main(args As String())
        CultureInfo.CurrentCulture=CultureInfo.InvariantCulture
        Dim n=0
        For Each price In {0,5,15,25,1000,1001,-5,2147483}
            For Each rateValue As Integer In {0,10,50,100,101}
                Dim p=price,r=rateValue : n+=1
                Check("DIS-" & n,"discount_rounding",Function() MyApp.GetBookDiscount(r,p).ToString(),Function() RebuiltRules.Discount(r,p).ToString())
            Next
        Next
        n=0
        For Each pair In {Tuple.Create(1000,100),Tuple.Create(5,10),Tuple.Create(0,0),Tuple.Create(-50,20)}
            Dim p=pair.Item1,d=pair.Item2 : n+=1
            Check("UNIT-" & n,"unit_price",Function() MyApp.GetBookPrice(p,d).ToString(),Function() RebuiltRules.UnitPrice(p,d).ToString())
        Next
        n=0
        For Each mode In {"ADD","EDT"}
            For Each minus In {False,True}
                For Each quantity In {"", "-1000","-999","-1","0","1","999","1000"}
                    Dim m=mode,b=minus,q=quantity : n+=1
                    Check("QTY-" & n,"quantity_and_abort",Function() (New OriginalFeature()).RunQuantity(q,m,b,900),Function() RebuiltRules.Quantity(q,m,b,900,-987))
                Next
            Next
        Next
        n=0
        For Each mode In {"ADD","EDT"}
            For Each bulk In {False,True}
                For Each failure In {False,True}
                    For Each action In {"persist","confirm","close"}
                        For Each answer In {MessageBoxResult.Yes,MessageBoxResult.No,MessageBoxResult.Cancel}
                            Dim m=mode,b=bulk,f=failure,a=action,v=answer : n+=1
                            Dim confirm=(answer=MessageBoxResult.Yes)
                            Check("DB-" & n,"sql_order_parameters_and_state",Function() OriginalUpdate(m,b,f,a,v,confirm),Function() RebuiltUpdate(m,b,f,a,v,confirm))
                        Next
                    Next
                Next
            Next
        Next
        Dim primary=New Dictionary(Of String,Object) From {{"booknm","見本"},{"sell_kbn",1},{"kbnmei","見本区分"},{"fixedprice",1000},{"discount",100},{"reducepercent",10}}
        Dim fallback=New Dictionary(Of String,Object) From {{"booknm","見本"},{"sell_kbn",1},{"kbnmei","見本区分"},{"fixedprice",800},{"discount",0},{"reducepercent",0}}
        Check("PRICE-primary","price_priority",Function() OriginalLookup(primary,fallback),Function() RebuiltRules.Lookup(primary,fallback))
        Check("PRICE-fallback","price_priority",Function() OriginalLookup(Nothing,fallback),Function() RebuiltRules.Lookup(Nothing,fallback))
        Check("PRICE-missing","price_priority",Function() OriginalLookup(Nothing,Nothing),Function() RebuiltRules.Lookup(Nothing,Nothing))
        Dim nullPrice=New Dictionary(Of String,Object)(fallback) : nullPrice("fixedprice")=DBNull.Value
        Check("PRICE-null","price_priority",Function() OriginalLookup(Nothing,nullPrice),Function() RebuiltRules.Lookup(Nothing,nullPrice),True)
        Dim failed=Results.Where(Function(r) Not CBool(r("passed"))).Count()
        Dim report=New Dictionary(Of String,Object) From {{"status",If(failed=0,"subset_pass","failed")},{"native_language","VB.NET"},{"native_runtime",Environment.Version.ToString()},{"cases",Results.Count},{"passed",Results.Count-failed},{"failed",failed},{"physical_database_tested",False},{"wpf_tested",False},{"full_feature_reproduction","not_verified"},{"results",Results}}
        Dim text=JsonSerializer.Serialize(report,New JsonSerializerOptions With {.WriteIndented=True})
        Dim path=If(args.Length>0,args(0),"native-result.json")
        IO.Directory.CreateDirectory(IO.Path.GetDirectoryName(IO.Path.GetFullPath(path)))
        IO.File.WriteAllText(path,text)
        Console.WriteLine("native cases=" & Results.Count & " failed=" & failed)
        Environment.ExitCode=If(failed=0,0,1)
    End Sub
End Module
