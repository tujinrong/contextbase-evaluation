# 変換・公開工程の準備手順

この記録はコードと合成検査の準備です。実文書、実変換、ステージ作成、出力置換の合格記録ではありません。

## 根拠と様式

今回のExcelは既存V2の表紙 `O6:AU36`・14結合枠、通常 `A:BJ`・62列方眼、項目一覧 `A:J`・10列を維持します。62は「既存様式を維持する」という依頼からの解釈で、利用者による数値指定ではありません。一般LISTはMarkdown宣言の列数、TABLEは宣言された9列の単一内容シートと書式用表紙です。原値・空欄・順番・図・先頭ゼロ・和暦・識別子・数式に見える文字列を変えません。

通常章から始まる場合は元の前文を通常シートに保存します。最初の章がLISTで前文がある場合は、列見出しの第1行を維持し、衝突を避けた「文書属性」通常シートを宣言章の前に置きます。追加するのは書式配置だけで、業務名、承認者、承認状態、会社値を補いません。

Excel著作はbundled Nodeの `@oai/artifact-tool` 公開APIだけで行います。印刷範囲・余白・向き・繰返しは、限定承認済みの印刷metadata接続処理だけで設定します。セル値・型・罫線・画像・結合をOOXMLで著作しません。

## 実行前の接続

1. rootが計画の正確なID集合、source-only capsule SHA、独立本文レビューと構造検査を承認します。計画文書数をコードに固定しません。analysis-reportの2件はREPORTに保持し、出力仕様書に含めません。
2. `collect_reviewed_r09.py` の承認済みcollectionと `render_reviewed_r05.py` の各render-pins/manifestを明示的に選びます。原MD、canonical HTML、全native assetがSHAで拘束され、元アプリは実行しません。
3. rootがselection・grantを固定した後だけ、`build_delivery_binding_r05.py` の機械的な接続を実行できます。grantにはsource SHAに加えてruntimeReceiptSha256とpermittedRuntimeRootを明記し、collection完全runtime inventoryのrenderer entryとrender-pinsのpath/SHAを束縛します。このbindingの権限はmetadata接続だけです。本文レビュー、native全画像、正式評価、公開承認を付与しません。
使用するruntimeは現collector r09／scope guard r05が監査済みのsource-13に限定します。rootはgrantのpermittedRuntimeRootを `D:/開発/contextbase-evaluation/agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/runtime-code/source-13/src`、runtimeReceiptSha256を `5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79` とします。新WORK/runtime-codeという配置を仮定しません。full128 runtimeFilesの正規化JSON SHA `07cc2d4ed07018b06be89a3f3df1083fc13e8368137ae9b3c8e0344bb9be66f0`、13 loadedImports、7 criticalModulesも正確に照合します。業務sourceへの一般読取り許可には拡張しません。

実binding builderはrenderer実bytesと技術receiptの前後SHAを検査しますが、残り127ファイルのfreshnessはcollection metadataだけでは保証しません。rootが実使用時にも凍結runtime full128の再検査とreceipt qualificationを維持します。これはnative表示・本文品質・source179の検査とは別の技術ゲートです。

4. 正式計画件数が確定した後、rootと同期して新runのExcel開始markerを一度だけ実行します。PDF開始markerは初回実writerの直前に一度だけ実行します。旧ASP.NETの11件markerは再実行しません。CLIのmarker acknowledgementは実markerの代わりになりません。

実行引数は次の形です。ここに実SHAや実selectionを代入するまで、これらは実行指示ではありません。

```text
build_delivery_binding_r05.py --selection <pinned-selection.json> --selection-sha256 <SHA>
  --grant <pinned-binding-grant.json> --grant-sha256 <SHA>
  --output <fresh-binding.json> --receipt <fresh-binding-receipt.json>

delivery_model_v2_62_r06.py --binding <binding.json> --binding-sha256 <SHA>
  --model <fresh-model.json>

build_xlsx_v2_62_r06.mjs --model <model.json> --model-sha256 <SHA>
  --output-root <fresh-xlsx-root> --authoring-marker-completed

export_pdf_bound_r05.py --binding <binding.json> --binding-sha256 <SHA>
  --output-root <fresh-pdf-root> --chromium <pinned-trusted-exe>
  --chromium-sha256 <SHA> --poppler <pinned-pdftoppm>
  --poppler-sha256 <SHA> --stage-timeout 90 --total-timeout 900 --pdf-marker-completed
```

bundled Python/Node、解析専用のpin済みbs4・markdown_it・Playwright、Artifact公開entry、Chromium、Popplerのpath/version/hashを実行前後に確認します。inputをPYTHONPATHに追加しません。解析依存の利用許可は業務アプリの実行許可ではありません。

新run markerの所在は以下です。rootが所有し、各初回実著作直前にだけ実行します。この準備作業では両markerを実行していません。

```text
C:/Users/tujin/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1011.11113/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs
C:/Users/tujin/.codex/plugins/cache/openai-primary-runtime/pdf/26.1011.11113/skills/pdf/container_tools/mark_artifact_operation_started.mjs
```

## 変換後の合否

