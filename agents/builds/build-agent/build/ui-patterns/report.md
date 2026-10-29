<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-UI-PATTERNS-REPORT","version":"1.0","path":"agents/builds/build-agent/build/ui-patterns/report.md","sheets":[{"heading":"対象と採用","kind":"GRID","sheet":"01_対象と採用"},{"heading":"工程への反映","kind":"GRID","sheet":"02_工程への反映"},{"heading":"検証と未実施","kind":"GRID","sheet":"03_検証と未実施"}]} -->
# 3パターンのUI規約と関連Agentへの反映

版1.0／2026-10-29。references/web-ui-standard/ v1.0を参照し、WEB・WinForms・TextのUI品質を要件定義・基本設計・詳細設計・実装へ反映した。規則/検査処理の変更記録であり、題材アプリの再生成・受入結果ではない。

## 対象と採用

参照原本は[web-ui-standard](../../../../../references/web-ui-standard/README.md)の9ファイル。設計/実装ルール、24用途パターン、設定ひな形、HTML/CSS、レビュー、原本の検証記録を確認し、原本は変更していない。個別SHAと入力/出力ファイルの版・SHAは[validation.json](validation.json)へ固定する。

| 共通正本 | 主な採用内容 |
| --- | --- |
| [UIパターン規約](../../../../../docs/UIパターン規約.md) | family/rendererと必要用途、共通画面契約、工程引継ぎ、原本との採用差分 |
| [WEB品質規約](../../../../../docs/WEB画面品質規約.md) | サイト枠/現在位置、独立見出し、直接行操作、役割別トークン/内容幅、検索/ページ/出力と保存/状態復元。WPFは専用のネイティブ条件 |
| [WinForms品質規約](../../../../../docs/WinForms画面品質規約.md) | 標準Form/Control、DPI/単位/伸縮、入力/列幅/対象識別、キー/保存/取消。Accessの専門規約・9カテゴリを併用 |
| [Text品質規約](../../../../../docs/Text画面品質規約.md) | 固定行桁/表示セル、端末/文字コード/DBCS、入力保護/カーソル/機能キー、一覧/継続入力/確定と実端末検査 |

外部標準の「独立HTMLを主成果物」は、現在のMD概要GRID内の静的HTML/CSS正本へ調整した。同じ断片を.tmp/へ抽出して検査し、単独HTML/PNGを二重の仕様正本にしない。参照JSのデモ保存、設定YAML、架空値、105項目という原本の過去PASSを、対象アプリの実装済み/検証済み根拠へ転用しない。

## 工程への反映

| Agent | 今回の版 | 具体化と引継ぎ |
| --- | --- | --- |
| requirement-agent | 入口0.4、規則/工程0.3 | 利用者タスク、環境/分類、保存/選択/出力の要求、4観点の受入条件とQA |
| basic-design-agent | 入口1.11、規則1.2、工程1.3 | 必要パターン/遷移/状態、トークン/部品の静的断片、設計レビューと下流合格条件 |
| detail-design-agent | 入口1.3、規則/工程1.2 | renderer別の実部品/単位/バインド/入出力、イベント/キー/保存境界、独立期待値と必要証拠 |
| build-agent | 入口7.12、UIパターン生成チェック1.0 | 事前期待値、同方式内共通部品、最終製品からの属性/描画/実操作/データ再読込 |

配置のscreenFamilyと実行/観測のrendererを分離し、WPFはWEB/WPFのままXAML/DIPを使う。DOM/CSS/URLやブラウザー履歴をWPFへ必須化せず、Webの20件や字体/寸法をWinForms/Textへ移植しない。Accessの保存方式・認証・字体等の既存採用条件と専用gateを維持する。

共通UI規約と生成チェック、該当family規約を入力へ凍結する。全方式集約では3family規約を含め、製品への適用は該当family/rendererに限定する。追加方式は同方式specRootの規約/UIパターン.jsonで分類を明示できる。未知familyのUIは未確定として完成判定を拒否し、理由・凍結根拠付き非UI免除は維持する。追加方式でもrenderer=ACCESSならAccess専用規約/9カテゴリ/操作証拠を継承する。

## 検証と未実施

| 検査 | 最新結果 |
| --- | --- |
| preflight-tests.mjs | PASS 198 assertions。隔離fixtureの入力選択/分類JSON/旧結果失効/方式隔離 |
| ui-conformance-tests.mjs | PASS 209 assertions。隔離fixtureのfamily/renderer、Access専門条件継承、端末の理由付き非適用と誤適用拒否 |
| 文書静的検査 | PASS 30文書、142見出し、13 LIST・151行、336ローカルリンク・9アンカー |
| 構文/差分 | 変更した4本のJavaScriptのnode --check、git diff --checkがPASS |
| 独立意味レビュー | 共通4規約と要件/基本/詳細/buildの引継ぎに未解決の指摘なし |

最終UI validatorVersionは1.4、契約/観測のschemaVersionは1を維持した。

隔離fixtureで分類規約の選択/非該当除外、規約の削除・変更と旧manifest失効、分類JSONの不正/版/組合せ/余分キー/非通常ファイル/リンク/既知方式不一致、追加方式の明示分類/未確定UI拒否/非UI免除、WPFのネイティブ観測、Access専門条件の継承を回帰した。最新の実行コマンド・終了値・assertionsと対象ソースSHAはvalidation.jsonへ記録する。

文書のspec-meta/path/版、章・sheet、LIST矩形/キー、ローカルリンク/アンカーと工程/正本のつながりを確認した。共通4正本と関連Agentは独立に意味レビューし、静的検査・合成fixtureの合格を実画面品質の証明へ置き換えていない。文字セル単位のTERMINALは、ピクセルDPI/倍率が非適用のときだけnullと理由を許容する。未測定の仮値や他rendererの検査回避にしない。

既存のproject仕様・ソース・配布物はこの依頼で変更/再生成していない。実ブラウザー/ネイティブ/端末の画面、キーボード/IME、DB/API保存/取消、DPI/倍率/ブラウザー別環境、正式アクセシビリティ評価、利用者受入・正式採点は未実施。正式評価値はnullとする。
