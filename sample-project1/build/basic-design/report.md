<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SAMPLE1-BASIC-DESIGN-APPLICATION","version":"1.0","path":"sample-project1/build/basic-design/report.md","sheets":[{"heading":"対象と方式パターン","kind":"GRID","sheet":"01_対象と方式パターン"},{"heading":"適用・検査結果","kind":"LIST","sheet":"02_適用と検査","key":["項目"]},{"heading":"保全・改名・未実施","kind":"GRID","sheet":"03_保全と未実施"}]} -->
# 基本設計規則の適用・project改名記録

版1.0／2026-10-28。入力projectId=test-project1、出力projectId=sample-project1。

## 対象と方式パターン

利用者の指示により、学生管理の基本7方式へ最新の基本設計書式を適用し、sample-project1を全登録方式のフル方式パターン（将来拡張可）として整理した。Access-To-CSharp_ASPNETは既存移行拡張として維持し、存在しない基本設計を自動作成していない。sample-project2はAccess・CSharp_ASPNETの2方式パターンで、社員経歴管理の機能設計を変更しない。方式数と実装・試験の達成を混同しない。

元の業務・権限・候補・文字の受理範囲・原入力と保存後上限・検索とページ・定員・重複確認・監査・確定境界は各方式の確定前提から引き継いだ。SharedAccess/Native、COBOLの認証なし固定主体、Access/WinForms/Text系の部品差を維持し、社員200件/20経歴など別題材の値を転用していない。

## 適用・検査結果

| 項目 | 結果 | 範囲と根拠 |
| --- | --- | --- |
| 基本項目一覧 | PASS | 14文書・388項目を11列へ。空欄/-/〇、入力と保存長の差、条件必須、候補/正規化/CHK/EV/DATEの対応を維持。候補・表示名のDB源も論理名へ追記 |
| 処理と整合性 | PASS | 91イベント。既存OP/項目更新/判定に実MSGと復帰を対応、4項目以上の17イベントを階層化 |
| 構造とDB名 | PASS | 309spec文書、章/表/キー/リンク/方式内依存、論理DB名とTABLE正本を照合 |
| 図 | PASS | 182Mermaid構文・77ERのSVG描画。画面HTML14断片は不変比較、製品実機とは別 |
| 独立レビュー | PASS | 原入力/保存長、必須、候補DB源、廃止ID、方式固有MSG、版数を照合し修復後確認 |
| project改名 | 完了 | Windowsの同一workspace直下でtest-project1→sample-project1、上書き/削除なし |
| Agent入力検査 | PASS（7方式） | inspect-onlyで方式内入力を確認。生成/配布/旧検査記録を変更しない |

## 保全・改名・未実施

1885追跡ファイルを改名前にSHA-256で固定し、現在の配置との対応と欠損なしを検査した。アプリsource・DB/fixture・既存build/解析/評価等の保全対象1546ファイルはraw SHA一致。詳細/DB/TABLE104文書は業務本文不変、現在のmetadata.path等の配置だけを同期する。ソースのREADMEでは過去の生成日・凍結入力は当時のパスとして保持した。

旧build/spec-eval/spec-analysis/spec-reverseのprojectId/絶対パス/hash、DB名・DB所有マーカー・共有排他名は歴史/互換識別子として保持した。現在のCLI/プロファイル/参照パスは新名を使用する。現在の解析requestは新projectIdだが、旧所有束縛のある解析exportを自動で再採用しない。

実アプリ/DB/ACCDB/SQLの生成・実行、コンパイル、実ブラウザー/端末/IME、実Excel/変換/印刷、性能、受入、逆解析の再採用、正式採点、Git commit/merge/pushは未実施。formalScore=null。Agentコードの隔離fixture試験は実アプリ試験とは分ける。入出力hash・今回の検査はmanifest/validation/render-review/rename.jsonと、各方式build/spec-generation/basic-design-application.jsonへ固定保存する。
