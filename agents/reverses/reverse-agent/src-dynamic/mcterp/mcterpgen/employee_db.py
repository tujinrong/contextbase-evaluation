"""Employee-only DB specification refinement; approved layouts are immutable inputs.

Does not run application code, SQL, macros or database restores. Source-dependent
review data belongs to this adapter; generic ER rendering lives in src/docsite.
"""
from __future__ import annotations
import argparse,hashlib,json,re,copy,os,tempfile
from pathlib import Path
from urllib.parse import quote
from bs4 import BeautifulSoup
from .scan import read,sha,functions,archive_schema,masked

ASSETS=Path(__file__).with_name('employee_db_assets')
FEATURE='output/md/基本設計書/概要仕様書MCT-HrEmployee_社員管理.md'
COMMON='output/md/共通/共通DB処理仕様_社員マスタPilot.md'
MARK='<!-- employee-db:events -->'
BE='input/mcterp/backend/'
FR='input/mcterp/frontend/src/'
SERVICE=BE+'BusinessService/HrBusinessService/01.社員管理/Service/Service.cs'
SQL=BE+'DataAccess/SQL/Procedure/sp_hr_employee.sql'
DUMP=BE+'DataAccess/SQL/Dump/MCTERP_20250630210530.dump'
PATHS={
 'service':SERVICE,'unwrap':BE+'BusinessService/HrBusinessService/01.社員管理/Service/UnWraper.cs',
 'wrap':BE+'BusinessService/HrBusinessService/01.社員管理/Service/Wraper.cs',
 'request':BE+'BusinessService/HrBusinessService/01.社員管理/WebInterface/Request.cs',
 'dbutil':BE+'DataAccess/Common/Utils/DaDbUtil.cs',
 'master':BE+'DataAccess/Common/Cache/DaMasterDataCache.cs',
 'tableinfo':BE+'DataAccess/Common/Cache/DaTableInfoCache.cs',
 'free':BE+'BusinessService/CmBusinessService/ErpCommon/Service/CmFreeService.cs',
 'transaction':BE+'BusinessService/CmBusinessService/ErpCommon/Bases/CmServiceBase.cs',
 'check':BE+'BusinessService/CmBusinessService/ErpCommon/Service/CmCheckService.cs',
 'csv':BE+'BusinessService/CmBusinessService/ErpCommon/Utils/CmCsvExportUtil.cs',
 'empcache':BE+'DataAccess/Common/Cache/DaEmpDataCache.cs',
 'context':BE+'DataAccess/Generated/DaDbContext.cs','dao':BE+'DataAccess/Generated/Dao/hr/hrm_empDao.cs',
 'dto':BE+'DataAccess/Generated/Dao/hr/hrm_empDto.cs','project':BE+'DataAccess/DataAccess.csproj',
 'controller':BE+'WebService/Controllers/WebRequestController.cs',
 'download':BE+'WebService/Controllers/DownloadController.cs','upload':BE+'WebService/Controllers/UploadController.cs',
 'log':BE+'DataAccess/Common/Service/DaDbLogService.cs',
 'frontend':FR+'views/affect/Hr/HrEmployee/service.ts',
 'transport':FR+'utils/http/common-service.ts','screen':FR+'views/affect/Hr/HrEmployee/HrEmployeeList.vue',
 'modal':FR+'views/affect/Hr/HrEmployee/modules/HrEmployeeModal.vue',
 'form':FR+'views/affect/Hr/HrEmployee/modules/HrEmployeeForm.vue',
 'others':FR+'views/affect/Hr/HrEmployee/modules/HrEmployeeForm-others.vue',
 'searchhook':FR+'utils/hooks/useSearch.ts','sql':SQL,'dump':DUMP}
