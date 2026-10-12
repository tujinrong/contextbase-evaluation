#!/usr/bin/env python3
"""Apply the STR-ACCESS-001 design correction to test-project1 specifications.
This maintenance script does not edit srcs, agents, or historical reports,
and does not execute application code or access any database.
"""
from pathlib import Path
import argparse, hashlib, html, itertools, json, os, re
VERSION='7.4'
REVIEWED_COMMIT='9ca00ce673a3f4533f79288d9854b578272b936b'
METHODS=['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']
REPORT_PATH='test-project1/report/20261012-spec-04-仕様修正回答.md'
LINK=re.compile(r'(!?\[[^\]\n]*\]\()([^\s)]+)(\))')
META=re.compile(r'<!-- spec-meta: (\{.*?\}) -->',re.S)

def metadata(text):
    m=META.search(text)
    return json.loads(m.group(1)) if m else None

def sections(text,level=2):
    lines=text.splitlines(keepends=True);headings=[];fence=None
    for i,line in enumerate(lines):
        marker=re.match(r'^\s*(`{3,}|~{3,})',line)
        if marker:
            ch=marker.group(1)[0]
            if fence is None:fence=ch
            elif fence==ch:fence=None
            continue
        if fence is None:
            m=re.match(r'^(#{1,6})\s+(.+?)\s*$',line)
            if m:headings.append((i,len(m.group(1)),m.group(2)))
    out={}
    for i,lev,name in headings:
        if lev!=level:continue
        end=next((j for j,k,_ in headings if j>i and k<=level),len(lines))
        if name in out:raise ValueError('Duplicate heading: '+name)
        out[name]=''.join(lines[i+1:end]).strip()
    return out

def splitrow(line):
    return [c.strip() for c in line.strip().removeprefix('|').removesuffix('|').split('|')]

def table_rows(block):
    rows=[splitrow(x) for x in block.splitlines() if x.startswith('|')]
    if not rows:return [],[]
    return rows[0],[r for r in rows[1:] if not all(re.fullmatch(r':?-{3,}:?',x) for x in r)]

def rowtext(cells):return '| '+' | '.join(str(c) for c in cells)+' |'

def replace_table_row(text,key,change):
    lines=text.splitlines();found=0
    for i,line in enumerate(lines):
        if line.startswith('|'):
            c=splitrow(line)
            if c[0]==key:lines[i]=rowtext(change(c.copy()));found+=1
    if found!=1:raise ValueError(f'Expected one row {key}; got {found}')
    return '\n'.join(lines)+'\n'

def append_section(text,heading,extra):
    needle='## '+heading+'\n'
    if needle not in text:raise ValueError('Missing section '+heading)
    start=text.index(needle)+len(needle);m=re.search(r'^## ',text[start:],re.M)
    end=start+m.start() if m else len(text)
    return text[:end].rstrip()+'\n\n'+extra.strip()+'\n\n'+text[end:]

def bump(text):
    m=META.search(text)
    if m:
        data=json.loads(m.group(1));data['version']=VERSION
        text=text[:m.start()]+'<!-- spec-meta: '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+' -->'+text[m.end():]
    text=re.sub(r'7\.[0-3]／2026-10-\d\d',VERSION+'／2026-10-12',text,count=1)
    text=text.replace('仕様書の書式改訂。業務アプリ・実DBの実行試験は未実施。','report指摘による設計改訂。本改訂の実DB・アプリ再検証は未実施。')
    text=text.replace('保存制約・型容量・業務上限は変更しない。','型容量・業務上限を維持。続柄分類のNULL条件は本改訂の保存契約に従う。')
    return text

def relative_link(source,target):return os.path.relpath(target,source.parent).replace(os.sep,'/')

def rebase(text,source,dest):
    def fix(m):
        uri=m.group(2)
        if re.match(r'^(?:[a-zA-Z][\w+.-]*:|#|/)',uri):return m.group(0)
        path,sep,anchor=uri.partition('#');target=(source.parent/path).resolve()
        return m.group(1)+os.path.relpath(target,dest.parent).replace(os.sep,'/')+(sep+anchor if sep else '')+m.group(3)
    return LINK.sub(fix,text)

def escape_cell(text):
    text=html.unescape(text.replace('<br>','\n'))
    return text.strip().replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>')

