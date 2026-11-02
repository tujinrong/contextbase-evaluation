# ContextBase 逆解析成果の索引

版3.5／2026-11-01。native候補の限定改訂、先行全体解析、従来の独立Agent実行を区別する。旧候補とその由来は変更しない。

## 現行native限定改訂

`csharp_aspnet_native`のworkを`.tmp/contextbase/csharp_aspnet-native-amended/project-analysis`へ分離し、engine `99b04cce9af566ccac7b56f4ce5526a823d93bd1b438fe1d772cab15dc2a1d92`で明示改訂を実行する。同一78ファイル・4,797行の封印入力とraw index、同じ作者・検証者設定を使用する。基準候補`2c98d496c550746f8ba084c89d3e87ab542acc03d79e24319b9604c72cf801b7`の`behavior.class`と`behavior.forms`を置換対象とし、旧passは継承しない。

作者は218.53秒で新候補`7e189cea0452eba9c647b5e7cc145df0779c6f1a92ac6f2475816e456a9a716d`を保存した。2記録だけが変更され、他82記録とそのfactUsage、既存未知のID・内容、followupが一致する。旧候補のhashも不変。作者へ今回交付した原文は22ファイル・470行であり、継承した記録を今回の原文交付へ数えない。処置欄の誤ったfield名による1回の提出診断を、同じCodex会話で修正した。

2026-11-01 20:34:44 JSTに改訂＋全量検証が完了した。壁時計908.97秒（15分09秒）、作者218.53秒、検証531.59秒、provider合計との差158.86秒。最後の差には導入・準備・検査・回放などを含み、回放CPU単独の時間ではない。新規全量解析や実装・検査・exportの時間を含む値ではない。検証者は全78ファイル・4,797行を今回独立に取得し、全3義務と2指摘処置がpass、新しいfindingは0件となった。hostの回放・採用を通過し、[正式native成果](CSharp_ASPNET/native/project-analysis/contextbase.json)を出力した（SHA `56aeddcd5213932068e38e46fcba0233183d41242df8bcdfd4236a6935b6fc03`）。これはソース解析の採用で、原アプリ・MSBuild・restore・SQL・DBの実行や人手受入れを意味しない。

成功MCPは作者20・検証47、累積入力17,255,511 token（cache hit 16,580,224）、出力22,424。基礎指示・モデル設定は前候補と同一で、両roleの有効Skill数0、instructionSources空を確認し、私有認証cache変更なし・清掃成功を記録した。[固定実行報告](../srcs/CSharp_ASPNET/build/contextbase-native-run.json)に今回と先行試行の時間、版、差分保持、独立判定、export検査を保存する。

