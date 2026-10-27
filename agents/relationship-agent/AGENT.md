<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-RELATIONSHIP","version":"1.3","path":"agents/relationship-agent/AGENT.md","sheets":[{"heading":"役割と独立性","kind":"GRID","sheet":"01_役割と独立性"},{"heading":"機能の意味と粒度","kind":"GRID","sheet":"05_機能の意味と粒度"},{"heading":"入力と前提","kind":"GRID","sheet":"02_入力と前提"},{"heading":"実行と完了","kind":"GRID","sheet":"03_実行と完了"},{"heading":"出力と権限","kind":"GRID","sheet":"04_出力と権限"}]} -->
# relationship-agent — 関係構築

版1.3／2026-10-26。独立プロジェクト・独立CLIの契約。新配置の独立導入・受渡しを構造・合成検証で確認した。実モデル品質・人手受入れとは区別する。

## 役割と独立性

機能・入口・実装・データ・共通・外部対象を根拠付きの関係として結ぶ。reverse-agentの配下ではなく、自身のsource・request・workで起動する。package／CLIはcontextbase-relationship、モジュールはcontextbase_relationship。共通runtimeはagents/shared/contextbase-runtimeに置き、reverse-agentのinstall・import・workは必要としない。

[運用規則](AGENTS.md)と[実行指示](PROMPT.md)を使う。他Agentはホストや利用者が必要に応じて別に起動する。独立検証はこの層の抽出作者と異なるtask・文脈で実行し、ローカルのホストが採用する。第4の抽出Agentや作者の自己合格にはしない。

## 機能の意味と粒度

[用語集](../GLOSSARY.md)と [機能分類境界](../shared/contextbase-runtime/docs/機能分類境界.md)を、主機能・子操作・共通の識別、分割・統合、件数集計を行う前に読む。入口、業務領域、意味上の粒度を別軸にし、UI・API・CLIや利用者roleだけで階層を決めない。

上流目録を受け取っても名称やkind=functionだけで主機能を確定しない。主機能と子操作の利用文脈上の帰属、共通の使用関係と共有責務を検査し、過分割・過統合の疑いはdiscoveryへ根拠付きで返す。同じ実装を複数文脈で使う場合も、実装の共有と業務上の帰属を混同しない。

新discoveryのcontextbase-catalog/1では、function／operation／common／unclassifiedを主／子／共通／保留としてtyped classificationと独立検査へ結び付ける。legacy記録のkindだけを新主機能へ読み替えず、旧classification欠落へnullを自動補完してhashを変えない。参照の同scope・kind・存在と意味上の粒度を確認し、入口共有は許可する。

contextbase-handoff/2のcatalogPolicyは互換拡張だが、新独立Agentの受信は合法なcontextbase-catalog/1を必須とする。discoveryは0レコードでもpolicyをexportし、後層はincomingの明示値を継承する。flagの欠落・不正値や旧handoffの自動格上げを認めず、旧入力はDから再抽出する。旧v2 task互換は裸Sessionだけに限定する。

今回の実測はdiscoveryだけで、本Agentのモデル実行や新成果生成は行わない。Dの新検査結果を本Agentの品質合格へ流用せず、portable前提と分類情報の扱いは正本と共通契約に従う。

## 入力と前提

requestはcontextbase-analysis/2の元goal・全前提グラフを保持し、各義務はid／question／stage／scope／requiresを持つ。本CLIが抽出するのはrelationship義務だけ。relationshipは同scopeのdiscovery、behaviorは同scopeのrelationshipを前提とする。

discoveryのportable handoffを受け取り、同一request・ソース・scopeを確認する。外部passは監査情報にとどめ、受信側の別文脈で目録前提を原文から再検証してから有効化する。受信handoffのrequestとソースmanifest／内容が一致しない場合は拒否し、別要求への汎用P6再利用へ広げない。前層workを開く必要はない。前提不足はneeds-prerequisitesとして返し、前層を自動実行しない。

可搬ソース束縛では絶対sourceRootを除き、それ以外のmanifest、相対パス、内容指紋、許可・除外材料を照合する。ソースの絶対配置が違っても、同一request・相対scope・材料の一致が必要である。

portable成果はcontextbase-handoff/2を使い、payload.premisesにstageから上流envelope SHAへの正確な依存を保存する。discoveryは空、relationshipは受信したdiscovery全成果のSHA、behaviorはそのdiscoveryを継承してrelationshipのSHAも持つ。audit集合や過去passを成果版の代用にせず、内容依存と原文の独立再検証を区別する。

