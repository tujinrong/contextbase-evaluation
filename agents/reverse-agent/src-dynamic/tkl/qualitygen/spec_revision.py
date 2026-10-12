"""Reviewed event contracts; product facts stay separate from engine rules."""
from __future__ import annotations
import json

EVENT_CONTRACT={
 'contract_scope':'pilot_event_revision','version':'1.0','feature':'TKL-011',
 'guarded_events':['rate','discount','book'],
 'unguarded_events':['calculate','minus','price','postal'],
 'rate_conversion':'binary32_model_then_to_even_integer_argument',
 'rate_effects':['update_binding_source','discount','unit','amount'],
 'discount_effects':['update_binding_source','unit','amount'],
 'calculate_effects':['amount_only'],
 'minus_effects':{'false':{'quantity':1,'maxlength':3,'style':'txt--money'},'true':{'quantity':-1,'maxlength':4,'style':'txt--money_minus'}},
 'book_empty':'reset_price_fields_and_quantity_in_both_modes',
 'book_selected_add':'reset_quantity_then_price',
 'book_selected_edit':'preserve_quantity_then_price',
 'price_priority':['conditional','base'],'base_discounts':'new_price_model_defaults',
 'missing_sales_kind':None,'postal':{'lengths':[3,4],'trim_lookup_arguments':True,'rewrite_postal_fields':False,'no_match':'preserve_address'},
 'binding_boundary':'source_already_updated_in_fixture; UpdateSource call counted; actual WPF timing not simulated',
 'tested_event_ids':['txtReducePercent_LostFocus','txtDiscount_LostFocus','btnCalc_Click','chkMinus_Click','cmbBook_SelectionChanged','btnPrice_Click','txtPostalno_LostFocus']
}

EXPLANATIONS=[
 ('値引率の入力確定','監視中だけ入力値の受渡しを更新する。保持情報の値引率は小数を保持できるが、共通の値引額計算へ渡す引数は整数である。その境界で整数へ偶数丸めした率を使い、次に金額の端数を偶数丸めする。率を小数のまま計算する処理とは区別する。通常のキーボード入力は共通入力部品にも制限されるため、モデルへ注入した小数の試験を画面入力の許容証明としない。','保持率10.5%、定価1,000円の場合、計算引数10%、値引額100円。保持率11.5%は計算引数12%、値引額120円。保持値自体を書き換える処理ではない。'),
 ('値引額の入力確定','監視中は入力値の受渡しを更新し、定価から直接入力した値引額を引き、数量を乗じて請求金額を更新する。値引率の再計算と価格マスタ照会は行わない。監視停止中は保持値と表示更新用の呼出回数をともに維持する。','定価1,000円、値引額200円、数量2なら単価800円・金額1,600円。保持率10%であっても200円を100円へ置き換えない。'),
 ('計算','現在の請求単価と数量だけで金額を求める。変更監視が停止していても実装上のガードはなく実行する。価格取得、値引率変換、値引額の更新はこのイベントの責務に含めない。','単価900円・数量3なら金額2,700円。定価や率の保持値が別の値でも、このイベントで単価を作り直さない。'),
 ('マイナス指定','数量を通常1・マイナス－1に置換し、入力長を通常3・符号付き4へ切り替える。符号を付け替えて元の絶対値を保持する処理ではない。金額を再計算し、価格の照会・値引額再計算は行わない。','数量5、単価900円でマイナスを選ぶと数量－1・金額－900円。解除すると数量1・金額900円。'),
 ('書籍の選択解除','書籍コードが空の場合、新規・修正のどちらでも書籍、売上区分、金額類、値引き、数量を初期化する。売上区分は0というコードではなく未設定であり、数量はマイナス指定に従う。価格取得を無効にし、DB価格照会は行わない。','修正モードで数量8でも、書籍解除後は通常1またはマイナス－1。請求単価・金額は0、売上区分は未設定。'),
 ('書籍選択と価格取得','書籍選択時、新規だけ数量を初期値へ戻してから価格を取得する。修正は現在数量を保持する。価格取得ボタンだけでは数量を初期化しない。条件別価格がなければ基本価格を検索し、基本価格では新しく用意した価格情報の値引額・率の初期値0を使う。取得行がない場合、売上区分は未設定、定価等は0であり、売上区分0と断定しない。','数量8で価格取得ボタンを押した場合は8を保持する。新規の書籍選択では1または－1へ戻す。修正の書籍選択では8を保持する。'),
 ('郵便番号の入力確定','このイベントには変更監視のガードがない。入力の受渡しを更新し、前後空白を除いた検索用の値が3桁・4桁のときだけ住所照会する。検索用の空白除去によって保持する郵便番号そのものを書き換えるわけではない。該当住所が空の場合は入力済み住所を維持する。','保持値「 100 」「 0001 」は検索引数「100」「0001」となるが、保持値の空白はこの処理では変更しない。対象なしなら旧住所を維持する。')]


