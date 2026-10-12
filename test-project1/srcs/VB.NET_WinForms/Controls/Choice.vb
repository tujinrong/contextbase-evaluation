Namespace Controls
    Public Class Choice
        Public ReadOnly Property Value As String
        Public ReadOnly Property Name As String
        Public ReadOnly Property Selectable As Boolean
        Public Sub New(value As String, name As String, Optional selectable As Boolean = True)
            Me.Value = value : Me.Name = name : Me.Selectable = selectable
        End Sub
        Public Overrides Function ToString() As String
            Return Name & If(Selectable, "", "（停止・期間外）")
        End Function
    End Class
End Namespace
