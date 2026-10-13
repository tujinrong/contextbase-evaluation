"""Materialize NEW human semantic decisions; never infer credit from keywords.

All 120 decisions below were made after rereading the frozen round-01 MD.
The builder checks evidence/pins and arithmetic only. No old score input exists.
"""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
FROZEN = HERE / "frozen"
DOC = "DET-CSharp_ASPNET-SCR-STU-001"
GEN = "generated/spec/detail/student-search.md"
ORIG = "current-reference/test-project1/srcs/CSharp_ASPNET/spec/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md"
CHECK = "evaluation/test-project1/spec-eval/checklists/DET-CSharp_ASPNET-SCR-STU-001.md"

# index | judgment | generated evidence ranges | independent semantic finding
DECISIONS = """
0|missing|14-90,892-896|機能責務・読取IO・メモリを説明しているが、共用契約/DB定義/開発規約との正本責務と画像併記の契約を満たさない。draft自身も関連計画ID未供給を記録。
1|missing|49-90,888-890|描画可能な現行ソースの静的HTMLは存在する。ただし参考設計画面のメニュー・表示範囲・先頭/最後操作の配置を再現せず、差分表の語句のみで画面対応一式を代替できない。
2|match|96,824-830,711-715|番号raw/正規化15、任意、番号形式、前方一致、保存なし、varchar15非NULLとSize31を区別して再現。
3|match|97,824-830,711-715|氏名raw8と照合キー160、保存表記との区別、部分一致、nvarchar320非NULLとSize642を再現。
4|match|98,824-830,711-715|カナraw36/表記18/空白除去キー、任意、部分一致、nvarchar36非NULLとSize74を再現。
5|match|99,122,685-707|年度任意・1900から9998・実在年度候補・一致条件・smallint非NULL・入力との型境界を再現。
6|match|100,123,685-707,830|2桁学年・GRADE分類・停止検索可・未所属と00の区別・varchar2非NULLを再現。
7|match|101,124,685-707|19桁正Int64・任意・実在/上位一致・学生class_id bigint NULL・IDと表示名の区別を再現。
8|match|102,320,520-558|未所属真偽・false初期・所属3条件排他・NULL判定・専用保存列なしを再現。
9|hold|103,125,830|原仕様は配列にN-07を指定するが実装はOrdinalで01から04を厳密照合しNFKCしない。新版は実装を正確に記すがこの設計変換の適用を裁定しない。重複/上限/空配列の意味は確認済み。
10|match|104,126,685-707|都道府県raw2・NFKC/ASCII2桁・PREFECTURE存在・停止許容・任意・varchar2非NULLを再現。
11|match|105,166,711-715|電話raw20/保存16・空条件なし・NFKC等・本人OR緊急完全一致・二列varchar16 NULLを再現。
12|missing|106,850-852,681-683|開始任意・ISO10入力・1900から業務日・片側/両端順序・date非NULL・Dateバインド・開始を含むは再現するが、入力ISOと区別した西暦表示形式の設計意図がない。ネイティブdate inputの説明を誤りとせず属性一式不足とする。
13|missing|107,850-852,681-683|終了任意・開始と同じ形式/範囲・開始以下拒否・date非NULL・Dateバインド・終了を含むは再現するが、入力ISOと区別した西暦表示形式の設計意図がない。
14|match|108,241-308|検索受付・現在入力検査・1ページ目・成功時のみ保持・業務DB書込みなしを再現。
15|match|110,421-463|クリアはメモリ条件/結果を消去し初期値/未検索へ戻る。DB DELETEとは区別して再現。
16|match|111,560-603|新規リンクはViewer非表示・入口権限確認・検索値を登録へ流用しない・遷移先責務を再現。
17|missing|108-116,888|メニューという差分名だけで、共通メニューへの戻り操作/イベント/責務を定義していない。現行ソースにないことは正しく説明。
18|missing|146,170,834-844,888|件数0から10000・未検索/超過/0件を区別するが、開始/終了位置の意味と範囲0から10000の表示定義がない。
19|match|146,170,850|サービス実行時刻・日本時間yyyy/MM/dd HH:mm:ss・未検索・保存値と表示の区別を再現。
20|match|112,127,360-419|20/50/100・既定20・入力制御/SQL取得指定・変更時1ページ・非DB保存を再現。固定候補により最大3桁が確定。
21|match|157,96,759|保存番号varchar15非NULL・15以内・文字順・検索パターンとの区別を再現。
22|match|158,826|表示氏名nvarchar16非NULLと業務8スカラー、登録表記と照合キーの区別を再現。
23|match|159,826|表示カナnvarchar36非NULLと業務18スカラー、キーと表記の区別を再現。
24|match|160,850-852|内部date非NULLから和暦表示、元年/2桁月日、時差を加えない・入力なしを再現。
25|missing|99,161-162,888|年度範囲/結合NULL/学年名称取得を説明するが名称の業務12スカラー上限がない。nvarchar24容量で代替しない。
26|missing|163,846,888|クラスコード9・nvarchar36非NULL・結合欠損/状態差を説明するが名称18スカラー業務上限がない。
27|missing|164,731-771|分類と値のLEFT JOIN・nvarchar24非NULL・名称欠損でも行保持を説明するが名称12スカラー業務上限がない。
28|missing|165,846|住所1業務45/容量90・都道府県名連結・住所2非表示を説明するが都道府県名称12スカラー業務上限がない。
29|match|166,105,846|本人電話のみ・varchar16 NULL・nullは－・緊急電話は検索対象だけを再現。
30|match|168,850|更新日時datetimeoffset7非NULL・日本時間19文字表示を再現。
31|match|116,156,560-603|行番号ではなく管理ID・long/bigint・入口最新再取得/存在/権限・参照と編集の切替を再現。
32|match|115,360-419,761,888|現行前後/反映と有効ページ補正を詳述し、先頭/最後は参考設計意図として区別。非DBの表示指定を再現。
33|match|113,128,752-761|固定4ソート・既定番号・入力とORDER BY許可列の分離・末尾ID昇順・保存なしを再現。列挙値から上限13が確定。
34|match|114,129,759|小文字asc/desc・既定asc・非DB指定・サービス検査を再現。列挙値から最大4が確定。
35|missing|122,568-573|検索年度の順序/停止過去/空値は記すが候補診断一式に含む登録当年度選択補助の説明がない。
36|missing|123,880|検索学年・停止/期間無制限・順序/00は記すが登録の新規有効値と既存値別枠保持の候補契約を記さない。
37|missing|124,880|検索クラスの現在表示/抽出/順序/解除を記すが参考候補の学年名称・登録所属の3区分の定義が不足。
38|missing|125,103|検索の01/02初期・全解除・許可4値は記すが保護コードの意味と登録新規有効値/既定01が不足。
39|missing|126|検索の都道府県候補は詳しいが登録新規有効値/既存同値保持の契約が不足。
40|match|112,127,362-375|固定20/50/100順・20初期・変更時1ページ・コードマスタではないを再現。
41|match|113,128,752-759|固定4キーの表示と順序・番号初期・自由DB列不可を再現。
42|match|114,129|固定asc/desc順・表示・asc初期を再現。
43|missing|146,170,834-844|件数の非負/成功/未検索/超過/上限を再現するが診断束にある0件範囲0から0がない。
44|missing|131-172,834-844,888|開始位置の非負型/5桁/0件0/成功設定を定義していない。単に表示範囲という設計意図だけ。
45|missing|131-172,834-844,888|終了位置の非負型/5桁/0件0/成功設定を定義していない。
46|match|99,161,888|年度int?・4桁範囲・クラス取得元・未所属－の設計意図と現行差を再現。
47|missing|162,888|学年名称string?/コード名称取得元と未所属差は説明するが12スカラー上限がない。
48|match|163,731-771,888|クラスコードstring?・9桁取得元・結合欠損でも行を落とさない・未所属の意図を再現。
49|missing|163,731-771|クラス名称の型/取得元/結合欠損は説明するが18スカラー上限がない。
50|match|106,160,850-852|必須DateOnlyの内部birth_date・ISO日付境界・和暦移送・無時差を再現。
51|match|101,116,156,568-573|正Int64/19桁・新規対象なし・既存DB採番/行/route・権限と存在再確認を再現。
52|match|135-141,178-194,887|状態IDは32バイト乱数64hex、主体/セッション/タブ/期限30分と非空Tabのみという実装差を再現。
53|missing|178-184|POST偽造防止の基盤検査は記すがopaque値/実値長は基盤決定事項/認可や再送制御の代替でないという診断束が不足。
54|match|524-558,184|初期非処理中・submit時の別ボタン非活性/aria-busy・DB排他とは別でソースの抑止限界を正しく再現。
55|missing|558,882|旧候補応答破棄の意図と要求連番未実装は記すが非負整数/初期0/桁あふれ採番停止の内部契約を定義しない。
56|match|202,206-213,178-184,888|認証済み起動・学生一覧取得なし・候補取得・メニューの設計/現行差を再現。
57|match|206-213,135-150,850,879,887|初期値・候補・状態発行/復帰・業務日時を説明。必須マスタ不足停止と応答照合を設計意図として実装と区別。
58|match|217-226,239,879|認証拒否/候補/未検索の図と必須マスタ不足停止の意図を組み合わせ、ソースに該当停止分岐がないことも明記する。図の存在だけではなく分岐意味を照合。
59|match|231,775-818|候補分類コード/学年クラスの関連・複合分類値・FKと読取JOIN/非削除連動を区別して再現。
60|match|235,773-803|候補コードとクラスをSNAPSHOT二結果セットで取得し操作順と抽出/移送を詳述。表番号綴りは評価しない。
61|match|239,306-308,854-884|初回は未検索/候補障害拒否、検索局所失敗と0/超過、所有権拒否、候補だけの非再検索を適用イベントごとに再現。
62|match|245,713-761|入力条件による非削除学生検索・業務DB読取りのみを再現。
63|missing|249-258,135-145,558,882,887|複製・検証・同一検索SNAPSHOT・上限/0/初頁・保持・日付表示は説明するが、検索結果応答そのものが最新要求である確認の設計契約が候補応答だけに限定され不足。
64|match|264-294,306,160,834-852|入力/存在失敗・件数超過・同一読取り単位のページ経路の図を、0件emptyと日付表示の明示仕様と併せて意味照合。
65|match|298,763-771,805-818|学生/クラス/学年/在籍/都道府県の用途alias・複合キーLEFT JOIN・NULL多重度・書込非対象を再現。
66|match|302,685-761|指定マスター確認→TOP10001件数→同条件ページ取得・typed bind・commitを再現。
67|match|306-308,834-844,854-884|入力保持/一覧消去の設計意図と局所適用限界、0件/超過区別、所有/版拒否、候補非再検索を再現。
68|match|314,320-323,520-558|所属条件連動と候補更新、まだ学生を検索しないを再現。
69|match|318-323,352-358,880-882|未所属解除/非活性/OFF非復元、不適合解除/通知、上位補完/古い応答破棄の設計意図、未反映とApplied保持を現行差付きで再現。
70|match|329-344,524-558,880-882|未所属分岐・候補取得・不適合解除/未反映の図と旧応答破棄の意図を組み合わせて意味照合。
71|hold|348-352,773-803|原ERはoccupancy付き学生関連だが原DB操作は検索で学生人数集計しない。実装Lookup(false)もOccupied=0。新版は未集計値と正確に記し、原仕様内のER/操作矛盾の正解を決めない。
72|match|348-352,773-803|クラス候補参照・上位条件による画面絞込み・業務書込/学生検索/人数集計なしを再現。
73|match|354-358,854-884|条件原入力と既存一覧・非再検索、所有/期限拒否、検証/検索の対象外結果、実装未検査の差を明示。
74|match|364-376|Applied由来の結果を別順序/ページで再取得、未実行値を混ぜないを再現。
75|match|366-375,415-419,885-887|状態/期限/版、許可表示指定、変更時1頁、同条件再検索/最終補正、0件非活性、設計期限初期化との差を再現。
76|match|380-405,184,885-886,759-761|保持条件有無/拒否・許可検索条件・件数/ページ補正・全体順序取得の図と明示した共通検査を意味照合。
77|match|409-411,763-771,805-818|ページも同じ学生/クラス/用途別コードLEFT JOINとFK/読取関係を参照し再現。
78|match|411,711-771|件数→ページ同条件の実行、補正再検索、typed offset/sizeと順序を再現。
79|match|415-419,834-844,854-884|ページはAppliedを保持し、局所拒否/共通障害/0/超過/候補のみ非再検索という該当結果を再現。
80|match|425,564,605-609|新規/行/クリア等の画面操作受付を独立イベントで再現。
81|missing|429-463,568-603,888|新規権限/値非流用、ID読込は遷移先、クリア状態初期化は再現するが、メニューへの戻り手順は差分名だけで操作契約を定義していない。
82|missing|440-451,579-590,888|新規/既存/クリアのフローはあるがメニューへの遷移経路は図にも手順にもなく、差分表の話題名だけでは操作分岐意味が不足。
83|match|453-459,595-603|検索画面の遷移/状態操作に業務DB ERを作らず、遷移先LoadのDB読取と候補再描画を別責務に分類。原非適用0点を保持。
84|match|455-459,595-603,892-896|遷移とメモリClearに業務DB更新なし・遷移先Loadと再描画候補読取を区別して再現。
85|match|459-463,599-603,854-884|操作対象の権限/未存在/版/候補障害と入力/0件/超過の発生対象を混同せず再現。
86|match|469,603,609,671-673|登録保存/削除Savedまたは取消/戻るから元検索状態復元、成功以外の非自動帰還を再現。
87|match|473-478,508-514,613-621,885-887|所有/期限/版・未検索復元・元条件の最新DB再検索・条件非変更・確定成功通知・期限初期化意図と実装拒否の差を再現。
88|match|484-500,508-514,625-642,885|所有/期限拒否、検索済み分岐、元条件再検索、通知移送のフローを再現。初期化は設計意図として別記。
89|match|504,763-771,805-818|復帰時も一覧読取関連を共通参照し用途alias/複合分類値/NULLを再現。
90|match|508,711-771|元Appliedの件数とページ再取得、同じ検索SQL・条件非変更、SQL用ページ補正を再現。
91|match|512-514,671-673,854-884|復帰拒否/失敗・成功通知の確定と消費・0/超過/未検索・元条件維持を区別して再現。
92|match|96,711-715,824-830|番号raw→正規化→student_no前方一致・NULL条件なし・保存なし・拒否原入力を再現。
93|match|97,711-715,824-830|氏名raw8→NameKey160→name_key部分一致・表記別・NULL条件なし・拒否原入力を再現。
94|match|98,711-715,824-830|カナ正規化/空白除去照合キー→kana_key部分一致・NULL条件なし・拒否原入力を再現。
95|match|99,685-707|年度任意/int?/smallint・実在範囲/完全一致・不正拒否を再現。
96|match|100,830,685-707|NFKC2桁GRADE→grade_code完全一致・00と未所属別・空なし/拒否を再現。
97|match|101,685-707|Optional正Int64→学生class_id完全一致・NULL任意・年度学年実値一致・不正拒否を再現。
98|match|102,320,520-558|未所属true→class_id IS NULL・false初期・所属条件排他/不正拒否を再現。
99|hold|103,125,830|在籍配列N-07の適用は原設計とOrdinal厳密実装の要裁定。空配列/複数IN/重複拒否は再現済み。0点診断も保留を隠さない。
100|match|104,685-707|PREFECTURE正規化2桁→prefecture_code完全一致・任意NULL・存在/拒否を再現。
101|match|105,711-715|正規化電話→本人または緊急二列完全一致・NULL条件なし/拒否を再現。
102|match|106,850-852|ISO10→DateOnly?→admission_date下端を含む・任意片側・範囲/拒否を再現。
103|match|107,850-852|ISO10→DateOnly?→admission_date上端を含む・任意片側・開始以下拒否を再現。
104|missing|170,834-844,888|件数と各結果状態は定義済みだが開始/終了位置の計算と表示移送はない。
105|match|146,170,850|SearchedAtの今回サービス時刻→日本時間表示・非DB保存・未検索区別を再現。
106|match|112,127,759-761|固定表示件数の入力/既定/検査/SQL範囲・非DB保存を再現。
107|match|157,759,826|保存番号を文字列表示/文字順・照合パターンを転用しない・行を黙って落とさないを再現。
108|match|158,826|登録表記のStudentName→表示・NameKeyと区別・非NULLDDL/行保持を再現。
109|match|159,826|保存表記カナ→表示・KanaKeyと区別・行保持を再現。
110|match|160,850-852|birth_date内部日付→無時差和暦表示・表示項目/原値分離を再現。
111|match|161-162,763-771,846,888|年度/学年名称のLEFT JOIN移送と未所属－の意図、現行欠損表示差/行保持を再現。
112|match|163,763-771,846,888|class_id→コード/名称のLEFT JOIN移送、未所属/停止/期間外表示の意図と現行注記欠落を再現。
113|match|164,763-771|分類と値→在籍名、名称欠落でも学生行を除外しないを再現。
114|match|165,731-771,846|都道府県名+住所1のみ連結・住所2なし・欠損[不整合]・行保持を再現。
115|match|166,846|本人電話のみ移送・null－・緊急電話非表示を再現。
116|match|168,850|DB更新日時→日本時間西暦表示・保存元と表示値を分離して再現。
117|match|113,128,752-761|固定4ソート→許可列・最後のID昇順・不正拒否を再現。
118|match|114,129,759|asc/desc・asc既定→主列方向・不正拒否を再現。
119|missing|820-896|移送/型/長さ/接続/状態版の説明は詳しいが開発入力の正本責務・共用仕様/DB/開発規約との参照契約と実装工程の試験観点を定義していない。
"""

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return path.read_text(encoding="utf-8-sig").splitlines()

