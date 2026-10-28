# discovery-agent — 独立した取得・目録化

版1.10／2026-10-28。package／CLIはcontextbase-discovery、Pythonモジュールはcontextbase_discovery。reverse-agentのインストール・import・統括起動を必要としない。ワンクリック起動も本Agentだけを対象にする。

新workのinit --incremental又はcontext_mode="incremental"で[分割調査・独立検証](../shared/contextbase-runtime/docs/分割調査・独立検証プロトコル.md)を選べる。単位草稿と対象別／全体レビューを保存し、元catalog義務全体で採用する。選択C#ではディレクトリ検索と要求回復を修正し、保存済み106件から同じworkで続行した。7単位・123件の未検証草稿を保存したが、全体closure中にモデルが満載と返し、候補化・独立検証・採用へ到達していない。[案件レビュー](../../../sample-project1/spec-reverse/discovery-agent/review.md)に時間と制限を記録し、前回正式成果を保持する。

新規workはinit --evidence、設定モードはprofileのcontext_mode="evidence"で[ホスト取証](../shared/contextbase-runtime/docs/ホスト取証プロトコル.md)を明示できる。必要な索引・原文をhostから取得し、別contextの独立検証と完全view採用は維持する。旧fullモードは既定のまま。新モードではrunへ--inline-sources／--compactを付けない。

## ワンクリック起動

Windowsでは [sample-project1/run-discovery.cmd](../../../sample-project1/run-discovery.cmd) をダブルクリックする。入力は同じディレクトリのcontextbase.tomlで選び、既定profileからdiscoveryだけを起動する。relationship／behaviorは起動しない。

事前にPython 3.11以降と、共通runtimeが使用するCodex CLIを利用可能な状態にする。初回は [launch.py](launch.py) が本Agent専用環境を作り、共通runtimeのanalysis依存とdiscovery-agentだけを導入する。パッケージ取得ができない場合はエラーと非零終了にし、正式成果を変更しない。reverse-agentは導入しない。

専用環境は本ディレクトリの.tmp/oneclick-environment。互換性とローカル実装の指紋が一致すれば再利用し、実装・依存定義の変更時は導入を更新する。別checkoutのpackageや他Agentの混入を検査し、所有を確認できない既存環境を削除・再作成しない。

起動処理は環境準備から解析終了までOSのロックを保持する。重ねてクリックした場合は「実行中」とロックの位置を表示して終了し、モデルを二重に呼ばない。単なるPIDファイルの存在を根拠にロックを削除しない。

解析は設定のwork基点/discovery-agent-launch配下のcurrent／stagingで管理する。毎回新しい原文封印・目録抽出・別文脈の独立検証・host採用を行い、採用後のJSONと人手reviewを同一版として公開する。拒否、故障、取消、報告作成失敗時は成功とせず、前回の正式成果を保持する。手動CLIのwork基点/discovery-agentとは別であり、既存の手動workや所有不明の内容を整理対象にしない。

結果の入口は選択profileのoutput/discovery-agent/review.md。正式成果はcontextbase.json、構文索引はfacts/、最終目録検証はresult/validation.json。候補・実行診断・テストログは.tmpへ置き、正式成果とは区別する。人手受入れや後続層の完了を自動判定しない。

コマンドからprofileを切り替える例（sample-project1で実行）：

```powershell
.\run-discovery.cmd --no-pause --profile csharp_aspnet
```

ダブルクリックでは終了時に画面を残す。自動実行では先頭の--no-pause、または環境変数CONTEXTBASE_DISCOVERY_NO_PAUSE=1で停止待ちを省略し、解析の終了コードをそのまま受け取る。作業ディレクトリが異なっても、設定と起動コードはcmdファイルの位置から解決する。

別projectの設定を指定する場合は、Pythonから `launch.py --config CONFIG --profile NAME` を実行する。直接導入済みの環境からは `python -m contextbase_discovery.launch --config CONFIG` を使える。通常の単独コマンドを細かく使う場合は以下の手動導入・実行手順に従う。

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

