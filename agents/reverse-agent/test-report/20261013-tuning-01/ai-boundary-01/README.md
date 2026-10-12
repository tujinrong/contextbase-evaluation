# AI境界レビュー・修正

2026-10-13。対象はcapsule.py／workflow.pyと新規test_ai_provenance.py。実AI、業務原本、ASP.NETの正解期待値、spec-evalは本検査で読取・実行していない。再現材料はreverse-agent/.tmp配下の人工Cartである。provider、validation、prompts、schemas、主CLI、batchは他担当の所有で、変更していない。

## 再現した問題と修正

確認時点の実コードを.tmpへコピーし、SHA-256を [baseline-code.json](baseline-code.json) に固定してから再現した。capsule.pyは `75694C12449E4CAF4BFF9989B25497134A1766BA947FF15516B11D5C7E13EF14`、workflow.pyは `C1856BCB00D0AD96AA430D765423513A810C7E4A792772E6C032A8F6B9331ED3`。この時点では親担当によるrequire_answer、factのbasis、review identity、indexed再構築の修正が既に入っていた。初期の読み取りで見つけたそれらを、この固定版の未修正不備と混同しない。

| 優先度 | 再現 | 影響 | 対応 |
| --- | --- | --- | --- |
| P1 | 1行の原文のmanifest linesを1000へ改変すると999行の根拠が受理された | 実在しない根拠範囲を認定できる | raw bytesからbytes／encoding／行数／SHAを再計算し、indexed全文とcanonical pathも照合する |
| P1 | manifest filesを空へ変更してもverifyが通過した | 元の入力範囲の削除を検出できない | 非空の原本一覧、重複、全列挙material、schema2 seal、各job前後のmanifestSHAを照合する |
| P1 | reviewのAI呼出中に原稿を変更しても旧本文へのapprovedを現在の原稿へ適用できた | 別内容をレビュー済みと扱える | 原稿SHA前後比較、計画pin再照合、レビューhandoffへ本文SHAを保存する |
| P1 | output rootをsymlinkにするとlexical出力領域外へMDが作られた | 出力先の禁止リンクを迂回できる | outputとtargetの全祖先でsymlink／reparse pointを拒否する |

修正前の4件は [synthetic-before.json](synthetic-before.json)／[生ログ](synthetic-before.raw.log) に保存した。成功結果ではなく不備再現である。既存ファイルを上書きしない排他openも維持し、既存出力をAI呼出前に拒否する。余分なraw／indexed／reference-design materialの追加も検出する。

## 計画・段階・資料区分

新snapshotはschema2のmanifestと新規seal.jsonを作る。既に実AIへ渡したschema1カプセルは移行・再書込みしない。毎回raw／indexed／metadataを再検証し、`legacy-v1-raw-indexed-metadata-revalidated-unsealed-manifest`という限定scopeを保存する。旧schema1でmodeがない場合は、referenceSpecificationIncluded=falseかつrefs空に限りsource-onlyを派生し、`modeDerivation=legacy-v1-explicit-no-references`を記録する。新schema2にはこのmode省略例外を適用しない。

plan-verified.jsonのAI文面へ属性を足さず、別plan-handoff.jsonでplanSHA／manifestSHA／mode／scopeを固定する。select_documentが返すdict subclassの内部属性にこのpinを保持し、モデルへ渡すJSONは元AI定義だけである。計画変更、別カプセルへの流用、各AI呼出前後の入力改変を拒否する。

計画材料はmanifestの原文path、`sources/`表示path、`indexed/`表示path、列挙されたreference-designsを厳密aliasで受理する。manifest.jsonは計画のinventory材料に限る。未知pathをbasenameや類似名で補完しない。事実のbasisがobserved-sourceなら原文だけ、reference-designなら設計資料を含む根拠が必要で、行範囲は実原文の範囲に限る。manifestを業務事実の原文根拠にはしない。

後付け計画回収のAPI:

```python
recovered = workflow.bind_existing_plan(snapshot, answer_file, expected_manifest_sha256)
definition = workflow.select_document(Path(recovered["planFile"]), document_id)
workflow.document(snapshot, definition, new_job_root, output_root,
                  deadline="2026-10-13T04:47:15Z")
workflow.review(snapshot, output_root / definition["path"], definition, new_review_job,
                deadline="2026-10-13T04:47:15Z")
```

default binding_scopeはcurrent-verified-capsule-correspondence-onlyであり、開始時の独立hash記録があったと主張しない。開始時の独立記録がある場合だけ明示`binding_scope="independently-recorded-starting-manifest-hash"`を指定する。answer.txtとplan-verified.jsonは同一バイトのコピーとして保持し、元capsuleは無変更である。

deadlineはanalysis、draft、reviewの各AI呼出直前に再計算する。残30秒以下ならRuntimeErrorTimeLimitで停止し、remainingから30秒を予約して各timeoutを制限する。タイムアウトや失敗を成功として補完しない。空原稿はexport／承認の対象にしない。書き終わりのstatusはAI_DRAFT_NOT_YET_INDEPENDENTLY_REVIEWEDのままで、独立レビュー未実施をPASSにしない。

## 検査結果と未実施

最終 [boundary-regression.raw.log](boundary-regression.raw.log) は74件PASS、FAIL／ERROR／SKIP 0。内訳は新provenance23、既存capsule9、provider42。全てsynthetic／provider mockであり、本物のAI文書品質の合格ではない。最初の実装検査ではsetとdictの比較を誤って11 ERRORとなったため、[初回ログ](synthetic-after.raw.log)を保持して修正した。後の18／20件の検査は途中改訂で、74へ加算しない。

新規seal／legacy scope、byte／行／encoding、alias、basis、計画pin、原稿変更、出力リンク・上書き、段階deadlineを検査した。長文原値と空白は既存capsuleの9,000文字fixtureでも保持された。親のlive schema1原本や元AI応答は、この担当のツールで開いて書き換えていない。

未実施・限定範囲: 実LLMのホスト読取行動の完全なOS隔離、実AI原稿の意味評価、HTMLブラウザー／Graphviz／PDF、訓練参考設計とコードの業務比較は別工程。provider自体がread-only sandboxは全ホストの読取隔離の証明ではないと明記している。この試験だけでその制約が解消されたとは報告しない。MDのリンク・資源・LIST／GRID・HTMLの公開検査は他担当validationのゲートで行う。

milestoneで破棄可能な試行は.tmpのsyntheticケース／コードコピーである。再現hashとログはこの報告へ保存してあり、rootが必要な証拠を保管してから.tmpを整理できる。input、過去の生成成果、元AI応答、過去レポートを勝手に削除していない。