cache = {}
def evidence(path, first, last=None, role="generated"):
    last = first if last is None else last
    physical = FROZEN / path
    if path not in cache:
        cache[path] = read(physical)
    assert 1 <= first <= last <= len(cache[path]), (path, first, last)
    return {"path": "frozen/" + path, "sha256": sha(physical),
            "startLine": first, "endLine": last, "role": role}

def ranges(text):
    result=[]
    for fragment in text.split(","):
        pair = fragment.split("-")
        result.append((int(pair[0]), int(pair[-1])))
    return result

selected = json.loads((HERE / "selected-rows.json").read_text(encoding="utf-8-sig"))
selected = [r for r in selected if r["documentId"] == DOC]
assert len(selected) == 120 and sum(r["originalPoints"] for r in selected) == 147
by_index = {r["index"]: r for r in selected}
original_lines, checklist_lines = read(FROZEN / ORIG), read(FROZEN / CHECK)
generated_lines = read(FROZEN / GEN)

# Hand selected event chapter evidence, not automatic outcome classification.
EVENT_CHAPTER = {"EV-SRC-001":(151,196), "EV-SRC-002":(197,247),
 "EV-SRC-003":(248,294), "EV-SRC-004":(295,342),
 "EV-SRC-005":(343,381), "EV-SRC-006":(382,430)}

