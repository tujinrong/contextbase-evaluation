<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-BUILD-UI-PATTERNS","version":"1.1","path":"agents/builds/build-agent/docs/UIパターン生成チェック.md","sheets":[{"heading":"適用と入力","kind":"GRID","sheet":"01_適用と入力"},{"heading":"共通の生成手順","kind":"GRID","sheet":"02_共通の生成手順"},{"heading":"WEB配置とブラウザー実装","kind":"GRID","sheet":"03_WEBとブラウザー"},{"heading":"WPFへの適用","kind":"GRID","sheet":"04_WPFへの適用"},{"heading":"WinForms配置とAccess","kind":"GRID","sheet":"05_WinFormsとAccess"},{"heading":"Text配置","kind":"GRID","sheet":"06_Text配置"},{"heading":"検証と完了","kind":"GRID","sheet":"07_検証と完了"}]} -->
# UIパターンを実装・検証へ接続する生成チェック

版1.1／2026-10-30。build-agentの実装工程に適用する。配置familyと描画技術を分け、[UIパターン規約](../../../../docs/UIパターン規約.md)と同方式specRootの採用仕様を、実装・独立期待値・最終製品の検査へ対応させる。設計工程の専用ルール・書式をこの文書へ複製しない。

## 適用と入力

既知の配置familyはWEB=CSharp_ASPNET/Vue_CSharpAPI/CSharp_WPF、WINFORMS=VB.NET_WinForms/Access、TEXT=COBOL/AS400_RPGとする。WPFはWEBの配置方針を使うネイティブXAMLアプリである。方式名からHTML化やブラウザー化を推測しない。

共通のUIパターン規約と本チェックを全方式、[WEB画面品質規約](../../../../docs/WEB画面品質規約.md)・[WinForms画面品質規約](../../../../docs/WinForms画面品質規約.md)・[Text画面品質規約](../../../../docs/Text画面品質規約.md)を該当familyだけ凍結入力へ含める。方式未指定の全方式集約では3規約を含める。Accessは従来の[Access画面品質規約](../../../../docs/Access画面品質規約.md)と[生成チェック](Access生成チェック.md)も併用する。

新profileでもrenderer=ACCESSを採用すればAccess専用2規約を凍結し、共通indexとAccess規約を凍結した今回のUIでは9カテゴリとinteraction証拠のgateを適用する。BROWSER/WPF/WINFORMS/TERMINALへAccess固有条件を適用しない。共通indexのない旧契約へは従来のAccess方式判定を保ち、現在必要な入力集合との差異による旧結果失効を別に確認する。

新profileは選択specRootの任意の`規約/UIパターン.json`へ`{"schemaVersion":1,"family":"WEB","renderer":"BROWSER"}`等を記録する。WEBのrendererはBROWSER/WPF、WINFORMSはWINFORMS/ACCESS、TEXTはTERMINALだけを認める。既知7方式は従来のfamily/rendererで解決し、JSONを置く場合も一致させる。非通常ファイル・リンク・不正JSON・未知値・組合せ不一致を拒否し、source側profile.jsonから入力familyを推測しない。

未知profileでJSONがない場合は共通indexと生成チェックだけで構造preflightを許容し、UI生成ではfamily未確定をFAILにする。JSONがあれば該当family規約も入力へ追加し、JSON自体も同方式仕様として凍結する。非UIは既存のuiConformance.required=false・理由・同方式の凍結根拠を用いる。CLIへサイトメニューや端末画面を追加せず、未確定を既知familyへ無理に割り当てない。

## 共通の生成手順

UIP-03aの認証入力群・既存の同型ペアは、方式内の共通トークン/部品へ幅・高さ・配置を集約する。size/maxlength/MaxLengthや入力値から個別の表示幅を決めず、採用済み補助部品やエラー表示、AutoSize/伸縮・初期化/再表示でも整列を保つ。実装を読む前に共通トークンから各部品の期待値を定め、最終製品のDOM矩形、ネイティブControl又は可視入力域のセル位置で初期/エラー/無効/再表示と採用環境を比較する。縦配置は左右端、横配置は上下端と欄間を確認する。認証/入力上限は保持し、用途別の別幅と、可視枠のない端末パスワード等の理由付き適用外を区別する。単一部品の幅だけの合格や、描画未検証を群全体の適合にしない。

