# 評価根拠の必須検査

R4試行の原回答・コード・封印capsuleは保存した。R5では安全性の判定も、確認した本文の原引用を必須にする。CLEAR/CONTRADICTIONには実ソースの原引用も必要。MISSING/NOT_APPLICABLEは本文の確認範囲を示し、UNASSESSEDを空根拠から合格へ変換しない。

27件の基盤検査と29件の集計検査がPASS。R4の36行の原回答は、新しい根拠要件にも適合することを機械再確認した。新しいAI推論、回答修正、減点変更はしていない。文書全体の点数と合格は未確定。

固定7,079行・8,682点、95％、重大矛盾0・必須欠落0、本文採点と視覚確認の独立性は維持する。正式採点はR5コードを封印する新batchから開始し、旧試行を全文得点へ流用しない。

- [基盤検査](infrastructure-verification-safety-evidence-r5.json)
- [集計検査](combiner-verification-safety-evidence-r5.json)
- [既存回答の根拠再確認](probe-r4-revalidated-safety-r5.json)
