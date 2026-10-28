# ContextBase 逆解析成果の索引

版2.8／2026-10-28。discoveryは保存済み7草稿の収束と23組の独立検証を完了した。123記録・33分類は逐項passだが、全体catalogはfail、scopeはunknownで未採用。許可済み設定だけでは除外領域のコンパイル所属と目録への影響を確定できないという阻害を保持し、旧正式機械成果を残す。

## 改名後の出力と旧実行記録

現在のprojectIdはsample-project1。既定ASP.NET profileの新しい出力は`spec-reverse/CSharp_ASPNET/{agent-name}/`、WPFは`spec-reverse/CSharp_WPF/{agent-name}/`である。三つの独立Agentは選択profileの同じ方式別出力を使い、旧rootの前層成果へフォールバックしない。新projectの解析・採用・正式成果はまだない。

以下のroot直下のdiscovery-agent／relationship-agent資料は、改名前test-project1で実施した記録である。保持するenvelope・target・検証添付は原projectId、絶対パス、hashを変更していない。新projectの有効成果とは扱わない。旧ignored workもtest-project1/.tmpの元位置に保ち、新projectへ移行・再束縛していない。

**旧projectのdiscovery確認入口は [review.md](discovery-agent/review.md)。** 今回の未採用候補、範囲阻害1件、軽微な補足1件、識別SHAと実測を掲載する。最終検証続行は65分21.0秒。再抽出・fresh・後続Agentの起動は行っていない。旧contextbase.json／validationの合格を今回の結果に流用しない。

relationshipは [前回実行の未採用レビュー](relationship-agent/review.md)を保持する。共有DDLを含む35件の関係候補は前回の機械検査を通過したが、独立原文検証が入力長上限・読取りプロセスの起動失敗・応答契約違反で完了せず、関係義務は未採用である。これを共有DDL不足の継続や意味上の検証結果として扱わない。discoveryの前回fullモード正式成果を保持しており、今回relationship／behaviorは実行していない。

| Agent | 人手確認の入口 | 機械可読の正式成果 |
| --- | --- | --- |
| discovery-agent | [最新検証と未採用候補](discovery-agent/review.md)・[成果案内](discovery-agent/README.md) | [前回fullモードの保持成果](discovery-agent/contextbase.json)（incrementalは未採用） |
| relationship-agent | [未採用レビュー](relationship-agent/review.md)・[成果案内](relationship-agent/README.md) | 未生成（関係義務は未採用） |
| behavior-agent | [成果案内](behavior-agent/README.md) | 生成した場合のbehavior-agent/contextbase.json |

## 一括起動

Windowsでは [run-discovery.cmd](../run-discovery.cmd)をダブルクリックする。[contextbase.toml](../contextbase.toml)の既定profileに従い、discoveryだけを起動する。incrementalの同一入力では保存checkpointを継続し、--freshは所有確認後の新規実行を選ぶ。新projectのworkはsample-project1/.tmp配下に独立して作成する。改名前workの自動継続はしない。上記の23分片と範囲阻害は旧projectの実行結果であり、新projectの検査結果には流用しない。後続2層は自動起動しない。profile切替は起動引数の--profileを使う。

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
