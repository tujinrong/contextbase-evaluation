<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-SPEC-README","version":"8.4","path":"agents/spec-agent/README.md","sheets":[{"heading":"使い方","kind":"GRID","sheet":"01_使い方"},{"heading":"成果物と確認","kind":"GRID","sheet":"02_成果物と確認"}]} -->
# spec-agent

定義版8.4／2026-10-25。指定projectの仕様書をCodexが作成・改善し、三種類の画面分類を新規画面にも適用するための運用入口。

## 使い方

[AGENT.md](AGENT.md)が役割・工程・境界の契約、[PROMPT.md](PROMPT.md)が起動指示と実行要求の指定項目である。PROMPT.mdと対象project・方式・specRoot・sourceRoot・今回の改善要求をCodexへ渡す。専用の業務アプリや自動採点プログラムを起動する構成ではない。

対象は実行要求で選ぶ。新規作成だけでなく、既存文書を入力にした局所的な改善を扱う。ユーザー指定の正本パスを優先し、指定外projectや方式へ変更を展開しない。全体docs・agentsの役割定義を読み、許可された入力の版とハッシュを固定してからAIが仕様本文を執筆する。

検索画面の改善では、業務で使う条件だけを残す理由、空条件・初期表示・クリア・一致方式・並び順・件数・ページングを仕様へ記述し、主要操作を近接させて余白を整理する。検索UIを簡素化しても、登録項目・保存制約・権限制約の削除とは扱わない。画面サイズと状態を固定して1画面の達成範囲を確認する。

2026-10-23に開始したPilotの現仕様正本は `test-project1/spec/CSharp_ASPNET`、sourceRootは `test-project1/srcs/CSharp_ASPNET`。小規模の学生管理に合わせた検索条件とレイアウトの改善を行う指定例をPROMPT.mdへ置く。これを将来のprojectや他方式への実行許可として流用しない。

## 成果物と確認

画面設計はWEB系（WPFを含む）・WinForms系・Text系の三種類とする。test-project1ではCSharp_ASPNET/CSharp_WPF/Vue_CSharpAPI、VB.NET_WinForms/Access、COBOL/AS400_RPGをそれぞれに対応させる。WPFのXAMLやAccessのフォーム等の実装技術は維持する。今後の画面も分類と方式別共通UIに従い、新方式の所属と制約は実装前に定める。Text系は固定行桁、半角/全角セル、保護/入力、カーソル、選択、キー、ページ、エラー/確認、長文の到達を定義する。

仕様の画面表現はMD内の埋込みHTMLだけとし、基本/詳細に別レイアウトを描かない。画面PNGや単独HTMLを併置せず、方式内.tmp/へ同じ断片を抽出して描画・目視する。Access/WinFormsは従来フォームと標準部品、入力桁数に応じた幅と整列を記述する。文書版、入力/出力SHA-256、HTML断片ハッシュ、ブラウザー版、画面サイズ・倍率、確認状態、計測と目視結果を残す。Text系の文字モック確認はCCSID/DBCS・端末キーの実行確認と分ける。再生成では同じ最終パスを更新し、runIdは記録の属性として保持する。

仕様の正本は指定specRoot（独立方式はproject/spec/方式ID/）へ更新する。ソース正本sourceRootと分離し、業務仕様と仕様間参照は選択方式のspecRoot内で閉じる。最終検査記録は選択方式の `sourceRoot/build/spec-generation/` の固定先へ更新しGitで管理する。作成途中の候補、一時HTML/画像、描画・変換・失敗試行は `sourceRoot/.tmp/` を使い、過去生成結果を累積しない。[配置規則](../../docs/リポジトリ構成.md)に従い、方式を持たない共通工程だけ担当Agentまたはproject内のbuild/・.tmp/を使う。原入力・QA・正式fixtureは画面補助成果物と区別して保全する。

本文レビュー、構造検査、描画・目視、実装、ビルド、DB/実機試験、正式採点を分けて報告する。構造や描画のPASSは正式合格を意味せず、未採点ならformalScoreはnull。入力・既存QAを維持し、重大な矛盾は根拠と再開条件を残して該当部分を保留する。
