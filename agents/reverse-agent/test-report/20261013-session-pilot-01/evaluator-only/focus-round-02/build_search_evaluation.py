"""Persist NEW independent semantic decisions for the frozen round-02 search.

Every decision was made after reading the current text and selected original
rows. This builder performs identity, evidence, pin, and arithmetic checks only.
It never reads an earlier semantic-score report or derives credit from keywords.
"""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'frozen'
ROOT = HERE.parents[5]
DOC = 'DET-CSharp_ASPNET-SCR-STU-001'
GEN = 'generated/spec/detail/student-search.md'
ORIG = 'current-reference/test-project1/srcs/CSharp_ASPNET/spec/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
CHECK = 'evaluation/test-project1/spec-eval/checklists/DET-CSharp_ASPNET-SCR-STU-001.md'

# index | NEW judgement | actual new generated ranges | independently read meaning
DECISIONS = '''
0|missing|14-58,60-118,921-947|機能・参照IO・メモリ/役割は詳述するが、原概要の描画画像併記と直接正本/開発規約の責務一式は再現されず、計画パスだけでは補完しない。
1|missing|54-118,912-915|ソース投影は条件・一覧・権限・メッセージを描くが、設計にあるメニュー・表示範囲・先頭/最後の配置を差分表だけで補完せず画面全体対応は不足。
2|match|126,26-34,252-256,844-850|任意番号raw15/正規化15、空NULL、形式だけ検査、前方一致、varchar15非NULLと型付き検索bind、保存なしを別層で再現。
3|match|127,26-34,252-256,844-850|氏名raw8と表記8、NameKey160/別DB容量、任意NULL、部分一致、表記/照合値を別に再現。
4|match|128,26-34,252-256,844-850|カナraw36→表記18/照合キー、カナ検査/空白処理、任意NULL、部分一致とnvarchar36非NULLの対応を再現。
5|match|129,152,242-248,850|任意年度int?、実在1900～9998、西暦、クラスsmallint非NULL属性、未所属との排他/完全一致を再現。
6|match|130,153,242-248,850|GRADE分類/値、raw2とNFKC数字2桁、任意NULL、実在、00と未所属の区別、クラスvarchar2非NULL条件を再現。
7|match|131,154,242-248,850|画面文字列→正Int64?、19桁/0拒否、存在/上位整合、任意NULL、学生class_id bigint NULLへ完全一致を再現。
8|match|132,480-487,679-718,907|false初期、trueはclass_id IS NULL、所属条件との排他、未所属解除/非活性とOFF非復元の意図/現行差を再現。
9|hold|133,155,850|配列既定01/02、最大4/Ordinal重複拒否/空配列全区分/IN/DB型は明確だが、原N-07正規化と厳密Ordinal実装の扱いが未裁定。正解を捏造しない。
10|match|134,156,242-248|都道府県任意、raw2/NFKC数字2桁、PREFECTURE存在、NULL条件省略、varchar2非NULL基表と検索bindを再現。
11|match|135,252-256,844-850|電話raw20→正規化最大16、形式/任意空NULL、本人または緊急の二列OR完全一致、両列varchar16 NULLを再現。
12|missing|136,844-866|開始日の任意ISO10/NFKC厳密変換/範囲/内部DateOnly/両端含むSQLは正確だが、独立した原表示形式の契約を入力値形式で代替している。
13|missing|137,844-866|終了日の任意ISO10/片側/開始以下/内部dateと包含比較は説明するが、原表示形式の独立契約が入力部品/解析形式の説明だけで不足。
14|match|138,407-470,870-880,908|検索操作・Page1・条件確定・DB参照のみ・UI再入抑止と応答順意図の現行差を再現。
15|match|139,476-519,906-910|条件変更/候補更新は学生検索せず、再取得/解除/通知/Applied維持と自動連動の設計意図を区別して再現。
16|match|140,585-623|クリアで同IDのApplied/結果とModelStateを初期化し未検索/初期条件へ戻る、学生DELETEなしを再現。
17|match|141,728-771,912|新規の権限確認/条件非転記、メニューへDB更新なく戻る意図と実装専用経路欠落を意味として明示。
18|match|203,854-864,913|TotalCountと範囲を別表示値、0～10000/0件0～0/未検索・超過未設定として意図を定義し、Presentの未実装範囲算出と区別。
19|match|176,203,866|検索日時は今回サービスSearchedAtから日本時間の西暦日時へ移送し、未検索非表示/非DB保存/更新日時との区別を再現。
20|match|142,157,300-302,529-537|表示件数は必須20/50/100、既定20、変更時Page1、SQL Int size/保存なしの制御を再現。
21|match|188,274-302,844-850|保存番号15/varchar15非NULLを表示、照合用パターンではなく文字順、初回未検索と行保持を再現。
22|match|189,274-304,844-850|氏名保存表記8/nvarchar16非NULLのまま出力、NameKeyから再構成せず行保持を再現。
23|match|190,274-304,844-850|保存カナ18/nvarchar36非NULLを表示、照合キーと区別、初回未検索/入力対象外を再現。
24|match|191,866|生年月日date非NULL→DateOnly→和暦の元年/mmdd表示、入力なし/時差なし/必須値欠損の不整合を再現。
25|match|192-193,304-312,915|年度smallint1900～9998とGRADE名称業務12/容量24/非NULL基表、JOIN任意出力、未所属－/欠損不整合の意図を再現。
26|match|194-195,304-312,915|クラスコード9/名称18と容量/非NULL基表、class_id経由LEFT JOIN、未所属/停止/期間外の区別意図と現行注記欠落を再現。
27|match|196,304-312,915|在籍名称12/容量24/基表非NULL、用途分類＋値LEFT JOIN、名称欠落で行を消さない/不整合表示の意図を再現。
28|match|197-198,304-312,915|都道府県名称12＋住所1の45/各容量と基表非NULL、住所2非表示、連結/欠損不整合/行保持を再現。
29|match|199,864,915|本人電話16/varchar16 NULL、null－、緊急電話を一覧へ出さず保存値を表示する対応を再現。
30|match|201,866|updated_at datetimeoffset7非NULLのUTC保存と+09西暦19桁表示を分け、未検索/非編集出力を再現。
31|match|146,187,724-771|行番号/表示名ではなく正64bit学生IDで参照編集へ遷移し対象最新取得/権限/未存在を登録側で再確認する。
32|match|145,525-579,914|先頭/前/次/最後と有効範囲補正の意図を、現行前後/変更反映とPage補正/Resume差から分離して再現。
33|match|143,158,295-302|13以内の固定4ソート/既定studentNo、許可列switch、末尾ID昇順、任意DB列を受けない/保存なしを再現。
34|match|144,159,295-302|小文字asc/desc固定2種/既定asc、主列方向/ID昇順、必須/非DB制御を再現。
35|missing|152,344,921-945|検索年度降順/停止過去/範囲/空候補は定義するが、診断候補の新規登録当年度補助を本書で一式定義しない。関連計画だけでは属性補完しない。
36|missing|153,344,921-945|検索GRADE名称/停止含む/順序/00区別は明確だが、登録新規有効と既存別枠保持の候補属性一式は本書では不足。
37|missing|154,344,724-771,921-945|検索クラス上位絞込/順序/空/解除と登録側責務は説明するが、年度・学年・コード・名の表示と登録新規/最終/既存保持の診断属性一式は不足。
38|missing|155,344,850,921-945|検索区分候補/01・02/全解除は明確だが、登録新規01、有効選択と保護01～04の役割をこの候補行で一式定義しない。
39|missing|156,344,921-945|検索PREFECTURE停止含む/名称/順序/任意空は定義するが、登録新規有効/既存同値保持/登録未選択の全診断属性は不足。
40|match|142,157,529-537|非業務コードの固定20→50→100、20既定、変更Page1、表示件数の意味を再現。
41|match|143,158,295-302|固定4候補の値/論理表示/順序/番号既定と自由DB列不可を再現。
42|match|144,159,295-302|固定asc→desc、昇順/降順ラベル、asc既定を再現。
43|match|176,203,854-864,913|件数は非負0～10000の別整数値、検索成功時/未検索・超過未設定/0件範囲0～0を意図と実装差付きで再現。
44|match|203,854-864,913|RangeFromを件数と別の非負位置値、同値域/成功時/未検索・超過未設定/0件0として明示。現行算式の不存在を捏造で埋めない。
45|match|203,854-864,913|RangeToを件数と別の非負位置値、同値域/成功時/未検索・超過未設定/0件0として明示。現行算式の不存在を分離。
46|match|192,304-312,915|任意年度出力の取得元/四桁1900～9998/西暦/未所属－の意図と現行差を再現。
47|match|193,304-312,915|GRADE名称string?の業務12、保存コードではなく名称、未所属－/名称欠損不整合を再現。
48|match|194,304-312,915|クラスコードstring?9、class_id経由、未所属の表示意図/名称欠落でも行保持を再現。
49|match|195,304-312,915|クラス名称string?18、容量36とは別、未所属の表示意図/名称欠落でも行保持を再現。
50|match|191,866|内部birth_dateはdate必須/DateOnly取得、欠損不整合、無時差で和暦変換し表示値と分離する。
51|match|146,187,724-771|対象ID正Int64/19桁/新規null/DB採番/ルート移送、行番号でなく権限/存在再確認を再現。
52|match|165-170,212-228,947|共通乱数32byte→64hex不透明Context、所有者/セッション/タブ/30分、初回発行と復帰/一覧要求を再現。
53|missing|181,208-214|Antiforgeryのフォーム生成とPOST検査/ID・版・排他非代替は正確だが、基盤opaque型と長さの基盤定義責務が内部項目として不足。
54|missing|679-718,870-880|ブラウザーform submit時のボタン非活性/ariaBusyとDB排他別は記載するが、IsBusy真偽の初期false/開始終了による内部制御一式は不足。
55|match|908-910,919|画面RequestSequenceは非負/初期0/非同期要求時/旧応答無視/桁あふれ採番停止の意図を再現し、サーバーRevisionと区別。
56|match|16-22,365-401|認証利用者起動と状態新規発行/候補取得だけ、学生一覧は初回取得しないを再現。
57|match|365-401,905|参照権限/業務時刻、候補/初期01・02/20/studentNo asc/未検索、状態発行と復帰経路、必須マスター不足停止の意図を再現。
58|match|379-389,905|認証/候補/初期未検索の実装図と必須候補不足時不可の設計意図を組み合わせ、未実装保証へ置き換えない。
59|match|314-344,350-357,393|分類→値→GRADE複合参照の読取関係、検索用途LEFT相当/停止保持/監査書込みなしを再現。
60|match|314-344,393-397|コード候補→クラス候補の順序/型/実行単位/学生未読取/業務書込みなしを再現。
61|match|401,886-897,911,917|初回の候補取得/状態拒否と検索結果対象外、失敗原入力/結果意図と実装差、他者/期限拒否/候補非再検索を再現。
62|match|407-422,252-312|入力条件による非削除学生検索、参照のみ/サービス結果意味を再現。
63|match|411-470,126-137,866,908|入力複製/正規化/存在整合、同条件SNAPSHOT件数ページ、上限/0/1頁、Applied保持/日付表示と最新検索応答意図を現行差付きで再現。
64|match|426-456,191,866,911|入力/存在失敗、上限/empty分岐、同じ読取単位の一覧、和暦/他日時変換を図と明示仕様で意味照合。
65|match|304-312,350-359,464|学生/任意クラス/GRADE/在籍/都道府県の複合用途alias LEFT JOIN、NULL多重度/読み関係とFK/監査非連動を再現。
66|match|242-312,464|マスター存在整合→TOP10001件数→同条件ページ、型付きbind/順序/commitを再現。
67|match|468-470,854-864,886-897,911|入力保持/空一覧の局所範囲、LastResult残存、0件/超過区別、所有/版拒否と候補非再検索を意図/現行差付きで再現。
68|match|476-487,906-910|所属条件変更と候補連動を、学生検索未実行/Applied維持のイベントとして再現。
69|match|480-519,679-718,906-910|未所属解除/非活性/OFF非復元、不適合解除/警告、クラス先行補完/古い候補破棄/未反映の意図と実装差を再現。
70|match|491-505,683-718,906-910|未所属分岐/候補取得/不適合解除/未反映の実装図を上位補完/旧応答破棄の意図と意味照合。
71|hold|314-344,509-513|原候補ERは学生occupancy関連、原OP-CLASSは検索人数集計なしで内部矛盾。新版Lookup(false)のゼロは未集計値と正確に説明。未裁定を新たな正解で埋めない。
72|match|314-344,509-513|クラス候補/上位条件絞込、学生検索/人数集計/業務書込みなしと操作型/順序を再現。
73|match|517-519,886-897,906-911|今回原入力/旧一覧、未反映/非再検索、不整合クラス解除/所有期限拒否、検証未実施の境界と対象外結果を再現。
74|match|525-537|元Appliedから順序/表示指定/頁だけを変更し、入力途中値を混ぜず再取得する目的を再現。
75|match|529-579,909,914,916-917|所有期限/厳密版と適用済条件、許可表示指定/変更1頁、同条件再検索/一度最終補正、0件不可、期限初期化意図と現行拒否を再現。
76|conflict|541-565,577-579|図はAppliedなし/状態WebFaultに加えQ/Nの検証WebFaultを409固定ノードへ併合。実際のValidationFailedは422でControllerが維持し、正しい579行本文では図の事実誤認を打ち消せない。元3点を保持。
77|match|304-359,569|ページでも同じ学生/任意クラス/用途別複合コードLEFT JOINと読み関係/FKの区別を再現。
78|match|242-312,569-573|件数→ページの同条件検索、許可全体順序/型付きoffset,size、一度補正は別検索SNAPSHOTとして再現。
79|match|577-579,854-864,886-897|結果説明固有の局所WebFault対応状態/Applied保持/空一覧/共通SQL取消/0件超過/候補非再検索は正確。別の図誤りをこの説明へ重複減点しない。
80|match|585-623,724-771,912|新規/学生行/クリア/メニューの操作受付を実装経路と設計意図に分けて再現。
81|match|589-623,728-771,912|新規権限/条件非流用、対象IDで遷移し読込は登録側、クリア初期状態/DB更新なく共通メニューへ戻る意図を再現。
82|match|600-611,738-749,912|クリア/新規/既存ID分岐の図とDB更新なくメニュー復帰の意図を組み合わせ操作分岐の意味を再現。
83|match|615-619,754-771|遷移/メモリClearに業務ERを作らず、遷移先学生読込と候補再描画の読取を別責務に分類。原非適用0点を維持。
84|match|615-619,754-771,947|操作自体の業務DB更新なし/遷移先読取を区別し、候補Lookupは再描画責務として示す。
85|match|619-623,767-771,886-897|操作固有の権限/未存在/版/候補障害と検索未実行時の0件/上限等対象外を混同しない。
86|match|629-641,777-789,830-838|保存/削除Savedと取消/戻るから元Context復帰、非Savedの非自動帰還/結果不明を区別して再現。
87|match|633-674,781-838,916-917|所有/期限/版、未検索復元/元条件最新DB再検索、条件非変更と確定成功通知/消費、期限初期化意図と実装拒否差を再現。
88|match|645-659,793-808,916|所有期限拒否/検索済有無/元条件検索/確定Flashの復帰図と設計初期化意図を意味照合。
89|match|304-359,663|復帰も同じ学生/任意クラス/用途別複合コード読取関係・FK/監査区別を参照し再現。
90|match|242-312,663-674|元Appliedの件数/ページを同条件検索、最新DB/条件非変更、SQL用頁補正と保持pageの違いを再現。
91|match|671-674,830-838,854-864,886-897|復帰拒否/失敗段階、確定通知と消費、0件/超過/未検索、元条件維持を区別して再現。
92|match|126,252-256,844-850|番号原入力→NFKC/大文字化→student_no前方一致、NULL条件省略/保存なし/不正原入力の対応を再現。
93|match|127,252-256,844-850|氏名原表記とNameKeyを分離し空NULL/部分一致/不正原入力、name_key型付きbindを再現。
94|match|128,252-256,844-850|カナ表記正規化と空白除去キーを分離、空NULL/kana_key部分一致/不正原入力を再現。
95|match|129,242-248,850|任意年度int?1900～9998、クラスsmallintへ完全一致/実在検査/拒否原入力を再現。
96|match|130,242-248,850|NFKC2桁GRADE→grade_code完全一致、00と未所属別、空NULL/実在/不正拒否を再現。
97|match|131,242-248,850|任意クラス正64bit→学生class_id完全一致、NULLなし/0不可、年度と正規化学年との実値整合を再現。
98|match|132,480-487,679-718|未所属bool false→true時class_id IS NULL、所属排他/拒否、Options解除をSearch自動解除としない。
99|hold|133,155,850|空配列全区分/IN/重複拒否は正確だがN-07適用とOrdinal厳密値の原設計対実装は未裁定。0点診断の保留も残す。
100|match|134,242-248|PREFECTURE2桁正規化→prefecture_code完全一致、任意空NULL/実在/不正拒否を再現。
101|match|135,252-256|電話正規化→本人または緊急の二列完全一致、空NULL/不正原入力/保存なしを再現。
102|match|136,844-866|開始ISO10→DateOnly?→admission_date包含下端、任意片側/範囲/不正原入力を再現。表示形式不足は親項目で別判定。
103|match|137,844-866|終了ISO10→DateOnly?→admission_date包含上端、任意片側/開始≦終了/拒否を再現。
104|match|203,854-864,913|件数/開始/終了を別表示値として未検索/0件/超過を区別する意図、現行範囲移送なしを明示し算式を実装保証にしない。
105|match|176,203,866|今回SearchedAt→日本時間日時、未検索区別/DB保存なし/行を黙って落とさない表示対応を再現。
106|match|142,157,300-302|表示件数20/50/100/既定20/必須検査/SQL取得範囲、非DB保存を再現。
107|match|188,274-302,844-850|保存番号文字列を表示/文字順、照合パターンとは別、取得型/必須/行保持を再現。
108|match|189,274-304,844-850|登録氏名表記のまま移送、NameKeyとの区別/基表非NULL/行保持を再現。
109|match|190,274-304,844-850|保存カナ表記を表示、照合キーと区別/基表非NULL/行保持を再現。
110|match|191,866|dateから無時差和暦へ変換し、内部日付/表示文字列/欠損不整合を分ける。
111|match|192-193,304-312,915|年度/学年名称LEFT JOINの移送、未所属－/欠損不整合の意図と現行表示差、行保持を再現。
112|match|194-195,304-312,915|class_id経由コード/名称、未所属/停止/期間外表示の意図と現行欠落、行保持を再現。
113|match|196,304-312,915|在籍分類と値→名称、欠落でも行保持/不整合意図と実装差を再現。
114|match|197-198,304-312,915|都道府県名＋住所1のみ連結、住所2非表示/欠損不整合/行保持を再現。
115|match|199,864,915|本人電話だけ移送、null－、緊急電話を一覧へ出さず行保持を再現。
116|match|201,866|DB更新日時→日本時間西暦、保存時刻と表示値/行保持を区別して再現。
117|match|143,158,295-302|固定4ソート→許可列、末尾学生ID昇順、自由列/不正指定の拒否を再現。
118|match|144,159,295-302|asc/desc、asc既定、主列方向/ID昇順/不正拒否を再現。
119|missing|840-947|typed移送/業務長/日付/接続/状態版と関連計画は詳しいが、直接正本/開発規約の入力責務と実装工程の往復/境界試験観点の契約を一式定義しない。
'''

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

