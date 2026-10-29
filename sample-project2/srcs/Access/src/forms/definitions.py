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
 control('txtLoginId','ログインID',TEXT,5700,2400,3600,label_x=3600,label_w=1950),control('txtPassword','パスワード',TEXT,5700,3300,4800,password=True,label_x=3600,label_w=1950),
 control('lblMessage','',LABEL,3600,4200,6900,1000),control('cmdLogin','ログイン',BUTTON,5700,5700,2300,510),control('cmdExit','終了',BUTTON,8400,5700,1800,510)])
FORMS['frmMenu'] = dict(caption='社員経歴管理 — メニュー',width=15000,height=9000,controls=[
 control('lblActor','',LABEL,2400,1700,10500),control('cmdEmployeeSearch','社員検索',BUTTON,4500,3000,6000,540),
 control('cmdCodeMaster','汎用コードマスタ',BUTTON,4500,4000,6000,540),control('cmdLogout','ログアウト',BUTTON,4500,5000,6000,540),
 control('lblMessage','',LABEL,1800,6300,11500,1000)])
FORMS['frmEmployeeSearch'] = dict(caption='社員経歴管理 — 社員検索',width=18900,height=10400,controls=[
 control('txtEmployeeNo','社員番号',TEXT,1800,900,1650,label_x=600,label_w=1050),control('txtName','氏名・カナ',TEXT,5700,900,3300,label_x=4050,label_w=1500),
 control('cboDepartment','部署',COMBO,1800,1800,2700,label_x=600,label_w=1050),control('cboStatus','在籍区分',COMBO,7200,1800,2700,label_x=5850,label_w=1200),
 control('cmdSearch','検索',BUTTON,12000,900,1800,510),control('cmdClear','クリア',BUTTON,14300,900,1800,510),
 control('lblCount','未検索',LABEL,600,2700,4500),
 control('lstEmployees','社員一覧',LIST,600,3660,18100,4800,columns=7,widths='0;1500;3600;3600;3300;2250;2250',headers=['','社員番号','氏名','氏名カナ','部署','在籍','入社日'],header_y=3120,header_h=480),
 control('lblSelection','未検索',LABEL,600,8530,18000,480),control('cmdNew','新規登録',BUTTON,600,9450,2200,510),
 control('cmdEdit','編集',BUTTON,3300,9450,1800,510),control('cmdExport','経歴書Excel',BUTTON,5700,9450,2800,510),control('cmdMenu','メニュー',BUTTON,15800,9450,2700,510)])
FORMS['frmEmployeeEditor'] = dict(caption='社員経歴管理 — 社員登録',width=18900,height=10900,
 tab_order={1:['lstCareers','txtStartMonth','txtEndMonth','cboRole','txtTeamSize','txtCompany','txtProject',
  'txtDescription','txtDuties','txtAchievements','txtTechnologies','txtPhases','cmdAddCareer','cmdApplyCareer','cmdRemoveCareer']},controls=[
 control('tabEmployee','',TAB,300,600,18300,8800,pages=['基本情報・職務','経歴']),
 control('txtEmployeeNo','社員番号',TEXT,2400,1400,1650,page=0),control('txtEmployeeName','氏名',TEXT,2400,2250,3900,page=0),
 control('txtEmployeeKana','氏名カナ',TEXT,2400,3100,4950,page=0),control('cboDepartment','部署',COMBO,2400,3950,2700,page=0),
 control('cboStatus','在籍区分',COMBO,11300,3950,2700,page=0),control('txtJoinDate','入社日',TEXT,2400,4800,2250,page=0),
 control('txtSummary','職務要約',TEXT,2400,5700,6900,1320,page=0,multiline=True),control('txtSkills','得意技術・スキル',TEXT,12000,5700,6000,1320,page=0,multiline=True),
 control('txtQualifications','資格',TEXT,2400,7500,6900,1320,page=0,multiline=True),control('txtSelfPr','自己PR',TEXT,12000,7500,6000,1320,page=0,multiline=True),
 control('lstCareers','経歴一覧',LIST,600,1650,4050,4650,page=1,columns=4,widths='0;1200;1200;1500',headers=['','開始年月','終了年月','案件名'],header_y=1110,header_h=480),
 control('txtStartMonth','開始年月',TEXT,5250,1650,1875,page=1,label_x=5250,label_y=1170,label_w=1875),control('txtEndMonth','終了年月',TEXT,8250,1650,1875,page=1,label_x=8250,label_y=1170,label_w=1875),
 control('txtCompany','会社名',TEXT,5250,3000,4800,page=1,label_x=5250,label_y=2520,label_w=4800),control('txtProject','案件名',TEXT,12000,3000,4800,page=1,label_x=12000,label_y=2520,label_w=4800),
 control('txtDescription','業務・案件概要',TEXT,5250,4200,6000,930,page=1,multiline=True,label_x=5250,label_y=3720,label_w=6000),control('txtDuties','担当業務',TEXT,12000,4200,6000,930,page=1,multiline=True,label_x=12000,label_y=3720,label_w=6000),
 control('txtAchievements','成果・工夫',TEXT,5250,5700,6000,930,page=1,multiline=True,label_x=5250,label_y=5220,label_w=6000),control('txtTechnologies','使用技術',TEXT,12000,5700,6000,930,page=1,multiline=True,label_x=12000,label_y=5220,label_w=6000),
 control('txtPhases','担当工程',TEXT,5250,7200,12750,720,page=1,multiline=True,label_x=5250,label_y=6720,label_w=12750),control('cboRole','役割',COMBO,11550,1650,2400,page=1,label_x=11550,label_y=1170,label_w=2400),
 control('txtTeamSize','人数',TEXT,15600,1650,1050,page=1,label_x=15600,label_y=1170,label_w=1500),control('cmdAddCareer','経歴追加',BUTTON,600,6900,1800,510,page=1),
 control('cmdApplyCareer','明細へ反映',BUTTON,600,7650,2400,510,page=1),control('cmdRemoveCareer','経歴除去',BUTTON,600,8400,1800,510,page=1),
 control('lblMessage','',LABEL,600,9600,12000,850),control('cmdSave','保存',BUTTON,13300,9900,1800,510),control('cmdCancel','取消・検索へ',BUTTON,15700,9900,2700,510)])
FORMS['frmCodeMaster'] = dict(caption='社員経歴管理 — 汎用コードマスタ',width=18000,height=10400,controls=[
 control('cboCategory','コード分類',COMBO,2400,900,2700),control('lstCodes','コード一覧',LIST,600,2500,7950,4800,columns=5,widths='1350;4050;1200;1200;0',headers=['コード','名称','順序','有効','']),
 control('txtCode','コード',TEXT,12300,2500,1350),control('txtCodeName','名称',TEXT,12300,3400,5100),control('txtSortOrder','並び順',TEXT,12300,4300,1350),
 control('chkEnabled','有効',CHECK,12300,5200,450),control('lblUsage','停止しても保存済みデータは保持します。',LABEL,600,7800,16800,600),
 control('cmdNew','新規',BUTTON,10500,6500,1800,510),control('cmdSave','保存',BUTTON,12900,6500,1800,510),control('cmdCancel','取消',BUTTON,15300,6500,1800,510),
 control('cmdMenu','メニュー',BUTTON,15000,9100,2400,510),control('lblMessage','',LABEL,600,8700,14000,1100)])

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
