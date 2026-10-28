<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SAMPLE-PROJECT1-REQUIREMENT-RUN","version":"1.0","path":"sample-project1/build/requirement-definition/report.md","sheets":[{"heading":"対象と成果物","kind":"GRID","sheet":"01_対象と成果物"},{"heading":"検査と保全","kind":"GRID","sheet":"02_検査と保全"},{"heading":"制限と未実施","kind":"GRID","sheet":"03_制限と未実施"}]} -->
# sample-project1 要件定義書の仕様逆生成

版1.0／2026-10-28。stage=requirement-definition、generationMode=spec-to-requirements、Agent=AG-REQUIREMENT 0.2。

## 対象と成果物

標準7方式と移行拡張1方式、計8方式の直下へ要件定義書.md 1.0を作成。目的・範囲、利用者/権限、機能/データ/非機能、受入条件、QA、根拠を整理し、方式/全体の索引へ入口を追加した。業務入力は同方式の既存仕様に限定し、コード・実DBの観測で補完していない。

| 方式 | 要件定義書 | 要件数 | 受入条件数 | QA/引継ぎ数 | 文書検査 |
| --- | --- | --- | --- | --- | --- |
| VB.NET_WinForms | [1.0](../../spec/VB.NET_WinForms/要件定義書.md) | 43 | 23 | 6 | PASS |
| CSharp_WPF | [1.0](../../spec/CSharp_WPF/要件定義書.md) | 43 | 23 | 6 | PASS |
| CSharp_ASPNET | [1.0](../../spec/CSharp_ASPNET/要件定義書.md) | 40 | 24 | 8 | PASS |
| Vue_CSharpAPI | [1.0](../../spec/Vue_CSharpAPI/要件定義書.md) | 40 | 24 | 8 | PASS |
| COBOL | [1.0](../../spec/COBOL/要件定義書.md) | 40 | 19 | 8 | PASS |
| AS400_RPG | [1.0](../../spec/AS400_RPG/要件定義書.md) | 40 | 19 | 8 | PASS |
| Access | [1.0](../../spec/Access/要件定義書.md) | 40 | 19 | 8 | PASS |
| Access-To-CSharp_ASPNET | [1.0](../../spec/Access-To-CSharp_ASPNET/要件定義書.md) | 19 | 10 | 5 | PASS |

requirement-agentへ仕様書からの逆生成を追加。契約/指示/案内を0.2、専用規則/工程を0.1とし、ルーティング・共通案内・隣接設計Agentの参照を同期。要求起点の汎用運用や業務承認の一般的な検証完了は主張しない。

## 検査と保全

全305要件に受入条件を対応し、計161条件をすべて未実施と記録した。81件の方式別根拠のID・版・SHA-256、方式内リンク、spec-meta/LIST、要件/QA対応を今回の実ファイルで検査してPASS。

既存309 Markdown中、既存業務仕様293件はSHA-256一致で保全。既存変更は入口16件だけ、新規業務文書は要件定義書8件。対象外のローカル変更は取り消していない。[manifest](manifest.json)と[検査結果](validation.json)に入出力の版・ファイル・ハッシュ、方式別記録への経路を保存。既存の設計/アプリ検査記録は上書きせず、requirement-definitionの固定サブフォルダへ記録した。

作成担当と異なるAI担当が方式内根拠に照合し、SharedAccess証明書例外、旧状態形式の方式差、所属期間、受入網羅、確定区分/QA列の指摘を修正。最終版を再検査し、独立レビュー範囲と対象ハッシュを記録した。文書検査・AIレビューの確認であり利用者による業務承認ではない。

## 制限と未実施

移行拡張は既存移行READMEだけが入力で、原Access/参考ソースは今回再取得していない。未記載の学生業務詳細を同方式QAへ保持。各方式の認証・DB・端末・ページング差分と既存設計案/未指定事項を継承し、他方式の前提を自動適用しない。

保持/復旧、性能案の採用・測定条件、実クラス、初期確認データ等は各要件定義書へ引き継いだ。利用者承認、アプリ生成/ビルド、実DB操作、実機/IME/端末/性能/受入試験、Excel/PDF変換、正式採点は未実施。formalScore=null。
