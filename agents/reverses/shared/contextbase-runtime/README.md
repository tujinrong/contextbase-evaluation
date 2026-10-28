# ContextBase 共通ランタイム

文書版0.1.5／2026-10-27。文書版はpackage版と区別する。独立した [discovery-agent](../../discovery-agent/README.md)、[relationship-agent](../../relationship-agent/README.md)、[behavior-agent](../../behavior-agent/README.md)が直接利用するPythonライブラリー。reverse-agentは依存先に含めない。

各Agentは独自のCLI、抽出責務、文脈構築、結果検査を持つ。共通ライブラリーはAgentを選択・起動せず、封印入力、構文アダプター、証拠、記録、別文脈の検証とローカル採用を提供する。導入・実行は [独立Agentガイド](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。

| ファイル | 責務 |
| --- | --- |
| agent.py | 単層Agentのライフサイクル、自層限定、実装版の束縛 |
| handoff.py | 可搬成果の整合検査、外部前提の独立再検証と有効化 |
| cli.py | 各Agentが渡す型を使ったコマンド処理。Agentの登録簿は持たない |
| controller.py／contracts.py／storage.py | 内容・版・依存に束縛した候補と検証、原子的な採用 |
| repair.py | 未信頼の失敗草稿とモデル作成patchの限定合成・全体再検査 |
| wire.py | task専用短縮参照と厳密なcanonical展開、採用時の再現検査 |
| facts.py | snapshot・抽出器版に束縛した構文事実、全inventory検査、query、モデル利用証跡 |
| sources.py／paths.py／adapters.py | source-only封印、原文位置、言語ごとの構文索引 |
| provider.py | 別のephemeral推論呼出しと実行記録 |

handoffは同一の元requestとソース材料に限定する。可搬source束縛から絶対sourceRootを除き、相対パス、内容、許可・除外範囲と残りのmanifestを一致させる。外部の検証要約は監査用であり、受信先の採用権限を復元しない。hashを署名や完全性の意味的証明とは扱わない。

tests/の正式テストは合成入力と模擬providerを使う。実モデルの業務精度・性能、人手受入れは別工程である。実行ログ・仮想環境・生成metadataはGit管理せず、.tmp/で検査する。

独立3環境でruntimeと当該Agentだけの導入・実行、portable成果の受信側原文再検証、活動中followupの解決gateを構造・合成試験で確認した。確定件数と除外範囲は [実装ガイド](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。実モデルの業務品質・人手受入れ・性能確認は含めない。

現行の利用者機能規則は独立ログインとメニュー責務を区別し、作者と独立検証へ同じ境界を適用する。実行・採用・試験の最新状態は実装ガイドへ集約し、過去の実行世代を本文へ累積しない。

## プロジェクトprofile設定

[sample-project1/contextbase.toml](../../../../sample-project1/contextbase.toml)はcontextbase-project/1の設定。各CLIはコマンド後の --configと任意 --profileでsource／request／work／outputを解決し、pathsは表示だけを行う。設定相対パスはconfigファイルの位置が基準である。

既定sourceはsample-project1/srcs/CSharp_ASPNET、正式結果はsample-project1/spec-reverse/各Agent/contextbase.json。設定exportはtarget.jsonの所有束縛・ロック・原子的更新を使い、手動--outputはfresh-only。現在の実行・採用・未実施範囲は[実装ガイド](../../reverse-agent/docs/ContextBase初期実装.md)で確認し、設定・合成検査とモデル品質・人手受入れを区別する。

## 可搬前提の版と過時拒否

portable成果はcontextbase-handoff/2を使い、payload.premisesにstageから上流envelope SHAへの正確な依存を保存する。discoveryは空、relationshipは受信したdiscovery全成果のSHA、behaviorはそのdiscoveryを継承してrelationshipのSHAも持つ。audit集合や過去passを成果版の代用にせず、内容依存と原文の独立再検証を区別する。

設定モードの後続Agentのrun／retry／exportは、現在の直接前層の固定成果SHAとworkに封印したincoming SHAを照合する。behaviorでは現在のdiscovery固定成果が存在すればpremises.discoveryとも照合する。採用範囲や内容が変わればaudit集合が同じでも過時として拒否し、新handoff・新workで受け直す。

contextbase-handoff/1は推測・自動移行せず、v2成果を再生成して新workを使う。解析requestはcontextbase-analysis/2のままである。手動portable --workは受領時の固定入力に束縛し、生成元workや前層ファイルの継続的な存在・更新には依存しない。固定前層の最新版を追跡するgateは設定モードに限定する。

## 新discoveryの分類契約

[用語集](../../../GLOSSARY.md)と[機能分類境界](docs/機能分類境界.md)を定義の正本とする。ホスト固定catalogPolicy=contextbase-catalog/1に従い、function／operation／common／unclassifiedとtyped classification、主・子・共通・保留の全対象recordのclassificationChecks・元要求全scopeのscopeChecksを用いる。scopeChecksはentry／data／support／material／dependency等を含む全viewを確認する。件数・今回必要な被覆へ影響する保留はpass検査だけで採用しない。詳細な必須項目、参照、unknown、失効と採用条件は分類正本§8～9へ集約する。

裸Sessionの旧v2タスク互換は新分類の合格ではなく、旧レコードへclassification=nullを自動追加して内容hashを変更しない。実装と新規回帰・実モデルの確認結果は[実装ガイド](../../reverse-agent/docs/ContextBase初期実装.md)を参照する。構造・合成回帰の詳細は実装ガイドに記録し、前改訂の70レコードは独立検証を実施したが未解決事項により未採用で、relationship／behaviorの実行や人手受入れを実施済みとしない。

contextbase-handoff/2のcatalogPolicyは互換拡張だが、新独立Agentの受信は合法なcontextbase-catalog/1を必須とする。discoveryは0レコードでもpolicyをexportし、後層はincomingの明示値を継承する。flagの欠落・不正値や旧handoffの自動格上げを認めず、旧入力はDから再抽出する。旧v2 task互換は裸Sessionだけに限定する。

保留のunknownIdsは物化前に大域IDへ固定する。可搬policyと未知IDの詳細は分類正本§8～10へ集約する。

## 構文事実の利用と文脈投影

索引の作成・キャッシュ・query／validate-index・factUsageを扱うときは[ソース事実索引契約](docs/ソース事実索引.md)を読む。完全な構文事実表とinventory・原文を提供し、重複する投影だけを除く。利用妥当性・目録分類・host採用は個別に確認し、索引機械検査のpassだけで業務品質を承認しない。

## 証拠一括検査と明示compact

証拠検査・短縮伝送は[短縮伝送契約](docs/短縮伝送と証拠一括検査.md)に従い、operation首尾のsnapshot確認、task束縛alias、canonical展開、通常gate・採用時再現検査を維持する。全原文を提供する現在の機構と、未実装のオンデマンド調査を区別し、局所replayを全体性能へ換算しない。

明示repairは[短縮伝送契約](docs/短縮伝送と証拠一括検査.md)に従い、同source/request/indexの拒否草稿を未信頼seedとして限定置換する。元回答と失敗診断は現在のworkで保持し、旧承認を継承せず全体検査・独立verify・採用時再生を行う。新規抽出と差分回復の測定を区別する。
