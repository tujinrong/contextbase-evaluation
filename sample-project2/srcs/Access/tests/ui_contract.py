"""Independently authored UI expectations from Access specifications.

This file never imports forms/definitions.py or reads an ACCDB/export/observation.
The physical identifiers come from the five detailed item tables. Widths are
96-DPI CSS px*15 or explicit Twips from the detailed overview. Classic settings
come from DQA-UI01/UI生成条件. Run before measurement and freeze the JSON hash.
"""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[2]
SPEC=REPO/'sample-project2/spec/Access'
SOURCES=['規約/UI生成条件.md','詳細設計QA.md','共通/03_共通UI・入力設計.md',
 '共通/方式別/01_共通実装仕様.md',
 '詳細仕様書/01_ログイン画面.md','詳細仕様書/02_メニュー画面.md',
 '詳細仕様書/03_社員検索画面.md','詳細仕様書/04_社員登録画面.md','詳細仕様書/06_汎用コードマスタ画面.md']
# Deliberately independent physical inventory, not read from the generator.
SCREENS={
 'F01':{'form':'frmLogin','width':15000,'height':9000,'detail':SOURCES[4],
  'TextBox':'txtLoginId txtPassword','Label':'lblMessage','CommandButton':'cmdLogin cmdExit'},
 'F02':{'form':'frmMenu','width':15000,'height':9000,'detail':SOURCES[5],
  'Label':'lblActor lblMessage','CommandButton':'cmdEmployeeSearch cmdCodeMaster cmdLogout'},
 'F03':{'form':'frmEmployeeSearch','width':18900,'height':10400,'detail':SOURCES[6],
  'TextBox':'txtEmployeeNo txtName','ComboBox':'cboDepartment cboStatus',
  'Label':'lblCount lblSelection','ListBox':'lstEmployees',
  'CommandButton':'cmdSearch cmdClear cmdNew cmdEdit cmdExport cmdMenu'},
 'F04':{'form':'frmEmployeeEditor','width':18900,'height':10900,'detail':SOURCES[7],
  'TextBox':'txtEmployeeNo txtEmployeeName txtEmployeeKana txtJoinDate txtSummary txtSkills txtQualifications txtSelfPr txtStartMonth txtEndMonth txtCompany txtProject txtDescription txtDuties txtAchievements txtTechnologies txtPhases txtTeamSize',
  'ComboBox':'cboDepartment cboStatus cboRole','Label':'lblMessage','ListBox':'lstCareers',
  'TabControl':'tabEmployee','Page':'page0 page1',
  'CommandButton':'cmdAddCareer cmdApplyCareer cmdRemoveCareer cmdSave cmdCancel'},
 'F06':{'form':'frmCodeMaster','width':18000,'height':10400,'detail':SOURCES[8],
  'TextBox':'txtCode txtCodeName txtSortOrder','ComboBox':'cboCategory','CheckBox':'chkEnabled',
  'Label':'lblUsage lblMessage','ListBox':'lstCodes','CommandButton':'cmdNew cmdSave cmdCancel cmdMenu'}
}
WIDTHS={
 'F01':{'txtLoginId':3600,'txtPassword':4800},
 'F03':{'txtEmployeeNo':1650,'txtName':3300,'cboDepartment':2700,'cboStatus':2700},
 'F04':{'txtEmployeeNo':1650,'txtEmployeeName':3900,'txtEmployeeKana':4950,'txtJoinDate':2250,
  'cboDepartment':2700,'cboStatus':2700,'txtStartMonth':1875,'txtEndMonth':1875,
  'txtCompany':4800,'txtProject':4800,'cboRole':2400,'txtTeamSize':1050,'lstCareers':4050},
 'F06':{'cboCategory':2700,'txtCode':1350,'txtCodeName':5100,'txtSortOrder':1350,'lstCodes':7950}
}
MULTILINE_HEIGHTS={
 'txtSummary':1320,'txtSkills':1320,'txtQualifications':1320,'txtSelfPr':1320,
 'txtDescription':930,'txtDuties':930,'txtAchievements':930,'txtTechnologies':930,'txtPhases':720}
HEADERS={'F03':('lstEmployees',[1,2,3,4,5,6]),'F04':('lstCareers',[1,2,3]),'F06':('lstCodes',[0,1,2,3])}

