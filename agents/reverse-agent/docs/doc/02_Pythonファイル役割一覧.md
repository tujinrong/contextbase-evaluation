# 2. Pythonファイル役割一覧

対象版は[案内](README.md)参照。`input`配下の業務原本・生成された比較用ソース・キャッシュを除き、`src`と`src-dynamic`配下の**全81 Pythonファイル**を列挙した。58件は実装・初期化、23件はテストファイル。テストファイル数とテストケース数は異なる。

| 範囲 | Pythonファイル | うちテストファイル |
| --- | ---: | ---: |
| src | 33 | 10 |
| src-dynamic/mcterp | 15 | 4 |
| src-dynamic/tkl | 33 | 9 |
| 合計 | 81 | 23 |

「主要入口」は実在するトップレベル関数・クラスの先頭から最大3個を示す。各ファイルの行数・Git blobハッシュは[ファイル台帳](python_inventory.json)に記録。呼出先の完全な型解決や実行済みを意味しない。

## 2.1 共通の実行・選択・外部仕様

| ファイル | 役割 | 主要入口／試験クラス |
| --- | --- | --- |
| [__init__.py](../../src/contextbase/__init__.py) | 共通パッケージの名称・版を定義する。解析は開始しない。 | パッケージ定義 |
| [__main__.py](../../src/contextbase/__main__.py) | probe／rebuild／build／checkの受付と振分け。文書変換だけならinputを必須にしない。 | `main` |
| [discovery.py](../../src/contextbase/discovery.py) | 入力の形式・言語候補・対象外を一覧化する。業務の完全理解や全方式対応の判定ではない。 | `probe` |
| [external_browser.py](../../src/contextbase/external_browser.py) | 生成された状態別画面の幅・列比率・配置・はみ出しをブラウザー検査する。原画面との画像一致検査ではない。 | `run` |
| [external_spec.py](../../src/contextbase/external_spec.py) | 外部仕様の契約と画面ツリーからMD・画面HTMLを描画。コードから業務契約を自動確定する処理ではない。 | `esc`, `mdtable`, `layout_node` |
| [generic.py](../../src/contextbase/generic.py) | 一致する案件別解析器がないときの限定抽出。基礎宣言、簡易Vue/VB項目等から暫定MDを作る。 | `VueTemplate`, `extract`, `generate` |
| [pipeline.py](../../src/contextbase/pipeline.py) | 空の作業領域で解析・検査・変換を実行し、合格後に公開領域へ入替。MCTERP、TKL、genericで経路が異なる。 | `write`, `hashes`, `negative_control_command` |
| [registry.py](../../src/contextbase/registry.py) | 設定の安全性を検査し、原本ハッシュが一致する案件別manifestを選ぶ。Pythonを生成する機能ではない。 | `digest`, `configure`, `resolve_profile` |
| [tests/test_generic_escape.py](../../src/contextbase/tests/test_generic_escape.py) | 暫定文書に原本のHTML等が意図せず実行可能な形で入らないかを試験。 | `GenericEscapeTests` |
| [tests/test_native_dispatch.py](../../src/contextbase/tests/test_native_dispatch.py) | 実言語比較の選択が案件固有の名前・固定ケース数へ依存しないことを試験。 | `NativeDispatchTests` |
| [tests/test_pipeline.py](../../src/contextbase/tests/test_pipeline.py) | 作業領域、公開前検証、入替・失敗時保護等の実行制御を試験。 | `PipelineTests` |
| [tests/test_publication_cli.py](../../src/contextbase/tests/test_publication_cli.py) | build/checkが業務原本なしで使えることと、危険なパス・手修正保護を試験。 | `PublicationCliTests` |
| [tests/test_registry.py](../../src/contextbase/tests/test_registry.py) | 案件照合、未照合時の汎用経路、パス境界・設定の扱いを試験。 | `IsolationTests` |

## 2.2 MD・HTML・図の変換

