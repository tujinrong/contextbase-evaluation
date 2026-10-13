# 第4稿 学生登録・編集画面 独立評価

評価者 `/root/evaluation_inventory/grade_details`。training-assisted。生成仕様4.0、現行原仕様8.0、採点表7.4。新稿全文1148行と161原行を新規再読し、旧一致点を使用していない。

確定 **150/169点**。一致150行、欠落7行/10点、矛盾2行/6点、保留2行/3点。0点の診断82行を保持。重要矛盾0。保留が残るため完了得点・達成率は未確定。

欠落は概要の責務・IO境界一式、参照画面の配置意味、生年月日と内部元号のraw上限設計、UI処理中・応答世代の具体契約、補足の開発入力/試験実施責務。原行の意味単位で判定し、物理容量だけを業務長として加点していない。

新規・既存読込のフローは、非空Context.Get成功枝もReturnRevision=NULLのSnapshot節点へ合流する。Controller25は現在Revisionを保持するため、当該2つのFLOWを矛盾とした。正しい別手順・結果説明へ重複減点していない。対象は復帰検索状態版であり、学生期待RowVersionやDB保存成功版ではない。元重要分類はNOT_CLASSIFIEDで、認可迂回・学生期待版上書き・未確定Saved通知に該当しない通常矛盾と判断した。

削除不備時の原入力保持保証と、現行非Saved後LoadによるDB最新値/版/新Snapshotの生成は適用裁定待ち。新稿の実装観測は正確であり、生成矛盾へ置換せず2原行をnullで保留した。原仕様品質軸と再現軸を分けた。

1064の表内未escape縦棒は表示セル分裂の診断を記録した。raw式・結果と1069等の意味は正確であり、新配点行や追加減点を作っていない。実HTML/PNGの閲覧はrootの別監査で、本評価者は行っていない。将来validatorを今回runtimeへ遡及適用していない。

全161最終理由・根拠を原stable ID、criterion、論理項目/操作の文脈と再照合。`row_context_guard.py`は161行のID/文脈/理由/全根拠ハッシュ結合を検査して通過した。機械検査は意味判定や合格を推論しない。

静的入力90pins、候補20pins、union130pinsをSHA照合。ソース43/許可教師11の固定入力と、使用したソースの該当範囲を新規レビューした。全43ソース行の全面監査、アプリ/DB/HTTP実行、native画像承認、Excel/PDF往復、全1408採点は実施していない。生成結合はlegacy-v1のunsealed範囲であり、sealed v2を主張しない。

保存済みlaunch-runnerのみを検査入力に用いた。runner SHA `cae525d98b1496f311539e5d515614a07d36b135b0b89a00eb11031d1f09b01e`。後続の現行driver変更を今回生成入力として扱わない。

初期JSONと初期contextレビューのbyte同一控えは保存前に上書きされた。既知SHA・訂正理由・保存欠落を `editor-evaluation-transition.json` に記録し、残存初期組立MDを `editor-evaluation-initial.md` としてそのまま保存した。初期JSONのbyte同一復元は主張しない。

最終成果物のSHA:

- editor-evaluation.json: `2d336a6fd68ba334330b4cb0af16bdcbda854438e61e55adc077f7da503b91fa`
- editor-row-context-review.json: `e423dfe0600229ba782c40356151236d358044265a8478c4ea8ef068fc5ad1ba`
- generated Markdown: `071001104d8ce7b1174dfbdccb848e04980de1d021ddc7bcf1a724780d83235c`
- selected rows: `701e387b9d425ab715c3a489bd2f96991e042283bc14de3e584a8b63dcc291c9`
- input manifest: `d3879d0d5d785f956154f75d4f8ca6eb6dee04393fce019649b3018912e69b0f`
- candidate snapshot: `62c75f03129f6180693496a5f94e431c2ca689cdd89b62855beab3a9e78c4e60`
- union manifest: `fb994346cf7023c9e15081a75620a9f91ce1dfacee582e2d4a0a01b6d47f97cb`