実装は[限定改訂設計](../../agents/reverses/reverse-agent/docs/ContextBase候補の部分改訂設計.md#12-native-joint候補の限定改訂v2)、固定版144件の検査は[検査記録](../../agents/reverses/shared/contextbase-runtime/build/native-tools/amendment-validation.json)を参照する。旧同一transcriptのローカル回放は143.63秒から28.05秒となったが、今回の改訂時間、新規全量解析時間、モデル時間とは別の測定である。native v2は指定既存記録の置換専用で、追加・削除・改訂候補からの連続改訂は未対応。

## 先行native全体解析

`csharp_aspnet_native`はCSharp_ASPNETの78ファイル・4,797行を、作者の連続Codex会話と独立検証で解析した。目録・関係・振舞いを含み、3 Agentの固定起動ではない。workは`.tmp/contextbase/csharp_aspnet-native-batched/project-analysis`。2026-11-01のrunは24分19秒（作者13分59秒、検証8分05秒、残り約2分16秒）。先行runの33分41秒から約28%短縮した。初期化・実装・検査時間を含まず、成果粒度も異なるため反復性能保証ではない。

候補84記録（目録56・関係11・振舞い17）、未知9件を保存した。両役割が全78ファイル・4,797行をhostから取得し、成功MCP呼出しは410から94へ減少した。一方で累積入力tokenは約1,163万から2,222万へ増加し、今回約2,152万はcache hitである。contextや費用削減を確認したとは扱わない。

この先行全量runは未採用。目録・関係はpassだが、振舞いにprofile文字列条件の過剰一般化と404／409の発生条件の混同がありfailとなった。将来runtime確認は現在義務外のfollowupとして保持され、阻害理由ではなかった。この時点でexportは拒否され、正式成果は未出力だった。[実行報告](../srcs/CSharp_ASPNET/build/contextbase-native-run.json)と[共通runtime](../../agents/reverses/shared/contextbase-runtime/README.md)で版・設定・時間・指摘を区別する。この2記録を対象とするv2の実行は上節に記載する。

## 従来の独立Agent実行（2026-10-30）

2026-10-30 09:54:59 JSTに、`csharp_aspnet`の全許可ソースを新規Discoveryから再解析し始めた。入力は`srcs/CSharp_ASPNET`、workはGit対象外の`.tmp/contextbase/csharp_aspnet-role-separated`、方式別出力は`spec-reverse/CSharp_ASPNET/{agent-name}/`である。旧草稿や旧検証の採用状態は継承しない。Discoveryの採用・公開後に、独立したRelationshipを起動して上流前提から再検証する。

両者の抽出は解析者、自層と上流前提の独立検証は検証者の基礎指示を使用する。実際のrole・指示SHA・CLI応答・使用量は各jobへ保存する。版のengineは`ccdf284a28346427e214954352a1ab6181142a48d6c3698174e6585aeb65ffd3`。snapshot、raw索引、静的宣言索引は先行実行と同一で、それぞれ`9bb6b8cecf4e8e1388936d873a1df116c6ef5eddfdb55ae485ddeb042850eaad`、`8dcf8c313e4ec3402547387ebac0f524b94230c178271b6a4cbdeb827615e776`、`6f806a619b76d4e5b5ee2a0120f3e6b0f3be304f0be3a7f0464c355205936f77`である。

索引検査は通過し、静的宣言索引の準備は12.422秒だった。現時点は実モデル解析中で、今回の採用・公開・総時間・業務品質は未確定である。指示の疎通確認や過去の途中passを今回の完走・品質改善として扱わない。原アプリ、MSBuild、restore、SQL、DBは実行しない。

8調査単位を完了して116記録の候補を得た。途中の分類scope不一致は、既存の差戻しと通常の継続操作で作者が修正し、完成済みの3草稿は再抽出していない。その後、配置支援スクリプトの`playwright`と`pyodbc`がdependency記録から漏れていることを原文照合で確認した。候補を採用前に停止し、公開Session APIから人工・独立性未確認の指摘を登録した。この指摘を独立検証の合格としては扱わない。

2026-10-30 11:20:18 JSTから、同じ入力・engineの封印済み候補を通常の部分改訂入口で継続している。元の116記録を保持し、追加可能なkindをdependencyだけに限定した。修訂候補は118記録（依存4件、主機能6件）で、2件の追加後に指摘別確認と全量の新しい独立検証を行っている。過去の部分passを継承せず、Relationshipは修訂後Discoveryの採用・公開まで待機する。基礎指示の分離だけで網羅性が改善したとは断定しない。

初回の部分改訂は未採用で終了した。全118記録の検査は117件pass・1件fail、分類43件はpassとなったが、Azure支援の「HTTPSを検査する」という記述が新規作成時の設定を過大に一般化していた。また、全体検査が学生Web入力契約・画面モデルのデータ候補不足を検出した。原文照合でも両指摘を確認した。原アプリやクラウドを実行して確認したものではない。

2026-10-30 12:32:23 JSTから、原始116記録に対する新しい人工・未検証フィードバックを用いて、3指摘をまとめた限定改訂を開始した。変更許可はHTTPS支援1記録の置換とdependency／dataの追加だけで、その他115記録と主機能の分類は保持する。workは`.tmp/contextbase/csharp_aspnet-role-separated-corrected`へ分け、旧候補・失敗検証・封印入力を上書きしない。既存のcustody導入はamend済み候補を再seed化できないため、原始候補を再利用した。引き継ぐのは未信頼の草稿であり、過去のpassではない。

この改訂で121記録（Webデータ3群・Python依存2件を追加）となり、全記録121件・分類43件・3指摘別の独立確認はpassとなった。ただし全体検査は、`IdParser.Required／Optional`によるWeb識別子・期待版の共通検証責任が既存の入力data／FormGuard／coordinator／Core正規化に収容されていないと指摘したため、採用・公開していない。元の記録の正しさと目録全体の網羅性を区別する。

追加改訂前に、取得78ファイルをWeb32件とCore／支援等46件へ分け、ソースの責務から既存記録への逆向き対応を一度照合した。大きい6ファイルは宣言・入口と関係する実装本文の限定読取りであり、全条件の完全な動作監査ではない。新たな資料上の欠落は上記IdParser以外に確認されず、WebFaultは既存記録で被覆されていた。この人工照合自体も独立検証のpassとして移植しない。

2026-10-30 13:49:58 JSTから、4指摘をまとめた原始候補の限定改訂を`.tmp/contextbase/csharp_aspnet-role-separated-coverage`で開始した。置換はHTTPS支援1件、新規追加はdependency／data／commonに限る。IdParserは1つの共通責任として登録し、消費者には根拠を持つ既存function／operation／entry／commonを用いる。元の115記録と主機能分類は保持し、全量を再び別文脈で検証する。Relationshipはこの採用・公開後に実行する。

## 静的解析を接続した先行実行（2026-10-29）

対象は`sample-project1/srcs/CSharp_ASPNET`、profileは`csharp_aspnet`、方式別固定出力は`spec-reverse/CSharp_ASPNET/{agent-name}/`である。`semantic_project=StudentManagement.Web.csproj`、`semantic_configuration=Release`を新workへ固定した。通常queryへコンパイル時の宣言・実装候補・条件付きDI登録を添え、作者と別文脈の検証者は各自の取証記録を保持する。確定した宣言をモデルに探し直させず、業務上の解釈と条件・SQL・未確定部分の確認を原文で行う。

取得78ファイル・構文Fact 1,883件は旧候補と同じsnapshotである。Web21／Core7のC#ファイルについて、対応する静的project構成は完全、compiler errorは0件。対象raw呼出位置1,373件はresolved 1,308／candidates 49／unresolved 16件となった。resolvedの内訳はソース宣言549件、framework等のmetadata宣言759件で、条件付きDI登録の観測は8件である。別にraw位置へ接続できないcompiler観測112件を残す。これはコンパイル時の宣言束縛であり、実行時の実装選択、業務関係、SQL列の正しさを一括証明しない。

原始索引全体の呼出位置は1,427件である。残る54件は独立projectの`maintenance/Program.cs`（32件）、`deployment/DatabaseSmoke/Program.cs`（12件）、`deployment/LoginPasswordHash/Program.cs`（10件）にあり、今回指定したWeb projectの参照閉包に含まれない。通常queryではこれらも原始事実として取得できるが、今回の派生索引によるコンパイル時束縛は添付しない。SQL、Razor生成、Java等を含む全言語・全工程の静的解決率とは扱わない。

実行workはGit対象外の`.tmp/contextbase/csharp_aspnet-semantic-bounded`である。初期自動交付を8,000文字以内・最大2つのソース接続callerに制限した版で、2026-10-29 17:17 JSTに実モデル実行を開始した。プロセス中断後、17:48 JSTに同じ版・同じ入力の完成checkpointから通常launcherで継続した。継続時の完成済み計画と2草稿は再抽出せず照合し、未完成の草稿は再開対象となった。現時点では採用・公開前であり、全体時間と品質の最終値を確定していない。中断空白、保存済み応答の呼出し・token使用量、未完了呼出し、検査・再生時間を区別する。応答を保存できなかった中断呼出しの実費は、このローカル集計から確定できない。

先行候補は105記録である。主機能6、子操作8、共通21、データ23（物理表9・DTO等14）、技術入口20、support19、material6、dependency1、system1に分かれる。候補SHAは`ecf20162a25d7e3abdae5b0a4ccb06e76d016bbf8abc846c87d11b47fc3b9d5e`。9草稿の完了後、`data:table-t-confirmation`の空のfactUsageを局所修訂し、元記録・DDL・設定の証拠を保持した。最終的に全105記録と分類35件はpassとなったが、全体scope検証が配備用Pythonスクリプトの`playwright`／`pyodbc`依存登録漏れを検出したため、catalogは未採用・未公開である。2026-10-29 21:45 JSTに当該実行を停止し、Relationshipは開始しなかった。途中のpassを今回の前提成果へ流用しない。

今回の途中観測では、静的索引の準備は約11.2秒で、モデルが交付済みのFormGuard等の宣言束縛を再利用している。一方、局所修訂に9ラウンドを要した例や、既知のfact IDを直接queryできるのに誤った登録名から4ラウンド検索した例がある。後者の実際の対象は`AddSingleton<LocalLogin>`であり、`AddScoped`の名前推測で取れなかった。これは宣言解析の再実行ではなく、取証の選択・回復の問題である。同一unit内のcontext増大と、ローカルの証拠・snapshot検査にも時間が残る。静的解決数から全体の速度改善を断定しない。

最初の診断実行は過大な初期交付を検出して明示中止したもので、今回の完走実績に混ぜない。正常フロー、独立検証、継続、原ソース・helper失効、引用権限の試験を実施したが、合成試験のpassを本案件の採用へ読み替えない。現行の接続契約は[通常D/Rへの接続](../../agents/reverses/shared/contextbase-runtime/docs/CSharp呼出先の静的解決.md#6-通常drへの接続)を参照する。

## 先行実行の保持状態

対象は`sample-project1/srcs/CSharp_ASPNET`、profileは`csharp_aspnet`である。保持候補の取得対象78ファイル・構文Fact 1,883件の索引検査はpass。対象snapshotは`9bb6b8cecf4e8e1388936d873a1df116c6ef5eddfdb55ae485ddeb042850eaad`、旧候補のengineは`5b4157a97836890407be9214ba6eb5a069b48fe030fa5493649bd0d3c4026931`であり、新実装の実案件合格を表すものではない。

最初の113記録候補は21組の独立審査を完了し、112記録pass・1記録fail、分類36件passとなった。ただし、配備状態ファイルの入力／出力説明とルートREADMEの資料登録不足を残し、catalogは未採用である。再試行は9調査単位を完了して119記録候補を作成した。配備状態の説明は草稿で修正されたが、ルートREADMEを参照する記録はゼロのままである。再試行の独立審査は1組・6記録のpassまでで中止し、全体判定・採用・正式成果の更新は行っていない。

保持候補は`2a3df304984ab596c5011b4ea035fb1515d5e86d4d150e5b6c7cca73875134d4`、viewは`72c4cea9b86d8a75c31bca0370c16389d329d4f98162ea15ea620da3b0b79ea6`。候補・伝送記録・中止理由は選択profileのGit対象外`.tmp/`に保持する。既存成果や途中のpassを新候補の採用証跡として流用しない。

通常`retry`とは別に、fresh incremental Discovery workで未信頼候補を導入する`amend-candidate`を追加した。指摘別処置とCAS差分から新しい完全候補を組み立て、全量・指摘別の新しい独立検証を要求する。[候補の部分改訂設計](../../agents/reverses/reverse-agent/docs/ContextBase候補の部分改訂設計.md)と[実装計画](../../agents/reverses/reverse-agent/docs/ContextBase実装計画.md)でコード・合成確認と実案件確認を分離する。旧119記録は読取り専用の由来検査を通して外部seedへ封印したが、実案件でこの新操作はまだ起動していない。通常の`--fresh`を局所修訂へ読み替えない。

先行する小型実験は`POST /students/{id}/delete`からNative DB分岐の更新・条件・監査までを対象とする。同じ質問での原文調査、原文を固定して渡す対照、同題のキャッシュ参照、原ソースを変えないscratchコピーでの失効を調べる。実験はGit対象外`.tmp/minimal-chain-probe`へ隔離し、正式ContextBaseの採用やD→R全体の速度改善へ読み替えない。旧Source-to-Docの「74%」「保存失敗19回」は手元の該当監査を確認できず、本案件の実測として使用しない。

小型実験Aはモデル8回・入力482,310 token、固定原文Bは1回・64,588 tokenで、両方が主経路・7列更新・監査を記述した。引用の位置・hash合格だけで意味合格にはせず、Aの一部条件説明には過剰一般化があった。同題キャッシュは0.719秒・モデル0回で、不変コピーと条件変更・入力追加の失効を確認した。意味更新の再構築は未実施。呼出し解析の小型試作は18の重要CallSiteに確定接続0・正しい候補4で実被覆条件を満たさず、正式runtimeへ採用していない。詳細と限界は[実装計画§13.10](../../agents/reverses/reverse-agent/docs/ContextBase実装計画.md#1310-単一経路と呼出し解析の先行実験)を参照する。三つのAgentの役割を再分割せず、Neo4j等も追加していない。

実測では構文索引の再構築・検査は約6.2秒、最初の全実行は約102分だった。159回のモデル応答に伴うCLI・サービス待ち・推論・出力は約83分である。総壁時計時間との差額は約19分で、初期化・ローカル検査など、個別集計していない処理・待ち時間を含む。再試行中にはモデル容量不足も2回発生した。原プログラム、MSBuild、SQL、DBは実行していない。Web projectの`Compile Remove`には`spec-eval/**/*.cs`と`spec/**/*.cs`を明記し、XML静的検査のみ実施した。

## 改名後の出力と旧実行記録

現在のprojectIdはsample-project1。既定ASP.NET profileの新しい出力は`spec-reverse/CSharp_ASPNET/{agent-name}/`、WPFは`spec-reverse/CSharp_WPF/{agent-name}/`である。三つの独立Agentは選択profileの同じ方式別出力を使い、旧rootの前層成果へフォールバックしない。現行のnative採用成果は上節の専用出力へ置く。以下のroot直下の資料は旧projectの記録として区別する。

以下のroot直下のdiscovery-agent／relationship-agent資料は、改名前test-project1で実施した記録である。保持するenvelope・target・検証添付は原projectId、絶対パス、hashを変更していない。新projectの有効成果とは扱わない。旧ignored workもtest-project1/.tmpの元位置に保ち、新projectへ移行・再束縛していない。

**旧projectのdiscovery確認入口は [review.md](discovery-agent/review.md)。** 旧projectの未採用候補、範囲阻害1件、軽微な補足1件、識別SHAと実測を掲載する。当該最終検証続行は65分21.0秒。旧projectのこの実行では再抽出・fresh・後続Agentの起動を行っていない。旧contextbase.json／validationの合格を現行projectの結果に流用しない。

relationshipは [前回実行の未採用レビュー](relationship-agent/review.md)を保持する。共有DDLを含む35件の関係候補は前回の機械検査を通過したが、独立原文検証が入力長上限・読取りプロセスの起動失敗・応答契約違反で完了せず、関係義務は未採用である。これを共有DDL不足の継続や意味上の検証結果として扱わない。discoveryの前回fullモード正式成果を保持しており、今回relationship／behaviorは実行していない。

| Agent | 人手確認の入口 | 機械可読の正式成果 |
| --- | --- | --- |
| discovery-agent | [最新検証と未採用候補](discovery-agent/review.md)・[成果案内](discovery-agent/README.md) | [前回fullモードの保持成果](discovery-agent/contextbase.json)（incrementalは未採用） |
| relationship-agent | [未採用レビュー](relationship-agent/review.md)・[成果案内](relationship-agent/README.md) | 未生成（関係義務は未採用） |
| behavior-agent | [成果案内](behavior-agent/README.md) | 生成した場合のbehavior-agent/contextbase.json |

## 一括起動

Windowsでは [run-discovery.cmd](../run-discovery.cmd)をダブルクリックする。[contextbase.toml](../contextbase.toml)の既定profileに従い、discoveryだけを起動する。incrementalの同一入力では保存checkpointを継続し、--freshは所有確認後の新規実行を選ぶ。新projectのworkはsample-project1/.tmp配下に独立して作成する。改名前workの自動継続はしない。上記の23分片と範囲阻害は旧projectの実行結果であり、新projectの検査結果には流用しない。後続2層は自動起動しない。profile切替は起動引数の--profileを使う。

専用環境を準備し、launcher所有のworkで原文取得・索引検査・抽出・独立検証・ホスト採用を行う。採用結果とレビューをstagingへ作成し、同一版であることを確認してから固定出力を更新する。阻害や故障時は旧正式成果を保持する。

## 配置と判定

- contextbase.json：ホストが採用した正式な可搬成果。後続Agentは同一request・source・正確な前提版を自身の原文で独立再検証する。
- review.md／README.md：人手レビューの入口と、その成果版の内訳・制限。
- result/validation.json：採用に使った最終独立検証。単体試験の実行ログとは区別する。
- facts/：構文事実索引、最終機械検査と利用証跡。構文の存在だけで業務上の正しさを承認しない。
- target.json：profile・source・requestに対する出力slotの所有保護。可搬受渡しはcontextbase.jsonを用いる。
- 候補、伝送記録、テストログ、環境と中間物：Git対象外の.tmpへ分離する。旧result/candidate.jsonは正式成果として渡さない。

launcherの最新診断は設定work基点/discovery-agent-launch/current、公開準備中の資料は同stagingへ置く。launcher自身の所有確認を通る範囲だけを再利用・清掃し、手動CLIのwork、他Agent、入力・QA・正式テストには触れない。実装指紋が変わった手動workを自動移行せず、新規解析と既存成果の再配布を区別する。

catalogの採用を元goal全体の完了へ広げない。人手受入れ、後続層、原プログラム・SQL・DBの実行結果は、それぞれの今回の記録で判定する。
