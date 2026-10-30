Option Compare Binary
Option Explicit
Public Function MessageText(ByVal id As String, Optional ByVal field As String = "") As String
    Dim s As String
    Select Case id
    Case "MSG-001": s = "ログインできません。入力内容を確認し、時間をおいて再度お試しください。"
    Case "MSG-002": s = "認証の有効期限が切れました。未保存の入力は保存されません。再ログインしてください。"
    Case "MSG-003": s = "この操作を実行する権限がありません。"
    Case "MSG-004": s = field & "を入力してください。"
    Case "MSG-005": s = field & "の形式または上限を確認してください。"
    Case "MSG-006": s = "この社員番号は登録されています。別の番号を指定してください。"
    Case "MSG-007": s = "開始年月・終了年月の前後関係を確認してください。未来の経歴は登録できません。"
    Case "MSG-008": s = "別の操作で更新されています。入力を確認してから再読込みしてください。"
    Case "MSG-009": s = "該当する社員はいません。"
    Case "MSG-010": s = "200件を超えています。条件を絞り込んでください。"
    Case "MSG-011": s = "社員を1人選択してください。"
    Case "MSG-012": s = "経歴を1件以上登録してから出力してください。"
    Case "MSG-013": s = "経歴書を作成できませんでした。時間をおいて再実行してください。"
    Case "MSG-014": s = "保存しました。"
    Case "MSG-015": s = "入力内容を破棄しますか。"
    Case "MSG-016": s = "選択値が利用できません。候補を再確認してください。"
    Case "MSG-017": s = "保存できませんでした。入力を保持しています。再実行してください。"
    Case "MSG-018": s = "社員は200人、経歴は社員1人につき20件までです。"
    Case "MSG-019": s = "対象の社員が見つかりません。検索し直してください。"
    Case "MSG-020": s = "保存データに不整合があります。管理者へ連絡してください。"
    Case "MSG-021": s = "変更はありません。"
    Case "MSG-022": s = "この分類とコードは登録されています。"
    Case "MSG-023": s = "固定コードの追加・変更・停止はできません。"
    Case "MSG-024": s = "コードは分類ごとに99件までです。"
    Case "MSG-025": s = "操作対象の経歴を確認できません。再読込みしてください。"
    Case "MSG-026": s = "同じ内容の経歴が重複しています。経歴" & field & "を確認してください。"
    Case "MSG-027": s = "ほかの処理が実行中です。入力を保持しています。時間をおいて再実行してください。"
    Case "MSG-028": s = "データを再取得してから、もう一度作成してください。"
    Case "MSG-029": s = "処理中です。完了までお待ちください。"
    Case "MSG-030": s = "処理を取り消しました。"
    Case "MSG-031": s = "この経歴を未保存一覧から除去しますか。"
    Case "MSG-032": s = "編集中の経歴を一覧へ反映しますか。"
    Case "MSG-033": s = "編集中の経歴を破棄しますか。"
    Case "MSG-034": s = "保存結果を確認できません。再読込みして反映状態を確認してください。"
    Case "MSG-037": s = "経歴書の内容を確認できませんでした。管理者へ連絡してください。"
    Case "MSG-038": s = "このコードを停止しますか。登録済みデータは保持され、新しい選択ができなくなります。"
    Case "MSG-039": s = "更新版が上限に達しています。管理者へ連絡してください。"
    Case "MSG-040": s = "データを読み込めませんでした。時間をおいて再実行してください。"
    Case Else: s = id
    End Select
    MessageText = s
End Function
Public Sub ShowResult(ByVal f As Access.Form, ByVal result As clsResult)
    If result.MessageId <> "" Then
        If f.Name = "frmEmployeeSearch" Then
            f.Controls("lblSelection").Caption = MessageText(result.MessageId, result.FieldId)
        Else
            f.Controls("lblMessage").Caption = MessageText(result.MessageId, result.FieldId)
        End If
    End If
    If result.Kind = "CommitUnknown" Then
        If f.Name = "frmEmployeeEditor" Then
            f!tabEmployee.SetFocus
            gEditor.Outcome = "CommitUnknown": f!cmdSave.Enabled = False
            f!cmdAddCareer.Enabled = False: f!cmdApplyCareer.Enabled = False: f!cmdRemoveCareer.Enabled = False
        End If
        If f.Name = "frmCodeMaster" Then f!cboCategory.SetFocus: f!cmdSave.Enabled = False: f.Tag = "CommitUnknown"
    End If
    If result.Kind = "AuthExpired" Then LogoutNow
    If result.Kind = "Validation" Then FocusResult f, result
End Sub
Private Sub FocusResult(ByVal f As Access.Form, ByVal result As clsResult)
    Dim name As String, field As String
    field = result.FieldId
    If f.Name = "frmEmployeeEditor" Then
        If Not IsEmpty(result.CareerOrdinal) And Not IsNull(result.CareerOrdinal) Then
            If CLng(result.CareerOrdinal) >= 1 And CLng(result.CareerOrdinal) <= gEditor.Careers.Count Then
                UiForcePage f, 1
                gUiLoading = True: f!lstCareers = CLng(result.CareerOrdinal): gUiLoading = False
                UiFocusCareer f, CLng(result.CareerOrdinal)
            End If
        End If
    End If
    Select Case field
    Case "ログインID": name = "txtLoginId"
    Case "パスワード", "確認用パスワード": name = "txtPassword"
    Case "社員番号": name = "txtEmployeeNo"
    Case "氏名": name = "txtEmployeeName"
    Case "カナ", "氏名カナ": name = "txtEmployeeKana"
    Case "氏名・カナ": name = "txtName"
    Case "入社日": name = "txtJoinDate"
    Case "職務要約": name = "txtSummary"
    Case "スキル": name = "txtSkills"
    Case "資格": name = "txtQualifications"
    Case "自己PR": name = "txtSelfPr"
    Case "開始年月": name = "txtStartMonth"
    Case "終了年月": name = "txtEndMonth"
    Case "会社名": name = "txtCompany"
    Case "案件名": name = "txtProject"
    Case "業務概要": name = "txtDescription"
    Case "担当業務": name = "txtDuties"
    Case "実績": name = "txtAchievements"
    Case "技術環境": name = "txtTechnologies"
    Case "工程": name = "txtPhases"
    Case "部署", "cboDepartment": name = "cboDepartment"
    Case "在籍区分", "cboStatus": name = "cboStatus"
    Case "分類", "cboCategory": name = "cboCategory"
    Case "役割", "cboRole": name = "cboRole"
    Case "チーム人数": name = "txtTeamSize"
    Case "コード": name = "txtCode"
    Case "名称": name = "txtCodeName"
    Case "表示順", "並び順": name = "txtSortOrder"
    End Select
    If name = "" Then Exit Sub
    If f.Name = "frmEmployeeEditor" Then
        If InStr(1, "|txtStartMonth|txtEndMonth|txtCompany|txtProject|txtDescription|txtDuties|txtAchievements|txtTechnologies|txtPhases|cboRole|txtTeamSize|", "|" & name & "|", vbBinaryCompare) > 0 Then UiForcePage f, 1 Else UiForcePage f, 0
    End If
    f.Controls(name).SetFocus
End Sub