CONTACT_RULE='''### 緊急連絡先の保存契約（STR-ACCESS-001）

入力の緊急連絡先氏名・続柄・電話は、従来どおり全未入力または全入力とする。続柄のコード分類は入力項目ではなく保存側の派生値とし、続柄が未設定なら分類も未設定、指定されたら「続柄」の分類を設定する。性別・都道府県・在籍区分の必須分類は変更しない。

| 状態 | 緊急氏名 | 続柄分類 | 続柄値 | 緊急電話 | 保存可否 |
| --- | --- | --- | --- | --- | --- |
| 全未入力 | NULL | NULL | NULL | NULL | 他の連絡手段等が成立すれば可 |
| 全入力 | 入力値 | 続柄分類 | 有効なコード値 | 入力値 | 分類付き存在・既存値保持規則を満たせば可 |
| 一部だけ入力 | 混在 | 混在 | 混在 | 混在 | 不可。分類だけ／値だけのNULLも不可 |

新規・通常更新の両方で、正規化・緊急一式検査後、変更なし判定より前に分類を算定する。全消去時は氏名・分類・値・電話の４保存項目を同時にNULLへ更新する。入力19項目／通常更新18項目の数は変えず、派生する分類の更新を別に追跡する。未入力の分類を既定値で復活させたり、ダミーの未設定コードを追加したりしない。

画面からの分類値は受け付けない。確認情報には正規化した業務値を結び付け、続柄の変更・消去後は既存の確認を流用しない。派生分類も変更なし比較と変更列名の監査対象に含む。論理削除は連絡先や分類を変更しない。名称取得は分類＋値の外部結合とし、全NULLの学生を除外しない。

全３DBで続柄分類をNULL可とし、４保存項目の一式制約と実際の参照整合付き複合外部キーを併用する。分類・値の片側NULL、別分類の流用、非存在コードを拒否し、参照中コードの削除は拒否する。固定値だけのCHECKではNULLによる判定抜けが起こらないよう、未設定／全設定を明示的に検査する。

旧仕様の「続柄値が空でも分類を保持」は本改訂で廃止する設計判断であり、実機で確認済みの結果ではない。SQL Server・Db2・ACEの物理表と保存入口を同一改訂で変更する。過去の中断報告は上書きせず、新しい空の検証DBで全NULL保存・不正コード拒否・参照中削除拒否・監査取消を確認するまで実機適合は未確認とする。
'''
AUDIT_RULE='''### 操作履歴種別の決定

監査種別は処理後の状態だけではなく、保存前後の遷移から決める。コード・クラスの名称変更にも同じ規則を適用する。種別は既存のCREATE／UPDATE／DELETE／DISABLE／ENABLEを使い、STOPという新しい値は追加しない。

| 保存前後 | 履歴種別 | 変更列 |
| --- | --- | --- |
| 新規 | CREATE | 実際の登録列 |
| 有効から停止 | DISABLE | 利用可否と同時に変更した列 |
| 停止から有効 | ENABLE | 利用可否と同時に変更した列 |
| 有効のまま／停止のまま、名称等が変更 | UPDATE | 実際に変更した列のみ |
| 値が全て同じ | 履歴なし | 更新日時・版も増加させない |
| 学生の論理削除 | DELETE | 削除属性・更新管理列のみ |

学生の続柄分類が登録・消去に伴って変化した場合も変更列名へ含め、学生と履歴を同じ保存単位で確定する。旧実装で停止中コードの名称変更を停止処理と記録する箇所は、仕様をその動作へ合わせず実装側の再検証対象とする。
'''
SQL_RULE='''### 続柄の任意参照と行内制約（7.4）

`m_student.relationship_category`と`relationship_code`は共にNULL可。前者はコード選択時だけ`RELATIONSHIP`を保存入口が設定する。緊急連絡先４保存列の許可状態を、C-010の既存「連絡手段が１つ以上」の条件とAND結合する。次の述語は各列のNULL状態を明示し、CHECKのUNKNOWNを利用して部分入力が通る実装を防ぐ。

```sql
(
  (emergency_contact_name IS NULL
   AND relationship_category IS NULL AND relationship_code IS NULL
   AND emergency_phone_number IS NULL)
  OR
  (emergency_contact_name IS NOT NULL
   AND relationship_category IS NOT NULL AND relationship_code IS NOT NULL
   AND emergency_phone_number IS NOT NULL
   AND relationship_category = 'RELATIONSHIP')
)
```

C-008の旧「学生４分類は常に固定」を、必須３分類の固定と、上記の条件付き続柄分類へ置換する。既存の複合FK `(relationship_category, relationship_code) → m_code(category_id, code_value)` は有効のまま維持し、親コードの参照中削除・キー更新を拒否する。新規および通常UPDATEのSET対象へ派生分類を含める。分類の固定DEFAULTは作らない。空文字・空白だけは共通正規化でNULLとして扱い、コードの既存値保持・有効性・一式必須も保存入口で検査する。

[SQL Server CHECKのNULL判定](https://learn.microsoft.com/en-us/sql/relational-databases/tables/unique-constraints-and-check-constraints?view=sql-server-ver17)は固定制約の記述根拠であり、当該構成の実機合格証拠ではない。

これは仕様の修正であってDBへ適用済みのDDLではない。導入時は旧データを事前検査し、既知の旧表現（緊急３項目全NULLかつ分類だけRELATIONSHIP）のみ承認済み移行で全NULLへ変換する。他の不整合を自動修正しない。制約・列変更の製品別DDL、移行前後件数・監査・バックアップ・戻し手順は移行工程で検証する。
'''
ACE_RULE='''### 続柄の任意複合参照：生成手順と検証条件（7.4）

続柄分類を常時必須とする旧定義を廃止する。`relationship_category`と`relationship_code`は双方`Field.Required=False`、文字列の`AllowZeroLength=False`とし、分類のDefaultValueへRELATIONSHIPを指定しない。保存時は緊急３入力が全部空なら４列すべて`Null`、全入力なら分類をRELATIONSHIPとする。VBAの空文字や文字列「NULL」はDBのNullの代わりにしない。

新規の空バックエンドは、(1)テーブルと列、(2)主キー・m_codeの分類＋値一意性、(3)必須３分類の固定と次の行内一式条件を含むTableDef.ValidationRule、(4)参照整合付きDAO.Relation、(5)承認済みコード初期値、の順で作成する。既存ValidationRuleを全体置換して他の日付・削除・連絡手段条件を落とさず、旧「続柄分類は常に固定」の節だけを次の条件へ置き換える。

```text
(([emergency_contact_name] Is Null)
 And ([relationship_category] Is Null) And ([relationship_code] Is Null)
 And ([emergency_phone_number] Is Null))
Or
(([emergency_contact_name] Is Not Null)
 And ([relationship_category] Is Not Null) And ([relationship_code] Is Not Null)
 And ([emergency_phone_number] Is Not Null)
 And ([relationship_category] = "RELATIONSHIP"))
```

上の全体を括弧で囲み、既存の「本人電話・メール・緊急電話のいずれかあり」および他の行制約とAND結合する。Field側に旧来の分類必須ValidationRuleを残さない。NULL値を列既定値で補完しない。

複合FKは`CreateRelation("fk_student_relationship", "m_code", "m_student", 0)`から新しいRelationを生成し、新しいFieldを２個作成する。`category_id.ForeignName="relationship_category"`、`code_value.ForeignName="relationship_code"`の順でFieldsへAppendし、Relationsへ一度だけAppendする。他の３組の必須コードFK、学生クラスFK等も維持する。`dbRelationDontEnforce`・CascadeDelete・CascadeUpdateを指定しない。削除したRelationオブジェクトの再Appendを行わない。

本報告で未成立だったIgnoreNulls索引の探索を解決済みの設定として採用しない。両列NULLへ変更した本設計でも、ACEの対象版で最小表と実学生表の両方を再検証する必要がある。TableDef.ValidationRuleを設定しても、FK存在・NULL状態の往復検証なしに適合済みとしない。親が別分類の同じ値なら拒否、非存在コードなら拒否、参照中親削除は拒否、部分NULLは全組合せ拒否が必要。

既存DBは通常起動時に無断変更しない。承認済み移行工程でバックアップ・不整合一覧・旧表現の明示変換・列Required/ValidationRule/Relationの更新・事後検証を行う。学生更新と履歴の一括確定・取消は維持する。

公式資料はDAOの設定契約の根拠であり、この組合せの実機合格を示すものではない（2026-10-12参照）。[Relation](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/relation-object-dao)、[TableDef.ValidationRule](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/tabledef-validationrule-property-dao)。旧構成の失敗証拠は[STR-ACCESS-001](../../../report/structural-problem-STR-ACCESS-001.md)を参照。
'''
CONTEXT_RULE='''### 検索状態の版照合

既に発行された検索状態を利用する検索・ページ・クリア・復帰は、状態IDと最後に受領したRevisionを渡す。新規初期表示だけは状態未発行として状態ID・Revisionをサーバーが発行する。所有者・認証状態・タブ・有効期限を確認後、同一状態の排他区間で期待Revisionを照合する。省略時にサーバーの最新Revisionで補完しない。旧Revisionは拒否し、検索状態・実行済み条件・一覧を上書きしない。

Revisionは既存の検索状態契約の版番号であり、学生のExpectedVersionとは別。成功して状態を変えた場合だけRevisionを進め、応答へ返す。拒否時は入力を保持し、再取得による再確認を案内する。単に古い要求を自動再送しない。並行する同じRevisionの２要求が両方とも状態更新に成功してはならない。
'''

