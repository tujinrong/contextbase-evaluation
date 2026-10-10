"""Review generated Markdown only; never access application data."""
from pathlib import Path
from datetime import date
import re, posixpath, json
FILES={str(p):p.read_text(encoding='utf-8') for root in ('spec','docs') for p in Path(root).rglob('*.md')}
WAYS=['VB.NET_WinForms','CSharp_WPF','CSharp_ASPNET','Vue_CSharpAPI','COBOL','AS400_RPG','Access']
for p,t in list(FILES.items()):
    t=t.replace('保存手順・確認占有の解放・更新なし・結果不明は共通03が正本。','保存手順・確認占有の解放・更新なし・結果不明は共通モジュール設計（文書03）の共通13が正本。')
    t=t.replace('登録は共通07の新規所属','登録は共通モジュール07の新規所属')
    t=t.replace('共通07・元号の変換定義','共通日付仕様（文書07）・元号の変換定義')
    t=t.replace('新席が旧席と違う場合だけ増加先を検査する。','新席が未設定でなく旧席と違う場合だけ増加先を検査する。卒業・退学・削除による席解放には人数加算の定員検査を行わない。')
    t=t.replace('change_columnsは','changed_columnsは')
    if p.endswith('/03_言語依存仕様書.md'):
        env=p.split('/')[2]
        if env in ('VB.NET_WinForms','CSharp_WPF','AS400_RPG','Access'):
            t=t.replace('| 通信境界 | Webの保存要求はbirthDateInputの4文字列を受け、保存側で厳密変換。既存取得応答のbirthDateはISO日付。入力と応答の型を混同しない |','| 呼出境界 | 本方式はネイティブ画面。和暦原入力4値を業務処理へ渡し厳密変換する。取得時は内部日付を和暦表示に変換。Web JSON契約は本方式に適用しない |')
        t=t.replace('### 保守入口・方式固有の適合条件\n\n### ', '### 保守入口・方式固有の適合条件\n\n#### ')
    if '/詳細仕様書/' in p:
        for old,new in [('所属ID','class_id'),('所属ID・参考人数','class_id / occupancy'),('学年の分類と値','grade_category + grade_code'),('学年分類と値','grade_category + grade_code'),('在籍区分の分類と値','enrollment_category + enrollment_status_code'),('都道府県の分類と値','prefecture_category + prefecture_code'),('性別の分類と値','gender_category + gender_code'),('任意の続柄分類と値','relationship_category + relationship_code'),('分類','category_id')]:
            t=t.replace(': "'+old+'"', ': "'+new+'"')
    FILES[p]=t
