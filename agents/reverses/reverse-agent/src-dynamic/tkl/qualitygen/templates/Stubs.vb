Option Strict Off
Imports System
Imports System.Collections.Generic
Imports System.Data
Imports System.Linq
Imports System.Text

' Evaluation-only adapters: no network, database connection, files or production settings.
Public Class RoutedEventArgs
    Inherits EventArgs
End Class
Public Class DummyText
    Public Property Text As String
End Class
Public Class DummyCheck
    Public Property IsChecked As Boolean
End Class
Public Enum MessageBoxResult
    Yes
    No
    Cancel
End Enum
Public Class NpgsqlParameter
    Public Property ParameterName As String
    Public Property Value As Object
    Public Sub New(name As String, value_ As Object)
        ParameterName=name : Value=value_
    End Sub
End Class
Public Class MyGlobal
    Public Shared UserNm As String = "試験利用者"
End Class
Public Class MyPara
    Public Class CommandMode
        Public Const ADD As String = "ADD"
        Public Const EDT As String = "EDT"
    End Class
End Class
Public Class MyMessage
    Public Const ORDER_CONFIRM_KAKUTEI As String = "確定確認"
    Public Const ORDER_CONFIRM_KARI As String = "仮注文確認"
    Public Shared Last As String = ""
    Public Shared Confirm As Boolean = True
    Public Shared Answer As MessageBoxResult = MessageBoxResult.Yes
    Public Shared Sub ShowWarning(text As String)
        Last = text
    End Sub
    Public Shared Function ShowYesNo(text As String) As Boolean
        Return Confirm
    End Function
    Public Shared Function ShowYesNoCancel(text As String) As MessageBoxResult
        Return Answer
    End Function
End Class
Public Class MyNpg
    Implements IDisposable
    Public Shared Sqls As New List(Of String)()
    Public Shared Batches As New List(Of List(Of NpgsqlParameter))()
    Public Shared Fail As Boolean
    Public Shared Executions As Integer
    Public Shared Queries As Integer
    Public Shared Primary As Dictionary(Of String,Object)
    Public Shared Fallback As Dictionary(Of String,Object)
    Public Shared Function SqlParameter(name As String,value As Object) As NpgsqlParameter
        Return New NpgsqlParameter(name,value)
    End Function
    Public Shared Function ExecuteData(sql As List(Of String),parameters As List(Of List(Of NpgsqlParameter))) As Boolean
        Executions += 1 : Sqls=sql : Batches=parameters
        Return Not Fail
    End Function
    Public Function DataReader(sql As String,parameters As List(Of NpgsqlParameter)) As DataTableReader
        Queries += 1
        Dim row = If(sql.Contains("m206_magazine_price"),Primary,Fallback)
        Dim t = New DataTable()
        For Each key In {"booknm","sell_kbn","kbnmei","fixedprice","discount","reducepercent"}
            t.Columns.Add(key,GetType(Object))
        Next
        If row IsNot Nothing Then
            Dim r=t.NewRow()
            For Each col As DataColumn In t.Columns
                r(col.ColumnName)=If(row.ContainsKey(col.ColumnName),row(col.ColumnName),0)
            Next
            t.Rows.Add(r)
        End If
        Return t.CreateDataReader()
    End Function
    Public Shared Sub Reset(failure As Boolean)
        Sqls=New List(Of String)() : Batches=New List(Of List(Of NpgsqlParameter))()
        Fail=failure : Executions=0 : Queries=0 : MyApp.Number=100 : MyMessage.Last=""
    End Sub
    Public Sub Dispose() Implements IDisposable.Dispose
    End Sub
End Class
Public Class SpecialModel
    Public Property OrderNo As Integer
    Public Property CustomerId As String = "000123"
    Public Property DeliveryKbn As Integer = 2
    Public Property CustomerKbn As Integer = 1
    Public Property OrderDate As Date = New Date(2026,4,1)
    Public Property SendId As String = "000456"
    Public Property BookCd As String = "B001"
    Public Property SeikyuKbn As Integer = 1
    Public Property SendCopies As Integer = 2
    Public Property SeikyuPrice As Integer = 1800
    Public Property SeikyuTanka As Integer = 900
    Public Property FixedPrice As Integer = 1000
    Public Property Discounts As Integer = 100
    Public Property UriageKbn As Integer = 1
    Public Property ReducePercent As Integer = 10
    Public Property SagawaNm As String = "見本宛先"
    Public Property SagawaTdfkCd As String = "13"
    Public Property SagawaPostalno1 As String = "100"
    Public Property SagawaPostalno3 As String = "0001"
    Public Property SagawaAddress As String = "説明用住所"
    Public Property SagawaTel As String = "000-0000-0000"
    Public Property SagawaBulkUpdate As Boolean
End Class
