Attribute VB_Name = "modMessages"
Option Explicit
Option Compare Binary

Public Function MessageText(ByVal value As String, Optional ByVal name As String = "", Optional ByVal data As String = "") As String
    Dim id As String, pieces As Variant, p As Variant, i As Long, template As String
    pieces = Split(value, "|"): id = pieces(0)
    Select Case id
    Case "I-SRC-001": template = "該当する学生がありません。"
    Case "I-STU-001": template = "学生を登録しました。（学籍番号：{studentNo}）"
    Case "I-STU-002": template = "学生情報を更新しました。"
    Case "I-STU-003": template = "学生情報を論理削除しました。"
    Case "I-STU-004": template = "変更内容がありません。"
    Case "W-SRC-001": template = "検索結果が10,000件を超えています。検索条件を追加してください。"
    Case "W-SRC-002": template = "検索条件の保持期限が切れました。条件を再指定してください。"
    Case "W-STU-101": template = "同じ生年月日で氏名または氏名カナが一致する学生が{count}件あります。別人であることを確認してください。"
    Case "W-STU-102": template = "入力内容または重複候補が変わりました。もう一度確認してください。"
    Case "W-STU-103": template = "変更内容を破棄して戻りますか。"
    Case "W-STU-104": template = "入力内容を取り消しますか。"
    Case "W-STU-105": template = "この学生を論理削除します。削除後は通常検索できません。よろしいですか。"
    Case "W-STU-106": template = "所属クラスが利用期間外です。住所等は変更できますが、クラスの見直しが必要です。"
    Case "W-STU-107": template = "選択条件が変わったためクラスの選択を解除しました。"
    Case "W-STU-108": template = "登録可能なクラスがありません。クラスマスタを確認してください。"
    Case "W-STU-109": template = "最新情報を再読み込みすると入力中の変更は破棄されます。続行しますか。"
    Case "W-MST-001": template = "同じ年度・学年に同名のクラスがあります。クラスコードと名称を確認してください。"
    Case "E-STU-001": template = "{field}を入力してください。"
    Case "E-STU-002": template = "{field}は{max}文字以内の使用可能な文字で入力してください。"
    Case "E-STU-003": template = "学籍番号は半角英数字・ハイフンで15文字以内にしてください。先頭は英数字です。"
    Case "E-STU-004": template = "氏名カナはカタカナで入力してください。中点・長音・空白は使用できます。"
    Case "E-STU-005": template = "{field}に正しい日付を入力してください。"
    Case "E-STU-006": template = "{fromField}は{toField}以前の日付にしてください。"
    Case "E-STU-007": template = "生年月日・入学日は本日以前とし、生年月日≦入学日となるよう入力してください。"
    Case "E-STU-008": template = "在籍区分に対応する卒業・退学日を設定してください。"
    Case "E-STU-009": template = "{field}のコードが存在しません。選択し直してください。"
    Case "E-STU-010": template = "指定したクラスが存在しません。選択し直してください。"
    Case "E-STU-011": template = "{field}は現在使用できないコードです。選択し直してください。"
    Case "E-STU-012": template = "在学・休学の学生はクラスを選択してください。"
    Case "E-STU-013": template = "このクラスには新たに所属できません。利用可否と利用期間を確認してください。"
    Case "E-STU-014": template = "年度・学年と選択したクラスが一致していません。"
    Case "E-STU-015": template = "郵便番号は7桁の数字で入力してください。"
    Case "E-STU-016": template = "{field}の形式が正しくありません。国内10～11桁または国番号付きの番号を入力してください。"
    Case "E-STU-017": template = "メールアドレスの形式が正しくありません。"
    Case "E-STU-018": template = "本人電話、本人メール、緊急連絡先電話のいずれかを入力してください。"
    Case "E-STU-019": template = "緊急連絡先は氏名・続柄・電話番号をすべて入力してください。"
    Case "E-STU-020": template = "削除理由を60文字以内で入力してください。"
    Case "E-STU-101": template = "この学籍番号は使用済みです。入力を確認してください。直前の送信結果が不明な場合は検索で登録状況を確認してください。"
    Case "E-STU-102": template = "クラスの定員を超えるため保存できません。別のクラスを選択してください。"
    Case "E-STU-103": template = "対象の学生が見つからないか、既に削除されています。"
    Case "E-STU-104": template = "登録済みの学籍番号は変更できません。"
    Case "E-STU-105": template = "他の操作で更新されています。入力内容を控え、最新情報を再読み込みしてください。"
    Case "E-STU-106": template = "卒業・退学からの在籍区分変更には管理者権限と変更理由が必要です。"
    Case "E-STU-107": template = "確認・変更理由を60文字以内で入力してください。"
    Case "E-SRC-001": template = "未所属のみを検索する場合、年度・学年・クラスは指定できません。"
    Case "E-SRC-002": template = "検索条件または表示指定が正しくありません。"
    Case "E-MST-001": template = "マスタの初期設定が不足しています。管理者に連絡してください。"
    Case "E-MST-002": template = "このコードまたはクラスコードは既に登録されています。"
    Case "E-MST-003": template = "参照中または保護対象のため、このマスタ変更はできません。"
    Case "E-MST-004": template = "定員または利用期間が現在の所属状況と整合しません。"
    Case "E-COM-001": template = "ログインの有効期限が切れました。再度ログインしてください。"
    Case "E-COM-002": template = "この操作を行う権限がありません。"
    Case "E-COM-003": template = "画面情報が無効です。画面を開き直してください。"
    Case "E-COM-004": template = "処理を完了できませんでした。受付番号：{correlationId}"
    Case "E-STU-108": template = "最終所属クラスの利用期間が学生の在籍期間と重なっていません。クラスまたは在籍日付を確認してください。"
    Case "E-DATE-001": template = "生年月日の元号・年・月・日を確認してください。"
    Case "E-DATE-002": template = "{field}は{minDate}から{maxDate}までの日付で入力してください。"
    Case "E-DATE-003": template = "{field}は西暦4桁の{minYear}年から{maxYear}年で指定してください。"
    Case Else: template = "入力内容を確認してください。"
    End Select
    For i = 1 To UBound(pieces)
        p = Split(pieces(i), "=", 2)
        If UBound(p) = 1 Then template = Replace(template, "{" & p(0) & "}", p(1))
    Next
    If name <> "" Then template = Replace(template, "{" & name & "}", data)
    template = Replace(template, "{field}", "入力項目")
    template = Replace(template, "{max}", "規定の")
    template = Replace(template, "{fromField}", "開始日")
    template = Replace(template, "{toField}", "終了日")
    template = Replace(template, "{correlationId}", GuidText())
    MessageText = id & ": " & template
End Function
Public Function ErrorKind(ByVal message As String) As String
    Select Case Split(message, "|")(0)
    Case "E-COM-001", "E-COM-002": ErrorKind = "Forbidden"
    Case "E-STU-103": ErrorKind = "NotFound"
    Case "E-STU-105": ErrorKind = "Conflict"
    Case "E-COM-004": ErrorKind = "SystemError"
    Case Else: ErrorKind = "ValidationFailed"
    End Select
End Function