def patch_specs(root):
    project=root/'test-project1';changed=[]
    def modify(rel,fn):
        p=project/rel;old=p.read_text();new=fn(old)
        if old==new:raise ValueError('No modification: '+rel)
        p.write_text(bump(new),encoding='utf-8');changed.append(p)
    for rel in ['spec/基本設計書/テーブル/01_m_student.md']+[f'spec/DB定義/{db}/テーブル/01_m_student.md' for db in ['SQLServer','Db2_for_i','Access']]:
        def table_fix(t):
            def cat(c):
                assert c[2]=='relationship_category' and c[4]=='〇';c[4]='';c[7]=''
                c[8]='続柄未選択はNULL。選択時はRELATIONSHIPを処理設定し、続柄と同時更新。';return c
            def val(c):
                c[8]=c[8].rstrip('。')+'。未選択時は分類もNULL。一部だけのNULLは不可。';return c
            return replace_table_row(replace_table_row(t,'23',cat),'24',val)
        modify(rel,table_fix)
    for db in ['SQLServer','Db2_for_i','Access']:
        def db_fix(t,db=db):
            def change(key,definition):
                nonlocal t
                t=replace_table_row(t,key,lambda c:c[:2]+[definition]+c[3:])
            action='NO ACTION' if db=='SQLServer' else '削除・更新連鎖なし'
            change('C-006',f'分類＋値→m_code、{action}。続柄は両列NULL可・片側NULL不可。参照中コード削除を拒否')
            change('C-008','学生の必須３分類をGENDER/PREFECTURE/ENROLLMENT_STATUS、クラスをGRADEに固定。続柄分類は値未設定ならNULL、指定時のみRELATIONSHIP')
            change('C-010','連絡手段１つ以上。緊急氏名・続柄分類・続柄値・緊急電話は全NULLまたは全非NULL。全非NULL時の分類はRELATIONSHIP')
            t=t.replace('DB既定値が「指定なし」の列','DB既定値が空欄の列')
            return append_section(t,'補足説明',ACE_RULE if db=='Access' else SQL_RULE)
        modify(f'spec/DB定義/{db}/01_DB定義書.md',db_fix)
    def data_access(t):
        t=replace_table_row(t,'OP-INSERT',lambda c:c[:2]+['検証済み19入力、生成照合値2、必須３分類・条件付き続柄分類、認証情報']+c[3:])
        t=replace_table_row(t,'OP-UPDATE',lambda c:c[:2]+['対象ID、期待版、学籍番号以外18入力、生成照合値2、条件付き続柄分類','対象ID＋期待版＋非削除。続柄分類を続柄と同時更新。作成情報・学籍番号・必須３分類・削除情報は変更なし']+c[4:])
        return append_section(append_section(t,'保存の責務境界',CONTACT_RULE),'検索状態と上限',CONTEXT_RULE)
    modify('spec/共通/08_データアクセス仕様.md',data_access)
    modify('spec/共通/03_共通モジュール設計.md',lambda t:append_section(t,'保存の標準手順','正規化・緊急一式検査後、[共通データアクセス](08_データアクセス仕様.md)の続柄分類を算定し、変更なし判定と保存・監査へ同じ値を渡す。\n\n'+AUDIT_RULE))
    modify('spec/共通/05_チェック・メッセージ設計.md',lambda t:replace_table_row(t,'CHK-020',lambda c:c[:1]+['緊急３入力が全空または全入力。保存４項目は全NULLまたは全非NULL、続柄選択時のみ分類RELATIONSHIP']+c[2:]))
    shared_description='続柄値・名称を対応。未選択なら続柄分類もNULL、選択時は分類を処理設定（UPD-103）'
    def field_list_fix(t):return t.replace('値保存／続柄分類のコード名称表示',shared_description)
    modify('spec/共通/09_項目制約定義.md',lambda t:append_section(t,next(reversed(sections(t))),'### 続柄未設定の保存条件\n\nREG-020～022の全未入力は保存時に続柄分類もNULLとする。選択時のみ分類を処理設定し、４保存項目を一式で検査する。[共通データアクセス](08_データアクセス仕様.md)の保存契約を適用し、画面入力や業務項目数を増やさない。'))
    for kind,method in [('基本設計書',None)]+[('詳細仕様書',m) for m in METHODS]:
        rel=f'spec/{kind}/'+(method+'/' if method else '')+'02_学生登録画面.md'
        def reg_fix(t,method=method):
            t=field_list_fix(t)
            def update_row(c):
                c[3]='必須３分類を固定設定。続柄未選択は分類もNULL、選択時のみ続柄分類を設定'
                c[4]='必須３分類は維持。続柄分類は続柄と同時に設定／NULL化'
                c[6]='利用者入力を受けず保存側で算定。新規・更新の派生値と変更列監査を一致';return c
            t=replace_table_row(t,'UPD-103',update_row)
            marker='1. 入力19業務項目を複製。和暦原入力は共通16で日付へ変換、共通04・05・17で正規化・必須・範囲・連絡手段を検査する。'
            assert marker in t
            t=t.replace(marker,marker+' 続柄未選択なら分類もNULL、選択時は続柄分類を算定する。緊急一式４保存項目を変更なし比較・保存・監査へ渡す。',1)
            t=t.replace('作成情報・学籍番号・分類・削除情報は変更なし','続柄分類を続柄と同時更新。作成情報・学籍番号・必須３分類・削除情報は変更なし')
            if method:
                adapters={
                  'Access':'`Variant Null`を両列へ設定する。`Nz(..., "")`や固定DefaultValueで未設定の分類を復活させない。DAOの列Required・一式ValidationRule・複合FKはAccess DB定義に従う。',
                  'VB.NET_WinForms':'続柄コードがNothingなら分類もNothing。DBバインドは両列DBNull.Value。値ありは保存側でRELATIONSHIPを設定する。',
                  'CSharp_WPF':'続柄コードがnullなら分類もnull。DBバインドは両列DBNull.Value。値ありは保存側でRELATIONSHIPを設定する。',
                  'CSharp_ASPNET':'続柄コードがnullなら分類もnull。分類はフォーム入力として受理せず、C#保存側で算定してDBへ渡す。',
                  'Vue_CSharpAPI':'続柄コードがnullなら分類もnull。分類をJSON業務入力へ追加せず、C# APIの保存側で算定してDBへ渡す。',
                  'COBOL':'続柄コードが未設定なら分類・値両方のSQL NULL標識を設定する。値ありの場合だけ分類RELATIONSHIPを設定し、通常UPDATEにも同じバインドを適用する。',
                  'AS400_RPG':'続柄コードが未設定なら分類・値両方のSQL NULL標識を負値とする。値ありの場合だけ分類RELATIONSHIPと非NULL標識を設定し、通常UPDATEも同様とする。'}
                t=append_section(t,'補足説明','### 続柄分類の派生・全消去\n\n'+adapters[method]+'\n\n分類は新たな画面入力ではない。全消去時は氏名・分類・続柄値・電話を同時にNULL化する。原入力保持・読込時スナップショット・論理削除の更新範囲は変えない。生成物の旧固定分類代入は修正対象であり、本仕様変更だけで更新済みと扱わない。')
            return t
        modify(rel,reg_fix)
    for method in METHODS:
        rel=f'spec/共通/方式別/{method}/01_共通実装仕様.md'
        def adapter(t,method=method):
            heading=next(reversed(sections(t)))
            note='### 派生分類と監査の共通実装\n\n新規／通常更新は[共通データアクセス](../../08_データアクセス仕様.md)の緊急４保存項目一式を適用する。続柄分類を常にRELATIONSHIPへ設定する処理は禁止し、続柄値未設定時は分類もNULLへバインドする。コード値を更新する際は分類も同時更新し、変更列監査へ含める。必須３分類は固定のまま。\n\nマスタ監査は[共通モジュール](../../03_共通モジュール設計.md)の状態遷移表に従い、停止中の名称変更はUPDATE、状態が実際に停止へ変わる時だけDISABLEとする。認証不成立はE-COM-001、認証済み利用者の認可拒否はE-COM-002を使用し、実装の誤った番号を仕様値として採用しない。'
            t=t.replace('通常更新は学籍番号以外の18入力＋生成NameKey/KanaKey＋更新者日時＋版加算。','通常更新は学籍番号以外の18入力＋生成NameKey/KanaKey＋条件付き続柄分類＋更新者日時＋版加算。')
            t=t.replace('19入力＋照合値2＋分類固定値','19入力＋照合値2＋必須３分類・条件付き続柄分類')
            return append_section(t,heading,note)
        modify(rel,adapter)
    for method in ['CSharp_ASPNET','Vue_CSharpAPI']:
        rel=f'spec/詳細仕様書/{method}/01_学生検索画面.md'
        def webfix(t,method=method):
            lines=[]
            for line in t.splitlines():
                if line.startswith('|'):
                    c=splitrow(line)
                    if any('ClassCode' in x for x in c):c=[('9' if x=='10' else x) for x in c]
                    if any('ClassName' in x for x in c):c=[('18' if x=='50' else x) for x in c]
                    if method=='Vue_CSharpAPI' and c[0] in ['POST /api/students/search','POST /api/students/context/clear','POST /api/students/resume']:
                        assert 'contextId' in c[1];c[1]=c[1].replace('contextId','contextId、contextRevision',1)
                    if method=='CSharp_ASPNET' and c[0] in ['POST /students/search','POST /students/clear']:c[1]='ContextId・Revision必須。'+c[1]
                    line=rowtext(c)
                lines.append(line)
            t='\n'.join(lines)+'\n'
            return append_section(t,'補足説明',CONTEXT_RULE+'\nAPI／HTTPパラメーターの省略補完ではなく、既存の状態Revision照合を全該当経路へ明示した。状態版の取得・拒否応答は方式別共通仕様へ合わせる。')
        modify(rel,webfix)
    modify('docs/開発規約/VB.NET_WinForms.md',lambda t:t.replace('`student_api.commit_save`','`student_api.persist_student`').replace('は確認情報・理由を再検証し学生＋履歴を確定する契約とする。','は確認情報・理由を再検証し学生＋履歴を保存する契約とする。保存手続内でCOMMITせず、呼出元UnitOfWorkが確定する。'))
    modify('docs/開発規約/Access.md',lambda t:append_section(t,'VBA型・NULL・Unicode','### 任意の複合参照\n\n続柄未選択は分類とコードを共にVariant Nullで扱う。両列のRequired=False、AllowZeroLength=Falseと行内ValidationRule、参照整合付きRelationを同時に定義する。[Access DB定義](../../spec/DB定義/Access/01_DB定義書.md)の生成手順・最小再検証を稼働条件とする。DAO3201を握りつぶす、FKを解除する、緊急連絡先を必須化する方法では解決しない。'))
    return changed

