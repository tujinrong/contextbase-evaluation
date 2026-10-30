Option Compare Binary
Option Explicit
Public Function UiEmployeesRows(fld As Control, id As Variant, row As Variant, col As Variant, code As Variant) As Variant
    UiEmployeesRows = ListRows(fld, id, row, col, code)
End Function
Public Function UiCareersRows(fld As Control, id As Variant, row As Variant, col As Variant, code As Variant) As Variant
    UiCareersRows = ListRows(fld, id, row, col, code)
End Function
Public Function UiCodesRows(fld As Control, id As Variant, row As Variant, col As Variant, code As Variant) As Variant
    UiCodesRows = ListRows(fld, id, row, col, code)
End Function
