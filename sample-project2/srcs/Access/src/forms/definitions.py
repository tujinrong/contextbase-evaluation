"""Canonical unbound Access forms. All coordinates are twips (96 DPI x 15).
Form code delegates to services; controls never bind to an ACE field.
"""
LABEL, TEXT, BUTTON, CHECK, LIST, COMBO, TAB = 100,109,104,106,110,111,123
def control(name, label, kind, x, y, w, h=480, **kw):
    if kw.get('page') == 1 and x == 7800:
        kw.setdefault('label_x',6250); kw.setdefault('label_w',1400)
    return dict(name=name,label=label,kind=kind,x=x,y=y,w=w,h=h,**kw)
FORMS = {}
FORMS['frmLogin'] = dict(caption='社員経歴管理 — ログイン',width=15000,height=9000,controls=[
 control('txtLoginId','ログインID',TEXT,6000,2400,4800),control('txtPassword','パスワード',TEXT,6000,3300,4800,password=True),
 control('lblMessage','',LABEL,2400,4200,10500,1000),control('cmdLogin','ログイン',BUTTON,6000,5700,2300,540),control('cmdExit','終了',BUTTON,8700,5700,1800,540)])
FORMS['frmMenu'] = dict(caption='社員経歴管理 — メニュー',width=15000,height=9000,controls=[
 control('lblActor','',LABEL,2400,1700,10500),control('cmdEmployeeSearch','社員検索',BUTTON,4500,3000,6000,540),
 control('cmdCodeMaster','汎用コードマスタ',BUTTON,4500,4000,6000,540),control('cmdLogout','ログアウト',BUTTON,4500,5000,6000,540),
 control('lblMessage','',LABEL,1800,6300,11500,1000)])
FORMS['frmEmployeeSearch'] = dict(caption='社員経歴管理 — 社員検索',width=20000,height=10400,controls=[
 control('txtEmployeeNo','社員番号',TEXT,1800,900,1800,label_x=600,label_w=1050),control('txtName','氏名・カナ',TEXT,5700,900,4800,label_x=4050,label_w=1500),
 control('cboDepartment','部署',COMBO,1800,1800,3600,label_x=600,label_w=1050),control('cboStatus','在籍区分',COMBO,7200,1800,3300,label_x=5850,label_w=1200),
 control('cmdSearch','検索',BUTTON,12000,900,1800,540),control('cmdClear','クリア',BUTTON,14300,900,1800,540),
 control('lblCount','未検索',LABEL,600,2700,4500),
 control('lstEmployees','社員一覧',LIST,600,3660,18100,4300,columns=7,widths='0;1500;3900;3900;3600;2400;2400',headers=['','社員番号','氏名','氏名カナ','部署','在籍','入社日'],header_y=3230,header_h=330),
 control('lblSelection','未検索',LABEL,600,8100,18000,650),control('cmdNew','新規登録',BUTTON,600,9200,2200,540),
 control('cmdEdit','編集',BUTTON,3300,9200,1800,540),control('cmdExport','経歴書Excel',BUTTON,5700,9200,2800,540),control('cmdMenu','メニュー',BUTTON,15800,9200,2700,540)])