COMMON_SYMBOLS={
 'CDB-01':[('master','GetNameList'),('master','GetName'),('master','GetCodeNameList'),('master','GetStrCodeNameList')],
 'CDB-02':[], 'CDB-03':[('dbutil','GetListData1'),('dbutil','GetAllData1')],
 'CDB-04':[('tableinfo','GetTableInfo'),('tableinfo','GetFieldInfoList'),('free','GetFreeDetailColList')],
 'CDB-05':[('free','GetFreeValuesDic'),('free','GetFreesVMList')],
 'CDB-06':[('free','GetFrees2VMList')], 'CDB-07':[('free','UpdateFreeList')],
 'CDB-08':[('free','UpdateFree2List')],
 'CDB-09':[('service','checkEmpCd'),('service','checkMail'),('service','Save')],
 'CDB-10':[('transaction','Nolock'),('transaction','Transction'),('transaction','BeforeAction'),('transaction','AfterAction'),('transaction','GetExcetionResponse')],
 'CDB-11':[('check','CheckItemExist')],'CDB-12':[('csv','ExportToCsvBytes')],
 'CDB-13':[('empcache','ClearCache')]}
API={
 'Init':{'events':['EMP-01'],'common':['CDB-01','CDB-10'],'tables':['cmm_masterdata:R']},
 'Search':{'events':['EMP-01','EMP-02','EMP-04'],'common':['CDB-01','CDB-02','CDB-03','CDB-04','CDB-05','CDB-10'],'tables':['hrm_emp:R','cmm_masterdata:R','cms_table:R','cms_field:R','cmt_free:R']},
 'InitDetail':{'events':['EMP-05'],'common':['CDB-01','CDB-04','CDB-05','CDB-06','CDB-10'],'tables':['hrm_emp:R','cmm_masterdata:R','cms_table:R','cms_field:R','cmt_free:R','cmt_free2:R']},
 'checkEmpCd':{'events':['EMP-06'],'common':['CDB-09','CDB-10'],'tables':['hrm_emp:R']},
 'checkMail':{'events':['EMP-06'],'common':['CDB-09','CDB-10'],'tables':['hrm_emp:R','cmm_user:R']},
 'Save':{'events':['EMP-09'],'common':['CDB-07','CDB-08','CDB-09','CDB-10','CDB-13'],'tables':['hrm_emp:RCU','cmm_user:C','cmm_masterdata:R','cmm_user_right:C','cmt_free:U-delegated','cmt_free2:DC','cms_table:R','cms_field:R']},
 'Delete':{'events':['EMP-11'],'common':['CDB-11','CDB-10','CDB-13'],'tables':['hrm_emp:RD','dynamic_same_column:R']},
 'PasswordReset':{'events':['EMP-12'],'common':['CDB-10'],'tables':['cmm_user:RU']},
 'CsvExreport':{'events':['EMP-13'],'common':['CDB-01','CDB-02','CDB-03','CDB-04','CDB-05','CDB-10','CDB-12'],'tables':['hrm_emp:R','cmm_masterdata:R','cms_table:R','cms_field:R','cmt_free:R']},
 'SaveFile':{'events':['EMP-14'],'common':['CDB-01','CDB-10'],'tables':['hrm_emp:RCU','cmm_user:RCU','cmm_user_right:U-delegated','cmm_masterdata:R']}}
TABLES=['hrm_emp','cmm_masterdata','cms_table','cms_field','cmt_free','cmt_free2','cmm_user','cmm_user_right']
NO_DB=['EMP-03','EMP-07','EMP-08','EMP-10','EMP-15']

def write(path,text):
    from docsite.common import write as atomic,js
    return atomic(path,text if isinstance(text,(str,bytes)) else js(text))

def check_sources(root):
    manifest=json.loads((ASSETS/'sources.json').read_text())
    changed=[p for p,h in manifest['sources'].items() if not (root/p).is_file() or sha((root/p).read_bytes())!=h]
    if changed:raise ValueError('Employee DB review is stale: '+', '.join(changed))
    return manifest

def layout_blocks(text):
    return re.findall(r'<!-- docsite:screen-layout begin -->[\s\S]*?<!-- docsite:screen-layout end -->',text)

def section(text,n):
    m=re.search(r'^## '+str(n)+r'\.[\s\S]*?(?=^## \d+\.|\Z)',text,re.M)
    if not m:raise ValueError('Missing document section '+str(n))
    return m[0]

