# relationship-agent — 独立した関係構築

版1.1／2026-10-26。package／CLIはcontextbase-relationship、Pythonモジュールはcontextbase_relationship。reverse-agentのインストール・import・統括起動を必要としない。新配置とportable受渡しの構造・合成検証は通過した。

## 導入

このディレクトリを作業先とし、専用仮想環境へ共通runtimeと本Agentだけを導入する。

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e '../shared/contextbase-runtime[analysis]' -e .
./.venv/Scripts/contextbase-relationship.exe --help
```

モジュール入口は `python -m contextbase_relationship`。コマンド形式は [実行指示](PROMPT.md)、責務と受入れ条件は [契約](AGENT.md)、作業規則は [AGENTS.md](AGENTS.md)を参照する。

## 単独実行と引渡し

本Agentはrelationship層だけを実行する。discoveryのportable handoffを受け取り、同一request・ソース・scopeを確認する。外部passは監査情報にとどめ、受信側の別文脈で目録前提を原文から再検証してから有効化する。入力・出力handoffは元request全体を保持し、同一の可搬manifest／ソース内容を必要とする。絶対sourceRootは束縛から除き、異なる配置でも相対scopeと材料を一致させる。別requestへの汎用P6再利用ではない。受信側の独立再検証が前提を有効化するまでneeds-prerequisitesとして扱う。

exportは前層workなしで読めるportable受渡し。全有効記録・未知・未閉鎖followup（raw履歴は監査用）を保存し、同じscope内の確認済み部分と未達を区別する。外部passは監査情報だけに使う。exportは受入れ済みの自層成果を必要とする。手動 --output はsource／work外の未作成パスを使い、設定経由の正式出力は所有束縛付きの固定先へ更新する。

## プロジェクト設定による実行

[contextbase.toml](../../test-project1/contextbase.toml)で入力と結果の置き場を切り替えられる。各相対パスは設定ファイルの位置から解決する。既定profile csharp_aspnetのsourceはtest-project1/srcs/CSharp_ASPNET、結果は [spec-reverse/relationship-agent/contextbase.json](../../test-project1/spec-reverse/relationship-agent/README.md)で、現在は未生成。

このAgentディレクトリからの例：

```text
contextbase-relationship paths --config ../../test-project1/contextbase.toml
contextbase-relationship init --config ../../test-project1/contextbase.toml
contextbase-relationship run --config ../../test-project1/contextbase.toml
contextbase-relationship export --config ../../test-project1/contextbase.toml
```

--profile NAMEで切り替える。--configはコマンドの後に指定し、明示 --source／--request／--work／--handoff／--outputとは併用しない。pathsは解決した入力・作業・出力・前層成果を表示するだけで、snapshot作成やモデル呼出しを行わない。

workは設定work基点/relationship-agent。後続層は同じ設定の前層固定成果だけを読み、自動実行せず原文で再検証する。前提をまだ受信していない空workでは、前層成果の到着後にrunで取り込める。非空workの入力を入れ替えず、新workを使う。封印後は元ソース変更を自動追従しない。

正式exportはtarget.jsonのprofile・source・goal等の所有束縛、ロック、原子的更新を使う。同所有範囲・同内容は冪等、別profile／source／goalの上書きは拒否する。切替例profiles.csharp_wpfはsource=srcs/CSharp_WPF、output=spec-reverse/CSharp_WPF、work=.tmp/contextbase/csharp_wpf、requestは共通。--profile csharp_wpfで入力・作業・出力を分けられるが、今回WPF解析は行わない。この設定改訂の設定・合成検証とpathsによる解決確認は通過した。範囲は実装ガイドを参照し、旧535件を重複計上しない。今回、実業務のLLM解析や結果JSON生成は行わない。

## 制約

共通runtimeは封印入力、SourceAccess、ID、store、アダプター、検証・host採用を担当する。共有実装を本Agent内へ複製しない。実モデルの業務品質、人手P0／P8、汎用P6再利用、長期運用は未完了。原仕様隔離、原工程・QA保護、.tmp／buildの配置は契約に従う。

共有する束縛・保存機構は [共通runtime](../shared/contextbase-runtime/README.md)を参照する。retryは既知の自層候補への明示1回再調査で、上流を自動起動・修訂しない。

独立導入と合成受渡しの検証範囲は [実装ガイド](../reverse-agent/docs/ContextBase初期実装.md)を参照する。これはreverse-agentの実行依存ではなく検証記録の参照である。
