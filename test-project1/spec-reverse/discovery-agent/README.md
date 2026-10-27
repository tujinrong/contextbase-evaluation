# discovery-agent の解析結果

版2.1／2026-10-27。**新しい利用者機能の分類規則で独立検証・ホスト採用した正式成果。** コード整理後にモデルを再実行した結果ではなく、採用時の内容を保持している。

読むファイルは[review.md](review.md)。ログイン、ログアウト、学生管理メニューを独立機能として可視化した。

| 項目 | 今回の結果 |
| --- | --- |
| 全記録 | 69 |
| 主機能 | 7（システム認証2・システム機能選択1・学生管理2・マスタ保守2） |
| 子操作／共通能力 | 8／15 |
| 技術入口／データ対象 | 15／12（物理表7を含む） |
| 支援／資料／依存 | 7／1／2 |
| 分類保留 | 0 |
| 独立検証 | catalog・scope・factUsageと30分類がpass、findingsなし |
| 採用範囲 | catalogのみ。relationship／behaviorと人手受入れは未実施 |

主機能はログイン、ログアウト、学生管理の操作選択、学生情報の検索・照会、学生情報の登録・保守、クラスマスタ保守、業務コード保守。

専用メニューは専用Controller／View、役割別の選択肢、検索画面からの復帰先を根拠に独立した操作選択として分類した。一般のメニューを一律に主機能とする規則ではない。ログアウトはセッション終了という独立した目的を根拠に分離し、認証セッション管理へまとめる別案もreviewへ記録した。詳細・編集準備・確認等は親機能の子操作として扱う。

## ファイル

- [review.md](review.md)：機能、目的、分類理由・反例、原文根拠、独立判定の閲覧入口。
- [contextbase.json](contextbase.json)：今回採用したcatalogの正式な可搬成果。
- [result/validation.json](result/validation.json)：正式成果を採用する際の最終独立検証。テスト実行ログとは区別する。
- [facts/facts-review.md](facts/facts-review.md)：技術入口・構文事実・利用証跡。[索引](facts/source-facts.json)と[facts/validation.json](facts/validation.json)：機械検査pass。
- target.json：profile・source・goalに対する出力slotの所有保護。
- .tmp/diagnostics/：今回の伝送・工程診断。Git対象外。

採用元のresult/candidate.jsonは作業用の提案であり、Gitへ登録しない。採用済み内容はcontextbase.jsonを正本とする。

## 未確認事項と実施範囲

管理10項目（作者質問6・followup4）の独立判定は非阻害4・解決4・後層阻害2。catalogへの阻害はないが、意味上の接続、DBの実配置差、動的利用・実行構成等は関係／動作工程で確認する。後続層は正式成果を受領しても、各自の原文で独立再検証する。

入力は75ファイル・353907 bytesで、元ソースは封印時と全件同一。1747 facts（328 symbols・1320 calls・77 imports・22 entries）を保存し、69記録が171 distinct factsを参照した。56記録はfactを使い、13記録は対応する構文factのない原文を理由付きで示す。.slnx／.mjs等のparser非対応材料はunsupportedと原文を保持し、ASTの呼出を意味結合や実行証明へ読み替えない。

原プログラム・SQL・DBは実行していない。今回の抽出・独立検証は封印済みソースと索引だけを入力とし、旧レポートや評価期待値を受け取っていない。過去調査の入力境界上の制限は実装ガイドに短く開示し、今回の新実行と分ける。

原文オンデマンド取得は未実装。速度・品質・対象範囲が異なる実行の結果を同一条件の比較値として扱わない。

正式テストの回帰と本成果のモデル検証を区別する。catalog採用を全suite・実機動作・人手受入れの合格へ広げず、実施範囲は各工程自身の結果で確認する。

workは.tmp/contextbase/csharp_aspnet/discovery-agentを使い、実行記録・診断・テストログはGitへ登録しない。コード指紋が変わった場合は新workを使い、既存の正式成果を自動で移行・再生成しない。[設定](../../contextbase.toml)・[全Agent案内](../README.md)・[実装ガイド](../../../agents/reverse-agent/docs/ContextBase初期実装.md)。