def checklist_sync(root):
    project=root/'test-project1';specs={}
    for p in (project/'spec').rglob('*.md'):
        md=metadata(p.read_text())
        if md:specs[md['documentId']]=p
    changes=[];rows_updated=0
    for p in (project/'spec-eval/checklists').glob('*.md'):
        old=p.read_text();em=metadata(old)
        if not em:continue
        docid=em['documentId'].removeprefix('EVAL-')
        if docid not in specs:continue
        source=specs[docid];raw=source.read_bytes();t=source.read_text();sm=metadata(t)
        previous_hash=re.search(r'原仕様SHA256=([0-9a-f]{64})',old)
        if not previous_hash:raise ValueError('No source hash '+str(p))
        new_hash=hashlib.sha256(raw).hexdigest()
        if previous_hash.group(1)==new_hash:continue
        sec=sections(t);lookup={};is_table=sm.get('layout')=='TABLE'
        for sh in sm['sheets']:
            for entry in sh.get('sections',[sh]):
                heading=entry.get('heading')
                if entry.get('kind')!='LIST' or heading not in sec:continue
                cols,rr=table_rows(sec[heading]);keys=entry.get('key',[cols[0]])
                for r in rr:
                    assert len(r)==len(cols),(source,heading,r)
                    obj=dict(zip(cols,r))
                    key=sm['table']['fieldIds'][obj['物理名']] if is_table else ' / '.join(obj[k] for k in keys)
                    lookup[(heading,key)]=obj
        def spec_cell(txt):return escape_cell(rebase(txt,source,p))
        lines=[]
        for line in old.splitlines():
            if line.startswith('|'):
                c=splitrow(line)
                if len(c)==14 and c[0] not in ['評価ID','---']:
                    heading,sid,view=c[1:4];expected=None
                    if is_table and sid=='TABLE-HEADER':
                        _,rr=table_rows(sec['テーブルヘッダー']);expected='；'.join(f'{a}={b}' for a,b in rr)+'。名称・目的・主キー順序・共通参照が一致して３点。'
                    elif (heading,sid) in lookup:
                        expected='；'.join(k+'='+v for k,v in lookup[(heading,sid)].items())
                        expected+=('。診断必須、親項目と二重加点しない。' if c[5]=='0' else '。全属性が一致した場合のみ1点。')
                    elif heading=='イベント仕様' and sid.startswith('EV-'):
                        ev=next((v for k,v in sections(sec[heading],3).items() if k.startswith(sid+' ')),None)
                        if ev is None:raise ValueError('Missing event '+sid)
                        expected=sections(ev,4).get(view)
                    elif view=='説明・制約の内容' and heading in sec:
                        body=sec[heading]
                        body=re.sub(r'<!-- screen.*?<!-- /screen.*?-->','',body,flags=re.S)
                        body=re.sub(r'<style\b.*?</style>|<div\b.*?</div>|<table\b.*?</table>','',body,flags=re.S|re.I)
                        if '<input' not in body and '<form' not in body and len(body)<=23000:
                            expected='原仕様の本章に示す対象・条件・関係・例外を意味として再現する。基本設計は論理名/言語非依存を維持する。\n\n'+body
                    if expected is not None:
                        val=spec_cell(expected)
                        if len(html.unescape(val).replace('<br>','\n'))>32767:raise ValueError('Oversized expectation '+c[0])
                        c[4]=val;rows_updated+=1
                    assert c[8]=='未評価' and c[10]=='未評価',(p,c[0])
                    line=rowtext(c)
            lines.append(line)
        new='\n'.join(lines)+'\n';new=new.replace(previous_hash.group(1),new_hash)
        new=re.sub(r'基準7\.[0-9]+','基準'+sm['version'],new)
        p.write_text(bump(new),encoding='utf-8');changes.append(p)
    return changes,rows_updated