1. 今回の要求、確定済み前提・規約/QA、最小有効領域、対象環境、family、描画技術、採用パターン、共通トークン、画面/項目/操作/検査IDと版/SHAを対応付ける。変更範囲がlayout_onlyなら保存方式・DB・認証・出力対象を変えない。
2. MDに埋め込んだ静的HTMLと文章・項目/イベント仕様を同じ設計版として読む。外部レビューの単独HTML、デモ配列、JSの保存成功表示、YAML例、CSS値を本番実装や採用済み業務条件へ昇格しない。正式なMDとHTMLの矛盾は先に報告する。
3. 共通枠・入力群・一覧・対象操作・状態・保存/離脱保護を同方式内の部品/共通処理へ実装する。他方式のソースやプロジェクトを参照して共用せず、方式内で再利用する。全24パターンや固定メニュー・認証を一括生成しない。
4. tests/ui-contract.jsonのfont/dimensions/appearance/render/interactionを、実装値の読取りより先に根拠から定義する。文字/余白/列幅、現在位置/対象識別、一覧状態、未反映入力、保存/取消/離脱とキーを画面・状態別の個別ruleへ分ける。family名の宣言だけで条件を満たしたとしない。
5. 採用技術の最終製品で属性・描画・実キー/クリック・必要なDB/API再読込を検査する。対象外には理由、未実施には範囲と次の確認条件を残す。静的HTMLの動作を実機試験に置き換えない。

## WEB配置とブラウザー実装

CSharp_ASPNET/Vue_CSharpAPI等の実ブラウザー方式では、共通ヘッダー・サイトナビゲーション・現在位置・本文を方式内の共通レイアウトへ実装する。原則は左サイトメニュー、機能数や採用規約に応じた上部ナビゲーション等の例外には理由を記す。独立メニューへ毎回戻る導線を必須にしない。移動はリンク、実行はボタンとし、単一行の詳細/編集へ行から直接到達できるようにする。権限に応じた入口とサーバー側認可を分ける。

見出し・フォーム・ラベル・ボタン・表の意味と関連付けを保つ。CSSの役割別トークンを共通定義し、採用フォント系列・代替字形・利用者の基本文字サイズ・ズームを尊重する。16px等はWebの採用初期値であり、ptやDIPやセルへ同値移植しない。無断の外部フォント配信や特定UIライブラリーの必須化を行わない。コントラスト・フォーカス・色以外の状態表現を採用条件ごとに確認し、一部の検査からWCAG全項目適合を主張しない。

最小高さ、実コンテンツ幅、折り返し、min-width、メニュー折りたたみ、表内スクロールを実装する。固定保存バーは入力・フォーカスを隠さず、小さい高さでは到達手段を確保する。320 CSS px相当・200%文字拡大等の採用対象条件を、ブラウザーのズーム・OS倍率と分けて実測する。overflow-x:hiddenによる隠蔽や文字縮小を可読性改善にしない。

一覧のページングは設計の採用契約に従う。20/50/100件は新規Webの候補であり、既存の件数/カーソル/固定一覧を無断変更しない。増加するデータはサーバー側の検索・安定順序・ページングとし、page/pageSize/sort等をサーバーでも検証する。入力中条件と適用済み条件、端ページ、0件/総数不明、検索/ソート/件数変更時のページ、削除後、詳細復帰を分ける。古い非同期応答が新しい結果を上書きせず、選択範囲と出力範囲を明示する。

直接URL、再読込、別タブ、ブラウザーの戻る/進むに対し、検索・ページ・並び順と対象を復元する。機密条件や秘密をURLへ入れない。アプリ内離脱とbeforeunloadの制約を分け、後者だけを入力保護策にしない。保存中/済み/失敗/競合、二重送信、認可、明細編集中の全体保存を実APIとデータ再読込で確認する。モーダル/タブの意味とフォーカス管理、通知とエラー項目への復帰も確認する。

## WPFへの適用

CSharp_WPFはWEBの情報構造・共通ナビゲーション・直接対象操作・密度・保存状態の考え方を、XAMLのGrid等、共通Window/UserControl、ResourceDictionary、ItemsControl/DataGrid、Command/Bindingで実現する。独立メニュー画面との不要な往復を避け、現在位置を示す。DOM、CSS、HTMLタグ、URL、ARIA、ブラウザー履歴をネイティブWPFの必須APIにしない。採用していないWebViewやフレームワークを追加しない。

寸法はDIP、フォントは採用したネイティブの単位で定義し、WebのCSS px/remからの読み替えと根拠を記録する。実Windowのclient領域、DPI/倍率、MinWidth/MinHeight、Gridの行列、ScrollViewer、DataGrid列/行高、長文、タブ/モーダルの実部品を測る。HTMLモックやXAMLソース値だけで実描画適合にしない。