cache = {}
def read(path):
    return path.read_text(encoding='utf-8-sig').splitlines()

def ev(path, first, last=None, role='generated'):
    last = first if last is None else last
    if path not in cache:
        cache[path] = read(FROZEN / path)
    assert 1 <= first <= last <= len(cache[path]), (path, first, last)
    return {'path': 'frozen/' + path, 'startLine': first, 'endLine': last,
            'sha256': sha(FROZEN / path), 'role': role}

def spans(value):
    for fragment in value.split(','):
        pair = fragment.split('-')
        yield int(pair[0]), int(pair[-1])

selected_raw = json.loads((HERE/'selected-rows.json').read_text(encoding='utf-8-sig'))
selected = [r for r in selected_raw if r['documentId'] == DOC]
assert len(selected) == 120 and sum(r['originalPoints'] for r in selected) == 147
by_index = {r['index']: r for r in selected}
orig_lines, check_lines = read(FROZEN/ORIG), read(FROZEN/CHECK)
gen_lines = read(FROZEN/GEN)
metadata = json.loads(re.fullmatch(r'<!-- spec-meta: (.+) -->',gen_lines[0]).group(1))
assert metadata['documentId']=='SM-DET-STUDENT-SEARCH' and metadata['version']=='2.0'
chapters = {'EV-SRC-001':(151,196), 'EV-SRC-002':(197,247),
            'EV-SRC-003':(248,294), 'EV-SRC-004':(295,342),
            'EV-SRC-005':(343,381), 'EV-SRC-006':(382,430)}