| ファイル | 役割 | 主要入口／試験クラス |
| --- | --- | --- |
| [__init__.py](../../src/docsite/__init__.py) | 文書変換パッケージの版・説明を定義する。 | パッケージ定義 |
| [__main__.py](../../src/docsite/__main__.py) | migrate／build／check／publishの文書変換用CLI。 | `main` |
| [browser_check.py](../../src/docsite/browser_check.py) | 生成HTMLを外部通信禁止のブラウザーで描画し、図・レイアウト等の結果を記録する。 | `run` |
| [ci.py](../../src/docsite/ci.py) | 文書変換の回帰試験、繰返し生成の一致、ブラウザー記録の有効性を確認して集計する。 | `fingerprints`, `run`, `validate_browser_report` |
| [common.py](../../src/docsite/common.py) | 原子的保存、パス検査、リンク移動、画面CSSの適用範囲制限、HTML断片の検査・埋込み。 | `sha`, `js`, `read_json` |
| [diagram.py](../../src/docsite/diagram.py) | 限定Mermaid構文を解釈してGraphvizのSVGへ描画。未知構文は停止。DB関係の抽出はしない。 | `parse`, `_svg`, `render` |
| [er_diagram.py](../../src/docsite/er_diagram.py) | ER図のエンティティ、属性、キー、基数を共通グラフへ変換する。 | `parse_er`, `edge_attributes` |
| [publish.py](../../src/docsite/publish.py) | 旧形式をMD原本へ移行し、文書全体をHTMLへ変換。所有ハッシュと本文・表・図・リンク整合性も扱う。 | `classify`, `migrate`, `slug` |
| [tests/test_diagram.py](../../src/docsite/tests/test_diagram.py) | フローチャートの構文・ノード・エッジ保持と未対応構文の拒否を試験。 | `DiagramTests` |
| [tests/test_docsite.py](../../src/docsite/tests/test_docsite.py) | HTML埋込み、CSS、移行、再変換、リンク、変更保護等を試験。 | `FragmentTests`, `PublicationTests` |
| [tests/test_integrity.py](../../src/docsite/tests/test_integrity.py) | 本文・表の欠落や古いブラウザー記録を、見えないIDだけで合格にしないための試験。 | `IntegrityTests`, `BrowserReportTests` |

## 2.3 基礎解析・旧形式生成

| ファイル | 役割 | 主要入口／試験クラス |
| --- | --- | --- |
| [__init__.py](../../src/specgen/__init__.py) | 初期の基礎解析パッケージの版を定義する。 | パッケージ定義 |
| [__main__.py](../../src/specgen/__main__.py) | 旧来のscan／generateを受け付ける入口。新しいcontextbaseとは別のCLI。 | `main` |
| [analyze.py](../../src/specgen/analyze.py) | PythonはAST、それ以外は限定的なトークン・括弧解析で宣言・呼出・条件等を抽出する。 | `symbol`, `python_analysis`, `brace_analysis` |
| [common.py](../../src/specgen/common.py) | 文字コード、ハッシュ、安全なID、トークン・括弧分割、共通解析レコード等の低水準処理。 | `digest`, `stable_json`, `atomic_write` |
| [engine.py](../../src/specgen/engine.py) | 旧設定からプロジェクト検出、機能割当、キャッシュ、所有保護、文書・QA・解析報告の生成を管理する。 | `matches`, `config`, `projects` |
| [render.py](../../src/specgen/render.py) | 基礎解析結果から基本・詳細・テーブル仕様書と確認事項を出力する旧形式レンダラー。 | `esc`, `table`, `evidence` |
| [sql.py](../../src/specgen/sql.py) | CREATE TABLEと静的なSQLから列・制約・CRUD参照を抽出。DBへ接続しない。 | `identifier`, `mask_literals`, `sql_facts` |
| [tests/test_paths.py](../../src/specgen/tests/test_paths.py) | Windows短縮パス等の正規化と、ルート外拒否・再開を確認する回帰試験。 | `RootPathTests` |
| [tests/test_specgen.py](../../src/specgen/tests/test_specgen.py) | 基礎言語・SQL解析、機能割当、キャッシュ、原本非実行、出力保護等を試験。 | `ParserTests`, `EngineTests` |

## 2.4 MCTERPの案件別解析と社員Pilot