一覧状態・編集中モデル・適用済み条件・保存中/競合・非同期Commandを分ける。Bindingの確定契機、検証エラー、現在編集中のセル/明細と最終保存、CanExecute、キーボード/フォーカス、Window終了・対象切替の入力保持を検査する。サーバーがある場合だけ通信/認可経路を確認し、ローカル方式へAPIやURL保存を無断追加しない。復帰は採用されたWindow/ページ/状態モデルで確認する。

## WinForms配置とAccess

VB.NET_WinFormsはForm/Panel/標準入力・選択部品/DataGridView等を使い、業務グループと対象操作を配置する。ネイティブのフォント、pt、client領域、DPI/AutoScaleMode、Anchor/Dock、TabIndex/TabStop、AcceptButton/CancelButton等を採用仕様に従って定める。枠線が見出しを横切らず、ラベル・列・入力・ボタンが欠けないことを実Formで確認する。CSSの寸法やWebのサイトメニュー・ページ件数を無条件に強制しない。

一覧の選択行と編集/出力対象、DataGridView等の編集中セルと保存データを一致させる。未選択操作、0件/失敗、長い名称、入力エラー、FormClosing、戻る/対象切替、複数行Enter、Esc、モーダル後のフォーカスを検査する。表示行数と取得/保存単位を混同せず、ページングの必要性は採用仕様で決める。Bound/Unbound、BindingSource、EndEdit等の確定時期と、DBトランザクション/取消を分けて実データで確認する。

Accessは同じWINFORMS配置familyでもAccessネイティブのForm/Control・Twips/pt・レコード確定経路を使う。既存Access規約・クラシック外観・役割別字体・InputMask・Dirty/Undo/BeforeUpdate・所有COMの終了を保持し、VB.NET APIへ置き換えない。新規約を凍結したAccessのaccessScreenChecksとinteraction証拠のgateを省略しない。

## Text配置

COBOL/AS400_RPG等は採用端末の行×列、文字コード、半角/全角・結合文字等の表示セル幅、入力可能桁、保護属性、項目位置を先に定める。pt/CSS px/DIPをセル寸法として扱わず、CSSやDOMを要求しない。固定の24×80等を全端末へ推測適用せず、採用済み画面サイズ、DSPF/端末機能と代替経路を使う。

画面ID/業務名/対象/モード、入力・一覧、メッセージ、使用可能なキーと操作結果を明示する。Tab/Enter/Fキー等は端末の実機能で対応させ、キー名だけを画面へ描画して完了としない。長い名称・複数ページの一覧は続き/詳細/前後操作で全文へ到達でき、表示範囲・選択対象・エラー行を特定できるようにする。Webの20/50/100件や共通サイトメニューを無断導入しない。

実端末でカーソル順、保護/入力、IME/文字コード、先頭ゼロ、境界桁、全角文字の列ずれ、最終行のメッセージ、キー/ページ遷移、取消/再表示を確認する。非対話CLI/バッチではText画面を作らず、非UIの理由を凍結仕様から採用する。端末エミュレーターやDBへ到達できなければ当該環境は未検証とし、stdoutの整列や静的HTMLだけで端末操作合格としない。

## 検証と完了

[UI適合検査](../../../../docs/UI適合検査.md)の既存schemaVersion=1を使い、native-property/computed-style/layout-measurement/render-review/keyboard-operationを実際の測定方法へ対応させる。ブラウザーは最終publishのDOM/computed style、WPF/WinForms/Accessは最終製品の実部品、Textは採用端末のセル/属性/キーを観測し、事前契約と照合する。該当する保存/破棄はデータ再読込まで確認する。

font/dimensions/appearance/render/interactionと、画面/状態/対象環境ごとの期待・実測・証拠を対応付ける。未知family、非UI理由、対象外の妥当性と観測の意味は独立レビューで確認し、規約ファイルの凍結やgeneric propertyの一致だけを高品質の証明にしない。共通規約や実装が変われば今回の入力/契約/観測/最終artifactのSHAから再検査する。

最終報告は設計MD/埋込みHTMLの静的確認、コード生成、コンパイル、属性測定、実描画、実キー/クリック、実API/DB・再読込、利用者受入を分ける。正式評価未実施はformalScore=null。今回の証拠は固定build/test-results/へ更新し、途中物・試行・fixture実行コピーは.tmp/、履歴はGitを使う。referencesの同梱105項目PASSを今回アプリや別familyのPASSとして流用しない。