def original_evidence(row):
    key = row['originalCells'][2]
    hits = [i+1 for i,line in enumerate(check_lines) if row['evaluationId'] in line]
    assert len(hits)==1
    result = [ev(CHECK,hits[0],role='original-evaluation-row')]
    if key in chapters:
        result.append(ev(ORIG,*chapters[key],role='current-original'))
    elif row['index']==0:
        result.append(ev(ORIG,14,78,role='current-original'))
    elif row['index']==1:
        result.append(ev(ORIG,27,45,role='current-original'))
    elif row['index']==119:
        result.append(ev(ORIG,540,len(orig_lines),role='current-original'))
    else:
        hits = [i+1 for i,line in enumerate(orig_lines) if '| '+key+' |' in line]
        result.append(ev(ORIG,hits[0],role='current-original') if hits else
                      ev(ORIG,118,148,role='current-original'))
    return result

rows=[]
for decision in DECISIONS.strip().splitlines():
    index_text, judgement, span_text, reason = decision.split('|',3)
    index=int(index_text); original=by_index[index]
    generated = [ev(GEN,a,b) for a,b in spans(span_text)]
    cited = {}
    for a,b in spans(span_text):
        for line in gen_lines[a-1:b]:
            for path, range_text in re.findall(r'`((?:sources|reference-designs)/[^`:\n]+):([\d,\-]+)`', line):
                for first,last in spans(range_text):
                    role = 'source' if path.startswith('sources/') else 'authorized-reference-design'
                    cited[(path,first,last)] = ev(path,first,last,role=role)
    if index in (9,99):
        cited[('status-source',111,112)] = ev('sources/Core/SqlServerStudentService.cs',111,112,role='source')
    if index==71:
        cited[('original-operation',446,456)] = ev(ORIG,446,456,role='conflicting-original-operation')
    if index==76:
        for path,a,b in [('sources/Web/Controllers/StudentsController.cs',18,19),
                         ('sources/Core/SqlServerStudentService.cs',107,108),
                         ('sources/Core/SqlServerStudentService.cs',169,170),
                         ('sources/Infrastructure/WebStudentCoordinator.cs',20,20),
                         ('sources/Infrastructure/WebPresentation.cs',23,23)]:
            cited[(path,a,b)] = ev(path,a,b,role='independent-source-contradiction-evidence')
    references=original_evidence(original)
    all_refs=generated+list(cited.values())+references
    points=original['originalPoints']
    rows.append({'index':index,'documentId':DOC,'evaluationId':original['evaluationId'],
        'targetChapter':original['originalCells'][1], 'specificationId':original['originalCells'][2],
        'viewpoint':original['originalCells'][3], 'originalPoints':points,
        'originalExpectationSha256':hashlib.sha256(original['originalCells'][4].encode('utf-8')).hexdigest(),
        'judgement':judgement,'awardedPoints':None if judgement=='hold' else points if judgement=='match' else 0,
        'diagnosticOnly':points==0,'reason':reason,
        'originalCriticalClassification':original['criticalClassification'],
        'criticalGeneratedContradiction':False,
        'criticalReason':'HTTP状態の図/ソース矛盾を記録するが認可許可・業務書込み・確定保証を捏造する重大矛盾ではない。' if index==76 else '現版に根拠のない重要制約保証の捏造は確認しない。',
        'originalQualityJudgement':'hold_reference_adjudication' if judgement=='hold' else 'not_scored_in_this_reproduction_review',
        'originalQualityAwardedPoints':None,
        'referenceReproductionJudgement':judgement,
        'sourceFidelity':'DIAGRAM_SOURCE_AND_PROSE_CONTRADICTION' if index==76 else 'SOURCE_AND_DESIGN_INTENT_SEPARATED',
        'semanticReview':'INDEPENDENT_NEW_VERSION_2_0_FULL_TEXT_AND_TARGET_ROW_REVIEW',
        'oldMatchReused':False,'evidence':all_refs})