def report(root,changed,evalchanges):
    p=root/REPORT_PATH;p.parent.mkdir(exist_ok=True)
    assert not p.exists(),'Refuse to overwrite existing report'
    rows=[]
    for i,f in enumerate(sorted(changed+evalchanges,key=str),1):rows.append(f'| {i} | [{f.name}]({relative_link(p,f)}) | 仕様／評価基準を更新。過去の実行結果は転記しない |')
    meta={'schema':'spec-md/1.0','documentId':'REPORT-SPEC-04','version':VERSION,'path':REPORT_PATH,'sheets':[
      {'heading':'判断と対象','kind':'GRID','sheet':'01_判断と対象'},
      {'heading':'指摘対応一覧','kind':'LIST','sheet':'02_指摘対応一覧','key':['指摘ID']},
      {'heading':'再検証条件','kind':'LIST','sheet':'03_再検証条件','key':['試験ID']},
      {'heading':'変更文書一覧','kind':'LIST','sheet':'04_変更文書一覧','key':['No']},
      {'heading':'確認結果と未実施','kind':'GRID','sheet':'05_確認結果と未実施'}]}
    content='<!-- spec-meta: '+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+' -->\n'+'''# report指摘への仕様修正回答 7.4

2026-10-12。対象test-project1。比較元`9ca00ce673a3f4533f79288d9854b578272b936b`。本書は設計修正・引継ぎであり、旧実行の停止解除や実機合格報告ではない。

## 判断と対象

[構造問題報告](structural-problem-STR-ACCESS-001.md)と[Access実機記録](legacy-implementation.md)が示すのは、既存の「分類固定NOT NULL＋続柄値NULL可」の構成で正当な未入力がDAO3201により拒否されたこと。別索引の未完了探索を解決証拠にせず、続柄の両列NULLを許容する設計へ変更する。全３DBと基本・詳細・共通を統一し、外部キーと行内一式制約を維持する。

これは今回の仕様改訂で新たに決定した変更であり、旧報告がこの解決策の実機成功を証明したものではない。画面項目長・必須３分類・緊急連絡先の任意入力・業務５表89列・コード５分類70値は維持する。旧報告・manifest・srcs・Agent実装・既存画面HTML／画像は変更しない。旧中断後の実装再開には、下表の新しい空fixtureでの再検証と明示した再開判断が必要。

## 指摘対応一覧

| 指摘ID | 根拠 | 分類 | 仕様側の対応 | 残る実装作業 |
| --- | --- | --- | --- | --- |
| STR-ACCESS-001 | [中断報告](structural-problem-STR-ACCESS-001.md) | 構造変更 | 続柄分類もNULL可。緊急４保存列の一式制約＋実FK。INSERT/UPDATE/全消去/監査を同期 | 新DDL・DAO設定・保存処理を新fixtureで検査。実機適合未確認 |
| LOCAL-14 | [局所修正記録](spec-bug-fixes.md) | 既存修正の保持 | 14文書の修正後ハッシュを基準にし、旧値へ戻さない。評価の期待値・原仕様ハッシュも再同期 | 新入力manifestを固定する |
| WEB-REV | [Web記録](web-implementation.md) | 記述補完 | search/clear/resumeにも状態IDとRevisionを明記。省略・古い要求の自動補完不可 | 既存HTTP契約を新版へ再照合。fake検査と実DB検査を分離 |
| WEB-LEN | [Web記録](web-implementation.md) | 上限の再掲統一 | 内部クラスコード9・名称18を他５方式と一致 | 表示領域を理由に業務上限を拡張しない |
| AUDIT-STATE | [全体報告](build-report.md) | 実装指摘の仕様明確化 | 停止のまま名称変更はUPDATE、状態遷移のみDISABLE/ENABLE。STOPを新コードにしない | 既存Coreの該当分岐を修正・再試験 |
| VB-PROC | [Native記録](native-implementation.md)と現仕様 | 記述不一致の残存 | VBに残ったcommit_saveをDB正本のpersist_studentへ統一。Tx確定は呼出元 | EXEC-only本番境界の未実装範囲を埋める |
| RPG-AUTH | [RPG記録](rpg-implementation.md) | 実装未修正 | 認証不成立E-COM-001と認可拒否E-COM-002を再確認 | STUSVCの既知残件・全メッセージを再検査 |
| BUILD-INCOMPLETE | [COBOL](cobol-implementation.md)／[RPG](rpg-implementation.md)／[全体](build-report.md) | 未完成・未検証 | 未定義CALL、DDS/UI、配備等は仕様削除で隠さない。元の要求を維持 | 参照閉鎖・各処理系コンパイル・実DB/画面検証は再開後 |

## 再検証条件

| 試験ID | 前提・操作 | 期待結果 | 実施区分 |
| --- | --- | --- | --- |
| R74-01 | 本人電話あり、緊急３入力全空で学生新規保存 | 緊急氏名・分類・値・電話が全NULL。学生とCREATE監査が各1件確定 | 未実施：ACE最小表・実学生表、SQL Server、Db2 |
| R74-02 | 緊急氏名・有効続柄・電話を全入力 | 分類RELATIONSHIPと値を保存、再読込と名称表示が一致 | 未実施：全方式 |
| R74-03 | 既存緊急一式を全消去、本人連絡手段あり | ４保存列を同時NULL化、版+1、変更列監査に分類を含む | 未実施：全方式 |
| R74-04 | ４保存列のNULL／非NULLの16組合せ | 全NULLと正しい全非NULLだけ許可。残14組は行制約で拒否 | 参照論理の全組合せのみ実行。実DB未実施 |
| R74-05 | 分類NULL＋値あり、分類あり＋値NULL | 保存入口とDB行制約の両方で拒否 | 未実施：独立DAO・SQL入口 |
| R74-06 | 全非NULLだが存在しない続柄コード | FKで拒否。学生・監査は双方未確定 | 未実施：独立DAO・SQL入口 |
| R74-07 | 続柄以外の分類と同じコード値を指定 | 行制約で拒否。値単独の照合をしない | 未実施：３DB |
| R74-08 | 使用中の続柄コードを物理削除・キー更新 | 実FKが拒否。未参照コードと区別 | 未実施：３DB |
| R74-09 | 緊急なし、本人電話・メールもなし | 既存連絡手段必須エラー。NULL対応を理由に許容しない | 未実施：全方式 |
| R74-10 | 通常更新または全消去で監査書込みだけ失敗 | 学生変更・版更新・監査すべてRollback | 未実施：２接続・実DB |
| R74-11 | 論理削除時に未保存の緊急入力あり | 入力は保存されず、既存連絡先４列を維持 | 未実施：全方式 |
| R74-12 | 同一値再保存／確認後に続柄変更・消去 | 前者NoChange、後者は旧確認を使わず全再検証 | 未実施：全方式 |
| R74-13 | WebのRevision省略・旧値・並行２要求 | 省略・旧値拒否。同じ旧版で２件とも状態更新成功しない | 未実施：HTTP状態ストア |
| R74-14 | 停止中コードの名称だけ変更 | UPDATE履歴。停止化・再有効化の場合だけDISABLE/ENABLE | 未実施：実保守＋監査 |
| R74-15 | 認証済み一般利用者が終了区分訂正／削除を要求 | E-COM-002。未認証E-COM-001とは別 | 未実施：RPGを含む全方式 |

## 変更文書一覧

| No | 文書 | 対応 |
| --- | --- | --- |
'''+ '\n'.join(rows)+'''\n
## 確認結果と未実施

既存の14局所修正版を比較元として保持。形式・リンク・項目ID・テーブル列・NULL対応・評価IDと配点・原仕様SHA256を今回改めて検査する。詳しい機械検査結果は同じ実行の検証記録へ保存する。評価期待値の改訂は採点ではなく、両評価軸とも未評価を維持する。

未実施：ACE/Office、SQL Server、Db2の実機再検証、途中プログラムの修正・再ビルド、アプリ実行、逆生成、得点計算、Excel再出力。過去の11通過・形式PASS・Core79件等を新版の合格へ流用しない。過去の成果と現行入力の違いは新manifestで区別する。

既存のassets整理依頼について、この改訂はreportに基づく仕様修正だけを対象とし、前回書込みが未完了だった素材移動を実施済みとは扱わない。補助画面の見た目を変更する改訂でもない。
'''
    p.write_text(content,encoding='utf-8');return p