def original_evidence(row):
    index, key = row["index"], row["originalCells"][2]
    matches = [i+1 for i,line in enumerate(checklist_lines) if row["evaluationId"] in line]
    assert len(matches) == 1
    refs = [evidence(CHECK,matches[0],role="frozen-evaluation-row")]
    if key in EVENT_CHAPTER:
        refs.append(evidence(ORIG,*EVENT_CHAPTER[key],role="current-original"))
    elif index == 0:
        refs.extend([evidence(ORIG,14,78,role="current-original")])
    elif index == 1:
        refs.append(evidence(ORIG,27,45,role="current-original"))
    elif index == 119:
        refs.append(evidence(ORIG,540,len(original_lines),role="current-original"))
    else:
        token = "| " + key + " |"
        hits=[i+1 for i,line in enumerate(original_lines) if token in line]
        if hits:
            refs.append(evidence(ORIG,hits[0],role="current-original"))
        else:
            # Candidate keys occur as human row labels within this original table.
            refs.append(evidence(ORIG,118,148,role="current-original"))
    return refs

rows=[]
for line in DECISIONS.strip().splitlines():
    index_text, judgment, span_text, reason = line.split("|",3)
    index=int(index_text)
    row=by_index[index]
    spans=ranges(span_text)
    refs=[evidence(GEN,a,b) for a,b in spans]
    source_refs={}
    for a,b in spans:
        for generated_line in generated_lines[a-1:b]:
            for path,start,end in re.findall(r"`(sources/[^`:\n]+):(\d+)-(\d+)(?:,[^`]*)?`",generated_line):
                entry=evidence(path,int(start),int(end),role="source")
                source_refs[(path,int(start),int(end))]=entry
    # Explicitly verify DDL business length omissions rather than assume capacity.
    if index in (25,27,28,47):
        e=evidence("sources/database/001_schema.sql",113,128,role="source")
        source_refs[(e["path"],113,128)]=e
    if index in (26,49):
        e=evidence("sources/database/001_schema.sql",63,81,role="source")
        source_refs[(e["path"],63,81)]=e
    if index in (9,99):
        e=evidence("sources/Core/SqlServerStudentService.cs",111,112,role="source")
        source_refs[(e["path"],111,112)]=e
    refs.extend(source_refs.values())
    refs.extend(original_evidence(row))
    if index==71:
        refs.append(evidence(ORIG,446,456,role="conflicting-original-operation"))
    source_fidelity="SUPPORTED_WITH_EXPLICIT_IMPLEMENTATION_DESIGN_SEPARATION"
    rows.append({"documentId":DOC,"index":index,"evaluationId":row["evaluationId"],
      "targetChapter":row["originalCells"][1],"specificationId":row["originalCells"][2],
      "viewpoint":row["originalCells"][3],"originalPoints":row["originalPoints"],
      "originalExpectationSha256":hashlib.sha256(row["originalCells"][4].encode("utf-8")).hexdigest(),
      "judgement":judgment,"awardedPoints":None if judgment=="hold" else row["originalPoints"] if judgment=="match" else 0,
      "reason":reason,"originalExpectationApplicability":"HOLD_REFERENCE_CONFLICT" if judgment=="hold" else "APPLICABLE",
      "originalQualityJudgement":"hold" if index in (9,71,99) else "not_fully_scored",
      "originalQualityAwardedPoints":None,"sourceFidelity":source_fidelity,
      "criticalConstraint": index in (9,51,52,53,54,55,63,65,69,75,81,87,99,119),
      "criticalGeneratedContradiction":False,"evidence":refs})