assert len(rows)==120 and [r['index'] for r in rows]==list(range(120))
assert len({r['evaluationId'] for r in rows})==120
counts=collections.Counter(r['judgement'] for r in rows)
earned=sum(r['awardedPoints'] or 0 for r in rows)
missing=sum(r['originalPoints'] for r in rows if r['judgement']=='missing')
conflict=sum(r['originalPoints'] for r in rows if r['judgement']=='conflict')
held=sum(r['originalPoints'] for r in rows if r['judgement']=='hold')
assert earned+missing+conflict+held==147
manifest=json.loads((HERE/'frozen-manifest.json').read_text(encoding='utf-8-sig'))
input_manifest=json.loads((HERE/'frozen-input-manifest.json').read_text(encoding='utf-8-sig'))
snapshot=json.loads((HERE/'student-search-snapshot.json').read_text(encoding='utf-8-sig'))
assert len(manifest['pins'])==110 and len(input_manifest['pins'])==78 and len(snapshot['pins'])==16
for pin in manifest['pins']:
    assert sha(FROZEN/pin['snapshotPath'])==pin['sha256'], pin['snapshotPath']
job=FROZEN/'provenance/jobs/488af9821732c8f6'
draft=json.loads((job/'draft-result.json').read_text(encoding='utf-8-sig'))
assert draft['contentSha256']==sha(FROZEN/GEN)==snapshot['generatedSha256']
published=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-02/spec/detail/student-search.md'
assert sha(published)==sha(FROZEN/GEN)
summary={'judgementCounts':dict(counts),'originalRows':120,'positiveRows':71,'zeroDiagnosticRows':49,
         'originalMaximum':147,'confirmedAwardedPoints':earned,'missingPoints':missing,
         'conflictPoints':conflict,'unearnedPoints':missing+conflict,'pendingPoints':held,
         'completeScore':None,'completePercent':None,'passed95':None,
         'criticalGeneratedContradictions':0,'generatedNonCriticalContradictions':1,
         'status':'WITHHELD_PENDING_REFERENCE_SOURCE_ADJUDICATION'}
