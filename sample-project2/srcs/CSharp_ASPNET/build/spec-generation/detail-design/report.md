# CSharp_ASPNET UI詳細再生成の記録

runId=sp2-ui-regenerate-20261029、detail-design、canonical-update、change_scope=ui_behavior。sample-project2/spec/CSharp_ASPNETの基本handoff/manifestと要件・確定条件を入力固定し、詳細6機能と必要な共通/API・型/規約/QA/索引・方式情報、技術メッセージMSG-041の12文書を改訂した。業務/DB本文の全面再作成は行わず、5画面6機能5表48列、83項目/17イベント、認証・seed・保存・帳票を継承する。

共通Razor shell/現在位置/独立見出し、役割別CSSトークン・確定欄幅、自然DOM順・行リンク・選択1名出力、タブ/確認/エラー/IMEと焦点の物理契約を具体化した。基本の6配置断片はバイト一致。最低14px、ログイン460/氏名260/カナ330/日付150等、200件/安定番号順/ページングなしの理由付き例外を維持する。

PH-05は未検証SearchRawと検証済みCriteriaを分け、専用Binderで空文字→null/Trimを避ける。Open/Exportは最後の全raw差分をサーバーでも先に失効させる。Newは未検索/未適用/不正な途中入力でも無検証で捕捉、Cancelは現在DOMを捕捉してからdirtyを判定しform妥当性/Saveを経ない。Unsearched/Unapplied/Failed/LimitExceededは原raw・元状態で検索0、Successだけapplied再取得と条件内選択/scroll復元。不明select rawは画面限定一時optionで保持し検索時は拒否する。旧一律再検索文/DTO/Open結果検査も同期し、後付け節だけの優先指定にはしていない。

通常のback/reloadは検索専用immutable snapshot参照をhistory.stateに置き、新State/leaseへ独立copyする。可変State/編集Draftは共有せず、コピー先変更が元liveStateを変えない。検索専用BFCache復帰も一回の新GET→resumeへ対応した。アプリ内Save/Cancelは最後の全rawを待つJSON POST成功200 NavigationEnvelope→一回GET、一回ticketで引き継ぐ。直接URL/複製/参照期限切れ、認証/所有/lease/確認の期限を既存Store内の最小契約へまとめた。ブラウザー強制離脱で最後の未ack検索値まで保証できない点と未保存編集復旧なしは区別して案内する。

MSG-041はUI状態失効だけに追加し、認証MSG-002・権限MSG-003・Busy/Unknownを優先する。古いdocumentの現在raw/対象を保持して操作停止、明示の破棄再読込だけを許し、再読込失敗でも旧表示/CanSave=falseを保つ。既知Committedに対するticket失敗をDB保存結果不明や再Saveへ読み替えない。新DB表・汎用基盤・heartbeatは追加しない。

静的検査は43文書、494リンク、43 LIST、10 TABLE（論理/物理各48列）、詳細83項目/17イベント、18列表、基本との6 strict断片一致、全H2/メタ/参照/ID、詳細SQLブロックと物理DBの保全でエラー0。F03-I01～04のraw輸送型/技術受理範囲/空値の説明だけをUI差分として変更し、検索時の業務制限・必須・書式・初期値・DB論理対応と物理列を維持する。

詳細MDから今回同じ断片を抽出し、Chromium148.0.7778.96で1366/390×768の12ケース、設計状態説明展開6、wrapper文字200%の6、計24ケースを描画/計測した。6通常面と狭幅F03/F04経歴を今回目視し、採用幅/独立見出し/対象識別/長い案件折返し/保存到達を確認。本文横溢れなし、確定基準欄幅を維持。54 Mermaidの構文解析/SVG生成もエラー0。後続の本文だけの修正では6断片SHAの不変を確認して描画を結合し、図変更は再解析した。状態説明は製品状態遷移ではなく、wrapper文字200%はOS倍率/ブラウザーzoomの実証ではない。

独立レビューはreview.json、規則/全入力/出力のID・版・SHAはmanifest.json、同一断片/描画範囲はrender.json、実装へ渡すBUI/UI-P→DUI→部品/状態/期待値/証拠はhandoff.jsonに固定する。基本6記録、親共通3文書、要件・基本・物理DB・確定条件の入力ドリフトを検査し、旧実行のPASSを今回製品の検査へ転記していない。

未実施はアプリ/ソース/ビルド/製品用UI JSON・実測、DB接続/SQL/投入、最終publishの実ブラウザー/キー/IME/履歴/警告、Excel/印刷、依存/実API互換性、利用者受入と正式採点。formalScore=null。詳細の条件設計と独立静的レビュー完了を、製品適合へ読み替えない。buildはrootの開始通知まで未開始。

旧固定render-review.jsonは旧工程の描画記録であり、今回のrender.jsonへ一本化して削除した。履歴はGitで参照し、今回のPASSと混在させない。

2026-10-30 / build実装前のDQA-UI05補正：通常form POSTエラーのreload再送、fetch303自動追随によるticket二重消費、全量JSONをform1値へ包む16k技術制限違反を避けるため、保護UIの既存JSON fetchを維持し正常移動200 NavigationEnvelope→client一回GETへ限定変更した。失敗JSONは現在GET document/raw/tab/対象を保持し、redirect:error・status/JSON shape検査で想定外応答を成功へしない。Login303、業務/DB/auth/保存結果、2MiB/1値16384、ticket所有/期限/一回消費、基本HTMLは保持。6文書の版と12候補集合を再固定する。初回詳細工程は製品source未読、今回補正はbuildのsource構成読取後・製品書込/DB/製品実測前と区分する。旧UI契約94127b…は未実装候補で、再preflight/新版UI根拠へ再束縛する。