assert len(rows)==120 and [r["index"] for r in rows]==list(range(120))
assert len({r["evaluationId"] for r in rows})==120
counts=collections.Counter(r["judgement"] for r in rows)
confirmed=sum(r["awardedPoints"] or 0 for r in rows)
missing=sum(r["originalPoints"] for r in rows if r["judgement"]=="missing")
pending=sum(r["originalPoints"] for r in rows if r["judgement"]=="hold")
assert confirmed+missing+pending==147

manifest=json.loads((HERE/"frozen-manifest.json").read_text(encoding="utf-8-sig"))
for pin in manifest["pins"]:
    assert sha(FROZEN/pin["snapshotPath"])==pin["sha256"],pin["snapshotPath"]
job=FROZEN/"provenance/jobs/488af9821732c8f6"
draft=json.loads((job/"draft-result.json").read_text(encoding="utf-8-sig"))
assert draft["contentSha256"]==sha(FROZEN/GEN)
summary={"judgementCounts":dict(counts),"originalRows":120,"positiveRows":71,
  "zeroDiagnosticRows":49,"originalMaximum":147,"confirmedAwardedPoints":confirmed,
  "missingPoints":missing,"pendingPoints":pending,"completeScore":None,
  "completePercent":None,"criticalGeneratedContradictions":0,
  "status":"WITHHELD_PENDING_REFERENCE_SOURCE_ADJUDICATION"}