FORMS['frmEmployeeEditor'] = dict(caption='社員経歴管理 — 社員登録',width=20000,height=10900,controls=[
 control('tabEmployee','',TAB,300,600,19100,8800,pages=['基本情報・職務','経歴']),
 control('txtEmployeeNo','社員番号',TEXT,2400,1400,1800,page=0),control('txtEmployeeName','氏名',TEXT,2400,2250,6900,page=0),
 control('txtEmployeeKana','氏名カナ',TEXT,2400,3100,6900,page=0),control('cboDepartment','部署',COMBO,2400,3950,4800,page=0),
 control('cboStatus','在籍区分',COMBO,11300,3950,4200,page=0),control('txtJoinDate','入社日',TEXT,2400,4800,3300,page=0),
 control('txtSummary','職務要約',TEXT,2400,5700,6900,1100,page=0,multiline=True),control('txtSkills','得意技術・スキル',TEXT,12000,5700,6500,1100,page=0,multiline=True),
 control('txtQualifications','資格',TEXT,2400,7300,6900,1100,page=0,multiline=True),control('txtSelfPr','自己PR',TEXT,12000,7300,6500,1100,page=0,multiline=True),
 control('lstCareers','経歴一覧',LIST,600,1500,5400,5900,page=1,columns=4,widths='0;1350;1350;2300',headers=['','開始年月','終了年月','案件名'],header_y=1110,header_h=330),
 control('txtStartMonth','開始年月',TEXT,7800,1500,2100,page=1),control('txtEndMonth','終了年月',TEXT,13700,1500,2100,page=1),
 control('txtCompany','会社名',TEXT,7800,2200,10500,page=1),control('txtProject','案件名',TEXT,7800,2900,10500,page=1),
 control('txtDescription','業務概要',TEXT,7800,3600,10500,850,page=1,multiline=True),control('txtDuties','担当業務',TEXT,7800,4700,10500,850,page=1,multiline=True),
 control('txtAchievements','成果・工夫',TEXT,7800,5800,10500,850,page=1,multiline=True),control('txtTechnologies','使用技術',TEXT,7800,6900,10500,650,page=1,multiline=True),
 control('txtPhases','担当工程',TEXT,7800,7800,5700,650,page=1,multiline=True),control('cboRole','役割',COMBO,15100,7800,3200,page=1,label_x=13800,label_w=1150),
 control('txtTeamSize','人数',TEXT,15100,8500,1500,page=1),control('cmdAddCareer','経歴追加',BUTTON,600,7800,2200,540,page=1),
 control('cmdApplyCareer','明細へ反映',BUTTON,3100,7800,2600,540,page=1),control('cmdRemoveCareer','経歴除去',BUTTON,600,8500,2400,540,page=1),
 control('lblMessage','',LABEL,600,9600,13500,850),control('cmdSave','保存',BUTTON,14500,9900,1800,540),control('cmdCancel','取消・検索へ',BUTTON,16700,9900,2700,540)])
FORMS['frmCodeMaster'] = dict(caption='社員経歴管理 — 汎用コードマスタ',width=20000,height=10400,controls=[
 control('cboCategory','コード分類',COMBO,2400,900,5700),control('lstCodes','コード一覧',LIST,600,2500,9600,4800,columns=5,widths='1500;5400;1200;1200;0',headers=['コード','名称','順序','有効','']),
 control('txtCode','コード',TEXT,13200,2500,1500),control('txtCodeName','名称',TEXT,13200,3400,5700),control('txtSortOrder','並び順',TEXT,13200,4300,1500),
 control('chkEnabled','有効',CHECK,13200,5200,450),control('lblUsage','停止しても保存済みデータは保持します。',LABEL,600,7800,18000,600),
 control('cmdNew','新規',BUTTON,11400,6500,1800,540),control('cmdSave','保存',BUTTON,13800,6500,1800,540),control('cmdCancel','取消',BUTTON,16200,6500,1800,540),
 control('cmdMenu','メニュー',BUTTON,16200,9100,2400,540),control('lblMessage','',LABEL,600,8700,14000,1100)])

def module_code(form_name, definition):
    lines=['Option Compare Binary','Option Explicit',
      'Private Sub Form_Load()', '    UiLoad Me', 'End Sub',
      'Private Sub Form_Timer()', '    UiTimer Me', 'End Sub',
      'Private Sub Form_KeyDown(KeyCode As Integer, Shift As Integer)', '    UiKey Me, KeyCode', 'End Sub',
      'Private Sub Form_MouseDown(Button As Integer, Shift As Integer, X As Single, Y As Single)', '    UiMouse Me', 'End Sub',
      'Private Sub Form_Unload(Cancel As Integer)', '    UiUnload Me, Cancel', 'End Sub',
      'Private Sub Form_Close()', '    UiClosed Me', 'End Sub']
    for c in definition['controls']:
        n,k=c['name'],c['kind']
        if k == BUTTON:
            lines += [f'Private Sub {n}_Click()',f'    UiAction Me, "{n}"','End Sub']
        if k == TEXT:
            lines += [f'Private Sub {n}_Change()',f'    UiChanged Me, "{n}"','End Sub',
                      f'Private Sub {n}_BeforeUpdate(Cancel As Integer)',f'    UiBeforeUpdate Me, "{n}", Cancel','End Sub']
        if k in (COMBO,CHECK,LIST):
            lines += [f'Private Sub {n}_AfterUpdate()',f'    UiSelected Me, "{n}"','End Sub']
        if k == TAB:
            lines += [f'Private Sub {n}_Change()',f'    UiSelected Me, "{n}"','End Sub']
    return '\r\n'.join(lines)+'\r\n'
