# discovery-agent — 独立した取得・目録化

版1.5／2026-10-27。package／CLIはcontextbase-discovery、Pythonモジュールはcontextbase_discovery。reverse-agentのインストール・import・統括起動を必要としない。新配置とportable受渡しの構造・合成検証は通過した。

## 導入

このディレクトリを作業先とし、専用仮想環境へ共通runtimeと本Agentだけを導入する。

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e '../shared/contextbase-runtime[analysis]' -e .
./.venv/Scripts/contextbase-discovery.exe --help
```

モジュール入口は `python -m contextbase_discovery`。コマンド形式は [実行指示](PROMPT.md)、責務と受入れ条件は [契約](AGENT.md)、作業規則は [AGENTS.md](AGENTS.md)を参照する。

## 単独実行と引渡し

本Agentはdiscovery層だけを実行する。この層には前層成果を要求しない。取得不足・除外・解析失敗を明示し、原文根拠を持つ目録候補を作る。入力・出力handoffは元request全体を保持し、同一の可搬manifest／ソース内容を必要とする。絶対sourceRootは束縛から除き、異なる配置でも相対scopeと材料を一致させる。別requestへの汎用P6再利用ではない。受信側の独立再検証が前提を有効化するまでneeds-prerequisitesとして扱う。

exportは前層workなしで読めるportable受渡し。全有効記録・未知・未閉鎖followup（raw履歴は監査用）を保存し、同じscope内の確認済み部分と未達を区別する。外部passは監査情報だけに使う。exportは受入れ済みの自層成果を必要とする。手動 --output はsource／work外の未作成パスを使い、設定経由の正式出力は所有束縛付きの固定先へ更新する。

## プロジェクト設定による実行

[contextbase.toml](../../test-project1/contextbase.toml)で入力と結果を切り替える。既定sourceはtest-project1/srcs/CSharp_ASPNET、workはtest-project1/.tmp/contextbase/csharp_aspnet。[成果案内](../../test-project1/spec-reverse/discovery-agent/README.md)で現在の実行・検証・採用状態を確認する。

このAgentディレクトリからの例：

```text
contextbase-discovery paths --config ../../test-project1/contextbase.toml
contextbase-discovery init --config ../../test-project1/contextbase.toml
contextbase-discovery run --config ../../test-project1/contextbase.toml
contextbase-discovery export --config ../../test-project1/contextbase.toml
```

--profile NAMEで切り替える。--configはコマンドの後に指定し、明示 --source／--request／--work／--handoff／--outputとは併用しない。pathsは解決した入力・作業・出力・前層成果を表示するだけで、snapshot作成やモデル呼出しを行わない。

workは設定work基点/discovery-agent。後続層は同じ設定の前層固定成果だけを読み、自動実行せず原文で再検証する。前提をまだ受信していない空workでは、前層成果の到着後にrunで取り込める。非空workの入力を入れ替えず、新workを使う。封印後は元ソース変更を自動追従しない。

正式exportはtarget.jsonのprofile・source・goal等の所有束縛、ロック、原子的更新を使う。同所有範囲・同内容は冪等、別profile／source／goalの上書きは拒否する。切替例profiles.csharp_wpfはsource=srcs/CSharp_WPF、output=spec-reverse/CSharp_WPF、work=.tmp/contextbase/csharp_wpf、requestは共通。--profile csharp_wpfで入力・作業・出力を分けられるが、今回WPF解析は行わない。この設定改訂の設定・合成検証とpathsによる解決確認は通過した。範囲は実装ガイドを参照し、旧535件を重複計上しない。実Dと過去の差分repairを実施し、validation修正後の新しい独立verifyでcatalog／scope／fact利用と29分類のpassを確認してcatalogを正式採用・exportした。目標・エンジンは変更せず、初回hash不一致の検証を新しい独立verifyで再実行した。

## 現在のレビュー成果と正式export

公開入口は[成果README](../../test-project1/spec-reverse/discovery-agent/README.md)。完了後はreview.mdに機能・根拠・独立判定を示し、機械材料はresult/、索引はfacts/へ保存する。利用者の指示により旧結果と過去の実行記録を清除してfresh解析を開始した。現在の件数や採用は実装ガイドへ集約し、過去のpassや合成確認を実モデルの合格へ広げない。

rootのtarget.jsonは公開slotの所有保護として残す。採用後のみroot/contextbase.jsonを出力し、後続層は同一request・source・前提版を照合した上で、別文脈の原文再検証を行う。候補を正式な前提へ代用しない。作業記録は現在の固定workに置き、旧世代やbackupを累積しない。

関連回帰255件（成功253・skip2）と、別の旧全量737件未通過・全原因切分け未実施を区別する。時間・環境制約の詳細は[実装ガイド](../reverse-agent/docs/ContextBase初期実装.md)へ集約し、差分回復時間や検証のみの再試行を含む所要時間を、cleanなfresh抽出の速度改善へ換算しない。

## 制約

共通runtimeは封印入力、SourceAccess、ID、store、アダプター、検証・host採用を担当する。共有実装を本Agent内へ複製しない。Dのcatalogは当該範囲で採用済みだが、後続関係・動作の業務品質、人手P0／P8、汎用P6再利用、長期運用は未完了。原仕様隔離、原工程・QA保護、.tmp／buildの配置は契約に従う。

共有する束縛・保存機構は [共通runtime](../shared/contextbase-runtime/README.md)を参照する。retryは既知の自層候補への明示1回再調査で、上流を自動起動・修訂しない。

独立導入と合成受渡しの検証範囲は [実装ガイド](../reverse-agent/docs/ContextBase初期実装.md)を参照する。これはreverse-agentの実行依存ではなく検証記録の参照である。