result={"schema":"semantic-detail-evaluation/1.0","classification":"EVALUATOR_ONLY",
 "generatorMayRead":False,"evaluator":"/root/evaluation_inventory",
 "evaluatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),"projectId":"test-project1",
 "profile":"CSharp_ASPNET","mode":"training-assisted","iteration":"20261013-focus-round-01",
 "documentId":DOC,"generatedVersion":"1.0","originalSpecificationVersion":"8.0",
 "evaluationVersion":"7.4","generatedPath":"frozen/"+GEN,"generatedSha256":sha(FROZEN/GEN),
 "originalSpecificationSha256":sha(FROZEN/ORIG),"evaluationChecklistSha256":sha(FROZEN/CHECK),
 "frozenManifestSha256":sha(HERE/"frozen-manifest.json"),"selectedRowsFileSha256":sha(HERE/"selected-rows.json"),
 "sourceCapsuleManifestSha256":manifest["sourceCapsuleManifestSha256"],
 "sourceFiles":43,"authorizedReferenceFiles":11,"oldMatchScoresReused":False,
 "originalPointsChanged":False,"denominatorReduced":False,"diagnosticRowsRetained":True,
 "generationBindingScope":manifest["generationBindingScope"],
 "generationReviewStatusAtFreeze":"AI_DRAFT_NOT_YET_INDEPENDENTLY_REVIEWED",
 "provenance":{"job":"488af9821732c8f6","draftResultSha256":sha(job/"draft-result.json"),
  "analysisVerifiedSha256":sha(job/"analysis-verified.json"),"draftPromptSha256":sha(job/"draft/prompt.txt"),
  "draftContentMatchesPublishedMd":True,"relatedDocumentPlanIndexSupplied":False},
 "scoringPolicy":["全120原行を新本文で再読し新規に意味判定。機械は算術/ID/証拠ハッシュだけを処理。",
  "当該文書内の図/参照先/複数章/明示した設計意図を組み合わせる。見出し/図/語句だけでは一致としない。",
  "設計意図を実装保証と混同しない正しい併記は再現に含める。実装やDBの成功を意味しない。",
  "画面配置そのものは対象操作/表示との対応を確認する。単なる未実装差分名だけでは配置一式を補完しない。",
  "1点は属性一式。DTO nullable/SQL param Size/物理容量で実DB NULL/業務長を代替しない。",
  "正解未裁定の原仕様/ソース矛盾はhold/null。ゼロ点診断と元147点を保持。",
  "一致だけ加点。原品質軸の全面採点は未実施。未裁定があるため完了率/95判定はnull。"],
 "summary":summary,"rows":rows,
 "notPerformed":["実装ビルド/実機/実DB試験","原仕様品質軸の全体採点",
  "この採点によるHTML/PDF/Excelの独立レンダリング検査","他の文書/1408点全体の採点"]}