設定モードの後続Agentのrun／retry／exportは、現在の直接前層の固定成果SHAとworkに封印したincoming SHAを照合する。behaviorでは現在のdiscovery固定成果が存在すればpremises.discoveryとも照合する。採用範囲や内容が変わればaudit集合が同じでも過時として拒否し、新handoff・新workで受け直す。

contextbase-handoff/1は推測・自動移行せず、v2成果を再生成して新workを使う。解析requestはcontextbase-analysis/2のままである。手動portable --workは受領時の固定入力に束縛し、生成元workや前層ファイルの継続的な存在・更新には依存しない。固定前層の最新版を追跡するgateは設定モードに限定する。

## 実行と完了

1. 自身の許可sourceを封印し、request・scope・能力と根拠を照合する。handoffを使う場合は受信側が原文から前提を独立再検証する。
2. 本層だけを抽出する。共有SourceAccess・アダプターで必要な原文・構造を読み、観測・推定・未解決を分ける。関係判断に必要な条件・引数・設定を読める。新対象や誤分類はdiscoveryへの補査質問にし、動作課題はbehaviorへ引き渡す。前層の実行は行わない。
3. recordにownerRequirementとdependsOnを付け、ホストがkey／version依存を固定する。未知はid・関連義務・阻害義務・範囲理由を保持する。
4. 別task・文脈の検証が原文、登録点、未調査領域から漏れ・反例を調べる。既存未知は作者の省略や上流失効で消さず、対象hashごとに影響を再判定する。
5. ホストが候補と保持成果のview、根拠、依存、検証を照合して採用する。有効な上流への補査はpassでも阻害し、未採用の将来義務への質問は引渡し材料に残す。

担当範囲の完了条件：必要な関係の起点・終点または候補集合、方向、条件、根拠、未解決理由が追跡でき、当該層の独立検証を受けられる。そのうち検証・採用できた範囲だけをローカル結果とする。元goal全体や他層の完了に読み替えない。前層だけで足りる要求、別scopeの未完了を理由に全体同期しない。

明示followupは安定ID followup:<digest> のunknownとして質問・対象義務・内容hashに束縛する。後続の独立検証はunknownChecksで各項目を判定し、原文根拠付きresolvedだけが閉鎖を意味する。acceptedやnon-blockingだけでは閉鎖しない。raw followupは監査履歴に残し、portableな活動中一覧には未閉鎖項目だけを含める。受信側の独立検証でresolvedを確認してから前提を有効化できる。引き継いだfollowupの対象義務が今回の採用予定集合へ入る場合、原文根拠付きresolvedを必須とする。この条件はローカルadoptと外部前提の有効化へ同じgateで適用し、最終behaviorも未閉鎖の本層質問を残したままcompleteにしない。未解決の有効上流と、現在候補が要求する有効上流への補査は採用を阻害する。

## 出力と権限

自身のworkへ候補・検証・採用版・未知・補査要求を保存し、受入れ済み自層成果がある場合にexportでportable handoffを出す。scope部分成果も出力できる。手動 --output はsource／work外の未作成パスに限定して上書きしない。--configによる正式exportはtarget.jsonの所有束縛、ロック、原子的更新で固定先へ保存し、同じ所有範囲・内容は冪等、異なるprofile／source／goalの上書きは拒否する。handoffは全有効記録・全未知・未閉鎖followupを保持し、raw履歴は監査用に分け、外部の合格を受信側の合格へ直接変換しない。入力・他Agentのwork・既存QAを直接変更しない。

入力はsource-only。project/spec全体とspec-evalは実行権限で禁止してsource根の外へ隔離する。CLI許可・除外パスはsource内の相対パスだけにする。入力プログラム・SQL・DB・build・pluginは実行しない。候補・試行は対象方式の.tmp/、最終成果・検査はbuild/固定先へ更新し、履歴はGitで管理する。

固定総時間・総token予算は置かず、単操作timeoutと阻害停止を区別する。hashはホスト管理下の内容整合であり認証ではない。型束縛・データフロー、一般的なcross-session増分再利用、長期運用、実モデル品質・人手受入れは別途検証する。

retryは本層の既知候補をfeedbackとして、一度だけ原文再調査・独立検証・採用を行う。初稿拒否後も使えるが、採用済み本層義務を変える場合は先にreviseする。他層や外部前提をretry／reviseで修訂せず、上流の新handoffは新workで受ける。故障停止からは同requestでresumeした後にretryする。

独立導入と合成受渡しの検証範囲は [実装ガイド](../reverse-agent/docs/ContextBase初期実装.md)を参照する。これはreverse-agentの実行依存ではなく検証記録の参照である。