result={'schema':'semantic-detail-evaluation/2.0','classification':'EVALUATOR_ONLY','generatorMayRead':False,
        'evaluator':'/root/evaluation_inventory','evaluatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),
        'projectId':'test-project1','profile':'CSharp_ASPNET','mode':'training-assisted',
        'iteration':'20261013-focus-round-02','attempt':'focus-round-02-attempt-02','documentId':DOC,
        'generatedVersion':'2.0','originalSpecificationVersion':'8.0','evaluationVersion':'7.4',
        'generatedPath':'frozen/'+GEN,'generatedSha256':sha(FROZEN/GEN),
        'originalSpecificationSha256':sha(FROZEN/ORIG),'evaluationChecklistSha256':sha(FROZEN/CHECK),
        'frozenManifestSha256':sha(HERE/'frozen-manifest.json'),
        'inputManifestSha256':sha(HERE/'frozen-input-manifest.json'),
        'candidateSnapshotSha256':sha(HERE/'student-search-snapshot.json'),
        'selectedRowsFileSha256':sha(HERE/'selected-rows.json'),
        'sourceCapsuleManifestSha256':manifest['sourceCapsuleManifestSha256'],
        'sourceFiles':43,'authorizedReferenceFiles':11,'runtimeAtLaunchFiles':13,
        'oldMatchScoresReused':False,'originalPointsChanged':False,'denominatorReduced':False,
        'diagnosticRowsRetained':True,'generationBindingScope':manifest['generationBindingScope'],
        'pinVerification':{'unionPinsVerified':110,'inputPins':78,'candidatePins':16,'mismatches':0},
        'provenance':{'job':'488af9821732c8f6','draftResultSha256':sha(job/'draft-result.json'),
                      'analysisVerifiedSha256':sha(job/'analysis-verified.json'),
                      'draftPromptSha256':sha(job/'draft/prompt.txt'),
                      'analysisPromptSha256':sha(job/'analysis/prompt.txt'),
                      'draftContentMatchesPublishedMd':True,
                      'relatedDocumentPlanIndexSupplied':True,
                      'wholePlanAndSafeFeedbackObservedInActualPrompt':True,
                      'runtimeFrozenAtLaunch':True,'laterProductionScopeChangesAttributed':False},
        'scoringPolicy':['全120原行と新本文を再読した新規意味判定。機械は算術/ID/ハッシュ/証拠範囲のみを処理。',
                        '図、参照先、複数章、明示した設計意図の意味を組み合わせる。語句/図存在だけの一致は不可。',
                        '未実装設計意図を正しく分離した記述は再現に含めるが実装/DB成功の証明にはしない。',
                        '1点は属性一式。基表とJOIN NULL、業務長と容量、rawとDTOと正規化を区別。',
                        '図の明示HTTP状態誤りは正しい本文でも打ち消さずFLOWをconflict。別結果説明を重複減点しない。',
                        '原仕様/実装または原仕様内の正解未裁定はhold/null、元147点と全診断行を保持。'],
        'summary':summary,'rows':rows,
        'notPerformed':['実装ビルド/実機/実DB試験','原仕様品質軸の全体採点',
                        'この採点による独立HTML/PDF/Excelレンダリング検査','他の文書/1408点全体の採点']}