def apply_facts(data):
    for f in data['features']:
        if f['id']!='TKL-011' or data['system'].get('system_name')!='Tokyo Librarian':continue
        for i in f['items']:
            if i.get('binding')=='Discounts':i['type']='金額'
            names={'txtReducePercent':'値引率','txtSendCopies':'数量','txtSeikyuPrice':'請求金額'}
            if i['key'] in names:i['name']=names[i['key']];i['label_origin']='reviewed_business_label'
        f['notes'].append('書籍解除は修正モードでも数量を初期値へ戻す。小数の保持率と共通計算の整数引数、売上区分の未設定と0を区別する。')


def amend_feature(text,f):
    if f['id']!='TKL-011':return text
    rows=['### 3.補足 詳細な状態変化と検証用データ','','以下はイベントごとの変更対象・変更しない値・中断条件を明確化した契約である。例は計算・状態の説明であり、画面の入力許容や実DBの正常動作の証明ではない。','']
    for title,description,example in EXPLANATIONS:rows+=['#### '+title,'','- '+description,'','**データ例**：'+example,'']
    rows+=['<details><summary>Pilotイベントの受入契約</summary>','','```json',json.dumps(EVENT_CONTRACT,ensure_ascii=False,indent=2),'```','</details>','']
    text=text.replace('## 4. 補足説明','\n'.join(rows)+'\n## 4. 補足説明')
    return text.replace('新規入力では数量も通常・マイナスの初期値へ戻す','新規・修正とも数量を通常・マイナスの初期値へ戻す')


def amend_shared(docs,data):
    if data['system'].get('system_name')!='Tokyo Librarian':return docs
    block='''
## 補足：入力値・引数・保存値の違い

値引率は特別出版注文の保持情報では小数を保持できるが、共通値引額計算は整数の率を受け取る。小数を含む保持値からの呼出しでは、整数引数への変換が先に発生する。その後の金額丸めと二段階に分けて扱う。小数を含むモデル入力の比較と、共通UIによるキーボード・貼り付け・フォーカス時の制御は別の検証である。

売上区分の未設定は、区分コード0の存在を意味しない。書籍解除および価格データを取得できない場合の未設定はDB列のNULL許可を証明しない。未取得の制約は、保存時の挙動も含めて確認する。

郵便番号の前後空白除去は検索用引数に適用される。保持値、画面表示、DBへ保存する値がすべて正規化されると断定しない。入力値の受渡し更新の時機はUIバインディングに依存するため、処理本体の単体比較とは分離する。
'''
    for name in ['概要仕様書COM-001_共通仕様.md','概要仕様書COM-002_共通関数仕様.md','開発規約.md']:docs[name]+=block
    docs['開発規約.md']+='''
## 補足：比較試験の品質規則

原本と再実装の両方で例外が起きたという理由だけで正常系を合格にしない。例外を期待するケースだけ明示的に例外型を比較し、失敗時の状態も検査する。試験用モデルの型・NULL表現・初期値は原本と照合する。未知の分岐や未使用の契約フィールドがあれば汎用生成器が対応したとせず、未対応として停止する。

項目表は見えないIDではなく、表示される行・タイプ・必須・長さ・説明・DB関連を検査する。見えないIDが正しいまま本文だけを削除・改変する欠陥注入テストを必須にする。生成終了から結果公開まで、原本・仕様・参照実装・再実装・テスト・コンパイル条件のハッシュを結び付け、古い結果を最新の成功として再利用しない。
'''
    docs['DB定義書.md']+='''
## 特別出版注文の列解釈の補足

| 論理項目 | 使用箇所と変換 | 保存時に区別すること |
| --- | --- | --- |
| 値引率 | 注文画面の保持値 → 値引額計算では整数引数へ変換 → 単価と金額を再計算 | 特別出版注文の値引率保存パラメータには保持値を渡す。計算時の整数化が保存値を書き換えるとは限らない。物理列の小数精度は未確認。 |
| 売上区分 | 書籍選択解除・取得なしで未設定、取得行がある場合は書籍の売上区分を設定 | 未設定と0の区別、DB側の許容制約・登録時の結果は未確認。 |
| 送り状郵便番号 | 3桁＋4桁を検索引数として利用し、必要時だけ住所を補完 | 検索用に除いた空白を、送り状の保存値からも自動除去するとは説明しない。 |

上記は直接代入・計算呼出・保存パラメータの文脈をつないだ説明であり、物理DDLの代替ではない。
'''
    return docs


def normalize_names(registry):
    """Keep multiline UI labels from introducing physical newlines into MD rows."""
    def inline(value):return ' '.join(str(value).split())
    for obj in registry['objects'].values():
        obj['logical_name']=inline(obj['logical_name'])
        for col in obj['columns'].values():col['logical_name']=inline(col['logical_name'])
    return registry
