Option Explicit
' 日本語版Access用のCP932入力fixture。期待値は別のUnicodeコードポイント列。
Public Function EncodingFixtureValue(ByVal index As Long) As String
 Select Case index
 Case 0: EncodingFixtureValue = "社員検索"
 Case 1: EncodingFixtureValue = "基本情報・職務"
 Case 2: EncodingFixtureValue = "氏名カナ"
 Case 3: EncodingFixtureValue = "ｱｲｳ"
 Case 4: EncodingFixtureValue = """A"" O'Brien"
 Case 5: EncodingFixtureValue = "〜"
 Case 6: EncodingFixtureValue = ChrW(&H301C)
 Case 7: EncodingFixtureValue = "−"
 Case 8: EncodingFixtureValue = ChrW(&H2212)
 Case 9: EncodingFixtureValue = ChrW(&HD83D) & ChrW(&HDE00)
 Case 10: EncodingFixtureValue = "g j p q y 0123"
 Case Else: Err.Raise 5
 End Select
End Function