(HERE/'search-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Focus round 02 学生検索 独立意味評価','','EVALUATOR ONLY — generation入力不可。','',
    f"生成2.0 SHA256 `{result['generatedSha256']}`。原仕様8.0／採点表7.4。",
    'source43・許可reference11・起動runtime13・新raw prompt/result/answer/schemaを固定。旧採点転用なし。',
    f'全120行（有配点71＋診断49）、観測一致{earned}/147点、不足{missing}点、矛盾{conflict}点、保留{held}点。',
    '重大矛盾0件、非重大の図/ソース/本文矛盾1件。完了得点・完了率・95%判定はnull。','',
    '図009は状態拒否とサービスValidationFailedを409固定へ併合し、実際の422と本文579に矛盾する。',
    'FLOW原3点をconflictとし、結果説明固有の正しい対応状態を同じ誤りで二重減点しない。',
    '残る有配点不足は概要の描画画像/正本責務、全画面配置、日付表示層、実装工程の試験/開発入力責務。',
    '在籍配列正規化と候補ER/人数操作の矛盾は原基準の要裁定として全行を残す。','',
    '| index | 評価ID | 配点 | 判定 | 加点 | 所見 |','| --- | --- | ---: | --- | ---: | --- |']
for r in rows:
    value='null' if r['awardedPoints'] is None else str(r['awardedPoints'])
    md.append(f"| {r['index']} | {r['evaluationId']} | {r['originalPoints']} | {r['judgement']} | {value} | {r['reason']} |")
md+=['','各行の現版生成/ソース/許可参考設計/原本/採点行のSHAと行範囲はJSONに保存。',
     'このbuilderは新規手判定の保存と検証のみで、期待セルをgenerationへ渡さず原稿を組み立てない。','']
(HERE/'search-evaluation.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
