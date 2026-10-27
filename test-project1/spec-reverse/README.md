# ContextBase 逆解析成果の索引

版2.1／2026-10-27。各Agentの固定出力先を示す。件数・採用範囲・未解決事項は、各成果の同じ版に束縛した案内と検証で確認する。

**discoveryの確認入口は [review.md](discovery-agent/review.md)。** 原文根拠、主機能・子操作・共通能力の分類理由、反例と未確認事項をここで確認する。

| Agent | 人手確認の入口 | 機械可読の正式成果 |
| --- | --- | --- |
| discovery-agent | [review.md](discovery-agent/review.md)・[成果案内](discovery-agent/README.md) | [contextbase.json](discovery-agent/contextbase.json) |
| relationship-agent | [成果案内](relationship-agent/README.md) | 生成した場合のrelationship-agent/contextbase.json |
| behavior-agent | [成果案内](behavior-agent/README.md) | 生成した場合のbehavior-agent/contextbase.json |

## 一括起動

Windowsでは [run-discovery.cmd](../run-discovery.cmd)をダブルクリックする。[contextbase.toml](../contextbase.toml)の既定profileに従い、discoveryだけを新規実行する。後続2層は自動起動しない。profile切替は起動引数の--profileを使う。

専用環境を準備し、launcher所有のworkで原文取得・索引検査・抽出・独立検証・ホスト採用を行う。採用結果とレビューをstagingへ作成し、同一版であることを確認してから固定出力を更新する。阻害や故障時は旧正式成果を保持する。

## 配置と判定

- contextbase.json：ホストが採用した正式な可搬成果。後続Agentは同一request・source・正確な前提版を自身の原文で独立再検証する。
- review.md／README.md：人手レビューの入口と、その成果版の内訳・制限。
- result/validation.json：採用に使った最終独立検証。単体試験の実行ログとは区別する。
- facts/：構文事実索引、最終機械検査と利用証跡。構文の存在だけで業務上の正しさを承認しない。
- target.json：profile・source・requestに対する出力slotの所有保護。可搬受渡しはcontextbase.jsonを用いる。
- 候補、伝送記録、テストログ、環境と中間物：Git対象外の.tmpへ分離する。旧result/candidate.jsonは正式成果として渡さない。

launcherの最新診断は設定work基点/discovery-agent-launch/current、公開準備中の資料は同stagingへ置く。launcher自身の所有確認を通る範囲だけを再利用・清掃し、手動CLIのwork、他Agent、入力・QA・正式テストには触れない。実装指紋が変わった手動workを自動移行せず、新規解析と既存成果の再配布を区別する。

catalogの採用を元goal全体の完了へ広げない。人手受入れ、後続層、原プログラム・SQL・DBの実行結果は、それぞれの今回の記録で判定する。