def validate(root,before):
    project=root/'test-project1';stats={'table_documents':0,'table_fields':0,'list_sections':0,'relative_links':0,'evaluation_rows':0,'null_matrix_cases':16}
    for p in (project/'spec').rglob('*.md'):
        t=p.read_text();m=metadata(t)
        if not m:continue
        sec=sections(t);expected=[]
        for sheet in m['sheets']:
            for entry in sheet.get('sections',[sheet]):
                h=entry['heading'];expected.append(h);assert h in sec,(p,h)
                if entry.get('kind')=='LIST':
                    stats['list_sections']+=1;lines=[l for l in sec[h].splitlines() if l.strip()]
                    assert lines and all(l.startswith('|') for l in lines),(p,h,'LIST mixed content')
                    cols,rows=table_rows(sec[h]);assert len(cols)==len(set(cols))
                    for r in rows:assert len(r)==len(cols),(p,h,r)
        assert set(sec)==set(expected),(p,'chapter declarations')
        if m.get('layout')=='TABLE':
            stats['table_documents']+=1;cols,rows=table_rows(sec['項目詳細']);stats['table_fields']+=len(rows)
            assert cols==['No','論理名','物理名','PK','NOT NULL','タイプ','長さ','初期値','説明']
            assert [int(r[0]) for r in rows]==list(range(1,len(rows)+1))
            if m['table']['physicalName']=='m_student':
                obj=next(r for r in rows if r[2]=='relationship_category');assert obj[4]=='' and obj[7]==''
    valid=[]
    for bits in itertools.product([False,True],repeat=4):
        if (not any(bits)) or all(bits):valid.append(bits)
    assert len(valid)==2
    for method in METHODS:
        p=project/f'spec/詳細仕様書/{method}/02_学生登録画面.md';t=p.read_text()
        r=next(splitrow(x) for x in t.splitlines() if x.startswith('| UPD-103 '))
        assert '同時' in r[4] and 'NULL' in r[3]
        assert '続柄の値が空でも分類情報を保持' not in t
    for p in (project/'spec-eval/checklists').glob('*.md'):
        t=p.read_text();old=before[p.relative_to(root).as_posix()].decode('utf-8')
        col,rows=table_rows(sections(t)['採点一覧']);_,oldrows=table_rows(sections(old)['採点一覧'])
        assert [(r[0],r[5],r[6]) for r in rows]==[(r[0],r[5],r[6]) for r in oldrows],p
        assert len({r[0] for r in rows})==len(rows);stats['evaluation_rows']+=len(rows)
        for r in rows:assert len(r)==len(col)==14 and r[8]=='未評価' and r[10]=='未評価'
    for rel,b in before.items():
        p=root/rel
        if not rel.startswith('test-project1/spec/') or p.suffix!='.md':continue
        m=metadata(b.decode('utf-8'));n=metadata(p.read_text())
        if m and m.get('layout')=='TABLE':assert m['table']==n['table']
    for p in (project/'spec').rglob('*.md'):
        for match in LINK.finditer(p.read_text()):
            dest=match.group(2)
            if re.match(r'^(?:[a-zA-Z][\w+.-]*:|#|/)',dest):continue
            target=(p.parent/dest.split('#')[0]).resolve();assert target.exists(),(p,dest)
            stats['relative_links']+=1
    return stats

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--verification',required=True)
    args=ap.parse_args();root=Path(args.root).resolve();assert (root/'test-project1/spec').is_dir()
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
    changed=patch_specs(root);evalchanges,count=checklist_sync(root);reportfile=report(root,changed,evalchanges)
    stats=validate(root,before);stats['updated_spec_and_rule_documents']=len(changed)
    stats['updated_checklists']=len(evalchanges);stats['refreshed_expectations']=count;stats['application_or_historical_report_edits']=0
    forbidden=[rel for rel,b in before.items() if (rel.startswith('test-project1/srcs/') or rel.startswith('agents/') or rel.startswith('test-project1/report/')) and (root/rel).read_bytes()!=b]
    assert not forbidden,forbidden
    changed_records=[]
    for p in sorted(changed+evalchanges+[reportfile],key=str):
        rel=p.relative_to(root).as_posix()
        changed_records.append({'path':rel,'beforeSha256':hashlib.sha256(before[rel]).hexdigest() if rel in before else None,'afterSha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    out={'reviewedCommit':REVIEWED_COMMIT,'revision':VERSION,'scope':'specification correction only','result':'static-checks-passed','statistics':stats,'runtimeVerification':'not-executed; Access structural stop not cleared','changes':changed_records}
    Path(args.verification).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()
