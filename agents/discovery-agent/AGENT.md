<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"AG-DISCOVERY","version":"1.6","path":"agents/discovery-agent/AGENT.md","sheets":[{"heading":"役割と独立性","kind":"GRID","sheet":"01_役割と独立性"},{"heading":"機能の意味と粒度","kind":"GRID","sheet":"05_機能の意味と粒度"},{"heading":"入力と前提","kind":"GRID","sheet":"02_入力と前提"},{"heading":"実行と完了","kind":"GRID","sheet":"03_実行と完了"},{"heading":"出力と権限","kind":"GRID","sheet":"04_出力と権限"}]} -->
# discovery-agent — 取得・目録化

版1.6／2026-10-27。独立プロジェクト・独立CLIの契約。新配置の独立導入・受渡しを構造・合成検証で確認した。実モデル品質・人手受入れとは区別する。

## 役割と独立性

概要、業務・システム機能、技術入口、テーブル／データ、共通処理の候補と被覆を整理する。reverse-agentの配下ではなく、自身のsource・request・workで起動する。package／CLIはcontextbase-discovery、モジュールはcontextbase_discovery。共通runtimeはagents/shared/contextbase-runtimeに置き、reverse-agentのinstall・import・workは必要としない。

[運用規則](AGENTS.md)と[実行指示](PROMPT.md)を使う。他Agentはホストや利用者が必要に応じて別に起動する。独立検証はこの層の抽出作者と異なるtask・文脈で実行し、ローカルのホストが採用する。第4の抽出Agentや作者の自己合格にはしない。

## 機能の意味と粒度

[用語集](../GLOSSARY.md)と [機能分類境界](../shared/contextbase-runtime/docs/機能分類境界.md)を、主機能・子操作・共通の識別、分割・統合、件数集計を行う前に読む。入口、機能領域、意味上の粒度を別軸にし、UI・API・CLIや利用者roleだけで階層を決めない。

主機能は指定actorが対象に対して独立した利用者目的と完了成果を説明できるタスクであり、業務機能とシステム機能の両方を含む。前提がないことを意味しない。子操作は各利用文脈で主帰属を明示する。共通は共有業務規則・集中責任・実装部品等の利用関係と根拠を持ち、独立した利用者機能の記録を代用しない。正本の具体例は候補判断の材料であり、特定件数へ合わせる答えではない。

独立したログイン画面で入力・送信・認証の成否を扱う場合は、ログインを主機能候補として可視化する。認証サービス・Cookie・共用レイアウトは別の共通能力として関連付けられる。メニューは汎用共通メニュー画面・共用ナビゲーションか顧客専用の完全画面・機能選択・ワークスペースかを責務から判定し、DB更新の有無だけで独立性を否定しない。独立画面は強い手掛かりだが、詳細・確認・ダイアログ・編集モードを一律に主機能へ昇格しない。

新discovery taskはホスト固定のcatalogPolicy=contextbase-catalog/1を使う。functionは主、operationは子、commonは共通、unclassifiedは保留とし、正本が定めるtyped classificationを必須にする。他分類はclassification=null。旧記録へnullを自動補完せず、legacy互換を新基準の合格としない。task.operation=extract／verifyは子操作のkindとは別である。

独立検証は主・子・共通・保留の全対象recordのkey／版hashをclassificationChecksへ、元要求の全scopeをscopeChecksへ正確に束縛し、ゼロrecordのscopeも確認する。scopeChecksは非意味分類を含む全viewを調べ、過分割・過統合と、support／material／dependencyへ誤分類した業務候補を探す。全検査passに加え、count-or-coverage保留がないことをhost採用条件にする。保留は実unknownへ結び付ける。

contextbase-handoff/2のcatalogPolicyは互換拡張だが、新独立Agentの受信は合法なcontextbase-catalog/1を必須とする。discoveryは0レコードでもpolicyをexportし、後層はincomingの明示値を継承する。flagの欠落・不正値や旧handoffの自動格上げを認めず、旧入力はDから再抽出する。旧v2 task互換は裸Sessionだけに限定する。