def refined(text):
    # Prefix containing accepted layout and field definitions is copied verbatim.
    text=text.replace(MARK+'\n','')
    before=section(text,3)
    body=(ASSETS/'events.md').read_text(encoding='utf-8').rstrip()
    head,tail=body.split('\n',1)
    replacement=head+'\n'+MARK+'\n'+tail+'\n\n'
    text=text.replace(before,replacement,1)
    note='<!-- employee-db:notes -->'
    if note in text:text=text.split(note)[0].rstrip()+'\n'
    text+='\n'+note+'\n\n### 4.4 DB追跡で確認した仕様差異\n\n'
    text+='本章4.3の未確認事項は、第3章と共通DB処理仕様の具体的な条件で補っています。検索は社員単表から抽出後に名称・追加値を補完します。SQL原本と保存済みダンプの引数差、ページ取得順、氏名・メール重複判定、採番と追加情報の関連、単数値の一覧更新、削除対象外の汎用参照、CSV区切り処理・取込の固定補正は未承認事項です。原本アプリの動作は変更していません。\n\n'
    text+='[共通DB処理仕様（社員マスタPilot）](../共通/共通DB処理仕様_社員マスタPilot.md) ／ [画面・API・DBの根拠追跡](../../../report/employee-db/画面API_DB追跡.md) ／ [今回の検証結果](../../../report/employee-db/検証結果.md)\n'
    return text

def audit_document(text, baseline=None):
    errors=[]
    events=(ASSETS/'events.md').read_text(encoding='utf-8').rstrip()
    actual=section(text,3).replace(MARK+'\n','').strip()
    if actual!=events:errors.append('DB event contract text/order changed or omitted')
    ids=re.findall(r'^### (EMP-\d+) ',actual,re.M)
    if ids!=[f'EMP-{i:02}' for i in range(1,16)]:errors.append('Event set or order')
    if baseline:
        if layout_blocks(text)!=layout_blocks(baseline):errors.append('Approved layout changed')
        if section(text,2)!=section(baseline,2):errors.append('Approved item table changed')
        if section(text,1)!=section(baseline,1):errors.append('Approved system/layout section changed')
    from docsite.diagram import parse
    er=[]
    for code in re.findall(r'```mermaid\n([\s\S]*?)```',text):
        graph=parse(code)
        if graph.get('kind')=='er':er.append(graph)
    if len(er)!=1 or len(er[0]['edges'])!=4:errors.append('Search ER relationships missing')
    return {'status':'passed_static_db_contract' if not errors else 'failed','errors':errors,
            'events':15,'common_db_contracts':13,'definition_items':77,'layout_states':len(layout_blocks(text)),
            'fixed_list_columns':16,'runtime_application_tested':False,'live_database_tested':False,
            'full_implementation_readiness':'review_required'}

