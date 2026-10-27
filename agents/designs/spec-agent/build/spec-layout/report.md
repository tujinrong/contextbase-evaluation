# test-project1 仕様正本の上位配置への移行

2026-10-25。7方式298文書の正本をtest-project1/srcs/<方式>/specからtest-project1/spec/<方式>へ移動した。旧specフォルダ7個は不存在。spec-meta.path、文書版・可視版、README/索引と規約コピー42文書を同期した。specRootと生成先sourceRoot=srcs/<方式>を分離し、build/.tmpと配布物は従来のsourceRoot側を維持する。

AGENTS、全体docs6種、spec-agent/build-agent/reverse-agentの定義・入口を同期した。順生成は新specRootだけを読む。逆生成の許可コード入力へproject/spec全体を混ぜない。三画面分類、検索/編集項目、イベントとDB項目/制約は維持した。業務256文書の配置・メタ・可視版・説明追加だけを逆変換して全件初期SHA一致、HTML28断片不変、規約42コピーの本文とsheets一致を独立確認した。画面再描画は未実施であり、以前の描画PASSを今回改訂版へ流用していない。

中央生成toolingは入力scope/manifest凍結集合/他方式と評価入力の除外を改訂し、旧仕様書writer3本を実行前に拒否する。preflightへ--inspect-only trueを追加し、実project7方式は同モードで指摘0。既存出力/ZIPを失効させる通常preflightは実projectで実行していない。中央fixture52項目とパッケージ8試験、方式toolingの構文33件・純粋lookup35件・schema provenance追加10件を確認した。Access source-only ZIP内では原仕様hash収集だけを原仕様なしの証跡へ置換するfixtureも含む。業務実装・配布物・実DBを生成/実行した検査ではない。

方法別の生成器・入力lock/config/現在ロケータ・運用手順を同期した。古いschema/input lock/入力manifestのpath・版・hashは生成時出典として保持し、新仕様からの生成済み証拠に偽装していない。COBOLは次回生成前に新rootで明示lockが必要。AS400 schema検査は旧出典と新canonical/版一致を分けて扱う。COBOL端末製品やDB共有等の既存留保を配置変更で承認したと扱わない。

入出力の版・ファイル・SHA、移動表、Agent/ツール変更と最終記録はmanifest.jsonへ、検査/独立レビュー/未実施はvalidation.jsonと各方式srcs/<方式>/build/spec-generationへ保存した。実アプリ再生成・コンパイル・DB実行・端末実機・Excel/PDF・正式採点・受入は未実施。formalScore=null。
