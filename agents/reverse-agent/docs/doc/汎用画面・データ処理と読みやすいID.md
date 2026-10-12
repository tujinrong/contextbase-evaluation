# 汎用画面・データ処理と読みやすいID

## 原因

基本設計書の汎用文書モデルは概要・項目表・根本のイベントを作るだけで、レイアウト素材とデータ関連を掲載していなかった。既存Staff Pilotの画像は案件別処理だけが生成していた。呼出解析も条件式内の呼出を取りこぼし、引数・注入型を使った実装の特定がなく、保存先の具体的なCRUDと画面項目が接続されなかった。文字列リテラルの空白正規化も比較規則の意味を失う原因だった。

## 実装の責任分離

| プログラム | 役割 |
|---|---|
| src/specgen/adapters/csharp_flow.py | 条件式を含む呼出・引数・ガード、文字列の意味を保持した静的フロー |
| src/specgen/adapters/csharp_relations.py | 受信型、DI登録、引数数・型候補による呼出先解決。保持領域とCRUDの追跡 |
| src/contextbase/detail/semantics.py | 検証メッセージ、項目の保存先、照合規則、保存値の加工、画面側の確認操作の共通投影 |
| src/contextbase/detail/layout.py | 非実行のHTML/CSS合成、静的画面PNG、部品位置、データ操作関連図 |
| src/contextbase/detail/documents.py | P2の情報を基本設計・詳細仕様・共通資料の文書ブロックへ展開 |
| src/contextbase/shared/identities.py | SCR/COMの永続採番、旧IDの別名、同一内容の移動に対する一意照合 |
| src/contextbase/validation/core.py | 世代・参照に加え、画像とCRUDの掲載・根拠・IDの契約検査 |

案件固有の名称だけをsrc-dynamic/jsbrms-pilot/terminology.jsonに保存する。新規・変更・削除画面の完成文章を差し替えるコードは追加していない。従来のStaffレビュー適用条件とMCTERP/TKLを変更しない。

## 保存先の区別

現行JSBRMSの年金予約サービスはList<PensionReservation>のメモリー保持である。保存時は照合した既存要素を置換、ない場合は追加する。削除は同じ照合方式で対象要素を取り除く。これらをMEM形式の論理データとして記載し、物理DB表は別に扱う。外部DBが本番にないことを保証する記述は行わない。原本内のサンプル顧客データ行を仕様書へ複製しない。

## 採番

公開IDはSCR-001、COM-001など。現在の対象画面はSCR-005、旧ID F-4DCE8CF540はalias。既存100008は変更しない。ContextBase/identities.jsonは解析キャッシュと別に永続保存し、クリーン再生成時も保持する。削除番号は再利用しない。名称変更・移動は原本内容と種類が一意に一致した場合のみ継承し、曖昧な移動は手動で台帳を確認する。

```shell
python -m contextbase rebuild --replace-output --pdf --excel --browser
# 次の２つの対象指定は同じ機能を指す
python -m contextbase.detail --feature SCR-005
python -m contextbase.detail --feature F-4DCE8CF540
```

## 検証範囲と制限

静的画面は実アプリの実行キャプチャではない。動的候補、モーダル操作後、Razor分岐、外部CSS、外部画像の再現は限定される。入力スクリプトを実行せず、外部通信を遮断して静的DOMの配置のみ取得する。

C#の呼出解決は対応した構文とDI登録に限定され、コンパイラーと同等の型解決ではない。未解決呼出、多重登録、再帰・追跡上限をreportに残す。データ操作の条件と実行時の完全な経路同等性は別の評価である。Java、VB6、Vue等を同精度で改善したとみなさない。

未完成・未検証はreport、質問・仮定・回答はQAに保存する。成果物には静的再構成等の仮定のQA番号を残す。従来のV2 Excelの表紙・通常・一覧と枠外無罫線は変更しない。
