# Access 最新仕様からの再生成

runId `20261025-regenerate` / test-project1 / Access。AGENTS 7.2、AG-BUILD/PROMPT 7.7に従い、`specRoot=test-project1/spec/Access`、`sourceRoot=test-project1/srcs/Access` で実行した。

## 入力と意味確認

詳細2本・基本設計・共通・方式別・DB定義・規約の意味を確認し、現在のAccess実ソースと照合した。他方式・spec-eval・旧srcs/Access/specは実装入力に使用していない。通常preflightを実行し、局所修正後に再凍結した。入力58ファイル（方式仕様42を含む）、構造0指摘でPASS。最終検査後も58件の実バイト一致を確認した。全版・bytes・SHA-256は [inputs.json](inputs.json)、構造結果は [structure.json](structure.json)。

主要入力版：検索/登録詳細8.4、プロジェクト/索引8.5、共通03 8.3、UI04 8.4、データアクセス08 8.4、項目制約09 8.4、コード10 8.2、方式別実装8.6、DB索引8.5、各物理表8.1。全入力の版はinputs.jsonを正とする。

局所誤記3件だけを修正・版更新して再凍結した。現役項目表に一致する検索20/合計54への説明修正、採用済みACEの参照先/相対リンク、試験DBの.tmp配置である。業務契約の変更ではない。[local-spec-fix.json](local-spec-fix.json) にHEAD原バイトのbeforeSHAと最終afterSHA・理由・版を列挙した。QAとfixture正本を保護した。

## 実ソース更新と維持

- 検索を全一致0～10000件一括へ変更。10001件はW-SRC-001・部分表示なし。4条件の後に上限判定し、原行10001だけの氏名一致も検査した。旧範囲引数・Page/PageSizeプロパティ・ページ操作を廃止、空の旧rawキーも拒否する。
- CriteriaFormatVersion=3、旧1/2/版不明はW-SRC-002で初期化。所有者/session/form/30分/Revision・Busyを維持。SORT/REFRESHはAppliedCriteriaを使い、条件変更未反映の通知を保持する。
- 非表示学生ID＋7表示列・許可4ソートの全体ソート＋IDタイブレークを維持。modListScrollで実native ListBoxスクロール位置と選択IDを復元する。対象フォーム内の子ウィンドウを検査し、DB照会や選択変更による代替をしない。Requery後の再描画を完了してから範囲内へ補正する。
- 実フォームをSingle Form、本文18240×8640twips、9pt、入力360/行420/ボタン390、検索一覧高4020、編集2列・項目別幅・備考/理由690へ更新。34論理項目・19保存入力を保持する。
- 未保存状態を最後の読込時raw（理由・日付4値・選択補助を含む）との比較へ変更。Control参照を保持せず.Valueをコピーする。元へ戻せば変更状態を解除し、取消は理由も初期化する。正常保存前には解除しない。重複/削除/破棄の別モーダルと既定取消を維持。
- 最新メッセージ文言を反映。環境のANSIで保持できない中点はChrWで生成する。配布自己診断・既存初期状態検査から旧ページ件数参照を除去。検査にrunId/最新入力版を記録し、初期状態/メッセージfixture検査も統合した。

新規19/更新18入力、Unicodeスカラー/正規化、和暦/西暦、マスタ存在/停止値、定員、権限、楽観版、変更なし、10分重複確認、全候補照合、一般入力を含めない論理削除、業務/監査同一保存単位を現在の契約と照合し維持した。今回の業務・拡張・FK・競合検査を再実行し、過去のPASSを流用していない。

最新DB/コード定義からschema/seedを再生成。6表・業務89列＋guard2列の物理定義、DDL本体と5分類70値seed本体は既存ソースHEADと同一で、最新入力の由来/版/ハッシュだけが変わった。[schema-review.json](schema-review.json) に記録。採用済み単体ACEを維持し、共有SQLの未確定事項を推測して移行していない。

## 今回の検査

リポジトリルートから `node agents/build-agent/scripts/preflight.mjs --project test-project1 --profile Access --run-id 20261025-regenerate` と `python -X utf8 test-project1/srcs/Access/tools/generate_schema.py`、Accessディレクトリから `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/Invoke-Verification.ps1 -RunId 20261025-regenerate` を実行した。

64bit Access 16.0で最終成果と専用fixtureのネイティブVBEコンパイラが完了（command578無効）。最終固定名のJSON/生ログは [../test-results/](../test-results/) に置く。

| 検査 | 今回の結果と境界 |
| --- | --- |
| 入力/構造 | 58入力凍結、0指摘、最終SHA一致 |
| 業務/拡張 | 31/77 PASS。専用.tmp fixtureのDAO実行 |
| 検索契約 | 50 PASS。空の旧rawキー拒否、DTO、format/revision/期限 |
| 全件境界 | 7 PASS。10000全返却/降順、10001抑止、全条件後上限 |
| nativeフォーム | 66 PASS。実ListBox42件、選択ID/scroll20復元・消失解除/scroll0、2列/寸法/19入力、raw理由/日付/年度の変更復元、取消 |
| 複合FK | 21 PASS。実ACE入力規則/参照整合性/非cascade |
| 2プロセス競合 | 別Access processで同時最終1席。1保存/1定員拒否、人数1/CREATE監査1 |
| 配布 | 19 PASS。最終ACCDB同一バイトコピー、5フォーム、学生/クラス/監査0、外部リンク0、試験モジュール除外 |
| 初期状態/物理形式 | 8 PASS。専用コピーのACE header/FileFormat12/在籍/既定ソート/旧control不在 |
| メッセージ/文字コード | 58文言完全一致、field label一致、ANSI非表現文字0、FileFormat12 |
| パス/構文 | 出力境界8 PASS、PowerShell17本PASS、方式内git diff --check |

途中の列幅丸め、縮小時のnative範囲、旧配布control参照、見出し中点、可変Control参照のraw保持を今回の検査で検出し修正した。途中失敗を合算せず、最新の通し結果だけを最終記録へ更新した。作業用DB/モジュール/補助出力は.tmp内。今回不要な過去出力削除は試行していない。

## 最終出力と未実施

最終は `build/StudentManagement.accdb` 1個、SHA-256 `3f7ffd9787fbb56273946292a27a808ff5d596b48430c5b111b11397fc21e68f`、1540096 bytes。[../test-results/summary.json](../test-results/summary.json) と一致し、配布コピー検査の前後で元成果のハッシュも一致。buildは最終ACCDB・最新test-results・generation・後続source.zip、および今回未変更の別工程spec-generationを許可、試行/VBE/fixtureは.tmp、生成履歴はGitで管理する。source.zipとoutputs manifestは最終ソース確定後に親工程が生成する。

Office32bit、手動ピクセル/キーボード受入、10万行/20利用者性能、ネットワーク切断、確定応答喪失、本番データ/配備、共有SQL移行、逆生成・正式採点は未実施。10000/10001は機能境界であり性能保証ではない。formalScoreはnull。

Native adapter参照：[Access ListBox](https://learn.microsoft.com/en-us/office/vba/api/access.listbox)、[Win32 GetScrollInfo](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getscrollinfo)。動作は今回の対象Accessで確認した。
