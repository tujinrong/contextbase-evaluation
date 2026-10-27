"""Vue-to-layout adapter for reviewed source states. Never executes application code."""
from __future__ import annotations
from pathlib import Path
import re, hashlib
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, CData, TemplateString
from .scan import vue

PREFIX='input/mcterp/frontend/src/views/affect/Hr/HrEmployee/'
CONTROLS={'a-input':'text','a-input-number':'number','ai-select':'select','a-select':'select','datejp':'date','monthjp':'month','a-radio-group':'radio','a-checkbox':'checkbox','a-textarea':'textarea','a-button':'button'}


def condition(expr:str,state:dict)->bool:
    """Small closed predicate vocabulary, deliberately not eval/JS execution."""
    e=' '.join(expr.split()).strip()
    if '||' in e:return any(condition(x,state) for x in e.split('||'))
    if '&&' in e:return all(condition(x,state) for x in e.split('&&'))
    if e.startswith('!'):return not condition(e[1:],state)
    if e in {'true','false'}:return e=='true'
    if e in {'props.isEditMode','isEditMode'}:return state['mode']!='view'
    if e in {'personflg','props.personflg'}:return False
    m=re.fullmatch(r'props\.editKbn\s*(===|!==|==|!=)\s*Enum編集区分\.(新規|変更|閲覧)',e)
    if m:
        same=state['mode']=={'新規':'new','変更':'edit','閲覧':'view'}[m[2]]
        return not same if '!' in m[1] else same
    if e=="String(formData.job_status_cd) === '3'":return state.get('retired',False)
    raise ValueError('Unresolved layout predicate: '+e)


class Adapter:
    def __init__(self,root:Path,filename:str,state:dict,labels:dict):
        self.path=PREFIX+filename;self.text=(root/self.path).read_text(encoding='utf-8-sig');self.state=state;self.labels=labels
        self.soup=BeautifulSoup(self.text.split('<script',1)[0],'html.parser')
        self.root=self.soup.find('template');self.counter=0;self.trace=[]
        self.rules={i['field']:i['required'].startswith('必須') for i in vue(self.text,self.path)['items']}
    def sequence(self,parent):
        out=[];last_if=None
        for n in parent.children:
            if not isinstance(n,Tag):continue
            if n.has_attr('v-if'):
                chosen=condition(n['v-if'],self.state);last_if=chosen
            elif n.has_attr('v-else-if'):
                if last_if is None:raise ValueError('Orphan else-if')
                chosen=not last_if and condition(n['v-else-if'],self.state);last_if=last_if or chosen
            elif n.has_attr('v-else'):
                if last_if is None:raise ValueError('Orphan else')
                chosen=not last_if;last_if=True
            else:chosen=True;last_if=None
            if chosen:
                converted=self.node(n)
                if converted:out.append(converted)
        return out
    def field(self,n,label='',display=False,default=''):
        binding=next((str(v) for k,v in n.attrs.items() if k.startswith('v-model')),'')
        key=binding.split('.')[-1] if binding else 'action-'+hashlib.sha256(n.get_text(' ',strip=True,types=(NavigableString,CData,TemplateString)).encode()).hexdigest()[:8]
        info=self.labels.get(key,{})
        label=label or (n.get_text(' ',strip=True,types=(NavigableString,CData,TemplateString)) if n.name in {'a-checkbox','a-button'} else info.get('label',''))
        typ=CONTROLS.get(n.name,'text')
        if typ=='radio':label=label or '選択'
        self.counter+=1
        if '{{' in label:label=info.get('label','設定に応じた項目')
        result={'kind':'field','id':key,'label':label,'aria_label':info.get('label',label),'type':typ,'mode':'display' if display else 'disabled' if self.state['mode']=='view' and typ=='checkbox' else 'input','required':self.rules.get(key,False)}
        if n.get(':maxlength',n.get('maxlength')):result['max_length']=n.get(':maxlength',n.get('maxlength'))
        result['placeholder']=n.get('placeholder',{'date':'YYYY-MM-DD','month':'YYYY-MM'}.get(typ,''))
        if typ=='textarea':result['rows']=int(n.get(':rows','2'))
        if key=='job_status_cd':result['value']='退職' if self.state.get('retired') else '在職'
        if key=='gender_cd' and display:result['value']='―'
        self.trace.append({'path':self.path,'line':n.sourceline,'binding':binding,'id':key,'label':label,'mode':result['mode']})
        return result
    def node(self,n):
        if n.has_attr('v-for'):
            return {'kind':'note','text':'追加設定に応じて項目・列が表示されます。固定数には含めません。'}
        tag=n.name
        if tag=='a-row':
            return {'kind':'row','id':'row-'+str(n.sourceline),'gap':int(n.get(':gutter',0)),'children':self.sequence(n)}
        if tag=='a-col':return {'kind':'col','span':int(n.get(':span',n.get('span','24'))),'children':self.sequence(n)}
        if tag=='aiview':
            label=n.get('label','');editing=condition(n.get(':is-edit-mode','true'),self.state)
            if not editing:
                inner=n.find(list(CONTROLS))
                if inner and inner.name=='a-button':return None
                key=re.search(r'formData\.(\w+)',n.get(':default-text',''))
                if inner:
                    item=self.field(inner,label,True);item['label']=label;return item
                if key:return {'kind':'field','id':key[1]+'-display','label':label,'type':'text','mode':'display'}
                return None
            children=self.sequence(n)
            if children:
                target=children[0]
                if target['kind']=='field' and target.get('type')!='button':target['label']=label
            return {'kind':'stack','children':children}
        if tag in CONTROLS:return self.field(n)
        if tag=='div' and 'group' in n.get('class',[]):
            title=n.find('span',class_=lambda x:x and 'title' in x)
            children=[]
            for child in self.sequence(n):
                if child.get('kind')!='text':children.append(child)
            return {'kind':'group','label':title.get_text(' ',strip=True,types=(NavigableString,CData,TemplateString)) if title else '関連項目','children':children}
        if tag=='span' and ('title' in n.get('class',[]) or 'icon' in n.get('class',[])):return None
        if tag=='a-space':return {'kind':'toolbar','children':self.sequence(n)}
        if tag=='vxe-table':return {'kind':'note','text':'設定された明細列と行を表示します。選択列の幅は50px、各明細列の幅と入力方式は追加設定に従います。'}
        if tag=='a-table':
            name=n.get(':columns','');m=re.search(r'const '+re.escape(name)+r'\s*=\s*\[([\s\S]*?)\n\]',self.text)
            if not m:raise ValueError('Table column definition is missing')
            labels=re.findall(r"title:\s*'([^']+)'",m[1]);return {'kind':'table','columns':[{'label':s,'width':200} for s in labels]}
        return {'kind':'stack','children':self.sequence(n)}
    def tree(self):return {'kind':'stack','children':self.sequence(self.root)}