parent／entryRefs／consumers等は同scope・適正kind・実在を検査し、入口共有を許可する。意味参照はowner間の失効に含めるが、不必要な循環を生むよう版依存DAGへ強制投入しない。詳細な必須項目は分類正本を参照する。前改訂では構造・合成回帰を確認したが、70候補は未解決事項により未採用だった。検証範囲は実装ガイドに集約し、人手受入れと区別する。

Tree-sitter事実の取得・検索、call／entryの解釈、factUsage、独立factUsageCheckを扱う前に[ソース事実索引契約](../shared/contextbase-runtime/docs/ソース事実索引.md)を読む。全索引・inventoryとsourceTextを使い、task.recordKindsの許可集合だけから作者の全recordを作る。各factは同record.evidenceと同path・行交差を持ち、跨ファイルの支持factにも正確な位置・hashを記録する。構文IDの存在を業務判断の正しさへ読み替えない。今回の新機構の検証結果は実装ガイドに記録し、前改訂の70候補未採用と区別する。

証拠検査の重複を減らすとき、又は--compactを指定するときは[短縮伝送と証拠一括検査](../shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)を読む。ホストがtask専用aliasを厳密に展開して通常gateと採用時再検査を行う。全原文・全索引は保持し、原文のオンデマンド調査ループを導入済みとしない。repair追加後の回帰は確認済みで、実repairは全体機械・独立検証を完了したがcatalog未解決で未採用である。

拒否草稿の指定recordだけを回復するときは[repair契約](../shared/contextbase-runtime/docs/短縮伝送と証拠一括検査.md)を読む。fresh workで未信頼seedを照合し、モデルの許可全置換だけを合成する。旧合格は継承せず、全体の機械検査・独立verify・採用再生照合を行う。範囲変更やrecord追加削除が必要なら未解決として戻す。

## 入力と前提

requestはcontextbase-analysis/2の元goal・全前提グラフを保持し、各義務はid／question／stage／scope／requiresを持つ。本CLIが抽出するのはdiscovery義務だけ。relationshipは同scopeのdiscovery、behaviorは同scopeのrelationshipを前提とする。

この層には前層成果を要求しない。取得不足・除外・解析失敗を明示し、原文根拠を持つ目録候補を作る。本層は上流handoffを受信せず、原文から開始する。後続Agentへ渡す成果は元requestと全前提グラフを保持し、受信側が自身の原文で検証する。別要求への汎用P6再利用へ広げない。

可搬ソース束縛では絶対sourceRootを除き、それ以外のmanifest、相対パス、内容指紋、許可・除外材料を照合する。ソースの絶対配置が違っても、同一request・相対scope・材料の一致が必要である。

portable成果はcontextbase-handoff/2を使い、payload.premisesにstageから上流envelope SHAへの正確な依存を保存する。discoveryは空、relationshipは受信したdiscovery全成果のSHA、behaviorはそのdiscoveryを継承してrelationshipのSHAも持つ。audit集合や過去passを成果版の代用にせず、内容依存と原文の独立再検証を区別する。

設定モードの後続Agentのrun／retry／exportは、現在の直接前層の固定成果SHAとworkに封印したincoming SHAを照合する。behaviorでは現在のdiscovery固定成果が存在すればpremises.discoveryとも照合する。採用範囲や内容が変わればaudit集合が同じでも過時として拒否し、新handoff・新workで受け直す。

contextbase-handoff/1は推測・自動移行せず、v2成果を再生成して新workを使う。解析requestはcontextbase-analysis/2のままである。手動portable --workは受領時の固定入力に束縛し、生成元workや前層ファイルの継続的な存在・更新には依存しない。固定前層の最新版を追跡するgateは設定モードに限定する。

## 実行と完了

