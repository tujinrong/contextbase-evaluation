"""Native unbound UI authored from Access detail UI 1.0; twips per Section.
Header Tab Pages are empty; logical Page inputs belong physically to Detail.
No specification or test file is needed by the distributed production helper.
"""
LABEL,TEXT,BUTTON,CHECK,LIST,COMBO,TAB=100,109,104,106,110,111,123
HEADER,DETAIL,FOOTER=1,0,2
def c(name,label,kind,section,x,y,w,h=480,**kw):
    return dict(name=name,label=label,kind=kind,section=section,x=x,y=y,w=w,h=h,**kw)
def l(name,text,section,x,y,w,h=330,**kw):return c(name,text,LABEL,section,x,y,w,h,**kw)
FORMS={
'frmLogin':dict(caption='社員経歴管理 — ログイン',width=18900,sections=(2520,3240,0),controls=[
 l('lblScreenTitle','社員経歴管理システム — ログイン',HEADER,6345,1440,6200,bold=True),l('lblLoginHelp','ログインIDとパスワードを入力してください。',HEADER,6345,2040,6200),
 c('txtLoginId','ログインID※',TEXT,DETAIL,7725,90,3600),c('txtPassword','パスワード※',TEXT,DETAIL,7725,750,4800,password=True),
 l('lblMessage','',DETAIL,6345,1380,6200,660),c('cmdLogin','ログイン',BUTTON,DETAIL,7725,2370,1650,510,bold=True,default=True),c('cmdExit','終了',BUTTON,DETAIL,9555,2370,1650,510)]),
'frmMenu':dict(caption='社員経歴管理 — メニュー',width=18900,sections=(1500,7800,0),controls=[
 l('lblScreenTitle','社員経歴管理システム — メニュー',HEADER,360,360,18180,bold=True),l('lblActor','',HEADER,360,900,15000),
 c('cmdEmployeeSearch','社員検索',BUTTON,DETAIL,360,60,3150,510,bold=True),l('lblSearchHelp','社員を探し、基本情報・経歴を登録・編集します。',DETAIL,3810,150,9000),
 c('cmdCodeMaster','汎用コードマスタ',BUTTON,DETAIL,360,810,3150,510),l('lblCodeHelp','管理者：部署・案件役割を管理します。',DETAIL,3810,900,9000),
 c('cmdLogout','ログアウト',BUTTON,DETAIL,360,2100,2250,510),l('lblMessage','',DETAIL,360,2940,15000,660)]),
'frmEmployeeSearch':dict(caption='社員経歴管理 — 社員検索',width=18900,sections=(1080,7500,1140),controls=[
 l('lblScreenTitle','社員検索',HEADER,360,360,15000,bold=True),c('cmdMenu','メニュー',BUTTON,HEADER,17400,360,1140,510),
 c('txtEmployeeNo','社員番号条件',TEXT,DETAIL,360,450,1650),c('txtName','氏名条件',TEXT,DETAIL,2250,450,3900),c('cboDepartment','部署条件',COMBO,DETAIL,6390,450,2700),c('cboStatus','在籍区分条件',COMBO,DETAIL,9330,450,2700),
 c('cmdSearch','検索',BUTTON,DETAIL,12270,435,1050,510,bold=True),c('cmdClear','クリア',BUTTON,DETAIL,13560,435,1050,510),l('lblCount','未検索',DETAIL,360,1320,15000),
 c('lstEmployees','',LIST,DETAIL,360,2115,18180,4380,columns=7,widths='0;1500;3900;4950;2970;2250;2250',callback='UiEmployeesRows'),
 l('lblSelection','条件を指定して検索してください。',DETAIL,360,6720,18180),c('txtSelectedDetails','',TEXT,DETAIL,360,7110,18180,330,multiline=True,readonly=True,visible=False),
 c('cmdNew','新規登録',BUTTON,FOOTER,360,240,1650,510),c('cmdEdit','編集',BUTTON,FOOTER,2190,240,2250,510),c('cmdExport','経歴書Excel',BUTTON,FOOTER,4620,240,3150,510)]),
'frmEmployeeEditor':dict(caption='社員経歴管理 — 社員登録・編集',width=18900,sections=(2400,7920,1140),controls=[
 l('lblScreenTitle','社員登録・編集［新規］',HEADER,360,360,18180,bold=True),l('lblEmployeeIdentity','新規社員',HEADER,360,810,18180),
 c('tabEmployee','',TAB,HEADER,360,1365,18180,900,pages=[('pgBasic','基本情報・職務'),('pgCareer','経歴（0件）')]),
 c('txtEmployeeNo','社員番号※',TEXT,DETAIL,360,480,1650,page=0),c('txtEmployeeName','氏名※',TEXT,DETAIL,2310,480,3900,page=0),c('txtEmployeeKana','氏名カナ※',TEXT,DETAIL,6510,480,4950,page=0),
 c('cboDepartment','部署※',COMBO,DETAIL,360,1530,3300,page=0),c('cboStatus','在籍区分※',COMBO,DETAIL,3960,1530,3300,page=0),c('txtJoinDate','入社日※',TEXT,DETAIL,7560,1530,2250,page=0),
 c('txtSummary','職務要約',TEXT,DETAIL,360,2565,8940,1320,page=0,multiline=True),c('txtSkills','得意技術・スキル',TEXT,DETAIL,9600,2565,8940,1320,page=0,multiline=True),
 c('txtQualifications','資格',TEXT,DETAIL,360,4380,8940,1320,page=0,multiline=True),c('txtSelfPr','自己PR',TEXT,DETAIL,9600,4380,8940,1320,page=0,multiline=True),
 l('lblCareerListHeading','経歴一覧',DETAIL,360,210,6300,page=1,bold=True),c('lstCareers','',LIST,DETAIL,360,1020,6300,3990,page=1,columns=4,widths='0;1200;1200;3600',callback='UiCareersRows'),
 c('cmdAddCareer','経歴追加',BUTTON,DETAIL,360,5190,1650,510,page=1),c('cmdRemoveCareer','経歴除去',BUTTON,DETAIL,2190,5190,2250,510,page=1),
 l('lblCareerHint','一覧への反映・除去は未保存です。\n最後に「社員・経歴を保存」で確定します。',DETAIL,360,5940,6300,1320,page=1),
 l('lblCareerEditHeading','選択経歴の編集',DETAIL,6960,210,11580,page=1,bold=True),
 c('txtStartMonth','開始年月※',TEXT,DETAIL,6960,915,1875,page=1),c('txtEndMonth','終了年月（空＝継続中）',TEXT,DETAIL,9075,915,1875,page=1,label_w=2580),c('cboRole','役割※',COMBO,DETAIL,11880,915,2400,page=1),c('txtTeamSize','人数※',TEXT,DETAIL,14520,915,1050,page=1),
 c('txtCompany','会社名※',TEXT,DETAIL,6960,1890,5670,page=1),c('txtProject','案件名※',TEXT,DETAIL,12870,1890,5670,page=1),
 c('txtDescription','業務・案件概要※',TEXT,DETAIL,6960,2865,5670,990,page=1,multiline=True),c('txtDuties','担当業務※',TEXT,DETAIL,12870,2865,5670,990,page=1,multiline=True),
 c('txtAchievements','成果・工夫',TEXT,DETAIL,6960,4335,5670,990,page=1,multiline=True),c('txtTechnologies','使用技術',TEXT,DETAIL,12870,4335,5670,990,page=1,multiline=True),c('txtPhases','担当工程',TEXT,DETAIL,6960,5790,11580,720,page=1,multiline=True),
 c('cmdApplyCareer','経歴一覧へ反映',BUTTON,DETAIL,6960,6690,2250,510,page=1),l('lblDraftState','経歴未選択',DETAIL,9450,6780,9090,page=1),
 l('lblMessage','',DETAIL,360,7440,18180),l('lblSaveScope','社員と全経歴の変更をまとめて保存します。',FOOTER,360,300,10800,660),c('cmdSave','社員・経歴を保存',BUTTON,FOOTER,14550,240,1980,510,bold=True),c('cmdCancel','取消・検索へ戻る',BUTTON,FOOTER,16710,240,1830,510)]),
'frmCodeMaster':dict(caption='社員経歴管理 — 汎用コードマスタ',width=18900,sections=(2520,5520,960),controls=[
 l('lblScreenTitle','汎用コードマスタ',HEADER,360,360,15000,bold=True),l('lblCodeIdentity','部署／未選択',HEADER,360,1080,18180),c('cmdMenu','メニュー',BUTTON,HEADER,17400,360,1140,510),
 c('cboCategory','分類※',COMBO,HEADER,900,1740,2700),c('cmdNew','新規',BUTTON,HEADER,3840,1740,1200,510),
 l('lblCodeListHeading','コード一覧',DETAIL,360,120,7950,bold=True),c('lstCodes','',LIST,DETAIL,360,930,7950,4380,columns=5,widths='0;1125;4020;1275;1125',callback='UiCodesRows'),
 l('lblCodeEditHeading','選択コードの編集',DETAIL,8670,120,9870,bold=True),c('txtCode','コード※',TEXT,DETAIL,8670,780,1350),c('txtCodeName','名称※',TEXT,DETAIL,8670,1755,5100),c('txtSortOrder','並び順※',TEXT,DETAIL,8670,2730,1350),c('chkEnabled','有効※',CHECK,DETAIL,8670,3450,240,240),
 l('lblUsage','停止しても保存済み業務データを置換しません。',DETAIL,8670,3990,9870,660),c('cmdSave','このコードを保存',BUTTON,DETAIL,8670,4770,2250,510,bold=True),c('cmdCancel','編集を取消',BUTTON,DETAIL,11100,4770,1800,510),l('lblMessage','',FOOTER,360,180,18180,660)])}