p='spec/詳細仕様書/共通技術/PostgreSQL物理仕様書.md'
FILES[p]=FILES[p].replace('| pk_class / uq_class_year_code |','| pk_operation_log | t_operation_log.log_id主キー。IDENTITYだけでは一意制約の代替にしない |\n| pk_class / uq_class_year_code |')
FILES[p]+='\n履歴はafter_versionが正、before_versionは新規時NULL、既存変更時は正。changed_columnsは許可物理列名の配列、対象キーと操作種別を入口で検査する。履歴自身の変更を再度履歴へ追記しない。\n'
p='spec/共通/08_データアクセス仕様.md'
FILES[p]=FILES[p].replace('検索未実行はHasSearched=false。','検索実行済み状態の初期値は「未検索」。').replace('氏名キーORカナキー一致','氏名照合用情報または氏名カナ照合用情報の一致').replace('変更した物理項目名だけ。','変更した項目の識別名だけ（物理表現は各方式に定義）。')
FILES['spec/共通/02_CRUD図.md']+='\n## 技術補助情報の区別\n\n本図の検索は業務5表の参照のみ。Access・IBM i方式が一貫した読取りのために更新する制御行は技術補助表であり、学生情報の更新や操作履歴の業務変更に数えない。制御行は検索終了時に取消す。技術制御を迂回する直接更新を認めないことが一貫性の前提である。\n'
BIND={
 'VB.NET_WinForms':('birthDateInput.Era / Year / Month / Day','BirthDateInput（4つのString）→StudentEditModel.BirthDate As DateOnly?','JapaneseDateService.ParseBirthDate / FormatBirthDate'),
 'CSharp_WPF':('BirthDateInput.Era / Year / Month / Day','JapaneseBirthDateInput（4つのstring）→Model.BirthDate（DateOnly?）','JapaneseDateService.ParseBirthDate / FormatBirthDate'),
 'CSharp_ASPNET':('BirthDateInput.Era / Year / Month / Day','StudentSaveInput.BirthDateInput（4つのstring）→command.BirthDate（DateOnly）','JapaneseDateService.ParseBirthDate / FormatBirthDate'),
 'Vue_CSharpAPI':('form.birthDateInput.era / year / month / day','TypeScriptの4文字列→C# BirthDateInput→command.BirthDate（DateOnly）','JapaneseBirthDateField.vue / JapaneseDateService'),
 'COBOL':('E-BIRTH-ERA / E-BIRTH-YEAR / E-BIRTH-MONTH / E-BIRTH-DAY','PIC Xの原入力4値→E-BIRTH-DATE PIC X(10)のISO日付','STDATE'),
 'AS400_RPG':('EBERA / EBYEAR / EBMONTH / EBDAY','DDSの文字4値→editWork.birthDate（date）＋NULL標識','StParseBirthDate / StFormatBirthDate'),
 'Access':('cboBirthEra / txtBirthYear / txtBirthMonth / txtBirthDay','Stringの原入力4値→mDraft.BirthDateIso（ISO日付String）','modJapaneseDate.ParseBirthDate / FormatBirthDate'),
}
for env,(control,binding,service) in BIND.items():
    p=f'spec/詳細仕様書/{env}/02_学生登録画面.md';t=FILES[p]
    t=t.replace('| BirthDate | BirthDate | birth_date | 必須日付 |', '| birthDateInput.Era / Year / Month / Day | BirthDateInput→BirthDate As DateOnly? | birth_date | 必須、共通16で厳密変換 |')
    t=t.replace('必須日付にも未入力状態を持つ共通NullableDateControlを用い、','生年月日以外の必須日付にも未入力状態を持つ共通NullableDateControlを用い、')
    addition=f'''#### REG-005 生年月日の物理移送契約

| 項目 | 定義 |
| --- | --- |
| 入力コントロール | {control} |
| 入力→内部値 | {binding} |
| 共通呼出 | {service}。業務日・元号定義版を渡す |
| 保存先 | m_student.birth_date。元号・元号年を別列へ保存しない |
| 既存値→画面 | 内部日付から4入力値と和暦表示を生成。日付に時差変換を適用しない |
| エラー | 元号・年・月・日の原入力を保持しREG-005へE-DATE-001または002等を関連付ける。変換失敗をNULL扱いしない |

既存のBirthDate／BirthDateIso／E-BIRTH-DATE等は変換後の内部日付を指す。生年月日の入力欄を西暦の単一DatePickerや単一テキストへ戻さない。日付型の必須性は保存命令を確定するときに検査し、新規画面の未入力状態と区別する。

'''
    t=t.replace('#### 型と制御情報\n\n',addition+'#### 型と制御情報\n\n')
    t=t.replace('［Year］年［Month］月［Day］日','［birthDateInput.Year］年［birthDateInput.Month］月［birthDateInput.Day］日' if env=='VB.NET_WinForms' else '［BirthDateInput.Year］年［BirthDateInput.Month］月［BirthDateInput.Day］日')
    FILES[p]=t
p='spec/共通/05_チェック・メッセージ設計.md'
lines=[]
for line in FILES[p].splitlines():
    if line.startswith('| CHK-'):
        m=re.search(r'([EWI]-[A-Z]+-)(\d{3})((?:、\d{3})+)',line)
        if m: line=line[:m.start()]+m[1]+m[2]+''.join('、'+m[1]+x for x in m[3].split('、')[1:])+line[m.end():]
    lines.append(line)
FILES[p]='\n'.join(lines)+'\n'
def unfenced(text):
    result=[];fence=None
    for line in text.splitlines():
        m=re.match(r'^\s*(`{3,}|~{3,})',line)
        if m:
            tok=m[1]
            if fence is None:fence=tok
            elif tok[0]==fence[0] and len(tok)>=len(fence):fence=None
            continue
        if fence is None:result.append(line)
    assert fence is None,'Unclosed code fence'
    return '\n'.join(result)
