"""Project-wide evidence graph. Never equate inferred names with physical DDL."""
from __future__ import annotations
from collections import defaultdict, Counter, deque
import re
from overviewgen.core import digest
from overviewgen.publish import db_catalog

# Reviewed interpretations of the supplied TKL usages, not schema declarations.
TKL_NAMES = dict(line.split('=',1) for line in '''m000_user=利用者
m001_control=運用制御・期首設定
m002_customerkbn=顧客区分
m003_bookkbn=書籍区分
m004_todofuken=都道府県
m005_uriagekbn=売上区分
m006_seikyusyokbn=請求書区分
m007_seikyukbn=請求区分
m009_annaisyokbn=案内書区分
m013_haisokbn=配送区分
m014_deliverykbn=配送方法区分
m015_cs_print_condition=顧客別印刷条件
m016_cs_class=顧客分類
m017_bizkbn=業務種別
m018_cs_discount_rate=顧客区分別値引率
m019_taxrate=消費税率
m101_customers=顧客
m102_customers_history=顧客対応履歴
m201_books=書籍
m202_bookprice=書籍基本価格
m205_monthly_magazine=月刊誌発行号
m206_magazine_price=顧客区分・配送区分別書籍価格
m208_book_display_priority_level=書籍表示優先順位
m301_bookcd_subject=書籍別科目
m302_bookcd_subjectkbn=書籍科目区分
m501_paymentkbn=振込先・入金種別
m700_report_sort=帳票並び順
m800_info=発行元基本情報
m900_postal_all=郵便番号取込原票
m901_postal=郵便番号・住所
mt201_books=書籍更新対象
rw404_invoice=請求書出力作業データ
t201_subscription_contract=月刊誌契約
t202_subscription_contract_send=月刊誌契約送付先
t203_subscription_contract_send_detail=月刊誌号別送付明細
t204_subscription_contract_annai=月刊誌案内対象
t301_order_publication=特別出版注文元データ
t302_order_publication_send=特別出版送付先元データ
t401_invoice_arrangements=請求計上対象注文
t402_publication_bills=請求計上データ
t403_publication_invoice=請求書
t404_publication_invoice_detail=請求書明細
t405_publication_no_issue=請求書未発行対象
t406_publication_bills_detail=月刊誌未計上通巻
t407_publication_submit=請求提出管理
t501_publication_paid=入金済み情報
t502_publication_payment=入金明細
tt200_order_pub_send=月刊誌契約・送付先
tt301_order_pub_send=特別出版注文
tt302_order_pub_send_list=特別出版送り状送付先
tw502_publication_payment=入金作業データ
v101_customers=顧客照会
v102_customers_history=顧客対応履歴照会
v200_monthly_magazine=月刊誌契約・送付照会
v201_books=書籍照会
v301_order_pub_send=特別出版注文・送付照会
v401_amount_monthly_magazine=月刊誌計上対象金額
v401_amount_order_pub=特別出版計上対象金額
v402_amount_data=請求金額照会
v403_invoice_data=請求書出力対象照会
v403_old_amount_data=過年度請求金額照会
v500_publication_payment=入金集計照会
v500_publication_payment_detail=入金明細照会
v501_unpayment_detail=未入金・未収金明細照会
vw404_invoice=請求書出力照会
vw501_unpayment_detail=入金入力用未入金明細照会
w405_publication_no_issue=未発行対象作業データ
func_seq_order_no=注文番号採番
func_seq_contract_no=契約番号採番
func_seq_cs_history_no=顧客対応履歴番号採番
func_seq_payment_no=入金番号採番
func_seq_amount_no=請求計上番号採番
func_seq_amount_detail_no=請求計上明細番号採番
func_send_no=送付番号取得
func_isnull=空値補完
func_substring=文字列部分取得
func_datestring=日付文字列変換
func_translate_case=検索文字表記変換
func_valuetext=コード名称表示
seq_m901_postal_postal_no=郵便番号管理番号シーケンス'''.splitlines())
COL_NAMES = dict(x.split('=',1) for x in '''order_no=注文番号
customer_id=顧客ID
send_id=送付先顧客ID
book_cd=書籍コード
booknm=書籍名
book_price=書籍定価
fixedprice=定価
fixed_price=定価
bookprice=本体価格
carriprice=送料
cs_kbn=顧客区分
haiso_kbn=配送区分
order_date=注文日
seikyu_kbn=請求区分
send_copies=送付数量
seikyu_price=請求金額
seikyu_tanka=請求単価
discounts=値引額
discount=値引額
reducepercent=値引率
curregeis=現行処理固定設定値
uriage_kbn=売上区分
sell_kbn=売上区分
send_name=送り状宛名
send_ken_cd=送り状都道府県コード
send_postalno1=送り状郵便番号前3桁
send_postalno3=送り状郵便番号後4桁
send_address=送り状住所
send_tel=送り状電話番号
updt=更新日時
upnm=更新者名
user_id=利用者ID
usernm=利用者名
pass=認証用保存値
postalno1=郵便番号前3桁
postalno3=郵便番号後4桁
seqno=管理連番
kbnmei=区分名称'''.splitlines())


def walk(graph, entry):
    """Breadth-first closure, with shortest evidence chains; cycles are retained by edges."""
    paths={entry:[entry]};queue=deque([entry])
    while queue:
        parent=queue.popleft()
        for child in graph.get(parent,[]):
            if child not in paths:
                paths[child]=paths[parent]+[child];queue.append(child)
    return paths