- Markdown、HTML、画像を原bytesのまま保存します。PDFは同canonical HTMLに印刷CSSと機械的画像閲覧補助だけを加え、逆変換で元HTMLとの一致を確認します。JSを無効、Service Workerを拒否、全通信をabortし、所有worker treeとtimeoutを記録します。
- PDFは全章・表値・重複・順序の実PDF抽出文字と照合し、全ページをPopplerで画像化します。本人が全ページの原寸画像を実見するまでnative合格にしません。A3横・scale 1の候補はExcelのA4印刷設定とは別記録です。
- Excelは全literal/空欄/順序、3様式とTABLE特例、枠外の無罫線、罫線3種類、結合、列幅、図、印刷metadata、全範囲coverageを独立検査します。Artifact native previewに識別子途中折れがあればHOLDを保持します。必要な実Excel静的確認はowned ReadOnly/UpdateLinks=0/マクロ無効/非表示/neverSaveだけで行い、保存や業務動作確認とは呼びません。
- source-onlyの不明事項と正式評価率は変換器で解決・合格に読み替えません。rootの本文/source/structure/native/equality全ゲートが別途必要です。

## 公開ファイル配置

出力は `D:/開発/contextbase-evaluation/agents/reverse-agent/output` だけです。公開planは原canonical MD階層をキーに、MD/PDF/XLSXの同stem・階層と、文書別HTMLディレクトリを宣言します。

```text
<MD-prefix>/<canonical/path.md>
<HTML-prefix>/<canonical/path-without-md>/<original-stem>.html
<HTML-prefix>/<canonical/path-without-md>/<original-render-asset-name>.png
<PDF-prefix>/<canonical/path.pdf>
<XLSX-prefix>/<canonical/path.xlsx>
index.md
manifest.json
```

例えば異なるrender dirに同名の `layout-1.png` があっても、それぞれのHTML文書ディレクトリに元名のまま置きます。HTML本文のURLを書き換えて衝突を避けません。Markdownのnative assetを公開する場合は、その文書ディレクトリの `assets/` に元名で明示選択し、元本文から実際に解決できることを検査します。どちらもlinkcheckが実配送先を確認し、未解決ならHOLDです。

root indexはAIが実bundle metadataを確認して作成・レビューしたbytesだけを選びます。analysis/*.mdや未生成文書へのリンクが残れば、stage linkcheckはHOLDにします。Pythonによる業務本文・indexリンクの補修はしません。レポート、QA回答、旧cache、provider raw応答、採点材料はoutputにコピーしません。

## ステージと置換

公開候補は `publication_bound_r04.py` です。独立監査が完了するまで実stageにも使いません。

1. rootがpublication plan SHAとstage grant SHAを固定します。grantは動的な正確ID集合、sourceReviewed/textCoverageReviewed/actualNativeReviewed/reviewedIndexReady、completeを必須にします。
2. original-input345、新source-capsule179、旧output906はそれぞれ別の完全inventoryで拘束します。inputとcapsuleには `protected-file-inventory/1` の正規化metadataが必要です。sourceのsealをoutput906のsealで代用しません。
3. rootの実stage許可後、初めに旧output906の全checksumと2source inventoryを照合し、fresh WORK/publication transactionへ明示pinされたファイルだけをコピーします。全bytesと実リンクを検査し、metadata manifestとstage receiptを作ります。この時点は未公開です。
4. rootが実stage manifestとstage receiptのpath/SHAを読み、全ゲートを確認した後だけ、別のpublication grantで `allowPublication=true`、`JOURNALED_TWO_RENAMES`、`acknowledgeTransientOutputAbsence=true`、stageReceipt descriptorとstageManifestSha256を固定します。
5. 再び旧906・source・stageを全照合し、旧OUTPUTをowned backupへrename、fresh stageをOUTPUTへrenameします。Windowsの各renameは個別にatomicですが、この2回を一組のatomic置換とは表現しません。中間にはOUTPUTが一時存在しない区間があります。
6. 失敗時だけ、所有identityを確認した新候補をfresh quarantineに移し、旧backupを復元して906checksumsを照合します。回復journalの書込み失敗がrollbackを飛ばすことはありません。ただし物理rename/復元自体の失敗はHOLDのまま、journal/backup/quarantineを保持します。lock receiptを残すため、再試行はrootの明示処理が必要です。削除は行いません。

```text
publication_bound_r04.py --plan <pinned-plan.json> --plan-sha256 <SHA>
  --grant <root-stage-grant.json> --grant-sha256 <SHA> --action validate-metadata

# 上のroot実許可がある場合だけ --action stage
# stage実検査後の別root grantがある場合だけ --action publish
```

旧ASP.NET deadline後の新実行を12時間実績へ加えません。準備コードの合成PASSも新業務本文や公開結果の合格へ読み替えません。

## 今回採用するproducer参照

collector9 `3788d437323b5db059a3afd908d7ba0dbd3b1dcd3ec7395502fe77e95c3392bc`、renderer5 `b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe`、binding5 `a8c7a4af6b64c2dc9fb2716a60995bc73df3aafbec35eaea0ee302c61037a95d` を採用します。binding4からの変更はCOLLECTORのpath/SHAだけです。metadata collector9の追加index/reportは元のAI bytesとreview bindingを保持するmetadata工程で、report-onlyを仕様書として公開する許可ではありません。実collection/renderはまだ未生成です。

実pilotの2文書ID、承認済みcollection descriptor、各render dir/pins/manifest SHA、root selection/grant descriptorが到着すればbindingとmodelを作り、rootの各一度だけmarker直後にExcel/PDFを実変換します。新しい準備suiteは繰り返さず、実ファイルの文字一致・全native画像QAへ進みます。