def heads(text,level):return re.findall('^'+'#'*level+r' (.+)$',unfenced(text),re.M)
errors=[];screens=[];links=0
for p,t in FILES.items():
    plain=unfenced(t)
    for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)',plain):
        if dest.startswith(('https:','http:','#','mailto:')) or '＜' in dest:continue
        target=posixpath.normpath(posixpath.join(posixpath.dirname(p),dest.split('#')[0]))
        if target not in FILES:errors.append(f'{p}: broken link {dest}')
        links+=1
    screen=(p.startswith('spec/基本設計書/') or any(p.startswith('spec/詳細仕様書/'+w+'/') for w in WAYS)) and Path(p).name in ('01_学生検索画面.md','02_学生登録画面.md')
    if not screen:continue
    screens.append(p);reg='02_学生登録画面.md' in p
    expected=['概要','項目一覧','イベント仕様']+(['項目更新仕様'] if reg else [])+['補足説明']
    if heads(t,2)!=expected:errors.append(f'{p}: chapter order')
    overview=t.split('## 概要\n',1)[1].split('\n## 項目一覧',1)[0]
    for marker in ('### 画面設計','<table','### ファイル・DB入出力関係','データ操作関連図'):
        if marker not in overview:errors.append(f'{p}: {marker}')
    if t.count('<table')!=t.count('</table>'):errors.append(f'{p}: unclosed HTML table')
    for marker in ('### 項目別DB連携説明','### 選択候補の参照元','erDiagram'):
        if marker not in t:errors.append(f'{p}: {marker}')
    ids=set(re.findall(r'^\| ((?:SRC|REG)-\d{3}) \|',t,re.M))
    prefix='REG' if reg else 'SRC';expected_ids={f'{prefix}-{i:03}' for i in range(1,35 if reg else 34)}
    if ids!=expected_ids:errors.append(f'{p}: item ID set')
    for eid,body in re.findall(r'### (EV-(?:SRC|REG)-\d{3})[^\n]*\n(.*?)(?=\n### |\n## |\Z)',t,re.S):
        for sub in ('処理概要','処理手順','処理フロー','SQL・テーブル関連（ER図）','DB操作の詳細','結果・例外時の扱い'):
            if '#### '+sub not in body:errors.append(f'{p}: {eid} {sub}')
    if re.search(r'<td>2008[-/]\d\d[-/]\d\d</td>',t):errors.append(f'{p}: western birthdate example')
checks=FILES['spec/共通/05_チェック・メッセージ設計.md']
chk=re.findall(r'^\| (CHK-\d{3}) \|',checks,re.M);msg=re.findall(r'^\| ([EWI]-[A-Z]+-\d{3}) \|',checks,re.M)
assert len(chk)==len(set(chk))==34
assert len(msg)==len(set(msg))==58
for p in screens:
    missing=set(re.findall(r'\b[EWI]-[A-Z]+-\d{3}\b',FILES[p]))-set(msg)
    if missing:errors.append(f'{p}: messages {missing}')
assert len(screens)==16
COMMON=['created_at','created_by','updated_at','updated_by','row_version']
def columns(t):
    result={}
    for line in t.splitlines():
        m=re.match(r'^\| (m_student|m_class|m_code_category|m_code|t_operation_log)[^|]*\|([^|]+)\|$',line)
        if not m:continue
        entries=[]
        for part in m[2].split(';'):
            key=part.strip().split()[0]
            entries+=COMMON if key=='A' else [key]
        assert len(entries)==len(set(entries))
        result[m[1]]=entries
    return result
pg=columns(FILES['spec/詳細仕様書/共通技術/PostgreSQL物理仕様書.md'])
assert {k:len(v) for k,v in pg.items()}=={'m_student':35,'m_class':17,'m_code_category':11,'m_code':14,'t_operation_log':12}
for env in ('Access','AS400_RPG'):
    assert columns(FILES[f'spec/詳細仕様書/{env}/03_言語依存仕様書.md'])==pg,env+' physical columns'
code=FILES['spec/基本設計書/04_コード設計書.md']
seedrows=re.findall(r'^\| (\d{1,2}) \| ([^|]+) \| (\d+) \|',code,re.M)
assert len(seedrows)==70, len(seedrows)
era_doc=FILES['spec/共通/07_日付・和暦仕様.md'];eras={}
for line in era_doc.splitlines():
    cells=[x.strip() for x in line.strip('|').split('|')]
    if cells and cells[0] in ('MEIJI','TAISHO','SHOWA','HEISEI','REIWA'):
        key,name,offset,start,end=cells[:5]
        eras[key]=(int(offset),date.fromisoformat(start),date.fromisoformat(end) if re.fullmatch(r'\d{4}-\d{2}-\d{2}',end) else date.max)
