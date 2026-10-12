# AI仕様書の派生表示検証 rendering-01

2026-10-13。最終実装R4で、人工入力による30件（安全境界15件、実Chromium描画15件）が52.071秒、終了コード0で成功した。実AI仕様書はまだ提供されておらず、今回の結果は人工入力の構造・静的表示・画像デコードに限る。業務仕様の正しさ、実アプリ動作、画素による正解判定、AIの意味レビューは未実施。

変更対象は `src/contextbase/ai/rendering.py` と `src/contextbase/tests/test_ai_rendering.py` の新規2ファイルのみ。既存provider・validator・workflowは変更していない。入力・依存・現行ソースのSHA、各試験結果は [results.json](results.json)、実行入口は [reproduction.ps1](reproduction.ps1)、今回の生ログは [r4-tests.raw.log](r4-tests.raw.log) に保存した。

## 動作と判定

`render_document(source, destination, *, mermaid_package, chromium_executable, document_path, asset_root)` は、原MDを読むだけで、排他的に新規作成するdestinationへ派生HTML・PNG・図のSVG/PNG・原Mermaidソース・manifestを出力する。`document_path` はspec-meta.pathと照合する期待相対パス、`asset_root` は閲覧を許可したローカル画像の境界である。省略時はそれぞれsourceのファイル名・親ディレクトリになる。リンク・Windows reparse point・評価用パスを拒否し、ローカル画像は境界内の検証済みPNG/JPEG/GIF/WebPだけを埋め込む。

特定方式・業務名・HTML class・章名に依存せず、Markdownの表、任意classのHTML/CSS、form/input/select/textarea/tableを含むHTMLブロックを表示する。図・抽出画面はIDと原MDの行範囲で関連づけ、原Mermaid文字列も保存する。原MDの書き換え、固定docsiteテンプレートへの本文再構成、Graphviz経由の描画は行わない。

構造判定は既存validatorの結果、表示判定は実ブラウザーと画像デコードの結果として分けている。構造が不正でも原稿を保持した検査用表示を生成できる。実行要素・イベント・外部依存を表示派生から除去した場合はremovedを記録し、`SANITIZED_ORIGINAL_REQUIRES_REVISION` とする。表示を原稿に忠実なPASSとは扱わない。図の構文エラーはERROR、Mermaid不足はNOT_RENDERED、空白画像・ブラウザー不足はERRORとなる。意味承認は常にNOT_ASSESSED。

静的HTMLのブラウザーはJavaScript無効、サービスワーカー無効、CSPと全リクエスト遮断を使う。図は別の空のブラウザー環境で、承認済みローカルMermaidだけを実行する。`securityLevel: strict` と `secure` を指定し、原入力からの設定引下げを拒否する。生成SVGを検査後、JavaScript無効の静的環境で撮影する。入力HTMLのscript・イベントやMermaidのbindFunctionsは実行しない。外部URLのリンクは自動取得せず、引用として静的に残す。ブラウザープロファイル、ドライバーの自動一時領域、ダウンロード・trace領域は各派生destinationの`.runtime`内に置き、今回の新規一時出力はすべてreverse-agent/.tmp内に限定した。

## 実結果

| 人工ケース | 構造 | 表示 | 確認内容 |
| --- | --- | --- | --- |
| positive | PASS | PASS | flowchart・sequence・ERの3図、任意CSSの画面1件、文書全体PNG、各artifact SHA一致 |
| sanitized | ERROR | SANITIZED | script・イベント・外部CSSを除去し6件記録、原稿は保持 |
| bad | PASS | ERROR | Mermaid構文不正、原.mmd保持 |
| missing | PASS | NOT_RENDERED | Mermaid依存不足を成功にしない |
| directive | PASS | PASS | securityLevel引下げ指定・クリック記述があっても実際のstrictを維持、入力イベントなし |
| blank | PASS | ERROR | 白一色の文書PNGを保存し、非空白表示の成功にはしない |
| unstructured | ERROR | PASS | meta欠落を直さず診断用文書画像を保存 |
| no-browser | PASS | ERROR | 未存在ブラウザーでも診断用HTMLを保存 |

