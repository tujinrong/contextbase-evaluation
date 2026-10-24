Imports System.Globalization
Imports System.Windows.Forms

Namespace Controls
    Public Class NullableDateControl
        Inherits UserControl
        Private ReadOnly _raw As New TextBox With {.MinimumSize = New System.Drawing.Size(0,34), .Dock = DockStyle.Fill, .MaxLength = 10}
        Private ReadOnly _calendar As New DateTimePicker With {.Dock = DockStyle.Right, .Width = 28, .Format = DateTimePickerFormat.Custom, .CustomFormat = " ", .ShowCheckBox = False, .AccessibleName = "西暦日付のカレンダー"}
        Private _syncing As Boolean
        Public Sub New()
            MinimumSize = New System.Drawing.Size(0,34) : Height = 34 : Dock = DockStyle.Fill : _calendar.Checked = False
            Controls.Add(_raw) : Controls.Add(_calendar)
            AddHandler _calendar.ValueChanged, Sub(sender, e)
                                                    If _syncing Then Return
                                                    _raw.Text = _calendar.Value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)
                                                End Sub
            AddHandler _raw.TextChanged, Sub(sender, e)
                                            If _syncing Then Return
                                            _syncing = True
                                            Try
                                                Dim dateValue As DateTime
                                                If DateTime.TryParseExact(_raw.Text, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, dateValue) AndAlso dateValue >= _calendar.MinDate AndAlso dateValue <= _calendar.MaxDate Then
                                                    _calendar.Value = dateValue : _calendar.Checked = True
                                                Else
                                                    _calendar.Checked = False
                                                End If
                                                OnTextChanged(EventArgs.Empty)
                                            Finally
                                                _syncing = False
                                            End Try
                                        End Sub
        End Sub
        <System.ComponentModel.Browsable(False), System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)>
        Public Property RawText As String
            Get
                Return _raw.Text
            End Get
            Set(value As String)
                _raw.Text = value
            End Set
        End Property
    End Class
End Namespace
