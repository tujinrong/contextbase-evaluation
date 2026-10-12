# 独立AI計画レビューの追加

2026-10-13。新規production変更は `src/contextbase/ai/plan_review.py` だけ。新規試験は `src/contextbase/tests/test_ai_plan_review.py`。workflow、schemas、prompts、CLI、既存live job、原計画、原業務入力、原設計、評価期待表を変更していない。本フェーズで実AIは呼んでいない。

入口は次のAPI。既存plan-handoffでsnapshotへ固定した計画と、新規jobディレクトリを指定する。

```python
from pathlib import Path
from contextbase.ai.plan_review import run

review = run(snapshot, plan_file, Path(fresh_job),
             timeout=1800, deadline="2026-10-13T04:47:15Z")
```

戻りは原AI JSONのdict。新しい計画が必要なら、呼出側が `workflow.plan` の別jobへ、原計画全文と原レビューを `revision_context` として渡す。Pythonは対象業務を決めず、文章・対象名・承認値を訂正しない。CLI接続と自動計画改訂は当モジュールの範囲に含めない。

| レビュー欄 | 役割 |
| --- | --- |
| subjects | AIが発見した対象のkind/name、observed-sourceかreference-design、根拠、関連sourcePaths、既存documentIds。kindを特定の業務辞書へ限定しない。 |
| documentCoverage | 全計画文書を各1回、元pathと同一で評価。subjectとの対応を双方向照合。covered/partial/missing/unknown/not-applicableはAIの判断。 |
| reachability | 入口・呼出・登録とその根拠、探索scope、confirmed/declaration-only/not-found-in-included-scope/unknown。未検出は含まれる範囲に限り、絶対の未使用と断定しない。 |
| findings | 欠落・矛盾と改善方向。計画自体の配置や粒度はplan-structure、原実装・許可設計の判断はそれぞれのbasisで根拠を付ける。 |
| blockingUnresolved | 承認を妨げる未確定。critical/major指摘かこれが残るapproved=trueは拒否し、原値を変更しない。 |
| scopeLimits | 明記された非blockingな探索・環境の制限。制限の存在だけで承認を取り消さない。 |

新schemaは当モジュール内に閉じ、既存schemaとlive jobへ移行処理をしない。source-onlyとuser-authorized training-assistedを明示し、designをobserved implementationの根拠にはしない。manifestは一覧材料であり業務・到達性の根拠にはできない。根拠のpath/line、read scope自己申告、ID/path対応を検査するが、実際の全読取や接続の意味を機械が証明するものではない。

計画JSONは原バイトから全文をprompt dataへ渡し、要約・長い文字列の切捨てを行わない。前後のsnapshot/plan/handoff SHAを照合する。deadlineはAI呼出し直前に再計算され、30秒以内なら開始せず、完了後にも時間を確認する。jobはsnapshotの外で新規作成し、既存出力とリンク/reparse経路を拒否する。

Providerの `answer.txt` を原バイトのまま `plan-review-verified.json` へコピーし、`plan-review-handoff.json` にsnapshot、plan SHA、元plan-handoff SHA、originの検証範囲、review SHA、modeを記録する。legacy planの後付け対応を独立した開始時ハッシュ記録へ読み替えない。`verified` はschema・範囲・固定入力の検証済みを意味し、原業務の正式採点PASSではない。approved=falseでも正しいレビューを保存する。不正/未成功の原応答は保持し、verified/handoffを作らない。job隣接の `*-plan-review-before.json` / `*-plan-review-after.json` と既存workflowのsnapshot前後記録も保存する。

試験はPython 3.11.9、方式内`.tmp/pydeps`のjsonschemaで実施した人工入力とmockだけ。初回39件は38 PASS/1 FAIL（テストのread_textがCRLFをLFへ変換した比較の不備）。失敗ログ `unittest.raw.log` を保存し、期待値を原バイトのdecodeへ直した。追加した許可設計の誤basis・job symlink・自由なsubject kindを含め、最終 `unittest-r2.raw.log` は42 PASS、0 FAIL、0 ERROR、0 SKIP。実ディレクトリsymlinkの負例もこのホストで実行できた。

最終42件は、原JSON/AI bytes不変、長いliteral/改行、mode/basis、行範囲、全doc対応、subject双方向対応、到達性scope、未知保持、非blocking制限、重要欠陥承認拒否、provider失敗、deadline、plan/handoff/snapshot変更、既存job・symlink・unbound planを検査した。42件に過去CLI11、capsule17、provenance26、iteration9、旧汎用280を加算していない。コードSHAと個別結果は `results.json`。JSONのコードSHAは報告作成時に採取し、独立した実行開始時記録があるとは主張しない。

未実施は、実AI計画レビュー、業務意味・期待表の採点、完全読取のtool監査、実業務プログラムの実行、全27文書生成、ID split/merge継承の自動保証。GWF-003/005/006/007を評価・改訂へ接続する汎用入口は追加したが、その問題が実AI成果で解消したという判定はこれから行う。