| ファイル | 役割 | 主要入口／試験クラス |
| --- | --- | --- |
| [__init__.py](../../src-dynamic/mcterp/mcterpgen/__init__.py) | MCTERP案件別パッケージの説明・版を定義する。 | パッケージ定義 |
| [__main__.py](../../src-dynamic/mcterp/mcterpgen/__main__.py) | 全体抽出→UI状態補正→機能MD→共通文書→構造検査→骨子・索引保存の案件別入口。社員のみ専用経路へ振り分ける。 | `save`, `Layout`, `validate` |
| [contracts.py](../../src-dynamic/mcterp/mcterpgen/contracts.py) | MCTERP共通の業務・開発ルール等のレビュー済み説明を生成する。固定された案件知識を含む。 | `shared` |
| [employee_contract.py](../../src-dynamic/mcterp/mcterpgen/employee_contract.py) | 社員の固定項目・状態・15イベント・IO・データ関連・確認事項をPythonデータとして組み立てる。汎用推論器ではない。 | `fields`, `flow`, `event` |
| [employee_db.py](../../src-dynamic/mcterp/mcterpgen/employee_db.py) | 社員の固定経路表と原本を照合し、DBイベント資産を第3章へ反映。専用共通DB文書、ER図、限定公開と保持検査を行う。 | `write`, `check_sources`, `layout_blocks` |
| [employee_external.py](../../src-dynamic/mcterp/mcterpgen/employee_external.py) | 社員の確認済み原本を照合し、画面・外部仕様を生成・検査。最後にemployee_dbの補強を適用する。 | `write`, `validate`, `generate` |
| [employee_layout.py](../../src-dynamic/mcterp/mcterpgen/employee_layout.py) | 社員用Vue部品の行・列・入れ子・状態条件を中立画面ツリーへ変換。対応条件は限定され、未知条件では停止する。 | `condition`, `Adapter`, `screens` |
| [model.py](../../src-dynamic/mcterp/mcterpgen/model.py) | ファイルキャッシュ、サービス境界、画面APIとC#・DBの関係、論理名・列・呼出到達範囲を構築する。MCTERPの配置規約に依存。 | `normalize`, `schema`, `walk` |
| [render.py](../../src-dynamic/mcterp/mcterpgen/render.py) | 通常機能の項目・イベント・DB・図・画面HTMLと共通文書を生成する。社員の高精度外部仕様経路とは別。 | `safe`, `cell`, `table` |
| [scan.py](../../src-dynamic/mcterp/mcterpgen/scan.py) | C#/TSの関数・呼出、Vue項目・イベント、保存ダンプ定義、Excelシート構造を読み取る。 | `sha`, `read`, `masked` |
| [tests/test_analysis.py](../../src-dynamic/mcterp/mcterpgen/tests/test_analysis.py) | 字句抽出、DB定義、原本収集・対応の限定構文を試験。 | `LexicalTests`, `SchemaTests`, `CollectionTests` |
| [tests/test_employee_db.py](../../src-dynamic/mcterp/mcterpgen/tests/test_employee_db.py) | ER描画、社員の原本・API・共通DB規則、欠落・順序・変更保護を試験。汎用ER試験もこの案件別テストに含まれる。 | `ErTests`, `EmployeeDbTests` |
| [tests/test_employee_external.py](../../src-dynamic/mcterp/mcterpgen/tests/test_employee_external.py) | 社員の状態別レイアウト、項目、IO、実装表記の混入、原本版変更時停止等を試験。 | `EmployeeExternalTests` |
| [tests/test_ui_state.py](../../src-dynamic/mcterp/mcterpgen/tests/test_ui_state.py) | 状態結合を入力項目に誤分類せず、実際の値結合を残すことを試験。 | `UIStateTests` |
| [ui_state.py](../../src-dynamic/mcterp/mcterpgen/ui_state.py) | 表示・開閉・処理中などの状態結合を業務入力から分離し、本文へ説明を追加する。 | `separate`, `describe` |

## 2.5 旧TKLの概要仕様解析

