<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"DOC-UI-CONFORMANCE","version":"1.0","path":"docs/UI適合検査.md","sheets":[{"heading":"適用と境界","kind":"GRID","sheet":"01_適用と境界"},{"heading":"期待値の契約","kind":"GRID","sheet":"02_期待値の契約"},{"heading":"実測の記録","kind":"GRID","sheet":"03_実測の記録"},{"heading":"判定と配布","kind":"GRID","sheet":"04_判定と配布"},{"heading":"回帰と未実施","kind":"GRID","sheet":"05_回帰と未実施"}]} -->
# UI条件と生成結果の共通適合検査

版1.0／2026-10-29。全方式の新規生成・UI改修に適用する。確定した方式別の字体、寸法、外観、読みやすさ、操作を、凍結した根拠から独立に期待値化し、今回の最終配布物の実測と比較する。Accessのptやクラシック外観をWeb・WPF・Textへ移植する規則ではない。

## 適用と境界

選択specRootの基本・詳細・方式別共通・QAに、利用者の確定条件と方式の標準既定の採用/例外を残す。文章、埋込みHTML、製品部品の同じ属性が異なる場合は、変換・単位・明示例外の根拠をそろえ、都合のよい値だけを選ばない。業務・DB・認証の再設計をUI修正へ混ぜない。過去の見本、同じAgent名、規則のmanifest包含は、今回の実装適合の証拠にならない。

UIを持つ方式はsourceRoot/profile.jsonへ`"uiConformance":{"required":true,"contract":"tests/ui-contract.json"}`を宣言する。UIを持たないCLI/ライブラリー等だけは`required:false`、空でない`reason`、同方式の凍結仕様を参照する`sourceFiles`を記す。UIのある製品を検査回避のため対象外にしない。今回の規則を凍結した生成では宣言自体の欠落も失敗とする。更新を依頼していない過去方式の成果物やmanifestを、規則追加だけで更新/合格へ書き換えない。

## 期待値の契約

正式な期待値はsourceRoot/tests/ui-contract.json、schemaVersion=1とする。実装・実測より先に仕様と確定指示の採用記録から作り、SHA-256を固定する。生成済み部品の実値を期待値へ転記してPASSを作らない。期待値変更には仕様根拠と理由を残し、新しい契約で実測からやり直す。

契約はprojectId、profileId、contractId、version、artifact.file、sources、components、rulesを持つ。artifact.fileは方式内build/の最終ACCDB、アプリ又はpublishディレクトリーで、generation/test-resultsを製品として指定しない。sourcesは同方式specRoot内のfile（repo相対POSIX）、documentId、version、sha256。今回のinputs.jsonと現ファイルの版・ハッシュに一致させ、各ruleのsourceFilesで根拠を対応付ける。

componentsは検査範囲の全製品部品をid・kind・textCapableで列挙する。画面surface、Tabの両Page、付属ラベル、一覧見出し、確認/エラー画面も必要状態を含める。OSタイトルバー等のアプリが字体を制御しないchromeは範囲外として理由を明記する。実測inventoryと異なる部品を黙って除外しない。全componentに必須rule、文字を描画する全componentにfont ruleを置く。

rulesはid、kind、target（component ID）、mandatory=true、sourceFiles、propertiesを持つ。font・dimensions・appearance・render・interactionの5種を全契約で必須とし、外観は方式ごとに採用した部品・色・コントラスト等を検査する。WebやTextへAccessの外観値を強制しない。propertiesは属性名と`{"op":"eq","value":11}`等の期待値。opはeq/min/max/range/oneOf、rangeは上下限2値、oneOfは空でない許容値配列とし、Nullや空の期待定義を認めない。fontにはfontFamily/fontSize/fontUnitが必要。寸法はwidth/heightや狭幅時overflow等を方式に合う単位で定義し、外観も部品ごとの適用可否を区別する。

## 実測の記録

