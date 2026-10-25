# Access 品質改善・初期データ

runId `20261025-access-quality` / test-project1 / Access。AGENTS 7.3、AG-BUILD 7.8に従い、入力を `test-project1/spec/Access/`、ソースを `test-project1/srcs/Access/` に限定する。他方式の業務仕様・ソース、spec-evalを実装入力に使わない。

## 入力と要求差分

凍結入力60件の文書ID・版・bytes・SHA-256は [inputs.json](inputs.json)、構造検査は [structure.json](structure.json) に記録する。今回追加の共通データ整備規約とAccess生成チェックも入力に含む。Access原仕様は変更しない。

旧仕様の本文9pt、学生/クラス/監査0件に対し、利用者は可読性の改善と初期確認用データを要求した。この要求変更は [user-overrides.json](user-overrides.json) とルートの [仕様問題報告](../../../../../test-project1-spec-bug-report.md) に記録し、次回仕様生成へ引き継ぐ。既存キー不変・新規キー入力・郵便raw10/正規化7桁の業務契約は維持する。`local-spec-fix.json` は前段の局所修正根拠であり、今回の新しい仕様変更ではない。

## 実装

- 本文・ラベル・ボタン等を11ptへ揃え、入力高390twipsと幅・見出し高さ・Tab順を調整。装飾OptionGroupをRectangleと文字幅に応じたラベルへ変更する。
- 管理番号を「自動」と明示しTab対象外へ。学籍番号は新規で入力可能、既存は読取専用を保つ。
- 直接編集フォーム起動で、`EnsureMaps:`がVBAラベルと解釈され初期化が抜け、`edits.Add`でエラー91となる旧実装を特定。明示`Call`、初期化中のイベント抑止、段階診断、失敗時の保存禁止へ修正。試験内の取消/清掃呼出も同じ曖昧な書式を除去する。
- 郵便番号はnativeマスク`000\-0000;1;_`で3桁–4桁表示・7桁保存。全角キー入力と全clipboard正規化を補助する。過長のRibbon/native貼付が黙って切り詰められる問題を検出し、貼付入口の検査を追加する。保存サービスでも再検査する。
- `modSampleData`が架空クラス4/学生12/監査16を正規業務サービスから作成する。既定在籍/休学検索は9件。定員満杯/空/前年停止クラス、4在籍状態、先頭ゼロ、和暦境界、補助Unicode、NULLを含む。
- サンプル追加はビルド用隔離stagingまたは明示試験fixtureだけに限定し、完成品では追加許可を無効化する。再確認で既存編集・論理削除・利用者追加行を保持し、予約キー衝突や不足は挿入前に停止する。Form_Loadで投入しない。
- VBEのANSI投入で中点・補助文字が`?`へ化ける問題を検出し、ChrWで構築。VBEを通らないPowerShellのコードポイント期待値でもDB実値を照合する。

一覧描画の安定性として、callback識別子の一意性、描画中のDB照会排除、native呼出中のフォーカス保持、busy中の終了取消、編集状態のForm_Close時解放を追加した。開発中に観測したnative例外の単一原因は未確定であり、改善後の反復試験と今回の通し検査を証拠とする。

## 検査と公開

最新の通し検査は [summary.json](../test-results/summary.json) を正とする。開発途中のPASSは最終合格へ合算しない。正式試験コードとfixture定義は`tests/`、実行コピー・診断・コンパイル途中はGit除外の`.tmp/`へ置く。

| 検査 | 固定記録 |
| --- | --- |
| 業務・拡張・検索・全件境界・既存実フォーム/権限 | application.json |
| 同一Accessプロセスのフォーム試験10回・件数保持・正常終了 | form-lifecycle.json |
| 複合FK・最終1席2プロセス競合 | relationship.json / race.json |
| サンプル・冪等性・利用者変更保持・独立Unicode照合 | sample-data.json |
| 実native入力・新規保存/再表示・フォント/枠・新しい完成品の画面 | native-quality.json / native-quality.png |
| Clipboard保護機構の合成ペイロード・暗号化退避・排他 | postal-clipboard-protection.json |
| Clipboard貼付・不正桁・切捨て防止・既存値保持・復元 | postal-paste.json |
| 完成ACCDBの件数・役割・外部リンク・試験コード除外 | deployment.json |
| 初期状態/物理形式・メッセージ・パス境界・PS構文 | format-initial-state.json / message-encoding.json / path-validation.json / syntax.json |
| ソースZIPのハッシュ/隔離と、原仕様なし独立Accessコンパイル | source-package-validation.json / source-package-build.json |

最終ACCDBを生成後に旧合格を失効させ、現在のACCDBを変更せず複製して検査する。入力と実ソースのSHA-256を検査前後で照合する。完成ACCDB、source.zip、最新検査記録、入出力manifestは`build/`の固定パスを更新する。履歴はGitへ委ねる。

今回の範囲は64bit Access 16のローカルACE。Office32bit、他DPI/物理キー/Japanese IMEでの利用者受入、10万行/20利用者性能、共有切断、確定応答喪失、本番配備、共有SQL移行、逆生成・正式採点は未実施。10000/10001件は機能境界であり性能保証ではない。formalScoreはnull。