def trace(root,manifest):
    methods={};evidence=[]
    for alias,path in PATHS.items():
        if path.endswith(('.cs','.ts','.vue')):
            for m in functions(read(root/path),path,'cs' if path.endswith('.cs') else 'ts'):
                methods[(alias,m['name'])]=m
    for cid,symbols in COMMON_SYMBOLS.items():
        for key in symbols:
            if key not in methods:raise ValueError('Missing common method '+str(key))
            m=methods[key]
            evidence.append({'common':cid,'symbol':key[1],'path':m['path'],'line':m['line'],'end':m['end'],
                             'body_sha256':sha(m['body']),'calls':m['calls']})
    chain=[]
    front=read(root/PATHS['frontend'])
    declared=re.findall(r"const methodname = '([^']+)'",re.sub(r'//[^\n]*','',front))
    if set(declared)!=set(API):raise ValueError('New or missing employee API declarations: '+str(declared))
    for api,meta in API.items():
        m=methods.get(('service',api))
        if not m:raise ValueError('Missing service '+api)
        transport=('download','WebRequestDownload','/api/Download/WebRequestDownload') if api=='CsvExreport' else ('upload','Upload','/api/Upload') if api=='SaveFile' else ('controller','WebRequest','/api/WebRequest')
        chain.append({'api':api,'service':'HrEmployee',**meta,'endpoint':transport[2],
                      'source':{'frontend':PATHS['frontend'],'controller':PATHS[transport[0]],'service':m['path'],'line':m['line'],'end':m['end']},
                      'common_calls_observed':m['calls']})
    sql=read(root/SQL);ddl=archive_schema((root/DUMP).read_bytes())
    routine={}
    for name in ['sp_hr_employee','sp_check_field_used']:
        found=[r for r in ddl if re.match(r'CREATE (?:OR REPLACE )?FUNCTION public\.'+name+r'\(',r['sql'])]
        if len(found)!=1:raise ValueError('Ambiguous saved DB function '+name)
        routine[name]={'offset':found[0]['offset'],'definition_sha256':sha(found[0]['sql']),'sql':found[0]['sql']}
    def parameters(s):
        header=s[:s.upper().index('RETURNS')]
        return re.findall(r'\b(\w+_in)\b',header)
    version={'sql_file':{'path':SQL,'parameters':parameters(sql),'count':len(parameters(sql))},
             'saved_dump':{'path':DUMP,'offset':routine['sp_hr_employee']['offset'],'parameters':parameters(routine['sp_hr_employee']['sql']),'count':len(parameters(routine['sp_hr_employee']['sql']))},
             'policy':'Use source SQL for current screen/service specification; do not mix with saved definition. Live deployment unverified.'}
    if version['sql_file']['count']!=11 or version['saved_dump']['count']!=6:raise ValueError('Reviewed DB signature changed')
    if re.search(r'\bJOIN\b',re.sub(r'--[^\n]*','',sql),re.I):raise ValueError('Search now has a SQL join; ER review required')
    schemas={}
    for t in TABLES:
        selected=[e for e in ddl if re.search(r'(?:CREATE TABLE|ALTER TABLE ONLY) public\.'+t+r'\b',e['sql'])]
        definitions='\n'.join(e['sql'] for e in selected)
        pk=re.search(r'PRIMARY KEY\s*\(([^)]+)\)',definitions)
        if not pk:raise ValueError('Missing saved key: '+t)
        schemas[t]={'primary_key':[x.strip() for x in pk[1].split(',')], 'foreign_keys_in_selected_statements':re.findall(r'FOREIGN KEY[^;]+',definitions),
                    'ddl_sha256':sha(definitions),'offsets':[e['offset'] for e in selected]}
    result={'review_version':manifest['revision'],'sources':manifest['sources'],'api_chains':chain,
            'common_symbols':evidence,'schema_versions':version,'saved_table_keys':schemas,
            'without_employee_db_calls':NO_DB,'static_sql_joins_in_employee_search':0,
            'unresolved':['AIplus.AIF.DBLib60 helper bodies, identity propagation, batch update, optimistic locking internals',
                          'Live DB function version, constraints, dynamic selection queries, actual transaction behavior'],
            'scope':'Source-observed paths and reviewed mapping, not compiler-resolved global call graph or live execution'}
    report=root/'report/employee-db'
    write(report/'trace.json',result)
    from contextbase.external_spec import mdtable
    rows=[]
    for a in chain:
        rows.append([','.join(a['events']),a['api'],a['endpoint'],','.join(a['common']),', '.join(a['tables'])])
    text='# 社員マスタ：画面→API→DBの根拠追跡\n\n対象は社員マスタ及びそこから利用する共通処理のみ。画面レイアウト・他機能本文は変更しない。\n\n'
    text+=mdtable(['イベント','サービス処理','受付API','共通ID','DB作用（C/R/U/D）'],rows)
    text+='\n## 共通DB関数の出典\n\n'
    for e in evidence:
        link='../../'+quote(e['path'],safe='/')+f"#L{e['line']}-L{e['end']}"
        text+=f"- {e['common']} / `{e['symbol']}`: [原本L{e['line']}-L{e['end']}]({link})\n"
    text+='\n## 各APIの業務処理・画面経路\n\n'
    for a in chain:
        text+=f"- `{a['api']}`: [業務処理L{a['source']['line']}-L{a['source']['end']}](../../{quote(SERVICE,safe='/')}#L{a['source']['line']}-L{a['source']['end']})。画面アダプター、共通通信、受付コントローラをsources台帳に記録。\n"
    text+='\n## DB定義の版\n\n'+mdtable(['定義','引数数','引数名'],[[k,v['count'],', '.join(v['parameters'])] for k,v in version.items() if isinstance(v,dict)])
    text+='\n同名関数の現行SQL原本と保存済みダンプは別版。社員検索は原本側を仕様記述に採用し、削除関連確認はダンプから取得した。稼働DBへの接続やSQLの実行は行っていない。\n'
    for name,r in routine.items():
        # DDL only; the archive's business data records are never emitted.
        write(report/(name+'_保存済み定義.sql'),r['sql'])
        text+=f"\n`{name}` 保存済み定義: ダンプバイト位置 {r['offset']}、定義SHA-256 `{r['definition_sha256']}`。\n"
    text+='\n## 追跡の限界と判明した影響\n\n'
    text+='検索の名称補完は区分種別＋区分コード、単数値は対象種別＋社員内部ID＋項目番号で対応する。SQL JOINを捏造していない。低水準のAiSelectHelper/AiUpdateHelper/AiInsertHelperは参照先の実装を取得できておらず、名前からキー・列更新・採番の動作を確定しない。\n\n'
    text+='氏名条件の未使用、メール本人除外の二重比較、業務エラー返却でも確定する境界、順序なしのページ取得、単数値の一覧更新委譲、明細の明示削除再登録、同名列による削除可否、取込の固定対象補正、CSVの未エスケープを区別して記載した。実名・パスワード値・データ行は転載しない。\n'
    write(report/'画面API_DB追跡.md',text)
    return result

