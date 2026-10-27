# ContextBase 逆解析結果の配置

版2.0／2026-10-27。**新分類規則で独立検証・catalog採用したdiscoveryの正式成果。** 人手レビューと後続2層は未完了である。

読む入口は[discoveryのreview.md](discovery-agent/review.md)。今回の7主機能はログイン、ログアウト、学生管理メニュー、学生照会、学生情報保守、クラス保守、業務コード保守。詳細・確認等は子操作とし、認証・レイアウト等の共通実装は別に保持する。

| Agent | 正式成果 | 状態 |
| --- | --- | --- |
| [discovery-agent](discovery-agent/README.md) | [contextbase.json](discovery-agent/contextbase.json) | catalog採用済み・人手レビュー待ち |
| [relationship-agent](relationship-agent/README.md) | 未生成 | 未実行 |
| [behavior-agent](behavior-agent/README.md) | 未生成 | 未実行 |

69記録は概要2・主機能7・子操作8・入口15・共通15・データ12・支援7・資料1・依存2。分類保留0。独立catalog／scope／factUsageと30分類はpass、findingsなし。[result/validation.json](discovery-agent/result/validation.json)と[facts/validation.json](discovery-agent/facts/validation.json)で確認できる。

採用はcatalogのみ。管理10項目には後続relationship／behaviorを阻害する2件が残り、Dの完了を全目標の完了へ広げない。人手受入れ・原プログラム・SQL・DB実行は未実施である。

入力はsrcs/CSharp_ASPNETの75ファイル・353907 bytes、1747構文facts。入力版と根拠は正式成果・索引の内容hashで追跡する。後のコード整理でモデル解析を再実行したものではなく、採用時の結果を保持する。

[contextbase.toml](../contextbase.toml)のworkは.tmp/contextbase/csharp_aspnet、出力はspec-reverse。reviewを人の入口、result/validation.jsonを最終目録検証、factsを索引と最終機械検査に使う。採用候補result/candidate.json、.tmp、テストログはGit対象外。後続Agentは正式contextbase.jsonだけを受け取り、同一request・source・正確な前提版を照合して独立再検証する。前層を自動起動せず、候補を正式前提へ代用しない。

設定・source・正式テスト・target.jsonの所有保護は保持する。最終の解析検証を添付することとテスト実行ログを保存することは区別し、ログや試行世代は累積しない。catalog採用を全量回帰・実機・人手受入れの合格としない。実装指紋が変わった場合、旧workを自動復元せず新workを使う。