sourceRoot/build/test-results/ui-observations.jsonにschemaVersion=1、projectId、profileId、任意のrunId、contractSha256、frozenInputManifestSha256、validatorSha256、artifact（file・sha256）、environment、components、observationsを記録する。validatorSha256は実測時のui-conformance.mjs本体。environmentはplatform、renderer、dpi、scale、viewportのwidth/height/unitを実測し、未測定のDPIを推測で埋めない。製品が複数ファイルならexport関数hashArtifactで全ファイルのPOSIX相対名・bytes・SHAをソートした配列のJSON.stringifyをSHA-256化する。CSSや資源だけの変更も旧観測を失効させる。

測定器と使用した試験/helperコードは必須のmeasurementSources配列へ`{"file":"tests/observe.py","sha256":"実測時のSHA-256"}`形式で記録する。fileは同方式内のtests/、tools/、src/、database/配下のPOSIX相対コードファイルとし、全使用コードと補助処理を含める。重複、外部/リンク、build/.tmp、原仕様、metadata、期待値JSON、実測・判定・画像等の証拠自身は認めない。実測中の前後一致だけでなく、gateとmanifest再検証時にも各現ファイルSHAを照合し、測定後にコードだけを変えて旧観測を使わない。

各observationsはruleId、target、method、properties（実値）、任意のevidence配列を持つ。methodはnative-property/computed-style/layout-measurement/render-review/keyboard-operation。fontはnative-property又はcomputed-style、renderはrender-review又はlayout-measurement、interactionは実キー/クリック等の意味ある操作をkeyboard-operationとして記録する。renderには今回の画像・計測記録等のevidenceを必須とし、方式内build/test-results配下のfile・sha256で参照する。期待値や実測JSON自身を画面証拠に使わない。

Accessは最終ACCDBと同一ハッシュの所有コピーから実Form/Controlの属性を読む。Webは最終publishだけを使う専用hostで実DOMのcomputed styleと矩形を測る。WPF/WinFormsは実部品、Textは採用端末のセルとキーを測り、方式の部品・単位・拡大/長文到達を検査する。生成定義の自己比較、HTML仕様モック、モデルへの値代入だけで製品適合を主張しない。幅・長文・空/エラー・新規/既存・Tab/モーダル等、仕様に必要な状態を独立ruleで記録する。

## 判定と配布

方式別preflightで入力を凍結した後に実装・ビルド・実測を行い、リポジトリーから`node agents/builds/build-agent/scripts/ui-conformance.mjs --project <project> --profile <方式> --run-id <今回ID>`を実行する。標準ライブラリーで比較し、固定build/test-results/ui-conformance.jsonへ今回のPASS/FAIL、propertyごとの期待/実値、入力・契約・実測・validator・製品SHAを残す。作業用fixture/途中画像は方式内.tmp/、最終証拠だけbuild/へ置き、履歴はGitを使う。

根拠の版/SHA、凍結入力集合、製品・契約SHA、全必須rule/property、全component inventoryを検査する。未観測、旧製品、未知rule/kind、未指定property/component、期待値欠落、font漏れ、証拠欠落/変更はFAIL。構造preflight、機能試験、見た目の自己宣言で補わない。人の目視をJSON比較だけで自動証明したことにせず、render/操作の方法と未実施を別に示す。

manifest.mjsはprofileの必須宣言を読み、契約削除での迂回を拒否し、現在の比較を再実行して保存済みui-conformance.jsonの入力/契約/実測/validator/製品SHAも再照合する。失敗・未実施・旧版ならoutputs.jsonを確定しない。testsと期待値は正本として保持する。source-only ZIPから原仕様・試験期待値とuiConformanceの試験参照を除外し、配布ソースの独立ビルドと原仕様に基づく適合判定を分ける。

## 回帰と未実施

隔離.tmp fixtureで、正常例、Tab字体漏れ、テーマ復活、寸法上書き、狭幅overflow、根拠/版不一致、未観測/未知rule、契約/証拠削除、旧ACCDB・CSS変更後の旧観測、manifest拒否、理由付き非UI例外を確認する。fixtureの合格を実アプリ合格にしない。Office/browser/処理系・bit・DPI・画面/状態・入力操作・未実施を方式内へ残し、正式受入・全利用者環境・採点は別状態とする。