| ファイル | 役割 | 主要入口／試験クラス |
| --- | --- | --- |
| [__init__.py](../../src-dynamic/tkl/overviewgen/__init__.py) | 旧TKL概要仕様パッケージの版・モデル版を定義する。 | パッケージ定義 |
| [__main__.py](../../src-dynamic/tkl/overviewgen/__main__.py) | 旧TKLの生成CLI。前調査・抽出・詳細補正・文書化・状態整理を実行。 | `compact_state`, `main` |
| [adapters.py](../../src-dynamic/tkl/overviewgen/adapters.py) | VB.NETとXAMLを静的に読み、宣言・SQL断片・イベント・画面ノードを抽出する。 | `decode`, `clean_vb`, `mask` |
| [contexts.py](../../src-dynamic/tkl/overviewgen/contexts.py) | WPFのデータ受渡し範囲と階層を照合し、別モデルの同名項目や表示順の誤対応を抑える。 | `grid_owner`, `filter_display_mappings`, `layout_order` |
| [core.py](../../src-dynamic/tkl/overviewgen/core.py) | TKLの原本列挙、キャッシュ、スタイル解決、項目・固定ID・骨子を集約する。 | `digest`, `dumps`, `save` |
| [customer.py](../../src-dynamic/tkl/overviewgen/customer.py) | 抽出条件・設定・メッセージを顧客向けの説明へ変換。未解釈の式は根拠と区別する。 | `words`, `expression`, `conditions_and_settings` |
| [dblineage.py](../../src-dynamic/tkl/overviewgen/dblineage.py) | SQLの項目、引数位置、値の受渡しを対応付け、DB列との関係を補足する。 | `parenthesized`, `placeholder_properties`, `query_bindings` |
| [delivery.py](../../src-dynamic/tkl/overviewgen/delivery.py) | 生成文書と根拠・評価を所有保護付きで保存し、既存文書と混同しないよう管理する。 | `publish` |
| [publish.py](../../src-dynamic/tkl/overviewgen/publish.py) | TKLの概要仕様、共通、DB、メッセージ、図などの内容を組み立てる。 | `esc`, `table`, `link` |
| [refine.py](../../src-dynamic/tkl/overviewgen/refine.py) | 呼出・共通イベント・項目対応を補足。後から実行する登録先と即時呼出を区別する。 | `split_args`, `source_calls`, `map_columns` |
| [review.py](../../src-dynamic/tkl/overviewgen/review.py) | 生成アダプターとは別の原本XML・文字列読取で項目・イベント・DB参照等を照合する。 | `read`, `local`, `original_items` |
| [tests/test_contexts.py](../../src-dynamic/tkl/overviewgen/tests/test_contexts.py) | 別データ範囲への項目誤対応と配置順の補正を試験。 | `ContextTests` |
| [tests/test_overview.py](../../src-dynamic/tkl/overviewgen/tests/test_overview.py) | VB/XAML抽出、骨子、文書生成の基礎を試験。 | `AdapterTests`, `PipelineTests` |
| [tests/test_refinements.py](../../src-dynamic/tkl/overviewgen/tests/test_refinements.py) | 呼出関係やSQL・項目対応の補正を試験。 | `RefinementTests` |

## 2.6 旧TKLの品質補強と実言語比較