def make_contract():
 sources=[]
 for name in SOURCES:
  path=SPEC/name; raw=path.read_bytes(); metadata=json.loads(re.search(r'<!-- spec-meta: (.*?) -->',raw.decode('utf-8-sig')).group(1))
  sources.append({'file':str(path.relative_to(REPO)).replace('\\','/'),'documentId':metadata['documentId'],'version':metadata['version'],'sha256':hashlib.sha256(raw).hexdigest()})
 components=[]; rules=[]
 def rule(kind,target,properties,detail,suffix=''):
  rules.append({'id':kind.upper()+'-'+target.replace('/','-')+suffix,'kind':kind,'target':target,'mandatory':True,
   'sourceFiles':[sources[0]['file'],str((SPEC/detail).relative_to(REPO)).replace('\\','/')],
   'properties':{key:({'op':'eq','value':value} if not isinstance(value,dict) else value) for key,value in properties.items()}})
 for sid,screen in SCREENS.items():
  components.append({'id':sid,'kind':'Form','textCapable':False})
  rule('dimensions',sid,{'widthTwips':screen['width'],'detailHeightTwips':screen['height'],'autoResize':True,'scrollBars':3,'fitToScreen':False},screen['detail'])
  viewport={'initialSectionTopTwips':0,'initialSectionLeftTwips':0}
  if sid=='F04': viewport.update(initialActiveTab=0,tabHeadingsTopInViewportTwips={'op':'min','value':0})
  rule('dimensions',sid,viewport,screen['detail'],suffix='-INITIAL-VIEWPORT')
  rule('appearance',sid,{'detailBackColor':15790320,'borderStyle':2},screen['detail'])
  rule('render',sid,{'textClipped':False,'unintendedOverlap':False,'allActionsReachable':True},screen['detail'])
  rule('interaction',sid,{'initialFocusVerified':True,'tabOrderVerified':True,'nativeOperationVerified':True},screen['detail'])
  controls=[]
  for kind in ('TextBox','ComboBox','CheckBox','Label','ListBox','CommandButton','TabControl','Page'):
   for name in screen.get(kind,'').split():
    controls.append((name,kind))
    if kind in ('TextBox','ComboBox','CheckBox'): controls.append(('label_'+name,'Label'))
  if sid in HEADERS:
   name,indexes=HEADERS[sid]
   controls += [('header_'+name+'_'+str(i),'Label') for i in indexes]
  for name,kind in controls:
   target=sid+'/'+name; text=kind not in ('CheckBox','Page')
   components.append({'id':target,'kind':kind,'textCapable':text})
   if text: rule('font',target,{'fontFamily':'Yu Gothic UI','fontSize':11,'fontUnit':'pt'},screen['detail'])
   appearance={}
   if kind not in ('Page','CheckBox'):
    appearance['foreColor']=0
    appearance['backColor']=16777215 if kind in ('TextBox','ComboBox','ListBox') else 15790320
    appearance['backThemeColorIndex']=-1; appearance['foreThemeColorIndex']=-1
   if kind in ('CommandButton','TabControl'):
    appearance.update(useTheme=False,shape=0,gradient=0,hoverColor=15066597,pressedColor=14013909,hoverForeColor=0,pressedForeColor=0,
     hoverThemeColorIndex=-1,pressedThemeColorIndex=-1,hoverForeThemeColorIndex=-1,pressedForeThemeColorIndex=-1)
   if kind=='CheckBox': appearance.update(borderColor=8421504,specialEffect=0)
   if kind=='Page': appearance['caption']='基本情報・職務' if name=='page0' else '経歴'
   rule('appearance',target,appearance,screen['detail'])
   dims={}
   if name in WIDTHS.get(sid,{}): dims['widthTwips']=WIDTHS[sid][name]
   if kind in ('TextBox','ComboBox'):
    dims['heightTwips']=MULTILINE_HEIGHTS.get(name,480)
   if kind=='CommandButton': dims['heightTwips']=540 if sid=='F02' else 510
   if kind=='ListBox': dims['heightTwips']=4650 if sid=='F04' else 4800
   if dims: rule('dimensions',target,dims,screen['detail'])
 contract={'schemaVersion':1,'projectId':'sample-project2','profileId':'Access',
  'contractId':'SP2-ACCESS-CLASSIC-UI','version':'1.1','artifact':{'file':'build/CareerManagement.accdb'},
  'sources':sources,'components':components,'rules':rules,
  'scopeNotes':['All five native form Details, both editor Pages, every owned control and attached/header Label.',
   'CheckBox has no font; its attached Label owns the caption. TabControl owns Page caption font.',
   'Windows/Access standard title bar, ribbon and MessageBox are external system chrome; record separately.',
   'Fixed Twips/pt with top-left anchors. Resizable Access host keeps native horizontal/vertical scrolling; no font shrinking.',
   'Visual/keyboard properties require current-final-artifact evidence, never a service Value assignment.']}
 (ROOT/'tests/ui-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'components':len(components),'rules':len(rules),'sha256':hashlib.sha256((ROOT/'tests/ui-contract.json').read_bytes()).hexdigest()}))

if __name__=='__main__': make_contract()