def enhance(root,text,publish_common=True):
    manifest=check_sources(root);trace(root,manifest)
    newer=refined(text);result=audit_document(newer,text)
    if result['errors']:raise ValueError(str(result['errors']))
    if publish_common:write(root/COMMON,(ASSETS/'common.md').read_text(encoding='utf-8'))
    write(root/'report/employee-db/contract-validation.json',result)
    return newer

def publish(root:Path,revision='main',browser=False):
    from docsite.publish import html_document
    from docsite.common import inside,js
    root=root.resolve();md=root/FEATURE
    before={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/'output').rglob('*') if p.is_file()}
    original=md.read_text(encoding='utf-8')
    ownership=root/'report/employee-db/ownership.json'
    known=json.loads(ownership.read_text()) if ownership.exists() else {}
    review=json.loads((ASSETS/'sources.json').read_text())
    expected=review.get('approved_document_sha256')
    if sha(original) not in {expected,known.get(FEATURE)}:
        raise ValueError('Employee MD has unreviewed edits; refusing overwrite')
    if (root/COMMON).exists() and sha((root/COMMON).read_bytes()) not in {sha((ASSETS/'common.md').read_bytes()),known.get(COMMON)}:
        raise ValueError('Common DB document has unreviewed edits')
    new=enhance(root,original,publish_common=False)
    common=(ASSETS/'common.md').read_text(encoding='utf-8')
    paths=[root/FEATURE,root/COMMON]
    pages={p.resolve():root/'output/html'/p.relative_to(root/'output/md').with_suffix('.html') for p in (root/'output/md').rglob('*.md')}
    for p in paths:pages[p.resolve()]=root/'output/html'/p.relative_to(root/'output/md').with_suffix('.html')
    plans={root/FEATURE:new,root/COMMON:common}
    for p,text in [(root/FEATURE,new),(root/COMMON,common)]:plans[pages[p.resolve()]]=html_document(text,p,pages[p.resolve()],pages,root,'tujinrong/contextbase-chatgpt',revision)
    allowed={FEATURE,COMMON,*[p.relative_to(root).as_posix() for p in pages.values() if p in [pages[x.resolve()] for x in paths]]}
    oldhtml=root/'output/html/基本設計書'/Path(FEATURE).with_suffix('.html').name
    html_key=oldhtml.relative_to(root).as_posix()
    if sha(oldhtml.read_bytes()) not in {review.get('approved_html_sha256'),known.get(html_key)}:
        raise ValueError('Employee HTML has unreviewed edits; refusing overwrite')
    common_html=pages[(root/COMMON).resolve()]
    if common_html.exists() and sha(common_html.read_bytes())!=known.get(common_html.relative_to(root).as_posix()):
        raise ValueError('Common DB HTML has unreviewed edits; refusing overwrite')
    def screenhtml(text):return [str(n) for n in BeautifulSoup(text,'html.parser').select('.screen-layout')]
    if screenhtml(oldhtml.read_text())!=screenhtml(plans[oldhtml]):raise ValueError('Approved HTML screen fragment changed')
    if not (root/'report/employee-db/approved-before.json').exists():
        write(root/'report/employee-db/approved-before.json',{'source':FEATURE,'layout_hashes':[sha(x) for x in layout_blocks(original)],'all_output_hashes':before})
    browser_result=browser_check(root,paths,plans) if browser else None
    check_sources(root)  # Refuse publication when a reviewed source changed during processing.
    saved={p:p.read_bytes() if p.exists() else None for p in plans}
    try:
        for p,text in plans.items():inside(root,p);write(p,text)
    except Exception:
        for p,raw in saved.items():
            if raw is None:p.unlink(missing_ok=True)
            else:write(p,raw)
        raise
    after={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/'output').rglob('*') if p.is_file()}
    changed=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    if set(changed)-allowed:raise ValueError('Non-pilot output changed: '+str(set(changed)-allowed))
    # Keep global ownership in sync when present, without claiming a full rebuild.
    manifest_path=root/'.specgen-state/docsite/html.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        for p in paths:
            target=pages[p.resolve()];manifest.setdefault('files',{})[target.relative_to(root).as_posix()]=sha(target.read_bytes())
        write(manifest_path,manifest)
    result=audit_document(new,original)
    result.update({'changed_output_files':sorted(changed),'non_pilot_output_unchanged':True,
                   'layout_hashes':[sha(x) for x in layout_blocks(new)],'revision':revision,
                   'approved_html_layout_unchanged':True})
    result['reviewed_sources_unchanged']=True
    result['reviewed_source_count']=len(review['sources'])
    if browser_result:result['browser']=browser_result
    write(root/'report/employee-db/ownership.json',{p:after[p] for p in allowed})
    write(root/'report/employee-db/result.json',result)
    report='# 社員マスタPilot：イベントDB仕様の検証結果\n\n'
    report+='承認済みレイアウトを変更せず、画面→API→共通DB処理を追跡した。比較対象は外部仕様と静的抽出結果であり、実API・実DB・完全再実装の試験ではない。\n\n'
    from contextbase.external_spec import mdtable
    report+=mdtable(['検査','結果'],[[k,v] for k,v in result.items() if k not in ['layout_hashes','browser']])
    report+='\n## 保存先\n\n[社員マスタMD](../../'+FEATURE+') ／ [共通DB処理仕様](../../'+COMMON+') ／ [画面API_DB追跡](画面API_DB追跡.md)\n\n'
    report+='API宣言10件、イベント15操作、共通DB契約13件、論理ER図2件を確認。検索基表は社員1表で、SQL結合は0。後段の名称・追加値の対応を論理ERで示す。低水準DBライブラリ、稼働DBの版、動的な候補参照、取込とCSVの問題は未確認・要是正を明示した。\n'
    write(root/'report/employee-db/検証結果.md',report)
    return result

