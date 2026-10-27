# 社員マスタPilotのDB仕様補強

対象は社員マスタ及びそこから呼ばれる共通DB処理だけ。承認済みレイアウト8状態と項目表はバイト単位で保持し、他機能88文書と既存の共通文書は変更しない。追加する共通DB処理仕様は社員Pilotの利用範囲を明記した別冊とする。

```bash
python -m pip install -e .
# Linux/macOS。WindowsではPYTHONPATHを環境変数に設定する。
PYTHONPATH=src:src-dynamic/mcterp python -m mcterpgen.employee_db --browser
```

.NETや業務アプリは実行しない。Graphviz、Playwright/Chromiumとリポジトリの原本が必要。ブラウザー確認を省くときだけ`--browser`を外す。レイアウトと項目の保持、API10件、共通契約13件、検索SQLと保存済みダンプの区別、図の描画、原本ハッシュを検査する。手修正した社員MD・共通DB文書を未確認のまま上書きしない。

汎用ER描画は`src/docsite/er_diagram.py`、対象別の根拠と記述規則は`src-dynamic/mcterp/mcterpgen/employee_db*`に配置する。ERはMermaidの基本エンティティ・属性・基数・関連の限定構文を静的SVGへ変換する。未知構文は省略せず失敗する。図は論理的な参照関係で、実際には存在しないSQL JOINや外部キーを追加しない。

`[employee-db-pilot]`を付けた変更コミットでは既存の全件再生成ワークフローをスキップし、専用ワークフローで2種類のMDと対応HTMLだけを更新する。将来、入力変更による通常の全件再生成でも、社員の新しいイベント仕様を適用する。未確認の原本変更時は停止し、古い説明を流用しない。

実API・実DB・低水準DBライブラリの内部・再実装同等性は今回の検査では未検証。生成器のテスト成功を原本業務の正しさと読み替えない。保存済みダンプは定義だけ抽出し、データ行・認証値・実名の固定補正内容は公開資料へ転載しない。