def build(data):
    methods=data['methods'];graph=data.get('call_graph',{})
    reverse=defaultdict(list)
    for parent,children in graph.items():
        for child in children: reverse[child].append(parent)
    consumers=defaultdict(list)
    for f in data['features']:
        for e in f['events']:
            entry=next((mid for mid in e['methods'] if methods[mid]['name']==e['source_name'] and methods[mid]['path']==e['path']),None)
            if entry:
                for mid,chain in walk(graph,entry).items():
                    consumers[mid].append({'feature':f['id'],'event':e['id'],'chain':chain,'relation':'immediate'})
        # A registered callback is NOT an immediate execution edge.
        for e in f['events']:
            for cb in e.get('deferred_callbacks',[]):
                for mid,m in methods.items():
                    if m['path']==f.get('code') and m['name']==cb:
                        for target,chain in walk(graph,mid).items():
                            consumers[target].append({'feature':f['id'],'event':e['id'],'chain':chain,'relation':'deferred_registration'})
    objects=db_catalog(data);objects.pop('WITH',None)
    usage=defaultdict(list);columns=defaultdict(list)
    for mid,m in methods.items():
        for ref in m.get('db',[]):
            usage[ref['object']].append({'method':mid,'operation':ref['operation'],'line':ref['line'],'path':m['path'],'consumers':consumers.get(mid,[])})
        for ref in m.get('columns',[])+m.get('db_mappings',[]):
            if ref.get('object') in objects and ref.get('column'):
                columns[(ref['object'],ref['column'])].append({'method':mid,'path':m['path'],'line':ref.get('line',m['line']),'role':ref.get('role',ref.get('direction','reference')),'property':ref.get('property','')})
                objects[ref['object']]['columns'].setdefault(ref['column'],{'type':'未確認','nullable':'未確認','length':'未確認','key':'未確認','origin':'利用箇所で観測'})
    labels=defaultdict(set)
    for f in data['features']:
        for i in f['items']:
            for mp in i['db']:
                if i['role']!='operation' and i['label_origin']!='unresolved':labels[(mp['object'],mp['column'])].add(i['name'])
    is_tkl=data['system'].get('system_name')=='Tokyo Librarian'
    for name,obj in objects.items():
        obj['logical_name']=TKL_NAMES.get(name,'用途名要確認：'+name) if is_tkl else '用途名要確認：'+name
        obj['name_status']='利用文脈に基づく論理名候補・未承認'
        obj['uses']=usage.get(name,[])
        obj['feature_ids']=sorted({x['feature'] for use in obj['uses'] for x in use['consumers']})
        obj['direct_method_ids']=sorted({u['method'] for u in obj['uses']})
        for col,d in obj['columns'].items():
            ls=sorted(labels[(name,col)])
            d['logical_name']=COL_NAMES.get(col) if is_tkl else None
            d['logical_name']=d['logical_name'] or (ls[0] if len(ls)==1 else '／'.join(ls) if ls else '用途要確認')
            d['label_candidates']=ls;d['uses']=columns.get((name,col),[])
            desc=[]
            for use in d['uses']:
                m=methods[use['method']];name_=m.get('summary') or '名称未確定の処理'
                desc.append(name_+'で'+{'write':'保存値','key':'対象特定条件','read':'読取値'}.get(use['role'],'参照・計算・結合候補')+'として使用')
            d['description']='。'.join(dict.fromkeys(desc)) or '画面・モデルとの対応候補。利用目的は原本の関連項目を照合して確定する'
            d['conflict']=len(ls)>1
    common=[]
    for mid,m in methods.items():
        owners={c['feature'] for c in consumers.get(mid,[])}
        # Common classification is based on usage OR explicit shared modules, not a single pilot.
        if len(owners)>1 or '/Classes/' in m['path']:
            common.append({'id':'COM-F-'+digest(mid)[:10].upper(),'method':mid,'name':m.get('summary') or '共通処理（名称確認）','feature_ids':sorted(owners),'consumers':consumers.get(mid,[]),'db':m.get('db',[]),'callers':reverse.get(mid,[])})
    return {'objects':objects,'common':common,'consumers':dict(consumers),'reverse_calls':dict(reverse),'calls':graph,
            'scope':{'files':len(data['records']),'methods':len(methods),'features':len(data['features']),
                     'recursive_edges':sum(map(len,graph.values())),'deferred_execution_confirmed':False}}


def quarantine_nested_keys(data):
    """Do not attach EXISTS-subquery keys to the outer UPDATE table by default."""
    ambiguous={(m['path'],m['name']) for m in data['methods'].values() if any(re.search(r'\b(?:UPDATE|DELETE)\b[\s\S]*?\bWHERE\b[\s\S]*?\bSELECT\b',f['sql'],re.I) for f in m.get('sql_fragments',[]))}
    quarantined=[]
    for feature in data['features']:
        for item in feature['items']:
            keep=[]
            for mp in item.get('db',[]):
                if mp.get('direction')=='key' and (mp.get('path'),mp.get('method')) in ambiguous:
                    entry=dict(mp,reason='副問合せのキーを外側の更新表の列と断定しない')
                    item.setdefault('db_candidates',[]).append(entry)
                    quarantined.append(dict(entry,feature=feature['id'],item=item['key']))
                else:keep.append(mp)
            item['db']=keep
            if not keep and item.get('binding'):item['db_status']='unresolved'
    return quarantined
