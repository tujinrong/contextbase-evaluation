# 調査に基づく改善方針

2026-10-13 JST。最初の調査で、P2がPythonの定型句として説明を完成し、P3がそのブロックをMDへ変換することを確認した。原文の条件分岐が弱い説明へ変わること、別案件の用語辞書が混ざること、構造PASSが意味の品質を保証しないことが主な問題である。詳細はresearch-architecture.mdとresearch-quality.mdを参照する。

新AI経路では、Pythonは原文を無損失で固定してAIへ渡す。AIが文書計画、根拠facts、本文を作成し、別プロセスのAIが原文と本文をレビューする。プログラムに特定業務の正解値・業務名を埋め込まない。旧互換経路は局所的な用語混入と文字列の切捨てを修正し、既存の動作を検査する。

原本の基本設計・詳細仕様の使用は利用者の追加指定による訓練材料である。source-only baselineとtraining-assistedのsnapshot、プロンプト、結果を別に保存する。期待配点付き評価資料は評価者専用とし、生成者へ渡さない。文章の完全一致ではなく、既存の意味単位・原配点で採点する。

参考にした[OpenAIのモデル最適化の公式説明](https://developers.openai.com/api/docs/guides/model-optimization)も、基準測定、文脈・指示の改善、評価による反復を推奨している。[モデル重みの強化学習](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning)は別の学習ジョブであり、本作業で実行したとは扱わない。現環境にはAPIキーがなく、利用可能な既存Codex CLIログインの推論でワークフローを調整する。[非対話Codexの公式説明](https://learn.chatgpt.com/docs/non-interactive-mode)とローカルCLI helpを照合した。

13時間の停止時刻は2026-10-13 13:47:15 JST。最初の対象はASP.NET pilotだけ。元ソース・原仕様・評価資料は読取り、試行はreverse-agent/.tmp、訓練MDはtest-project1/spec-analysis、実測はreverse-agent/test-reportとする。題材の内容をプログラムへ固定する改善や、配点の変更で閾値を満たす改善は採用しない。

現在は実行中であり、正式得点・95%達成・他方式への汎用性・input全体の再解析を合格とは報告しない。