全8ケースで原MDのSHAが実行後も一致し、`originalModified=false`。すべての描画環境で外部リクエスト件数0。正例の文書全体PNGと抽出画面PNGをR2で目視し、表・日本語ラベル・図・入力欄の表示を確認した。最終R4の両PNGは、その目視済みR2画像とバイト単位で同一である。これは任意原稿の意味やレイアウト完成度を承認するものではなく、実原稿は別途目視する必要がある。

正例成果は `agents/reverse-agent/.tmp/publication/rendering-01-r4/positive/`。全体はdocument.html/document.png、抽出画面はlayout-001.html/layout-001.png、各図はdiagram-001～003.mmd/.svg/.png。元行・元SHA・派生SHA・判定は同ディレクトリのmanifest.jsonにある。

## 依存と再現

Python3.11.9、Python Playwright1.60.0、既存Chromium1223（CDP実取得 `Chrome/148.0.7778.96`）、markdown-it-py4.2.0、BeautifulSoup4.14.3、tinycss2 1.5.1、Pillow12.1.1、ローカルMermaid12.1.0で実行した。Chromium実体とMermaid bundleのSHAもresults.jsonに記録した。User-Agentの縮退版番号を実ブラウザー版として流用せず、CDP Browser.getVersionで取得している。

Mermaidのinitialize/render API、Node22.12以降・12.xのブラウザーES2024要件は、実装前に[公式usage](https://mermaid.js.org/config/usage.html)とローカルpackage/API型を確認した。strictおよびsecureの意味は[公式設定schema](https://mermaid.js.org/config/schema-docs/config.html)を参照した。Mermaidは親Agentが`.tmp/render-tools`へ準備した承認済みパッケージを使用した。この担当からグローバル依存のインストール、ブラウザーダウンロード、モデルAPI呼出、モデル重み訓練はしていない。

新しい実行ごとに `CONTEXTBASE_RENDER_TEST_RUN` を未存在の絶対パスへ変更する。既存フォルダ再利用は失敗する。環境変数未設定を合格・skipへ置き換えない。依存するPillow/Playwrightは既存Python環境、Markdown等は`.tmp/pydeps`の実体を使用する。

## 履歴と未実施

R1の19件中1失敗はWindows CRLFを生成した人工fixtureのLF比較であり、原MD変更や描画失敗ではなかった。fixtureをwrite_bytesへ変更し、R2は23件成功。最終境界検査で、内部SVG URLの引用表記を誤拒否すること、SVG presentation属性の外部URLを検査していないこと、静的内容へSVG宣言アニメーションが残ることを新負例で再現した。修正前13件のログには5failure・1error（subtestを含む）がある。内部参照を保持、外部参照を検査、アニメーションを除去し、空白画像の回帰を加えたR3は30件成功。正確なブラウザー版の記録を追加した最終R4も30件成功した。旧ログと修正前ソース/hashはこの報告へ別名保存した。

root側の旧統合r3で、この実装途中のtestを環境変数なしでdiscoverして発生したsetUpClassエラーは、設定不足として原ログを保持する。この専用R4とは別実行であり、旧統合結果を新実装の合格へ流用しない。

実AI原稿の描画・目視、原アプリの起動・撮影、実DB業務試験、AI意味レビュー、独立peer review、他OS・他ブラウザー対応は未実施。ローカル入力SVG画像は承認済みraster画像の代わりに読み込まない。巨大な表示領域は上限を超えた場合にERRORとし、切り落としてPASSにしない。外部依存を必要とする原稿は作者側の修正が必要である。

現行rendering.py SHA256: `CF695505B1465844917DCC80D78B779747632AE9D44EE2873D74CD541620E039`。

現行test_ai_rendering.py SHA256: `64E76830782CDE621A6D0853B9B906B4294E8520760FAC29E2CD8C8ECC81BDF0`。