| ファイル | 役割 | 主要入口／試験クラス |
| --- | --- | --- |
| [__init__.py](../../src-dynamic/tkl/qualitygen/__init__.py) | 旧TKL品質補強パッケージの版を定義する。 | パッケージ定義 |
| [__main__.py](../../src-dynamic/tkl/qualitygen/__main__.py) | TKLの横断DB・共通・文章量・HTML・Pilot準備・独立評価をまとめる入口。 | `LayoutReader`, `independent_review`, `run` |
| [catalog.py](../../src-dynamic/tkl/qualitygen/catalog.py) | 呼出を再帰・逆参照し、テーブル利用・論理名・共通関数をまとめ、副問合せキーの誤対応を隔離する。 | `walk`, `build`, `quarantine_nested_keys` |
| [ci.py](../../src-dynamic/tkl/qualitygen/ci.py) | TKL回帰試験→全量／再利用生成比較→実言語検査を実行するCI用入口。 | `fingerprints`, `main` |
| [native_checks.py](../../src-dynamic/tkl/qualitygen/native_checks.py) | 新しい実言語比較結果を入力・実装ハッシュと結び付け、意図的欠陥の検出も実行する。 | `inputs`, `validate`, `run_native` |
| [pilot.py](../../src-dynamic/tkl/qualitygen/pilot.py) | Pilot準備・試験データ型調整・最終報告の窓口。基礎処理と拡張をまとめる。 | `normalize_fixtures`, `prepare`, `finalize` |
| [pilot_base.py](../../src-dynamic/tkl/qualitygen/pilot_base.py) | 固定仕様からVB比較用実装を作り、原本側は評価用メソッドだけを抽出する基礎処理。完全アプリ生成ではない。 | `json_contract`, `generate_only`, `prepare` |
| [pilot_extension.py](../../src-dynamic/tkl/qualitygen/pilot_extension.py) | TKLの比較対象イベントを増やし、仕様入力側と原本評価側を分けて比較プログラムを準備する。 | `generate_events`, `prepare_extension` |
| [profile.py](../../src-dynamic/tkl/qualitygen/profile.py) | TKLのレビュー済み共通業務、個別イベント、Pilot受入契約等の案件固有定数。 | パッケージ定義 |
| [render.py](../../src-dynamic/tkl/qualitygen/render.py) | TKLの説明粒度、共通関数、DB辞書、開発規約、画面HTMLを生成する。 | `name_text`, `captions`, `layout` |
| [semantic_review.py](../../src-dynamic/tkl/qualitygen/semantic_review.py) | 生成された実際の表・イベント本文を読み、隠しIDだけでは見つからない欠落・誤記を検査する。 | `plain`, `item_rows`, `event_sections` |
| [spec_revision.py](../../src-dynamic/tkl/qualitygen/spec_revision.py) | 追加イベント比較で確認したTKL仕様・表現を既存の個別／共通文書へ反映する補正層。 | `apply_facts`, `amend_feature`, `amend_shared` |
| [tests/test_components.py](../../src-dynamic/tkl/qualitygen/tests/test_components.py) | 帳票ビューアの項目数扱い、比較用の固定値が製品ロジックへ漏れないことを試験。 | `ComponentTests` |
| [tests/test_event_extension.py](../../src-dynamic/tkl/qualitygen/tests/test_event_extension.py) | 追加したTKLイベント契約と比較範囲を試験。 | `EventContractTests` |
| [tests/test_fixture_contract.py](../../src-dynamic/tkl/qualitygen/tests/test_fixture_contract.py) | 原本受取型に合わせた試験用データとNULL等の契約を試験。 | `FixtureTypesTests` |
| [tests/test_native_validation.py](../../src-dynamic/tkl/qualitygen/tests/test_native_validation.py) | 古い・改変された比較結果を最新の合格として使わないための試験。 | `NativeEvidenceTests` |
| [tests/test_quality.py](../../src-dynamic/tkl/qualitygen/tests/test_quality.py) | 再帰追跡、仕様だけの生成入口、文書・HTMLの項目照合、未実行判定等を試験。 | `QualityTests` |
| [tests/test_semantic_review.py](../../src-dynamic/tkl/qualitygen/tests/test_semantic_review.py) | 表示表とイベント本文の意図的欠落・誤記を検出する試験。 | `VisibleTextTests` |
| [ui_components.py](../../src-dynamic/tkl/qualitygen/ui_components.py) | 帳票ビューアや進捗領域を、通常の入力項目とは別の部品としてHTMLへ加える。 | `enrich_layout` |

## 2.7 Python以外にも仕様を決める重要ファイルがある

| ファイル・領域 | 役割・注意 |
| --- | --- |
| `config/project.toml` | 選択案件と入力位置。Pythonを変更せず設定できる部分 |
| `src-dynamic/*/manifest.json` | 案件原本の照合条件、起動モジュール、テスト群 |
| `mcterpgen/employee_evidence.json` | 画面・外部契約のレビュー対象版 |
| `mcterpgen/employee_db_assets/sources.json` | DB仕様の原本版と承認済み文書のハッシュ |
| `mcterpgen/employee_db_assets/events.md` | 社員イベントの詳細なレビュー済み文章。再解析時に挿入する資産 |
| `mcterpgen/employee_db_assets/common.md` | 社員Pilotに必要な共通DB処理の詳細文章 |
| `src-dynamic/tkl/profile.json`、`baseline.json` | TKLの固定した説明・ID等と比較基準 |
| `src-dynamic/tkl/qualitygen/templates/` | VBの比較実装・参照・試験データ用テンプレート |
| `src/docsite/assets/site.css` | 全文書の閲覧スタイル。画面の業務定義とは別 |
| `.github/workflows/` | 全件生成・社員限定更新等の実行と保存範囲 |

ファイル名に`dynamic`が付くこと、Pythonで辞書を組み立てること、AIが開発中にPythonを書くことは、実行時にPythonを自動生成する機能とは別である。

## 2.8 今後の分離候補（今回は変更しない）

共通ERの回帰試験は案件別`test_employee_db.py`にも置かれており、共通変更時に必ず走る配置へ移す余地がある。社員の日本語項目名・本文は宣言データへ寄せ、Pythonは解析と検査を担当させる方が再利用しやすい。`model.py`にはファイル収集、DB定義、サービス識別、画面対応など複数の責務があり、未知案件対応のたびに条件分岐を増やす前に境界を明確にする。