def screens(root:Path,labels:dict):
    modal=(root/PREFIX/'modules/HrEmployeeModal.vue').read_text(encoding='utf-8-sig')
    width=int(re.search(r'width="(\d+)px"',modal)[1])
    listtext=(root/PREFIX/'HrEmployeeList.vue').read_text(encoding='utf-8-sig');lst=BeautifulSoup(listtext.split('<script',1)[0],'html.parser')
    columns=[{'label':n['title'],'width':int(n['width']),'fixed':n.get('fixed','')} for n in lst.find_all('vxe-column') if n.get('title') and n.get('width')]
    toolbar1=[]
    for key,label in [('deptCd','部署'),('emptypeCd','社員形態'),('worklocCd','作業場所')]:
        toolbar1.append({'kind':'col','span':6,'children':[{'kind':'field','id':key,'label':label,'type':'select'}]})
    toolbar1.append({'kind':'col','span':6,'children':[{'kind':'toolbar','children':[{'kind':'button','label':'検索','style':'primary'},{'kind':'button','label':'クリア'}]}]})
    toolbar2=[{'kind':'button','label':x,'style':'primary','disabled':x=='編集'} for x in ['新規','編集','CSV出力','アップロード']]
    toolbar2 += [{'kind':'field','id':'fullText','label':'','type':'text','placeholder':'全文検索'},{'kind':'field','id':'jobStatusCd','label':'','type':'select','value':'在職'},{'kind':'text','text':'0件　1ページ　25件／ページ'}]
    views=[{'id':'employee-list','caption':'社員一覧（行未選択）','title':'社員マスタ','width':1500,'tree':{'kind':'stack','children':[{'kind':'row','children':toolbar1},{'kind':'toolbar','children':toolbar2},{'kind':'table','columns':columns},{'kind':'note','text':'固定16列の後ろに、設定されたフリー項目列を追加します。左右にスクロールできます。'}]},'note':'一覧の幅1500pxは確認用の表示幅です。固定16列の個別幅・順序・左固定2列は原本指定です。検索条件と操作列は上段にまとめます。'}]
    traces=[]
    for mode,retired,tab,file,caption in [('edit',False,'基本','HrEmployeeForm.vue','変更・在職'),('new',False,'基本','HrEmployeeForm.vue','新規'),('view',False,'基本','HrEmployeeForm.vue','閲覧'),('edit',True,'基本','HrEmployeeForm.vue','変更・退職'),('edit',False,'その他','HrEmployeeForm-others.vue','その他'),('edit',False,'給与','edit-page-salary.vue','給与'),('edit',False,'追加設定タブ','HrEmployeeForm-skill.vue','追加設定の明細')]:
        a=Adapter(root,'modules/'+file,{'mode':mode,'retired':retired},labels);tree=a.tree();sid='employee-'+mode+('-retired' if retired else '')+'-'+str(len(views))
        buttons=[{'kind':'button','label':'閉じる'}] if mode=='view' else [{'kind':'button','label':'登録','style':'primary'},{'kind':'button','label':'キャンセル'}]
        delete={'kind':'button','label':'削除','style':'danger'} if mode=='edit' else None
        views.append({'id':sid,'caption':'社員情報：'+caption,'title':'社員情報','width':width,'modal':True,'tabs':['基本','給与','追加設定タブ','その他'],'active_tab':tab,'tree':tree,'buttons':buttons,'delete':delete,'note':('追加設定タブは定義がある場合だけ表示します。給与欄は現行の固定表示例で、社員別の給与取得・登録は確認できていません。' if tab=='給与' else '領域内を縦スクロールして下段の項目を確認します。氏名・カタカナは入力時に姓／名を分割し、閲覧時に連結表示します。' if tab=='基本' else '追加設定の名称、項目数、列数、候補値は実際の設定に依存します。')})
        traces+=a.trace
    return views,traces,columns
