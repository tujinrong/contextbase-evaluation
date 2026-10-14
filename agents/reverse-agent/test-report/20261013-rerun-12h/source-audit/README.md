# 独立原ソース照合

`checklist.v1.json` は学生検索・登録の封印snapshotだけをAIが読んで作成した初版です。原仕様、spec-eval、過去生成稿、当日の生成稿、採点期待値は初版固定まで読んでいません。対象は `test-project1 / CSharp_ASPNET` の2機能だけです。アプリケーション、DB、原プログラムは実行していません。

初版は40項目対応（一覧・hidden・管理情報はグループ）、53動作照合、13未確認/ソース境界差、6画面・図観点です。25ファイルの `sources` と `indexed` の全行一致、参照行範囲、安定IDの一意性、全根拠参照を検証しました。各根拠はraw sourceのSHA、indexedファイルSHA、指定範囲の行SHAを持ちます。範囲SHAはUTF-8/BOMなし/改行LF/末尾LFです。snapshotの全体sealはこの担当では読まず、指定されたsources/indexed範囲だけを読みました。

固定SHA256: `40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242`

`checklist.v1.seal.json` に固定時刻、SHA、対象sourceハッシュを保存しています。`seal_checklist.py` はAI記述内容を検証・ハッシュ化するだけで、業務ファクトを抽出・生成しません。既存sealへの上書きを拒否します。初版を後の生成稿に合わせて改変せず、本文/図/画像レビューは別ファイルへ記録します。

チェックリストは原仕様との採点表ではありません。静的に判明した実装事実、実装上の境界差、実機未検証を分けています。HTML maxlength、サーバーUnicode scalar数、SQL格納幅/SC CHECK数はそれぞれ別の値・単位です。定義されるだけでMVCから到達未確認のJSON/API経路やDB状態テーブルを稼働仕様として扱いません。

本文・図レビューは親Agentが指定する現稿SHAに対して行います。画面画像は親Agentが現稿SHAに固定して描画・native view_image確認します。初期/正常/異常/参照・編集の材料が不足した場合、ソース位置と照合IDを持つ独立欠陥として記録します。