HEADERS={
'frmEmployeeSearch':('lstEmployees',[('lblEmpNoHead','社員番号',1500),('lblEmpNameHead','氏名',3900),('lblEmpKanaHead','氏名カナ',4950),('lblEmpDeptHead','部署',2970),('lblEmpStatusHead','在籍',2250),('lblEmpJoinHead','入社日',2250)]),
'frmEmployeeEditor':('lstCareers',[('lblCareerStartHead','開始年月',1200),('lblCareerEndHead','終了年月',1200),('lblCareerProjectHead','案件名',3600)]),
'frmCodeMaster':('lstCodes',[('lblCodeHead','コード',1125),('lblCodeNameHead','名称',4020),('lblCodeSortHead','順序',1275),('lblCodeEnabledHead','有効',1125)])}
for form,d in FORMS.items():
    extra=[]
    for ctl in d['controls']:
        if ctl['kind'] not in (TEXT,COMBO,CHECK) or not ctl['label']:continue
        x,y,w,h=ctl['x'],ctl['y']-330,ctl.get('label_w',ctl['w']),330
        if form=='frmLogin':x,y,w=6345,ctl['y'],1200
        elif ctl['name']=='cboCategory':x,y,w,h=360,1740,480,480
        elif ctl['kind']==CHECK:x,y,w=ctl['x']+420,ctl['y'],8000
        extra.append(l('lbl_'+ctl['name'],ctl['label'],ctl['section'],x,y,w,h,**({'page':ctl['page']} if 'page' in ctl else {})))
    if form in HEADERS:
        name,columns=HEADERS[form];lst=next(x for x in d['controls'] if x['name']==name);offset=0
        for name,title,width in columns:
            extra.append(l(name,title,lst['section'],lst['x']+offset,lst['y']-420,width,420,bold=True,**({'page':lst['page']} if 'page' in lst else {})))
            offset+=width
    d['controls']+=extra