(HERE/"search-evaluation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
md=["# 新規 focus round 01 学生検索 意味評価", "", "EVALUATOR ONLY — generation 入力不可。", "",
 f"新本文SHA256 `{result['generatedSha256']}`。原仕様8.0／採点表7.4／生成1.0。",
 "source 43件・利用者承認reference 11件・候補本文・原仕様・配点行・生成prompt/resultを同じ95-pin凍結で照合した。",
 "旧match/合格の転用なし。全120行（71有配点＋49診断）を新本文で再読した。", "",
 f"観測一致 {confirmed} / 147点、欠落 {missing}点、要裁定 {pending}点。重要な生成矛盾0件。",
 "完了得点・完了率・95%判定はnull。これは検索1文書の部分実測である。", "",
 "判定は意味単位。図の分岐は参照先と明示した設計意図も併せ、字面/番号/図存在だけでは採点していない。",
 "画面構成は本文の設計差分表だけでは未描画の操作配置を補完しない。未実装設計意図を現行動作と偽装していない。", "",
 "主な不足は画面の設計対応、名称の業務長、表示範囲、検索応答の最新要求確認、共用文書と実装試験の責務。",
 "在籍配列の正規化と候補ERのoccupancy関係は原基準/実装または原基準内の要裁定。全原行を残す。", "",
 "## 行別判定", "", "| index | 評価ID | 配点 | 判定 | 加点 | 所見 |", "| --- | --- | ---: | --- | ---: | --- |"]
for row in rows:
    value="null" if row["awardedPoints"] is None else str(row["awardedPoints"])
    md.append(f"| {row['index']} | {row['evaluationId']} | {row['originalPoints']} | {row['judgement']} | {value} | {row['reason']} |")
md += ["", "各行の生成/原本/採点表/ソースのSHA256付き行範囲は search-evaluation.json に記録。",
 "build_search_evaluation.py はこの手判定の保存・証拠参照・算術だけを行い、AI原稿の組立てやキーワード採点を行わない。", ""]
(HERE/"search-evaluation.md").write_text("\n".join(md),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False))