[contextbase.toml](../../../sample-project1/contextbase.toml)で入力と結果を切り替える。既定sourceはsample-project1/srcs/CSharp_ASPNET、workは選択profileのwork基点を使う。[成果案内](../../../sample-project1/spec-reverse/README.md)で現在の実行・検証・採用状態を確認する。

このAgentディレクトリからの例：

```text
contextbase-discovery paths --config ../../../sample-project1/contextbase.toml
contextbase-discovery init --config ../../../sample-project1/contextbase.toml
contextbase-discovery run --config ../../../sample-project1/contextbase.toml
contextbase-discovery export --config ../../../sample-project1/contextbase.toml
```

--profile NAMEで切り替える。--configはコマンドの後に指定し、明示 --source／--request／--work／--handoff／--outputとは併用しない。pathsは解決した入力・作業・出力・前層成果を表示するだけで、snapshot作成やモデル呼出しを行わない。

workは設定work基点/discovery-agent。後続層は同じ設定の前層固定成果だけを読み、自動実行せず原文で再検証する。前提をまだ受信していない空workでは、前層成果の到着後にrunで取り込める。非空workの入力を入れ替えず、新workを使う。封印後は元ソース変更を自動追従しない。

正式exportはtarget.jsonのprofile・source・goal等の所有束縛、ロック、原子的更新を使う。同所有範囲・同内容は冪等、別profile／source／goalの上書きは拒否する。切替例profiles.csharp_wpfはsource=srcs/CSharp_WPF、output=spec-reverse/CSharp_WPF、work=.tmp/contextbase/csharp_wpf、requestは共通。--profile csharp_wpfで入力・作業・出力を分ける。設定例の存在を解析の実施指示や完了証明としない。

## 現在のレビュー成果と正式export

公開入口は[成果README](../../../sample-project1/spec-reverse/README.md)。完了後はreview.mdに機能・根拠・独立判定を示し、最終検証はresult/、索引はfacts/へ保存する。現在の件数・根拠・採用範囲は今回の正式成果で確認し、過去のpassや合成確認を実モデルの合格へ広げない。

rootのtarget.jsonは公開slotの所有保護として残す。採用後のみroot/contextbase.jsonを出力し、後続層は同一request・source・前提版を照合した上で、別文脈の原文再検証を行う。候補を正式な前提へ代用しない。作業記録は現在の固定workに置き、旧世代やbackupを累積しない。

正式試験の回帰、実モデルによる目録検証、人手受入れを区別する。実施していない範囲や異なる入力・実装版の結果を流用せず、差分回復や検証再試行の時間をfresh抽出の速度改善へ換算しない。

## 制約

プロセスの強制終了で既存のpublication.lockが残った場合は、復旧記録を保持して停止する。ロックを自動削除したり、未完了の公開後に別操作が更新した正式成果を旧バックアップへ戻したりしない。

full／evidenceは報告作成失敗後の通常クリックも従来どおり新規解析となる。incrementalの通常クリックは同一入力・規則のowned currentを継続し、完了済みなら再推論せず再公開する。source等の変更時は旧checkpointを保持して拒否し、--freshを明示して同ownerのworkを新規化する。外部所有範囲は--freshでも削除しない。--publish-workによる手動成果の再配布は別経路であり、全失敗の無推論回復を保証しない。

共通runtimeは封印入力、SourceAccess、ID、store、アダプター、検証・host採用を担当する。共有実装を本Agent内へ複製しない。Dのcatalog採用、後続関係・動作の業務品質、人手P0／P8、汎用P6再利用、長期運用を別に判断する。原仕様隔離、原工程・QA保護、.tmp／buildの配置は契約に従う。

共有する束縛・保存機構は [共通runtime](../shared/contextbase-runtime/README.md)を参照する。retryは既知の自層候補への明示1回再調査で、上流を自動起動・修訂しない。

独立導入と合成受渡しの検証範囲は [実装ガイド](../reverse-agent/docs/ContextBase初期実装.md)を参照する。これはreverse-agentの実行依存ではなく検証記録の参照である。

新sample-project1の既定出力はspec-reverse/CSharp_ASPNET/各Agent/。根のspec-reverse/各Agent/は旧test-project1の保持記録であり、新projectの前提成果へ自動転用しない。新projectの解析は未実施。