TAB_ORDER={
'frmLogin':['txtLoginId','txtPassword','cmdLogin','cmdExit'],
'frmMenu':['cmdEmployeeSearch','cmdCodeMaster','cmdLogout'],
'frmEmployeeSearch':['txtEmployeeNo','txtName','cboDepartment','cboStatus','cmdSearch','cmdClear','lstEmployees','txtSelectedDetails','cmdNew','cmdEdit','cmdExport','cmdMenu'],
'frmEmployeeEditor':{0:['tabEmployee','txtEmployeeNo','txtEmployeeName','txtEmployeeKana','cboDepartment','cboStatus','txtJoinDate','txtSummary','txtSkills','txtQualifications','txtSelfPr','cmdSave','cmdCancel'],1:['tabEmployee','lstCareers','cmdAddCareer','cmdRemoveCareer','txtStartMonth','txtEndMonth','cboRole','txtTeamSize','txtCompany','txtProject','txtDescription','txtDuties','txtAchievements','txtTechnologies','txtPhases','cmdApplyCareer','cmdSave','cmdCancel']},
'frmCodeMaster':['cboCategory','cmdNew','lstCodes','txtCode','txtCodeName','txtSortOrder','chkEnabled','cmdSave','cmdCancel','cmdMenu']}
assert sum(len(d['controls']) for d in FORMS.values())==127

def module_code(form_name,definition):
    lines=['Option Compare Binary','Option Explicit',
     'Private Sub Form_Load()','    UiLoad Me','End Sub',
     'Private Sub Form_Activate()','    UiActivate Me','End Sub',
     'Private Sub Form_Resize()','    UiResize Me','End Sub',
     'Private Sub Form_Timer()','    UiTimer Me','End Sub',
     'Private Sub Form_KeyDown(KeyCode As Integer, Shift As Integer)','    UiKey Me, KeyCode, Shift','End Sub',
     'Private Sub Form_MouseDown(Button As Integer, Shift As Integer, X As Single, Y As Single)','    UiMouse Me','End Sub',
     'Private Sub Form_Unload(Cancel As Integer)','    UiUnload Me, Cancel','End Sub',
     'Private Sub Form_Close()','    UiClosed Me','End Sub']
    for ctl in definition['controls']:
        n,k=ctl['name'],ctl['kind']
        if k==LABEL:continue
        if k!=TAB:lines += [f'Private Sub {n}_GotFocus()',f'    UiGotFocus Me, "{n}"','End Sub']
        if k==BUTTON:lines += [f'Private Sub {n}_Click()',f'    UiAction Me, "{n}"','End Sub']
        if k==TEXT:lines += [f'Private Sub {n}_Change()',f'    UiChanged Me, "{n}"','End Sub',f'Private Sub {n}_BeforeUpdate(Cancel As Integer)',f'    UiBeforeUpdate Me, "{n}", Cancel','End Sub']
        if k in (COMBO,CHECK,LIST):lines += [f'Private Sub {n}_AfterUpdate()',f'    UiSelected Me, "{n}"','End Sub']
        if k==COMBO:lines += [f'Private Sub {n}_Change()',f'    UiComboChanged Me, "{n}"','End Sub',f'Private Sub {n}_NotInList(NewData As String, Response As Integer)',f'    UiNotInList Me, "{n}", NewData, Response','End Sub']
        if k==TAB:lines += [f'Private Sub {n}_Change()',f'    UiSelected Me, "{n}"','End Sub']
    return '\r\n'.join(lines)+'\r\n'
