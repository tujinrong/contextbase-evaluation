# 汎用変換処理の昇格案

現候補は今回の `.tmp` とREPORTに限定した準備コードです。実export、本人全native画像QA、literal/equality、source/structure検査が合格した後、rootが再使用可能な形で `agents/spec-agent/tools` へ昇格します。まだ昇格・旧出力置換・業務input変更を実施していません。

## 配置候補

```text
agents/spec-agent/tools/delivery/
  run_contract.py          # 許可roots・path/sha・Windows reparse共通gate
  binding_from_review.py   # 動的計画ID集合とcollector/render metadata接続
  markdown_model.py        # 原literalとspec-metaから配置modelだけを抽出
  artifact_xlsx.mjs        # bundled @oai/artifact-tool公開APIだけで著作
  print_metadata.py        # 限定印刷metadataとraw inverse/equality検査
  verify_xlsx.py           # 独立read-only literal/様式/印刷検査
  pdf_projection.py       # 元HTML inverseと画像coverage/文字照合
  offline_pdf.py           # trusted Chromium JS無効・通信拒否・owned timeout
  publication.py          # 明示allowlist・別source/output seal・journaled2rename
  profiles/v2-62.json      # 14枠表紙/62通常/項目10/TABLE9と根拠版
  tests/                  # synthetic負例＋実native資格回帰
```

これは配置案です。機能を再設計せず、資格が取れた候補のpublic関数と検査を移します。依存package内部を変更しません。

## 設定で受け取る値

- run identity、agent role、許可workspace/run/report/source/render/collection/output roots。
- 承認済みplan/review/collection/render recordsのpath/SHA、動的documentId集合、sourceSnapshotManifestSha256、referenceMode。
- formatter profile path/SHAと根拠AGENTS/docsite版。62列の意味は「既存V2様式保持の解釈」と記録。
- bundledPython/Node/Artifact公開entry、解析専用依存、trustedChromium、Popplerのpin済みpath/version/SHA。
- 一度だけのauthoring marker receipt、metadata-only stage grant、後続publication grant。
- source完全inventoryとold output完全inventoryの別descriptor、同volumeのowned transactionroot。

年金の業務値、今回のruntime番号、固定61件、時刻、題材の文書名を汎用コードに埋めません。設定には業務本文を含めず、reviewed原稿の明示literal mappingだけを渡します。

## 昇格時に残す証拠

1. `.tmp` 資格対象のcode SHAと全実成果物SHA、元MD/HTML/画像前後一致。
2. Artifact/XML/実Excelの表示差を分けた結果、全ページ/全範囲の本人actual view一覧、全pixel coverage。
3. 設定化以外のAST/関数差分がないこと、未入力/不正roots/reparse/異mode/異cap/不足文書/文字型/画像drift/リンク欠落のsynthetic拒否。
4. 実native fixtureによる回帰と公開helperの仮想rollback回帰。実swapはrootの別許可と実bundle検査後だけ。
5. 過去のHOLDとコード準備PASSを残し、昇格を業務意味や95%の自動合格と扱わないこと。

共通guardの抽出や設定schemaの追加は昇格時の新候補です。旧資格をそのまま流用せず、差分独立監査と必要な実native再検査をしてrootが採用します。
