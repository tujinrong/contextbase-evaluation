# 汎用文書契約と構造検証の改善

2026-10-13。出力契約schema `reverse-ai-document-contract/1`。規定依存版を確認した最終検査はAI工程327テストが92.878秒で成功、exit 0。`ai-tests-r6.raw.log`、機械可読の`results.json`、再実行用`reproduce.ps1`を保存した。過去レポートの合格は使用していない。

入力は全体docs v7.2、reverse-agent規則、現AIコード、人工ソース/原稿、およびユーザー指定の文書ID・kind・出力path・ソース開始点だけの契約。原仕様・評価期待値・既存生成仕様本文を読まず、業務固有の正解値をコードへ組み込んでいない。

`plan --document-contract`は契約の全件だけを同じID/kind/pathでAIに計画させる。sourcePathsは封印manifestの原本相対パスで、依存探索の開始点。文書の追加・欠落・改名・重複・開始点の脱落を拒否する。契約原JSONをそのままjobへ固定し、後続の解析・執筆・独立レビューでハッシュと計画対応を再検査する。Pythonが本文やAIの意味判断を組み立てる処理は追加していない。

指定kindが機能基本/詳細の場合だけ4主章と各イベントの6下位見出しを要求する。TABLEは指定二章、ヘッダー2列、NOT NULLを含む明細9列の宣言と実表を検査する。機能構造不足へのAI承認は拒否される。静的HTMLのbuttonはtype=buttonを要求し、submit/image入力は拒否する。入力文書を修正する処理はない。

最後にsnapshotとjob/outputの重なりを拒否した。同一・snapshot配下・snapshotを含む親ディレクトリを拒否し、plan/document/batch/iterateのAI起動やmkdir前に止める。CLI結果がFAILED/NOT_RUN_TIME_LIMITならexit 1、保存済み未採択のREQUIRES_AI_REVISIONはexit 0を維持する。関連150試験と上記最終327試験を通した。この変更前の生成ジョブや停止証跡は改変していない。

負例で全件対応・path境界・契約変更拒否・章/イベント欠落・TABLE旧8列・列宣言欠落・HEADER文章だけ・送信部品を確認した。人工文書の実Chromium表示、Mermaid、長文分割、原稿バイト不変も既存テストとともに検査した。初期の環境不足や人工負例の作成不備は旧ログとして保存し、最終検査と区別した。

runtimeはbundle Python3.12.14。規定のjsonschema4.25.1、markdown-it4.2.0、bs4 4.14.3、tinycss2 1.5.1、Pillow12.3.0、playwright1.57.0を今回専用の`engine-runtime-deps`へ導入し、先頭で使用した。旧pydepsのrpds cp311を混用したr4失敗と、旧session依存jsonschema4.26.0を使用したr3合格も保存した。生成用のsource-pilot専用venvは変更していない。

fact根拠の許可ファイル/行範囲とobserved-source/reference-design区別は既存検証を維持した。factの意味的網羅性、実際の読了、章本文の正確さはこの構造合格だけで確認済みにしない。実アプリ/DB、正式意味採点、原ビュー/CSSとの画像比較、モデル重み学習は本担当では未実施。