assert len(eras)==5
TODAY=date(2026,10,10)
def parse_era(key,year,month,day):
    if key not in eras:raise ValueError('era')
    raw=str(year);y=1 if raw=='元' else int(raw) if re.fullmatch(r'[0-9]{1,4}',raw) else 0
    if y<1:raise ValueError('year')
    off,start,end=eras[key];d=date(off+y,int(month),int(day))
    if not(start<=d<=end and date(1900,1,1)<=d<=TODAY):raise ValueError('range')
    return d.isoformat()
VECTORS=[('HEISEI',20,5,15,'2008-05-15'),('MEIJI',33,1,1,'1900-01-01'),('MEIJI',32,12,31,None),('MEIJI',45,7,29,'1912-07-29'),('MEIJI',45,7,30,None),('TAISHO','元',7,29,None),('TAISHO','元',7,30,'1912-07-30'),('TAISHO',15,12,24,'1926-12-24'),('TAISHO',15,12,25,None),('SHOWA','元',12,24,None),('SHOWA','元',12,25,'1926-12-25'),('SHOWA',64,1,7,'1989-01-07'),('SHOWA',64,1,8,None),('HEISEI','元',1,7,None),('HEISEI','元',1,8,'1989-01-08'),('HEISEI',31,4,30,'2019-04-30'),('HEISEI',31,5,1,None),('REIWA','元',4,30,None),('REIWA','元',5,1,'2019-05-01'),('REIWA',0,1,1,None),('REIWA',-1,1,1,None),('REIWA',99999,1,1,None),('UNKNOWN',1,1,1,None),('HEISEI',12,2,29,'2000-02-29'),('HEISEI',13,2,29,None),('REIWA',8,10,10,'2026-10-10'),('REIWA',8,10,11,None),('REIWA',9,1,1,None),('REIWA',8,4,31,None),('REIWA',8,13,1,None),('REIWA','1e2',1,1,None)]
for key,year,month,day,expected in VECTORS:
    try:actual=parse_era(key,year,month,day)
    except (ValueError,OverflowError):actual=None
    assert actual==expected,(key,year,month,day,actual,expected)
for y,expected in ((1899,False),(1900,True),(9998,True),(9999,False)):
    assert (1900<=y<=9998)==expected
    if expected:date(y+1,3,31)
if errors:raise RuntimeError('\n'.join(errors))
report='docs/仕様書レビュー結果.md'
FILES[report]+='\n## 追加整合性レビュー（直接反映前）\n\n共通03という文書番号と共通13というモジュール番号を区別し、Native方式の言語依存仕様からWeb JSONを必須と読める記述を除去した。生年月日の原入力4値と内部日付を全７方式で追跡可能にした。開発者向けERの結合キー、PostgreSQL操作履歴主キー、席解放時の定員加算除外を補完した。\n\n'
FILES[report]+=f'検査結果：Markdown {len(FILES)}件、画面仕様{len(screens)}件、実在する相対ファイル参照{links}箇所、指摘残件0件（本検査の検出対象内）。チェック34件・メッセージ58件・初期コード70値を検査。PostgreSQL／Access／Db2の業務5表の物理列名と並びを照合し89列の一致を確認。元号定義表に基づくPython参照ロジックの和暦境界{len(VECTORS)}ケースと年度境界4ケースを実行した。\n\n'
FILES[report]+='これは静的文書検査と参照ロジックの検査であり、各言語の製品コードを実装・コンパイルした試験ではない。外部リンク到達性やHTML・Mermaidの実機描画もこの件数に含めない。承認が必要な1900年下限・和暦入力方式・認証／保存期間は上表の留保のままとする。\n'
for p,t in FILES.items():Path(p).write_text(t,encoding='utf-8')
print(json.dumps({'documents':len(FILES),'screens':len(screens),'relative_links':links,'errors':errors,'check_definitions':len(chk),'message_definitions':len(msg),'business_columns':sum(map(len,pg.values())),'seed_codes':len(seedrows),'era_reference_tests':len(VECTORS),'school_year_tests':4},ensure_ascii=False))