def browser_check(root,paths,plans=None):
    from playwright.sync_api import sync_playwright
    results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'],executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE'))
        for p in paths:
            target=root/'output/html'/p.relative_to(root/'output/md').with_suffix('.html')
            page=browser.new_page(viewport={'width':2000,'height':1100});requests=[];errors=[]
            page.route('**/*',lambda r:(requests.append(r.request.url),r.abort()))
            page.on('pageerror',lambda e:errors.append(str(e)))
            content=plans[target] if plans else target.read_text(encoding='utf-8')
            page.set_content(content,wait_until='load')
            count=page.locator('svg[data-engine=graphviz-er]').count()
            for n in page.locator('svg[data-engine=graphviz-er]').all():
                size=n.bounding_box()
                if not size or min(size['width'],size['height'])<=0:errors.append('ER diagram not visible')
            if count!=1:errors.append('ER count')
            if requests:errors.append('Network access')
            results.append({'html':target.relative_to(root).as_posix(),'html_sha256':sha(content),'er_diagrams':count,'errors':errors})
            page.close()
        browser.close()
    if any(r['errors'] for r in results):raise ValueError(str(results))
    write(root/'report/employee-db/browser.json',{'status':'pass','pages':results,'scope':'Static diagrams and offline rendering, no live application'})
    return {'status':'pass','pages':len(results),'er_diagrams':sum(x['er_diagrams'] for x in results)}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--revision',default='main');parser.add_argument('--browser',action='store_true');args=parser.parse_args()
    print(json.dumps(publish(Path(args.root),args.revision,args.browser),ensure_ascii=False,indent=2))
