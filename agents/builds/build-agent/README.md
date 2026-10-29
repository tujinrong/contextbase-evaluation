# build-agent

定義版7.11／2026-10-29。[契約](AGENT.md)・[起動指示](PROMPT.md)に従い、選択方式のspecRoot=project/spec/方式ID/からsourceRoot=project/srcs/方式ID/へ独立したシステムを生成する。旧sourceRoot/specへの自動復帰や他方式仕様の共用は行わない。業務コード・DB・試験の横断共用はしない。

最終ソースはsrcs/方式ID/の正本を更新する。最終配布物は方式内build/app・build/publish等、Accessは採用プロファイル又は方式の配布設定で指定した最終ACCDB1個。最終検査記録はbuild/test-results/、入力・出力manifestはbuild/generation/、解析用ZIPはbuild/source.zipへ固定名で更新し、Gitで履歴を管理する。中間生成・失敗試行・処理系・cache・隔離展開は各方式.tmp/へ置く。過去成果をrun-id別・backup別に累積しない。共通集約だけproject/build/、共通作業だけproject/.tmp/を使用する。

全方式の次回生成は[テストデータ整備規約](../../../docs/テストデータ整備規約.md)に従い、起動後に検索・新規登録・編集を試せる架空の初期確認用データと確認手順を備える。必要マスタ、確認用の業務行、異常系fixture、利用者の既存データを分け、初回投入と冪等な再投入・既存値保護を検査し、件数と基準日を固定manifestへ残す。共通規則の追加だけで指定外方式の投入済みとは扱わない。

Accessの生成・更新では[Access生成チェック](docs/Access生成チェック.md)を併用する。標準フォーム/部品、フォントとグループ見出し、モード別の入力属性、マスク/表示/保存の契約を確認し、実ACCDBのキーボード/貼付操作と画面表示を検査する。VBAコンパイルやプロパティ検査のみで入力と可読性を保証しない。

Accessの画面タイプ別品質は[Access画面品質規約](../../../docs/Access画面品質規約.md)を要件/基本/詳細から引き継ぎ、利用者の合理性・統一性・見やすさ・操作性で確認する。新規約を凍結した今回生成は全Form/Page/DialogのaccessScreenChecksで9カテゴリと個別ruleを対応させ、操作のevidenceも必須にする。対象の常時識別、長い案件名等の全文到達、未反映入力と保存/取消/離脱を検査する。既存の保存方式・認証・DBをレイアウト改善で変更せず、タイトルと本文は役割別トークンを使う。寸法や倍率の候補、仕様モックの描画を実ACCDBの合格にしない。

全方式のUI生成/改修は[UI適合検査](../../../docs/UI適合検査.md)で、事前に固定したtests/ui-contract.jsonと最終製品のui-observations.jsonを比較する。profile.uiConformanceの必須宣言、仕様根拠の版/SHA、全component/font対象、寸法/外観/render/操作、今回artifact/validator SHAを照合する。`node agents/builds/build-agent/scripts/ui-conformance.mjs --project <project> --profile <方式> --run-id <今回>`の記録をmanifestが再検査する。必須gateの未実施/削除/旧結果ではoutputsを確定しない。CLI等の非UIは理由と同方式の凍結根拠sourceFilesを明記する。方式ごとに適切な標準部品・単位・実測を使い、Access既定のクラシック外観/11ptをWeb等へ強制しない。

```powershell
node agents/builds/build-agent/scripts/preflight.mjs --project sample-project1 --profile CSharp_ASPNET --run-id current
python -X utf8 sample-project1/srcs/CSharp_ASPNET/tools/build.py
python -X utf8 agents/builds/build-agent/scripts/package-source.py current --project sample-project1 --profile CSharp_ASPNET
python -X utf8 agents/builds/build-agent/scripts/verify-packages.py current --project sample-project1 --profile CSharp_ASPNET --hashes-only
node agents/builds/build-agent/scripts/manifest.mjs --project sample-project1 --profile CSharp_ASPNET --run-id current
node agents/builds/build-agent/scripts/check-isolation.mjs current --project sample-project1 --profile CSharp_ASPNET
python -X utf8 agents/builds/build-agent/scripts/check-output-layout.py --project sample-project1 --profile CSharp_ASPNET
```

配置検査だけを行う場合は上記preflightへ`--inspect-only true`を付ける。inputs/structureは標準出力JSONへ返し、build/と.tmp/への書込み、旧outputs.jsonの失効、source.zipの移動は行わない。検査専用結果からmanifestを確定せず、実装生成時は通常preflightを実行する。

再構築/初期設定helperはsourceRoot/profile.jsonのproductionHelpersへ完全相対ファイル名で宣言する。toolsの未宣言ファイルは含めず、path escape・リンク・tests/.tmp/spec/eval・バイナリ等は宣言しても拒否する。通常seed、license/notice、CLIを保ち、原仕様なしの隔離展開から実ビルドできることを確認する。

run-idは記録の属性であり、同名再実行も固定出力先を更新する。preflightは旧outputs.jsonと旧ZIPを失効させる。manifestは今回のproject/profile/run-idと凍結入力hashを照合し、古いpackageを現在の成果として収録しない。入力が変更されたらpreflightからやり直す。構造PASS・hash一致は実装合格や正式受入ではない。

--hashes-onlyはZIPの全メンバーhash・除外境界・方式内の別展開だけを検証する。省略時は利用可能な独立.NET/native/Vueビルドも実行するが、SQLやIBM i等の受入とは別に記録する。ZIPには原仕様・project/spec/全体・spec-eval・試験期待値・中間物を含めず、production buildに必須の配置helperだけを許可する。

工程制御の回帰検査はnode agents/builds/build-agent/scripts/preflight-tests.mjs、python -X utf8 agents/builds/build-agent/scripts/output-layout-tests.py、node agents/builds/build-agent/scripts/isolation-tests.mjs、python -X utf8 agents/builds/build-agent/scripts/final-integrity-tests.py。使い捨てfixtureで方式選択、入力隔離、ZIP、配布hashと失敗時の旧合格失効を検査する。isolate-*、split-dotnet-tests、materialize-*、旧文書生成補助は一度限りの移送資源であり、現行アプリへ再実行しない。旧仕様配置を生成するisolate-specs・finalize-isolation-docs・document-dotnet-projectsは現配置の正本作成に使用しない。

共有SQL Server DB移行は選択方式で採用済みの場合だけ、認証・権限・排他・正規化等の同方式内共有契約を確認してから扱う。インストール・DB作成・配備は本配置修正の実行範囲に含めない。SQL補助の中間物はproject/.tmp/sqlserver-setup、最終記録はproject/buildの固定先へ出力する。既存DBを上書きしない安全条件は継続する。環境不足・未実施・失敗を最終記録へ明記し、以前のPASSを流用しない。

品質水準・改善回数を実行要求から固定し、品質「高」では正常・境界/複合/権限/競合/障害・独立テスト・利用可能な実UI・配布隔離の検査を行う。N回の検査→修正→回帰確認は固定build/test-results/quality-cycles.jsonへまとめ、実装/自己検証/独立テスト/製品受入を分ける。Agent不備の修正が許可されている場合は処理不備を回帰検査付きで修正する。別工程問題の報告先が明示されていればそのファイルへ根拠/影響/対応/残件を記録する。