1. 自身の許可sourceを封印し、request・scope・能力と根拠を照合する。handoffを使う場合は受信側が原文から前提を独立再検証する。
2. 本層だけを抽出する。共有SourceAccess・アダプターで必要な原文・構造を読み、観測・推定・未解決を分ける。新対象・分類矛盾の補査は該当目録へ戻す。関係や動作の追加要求は相手Agent向けの質問として残し、自動起動しない。
3. 機能候補の過分割と過統合の両方を見直す。主とした目的・対象・成果、子操作の利用文脈と帰属、共通の共有責務を根拠付きで説明し、反例も示す。分類未確認は別に残し、現在の集計対象scopeの主機能だけを数える。recordにownerRequirementとdependsOnを付け、ホストがkey／version依存を固定する。未知はid・関連義務・阻害義務・範囲理由を保持する。
4. 別task・文脈の検証が原文、登録点、未調査領域から漏れ・反例を調べる。既存未知は作者の省略や上流失効で消さず、対象hashごとに影響を再判定する。
5. ホストが候補と保持成果のview、根拠、依存、検証を照合して採用する。有効な上流への補査はpassでも阻害し、未採用の将来義務への質問は引渡し材料に残す。

担当範囲の完了条件：取得したソース範囲と数える機能範囲を区別し、正本に従う粒度判断の理由・反例・未確認がある。主機能を2件や4件等の予定数に合わせない。各目録義務に候補・根拠付き非該当・未解決が対応し、独立検証で当該範囲を確認できる。そのうち検証・採用できた範囲だけをローカル結果とする。元goal全体や他層の完了に読み替えない。前層だけで足りる要求、別scopeの未完了を理由に全体同期しない。

明示followupは安定ID followup:<digest> のunknownとして質問・対象義務・内容hashに束縛する。後続の独立検証はunknownChecksで各項目を判定し、原文根拠付きresolvedだけが閉鎖を意味する。acceptedやnon-blockingだけでは閉鎖しない。raw followupは監査履歴に残し、portableな活動中一覧には未閉鎖項目だけを含める。受信側の独立検証でresolvedを確認してから前提を有効化できる。引き継いだfollowupの対象義務が今回の採用予定集合へ入る場合、原文根拠付きresolvedを必須とする。この条件はローカルadoptと外部前提の有効化へ同じgateで適用し、最終behaviorも未閉鎖の本層質問を残したままcompleteにしない。未解決の有効上流と、現在候補が要求する有効上流への補査は採用を阻害する。

## 出力と権限

自身のworkへ候補・検証・採用版・未知・補査要求を保存し、受入れ済み自層成果がある場合にexportでportable handoffを出す。scope部分成果も出力できる。手動 --output はsource／work外の未作成パスに限定して上書きしない。--configによる正式exportはtarget.jsonの所有束縛、ロック、原子的更新で固定先へ保存し、同じ所有範囲・内容は冪等、異なるprofile／source／goalの上書きは拒否する。handoffは全有効記録・全未知・未閉鎖followupを保持し、raw履歴は監査用に分け、外部の合格を受信側の合格へ直接変換しない。入力・他Agentのwork・既存QAを直接変更しない。

入力はsource-only。project/spec全体とspec-evalは実行権限で禁止してsource根の外へ隔離する。CLI許可・除外パスはsource内の相対パスだけにする。入力プログラム・SQL・DB・build・pluginは実行しない。候補・試行は対象方式の.tmp/、最終成果・検査はbuild/固定先へ更新し、履歴はGitで管理する。

固定総時間・総token予算は置かず、単操作timeoutと阻害停止を区別する。hashはホスト管理下の内容整合であり認証ではない。型束縛・データフロー、一般的なcross-session増分再利用、長期運用、実モデル品質・人手受入れは別途検証する。

retryは本層の既知候補をfeedbackとして、一度だけ原文再調査・独立検証・採用を行う。初稿拒否後も使えるが、採用済み本層義務を変える場合は先にreviseする。他層や外部前提をretry／reviseで修訂せず、上流の新handoffは新workで受ける。故障停止からは同requestでresumeした後にretryする。

独立導入と合成受渡しの検証範囲は [実装ガイド](../reverse-agent/docs/ContextBase初期実装.md)を参照する。これはreverse-agentの実行依存ではなく検証記録の参照である。

規則を変更したときはfresh workを用意し、旧workへ新指紋を上書きせず通常gateで再採用する。利用者の明示指示により旧成果・旧実行記録を削除して再実行する場合も、source・設定・正式テスト・target.jsonを保護する。最新の実行状態は成果READMEと実装ガイドへ集約し、旧passを新規則の合格へ流用しない。
