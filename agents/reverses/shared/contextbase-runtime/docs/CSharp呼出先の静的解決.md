# C# 呼出先の静的解決

版0.2／2026-10-29。構文上の呼出位置を、解析条件と根拠を伴うコンパイル時の宣言へ接続する。3つの独立Agentが同じPython API／CLIを使い、通常D/Rの取証は§6の明示設定で接続する。新しいAgent、グラフDB、対象アプリのビルドは追加しない。

## 1. 責務と境界

| Module | 責務 |
| --- | --- |
| `semantic_project.py` | 封印済みcsproj／props／lock、ソース選択、project参照、解析用metadataの固定 |
| `dotnet_host.py`／`dotnet/` | 自作helperだけを固定引数でコンパイル。Roslynの構文木・Compilation・SemanticModel、NuGetの内容hashを取得 |
| `semantic_calls.py` | 生FactIndexとの位置による接続、派生索引、失効確認、有界query |
| `cli.py` | 各独立Agentから同一APIを呼ぶ薄い入口 |

対象のMSBuild／restore／ビルドtask／analyzer／source generator／スクリプトを起動しない。対象CompilationをEmitせず、対象assemblyをロード・実行しない。project間の参照はメモリー上のCompilationReferenceとする。実行するのは同梱した自作helperとインストール済みSDKのコンパイラだけで、生成したhelperはGit対象外のruntime `.tmp/`へ置く。

Tree-sitterの`contextbase-source-facts/1`は変更しない。生callは引き続き`resolution=unresolved`である。`contextbase-semantic-calls/1`を別に保存し、raw ID、旧候補、旧work、119件seedの指紋を上書きしない。新しいモデル抽出・採用の記録を捏造しない。

## 2. 解析条件

対応するのはSDK形式のC#、net8.0／net9.0／net10.0、明示した単一projectからのproject参照閉包である。既定の解析構成はRelease、CLIでDebugを選べる。対象TFMに対応するC#言語版、定義済みsymbol、nullable、implicit usings、assembly名、出力種別を明示する。

封印範囲内の`Directory.Build.props`とcsprojを静的に読む。既定Compile、順序付きInclude／Remove、除外規則を扱い、欠落した明示入力や未取得のC#候補を無視しない。除外したsubtreeはproject設定で除外が確認できる場合だけ許容する。未対応の意味を変え得るCondition／Import／compiler item／targets等では構成不完全を残す。出力先計算等は実行せず、解析に使わなかった属性として記録する。許可境界の外へ設定やソースを探しに行かない。

metadataはインストール済みSDK reference packと明示したローカルpackage cacheから読む。PackageReferenceは固定版と元lockの解決版・内容hashを照合する。署名付きnupkgの内容hashはSDKのNuGet APIで取得し、抽出済みDLLが同archiveのentryと一致することも確認する。raw ZIP SHA-512を署名非依存のlock contentHashと混同しない。hash一致は発行者の信頼性や配備済みassemblyの証明ではない。不足を自動restoreやstubで埋めない。

これは対応した静的入力の解析条件であり、MSBuild全体の評価や配備環境の再現ではない。Razor生成木や任意source generatorは推定しない。metadataのTFM・版・選択元・hash、構成と制約を索引へ残す。

## 3. 呼出位置と宣言の契約

呼出位置は既存`callSiteId`、包含元`callerId`、`callerContext`、path、原文hash・行を持つ。RoslynのUTF-16位置を同じ復号原文のUTF-8 byte位置へ変換し、pathと完全なnode範囲でraw symbol／callへ接続する。名前一致で位置接続を補完しない。BOM、CRLF、日本語、補助文字と重載を回帰対象にする。

| status | 意味 |
| --- | --- |
| resolved | 記録した解析条件の下で、問題のないコンパイラ宣言束縛が得られた。source宣言はraw symbol IDにも厳密接続済み |
| candidates | 複数候補、又はcompilerは宣言を返したが構成・型・位置接続に不足がある。宣言候補と不足理由を保持 |
| unresolved | 宣言を確定できない。未接続の構文呼出位置も保持 |
| dynamic | 実行時束縛を必要とする。静的な確定先へ格上げしない |

`compilerStatus`と最終statusを分け、対象呼出のエラー、ErrorType、構成の不足を保持する。別箇所の無関係なエラーだけを理由にすべての呼出を破棄しない。元のrawが表現しない暗黙生成nodeや暗黙constructorは、無理に既存methodへ変換せず未接続として台帳に残す。

`declaredTarget`はコンパイル時の宣言である。`dispatchKind`はdirect／interface／virtual／delegate／constructor／dynamic等を区別する。interfaceの実装候補を別の`implementationCandidates`へ保存し、全行`runtimeTargetConfirmed=false`とする。lambdaの包含元を即時実行の辺にしない。

外部symbolはassembly identityとコンパイラID、metadata参照集合へ結び、ローカルsource IDや原文根拠を捏造しない。同じソースの別project文脈も区別する。

`definitionKey`と原定義の位置はraw宣言への接続に使い、具体的な型引数を持つkey・signature・`containingTypeKey`は別に保持する。`I<int>`と`I<string>`の実装候補・DI登録を混ぜず、generic methodの具体化も同じ定義IDから区別する。

## 4. DIの観測

コンパイラが実際にframeworkの`AddScoped`／`AddSingleton`／`AddTransient`へ束縛した登録を対象にする。同名の利用者定義methodは対象にしない。型引数又は単純factoryのreturn newで観測したservice／実装型と、登録callの元原文位置を保存する。factory内の条件やprofileの評価、登録の実行・上書き・最終選択は推定しない。

呼出対象のinterface型と登録service型のコンパイラIDを照合し、該当観測を`registrationObservations`へ添える。`conditional=true`、`runtimeTargetConfirmed=false`を保持する。型が実装すること、登録文が存在すること、実行時にその実装が選ばれることは別の主張である。

## 5. APIと操作

```python
index = SemanticCallIndex.open(facts, store, project="StudentManagement.Web.csproj")
index.assert_current_source()  # 現行ソースとの一致を必要とする場合
result = index.query(caller="StudentManagement.Web.WebStudentCoordinator.Delete", limit=20)
```

```text
contextbase-discovery semantic-calls --snapshot SNAPSHOT --project StudentManagement.Web.csproj --work NEW_CACHE --caller StudentManagement.Web.WebStudentCoordinator.Delete --limit 20
contextbase-relationship semantic-calls --snapshot SNAPSHOT --project StudentManagement.Web.csproj --work NEW_CACHE --validate-only
contextbase-behavior semantic-calls --snapshot SNAPSHOT --project StudentManagement.Web.csproj --work NEW_CACHE --path Core/SqlServerStudentService.cs --callee Audit
```

`SNAPSHOT`はSourceAccessの封印済みディレクトリ、`NEW_CACHE`は原ソース・snapshot・旧Agent workと別に明示する解析用cacheである。通常のSessionを開かず、旧engineのworkを書き換えない。コマンドはモデルを呼ばず、他Agentを起動しない。`--configuration Debug`、`--package-root LOCAL_CACHE`を明示できる。`--config`との混在は認めない。

CLIは既定で元ソースの現行inventoryとhashも照合し、不一致時は新snapshotを求める。過去の封印版だけを調べるときは`--frozen`を明示する。APIのqueryは明示した封印版を対象とし、現行確認は別操作である。新規ファイル・source／project変更・metadata／archive／compiler／helper変更は旧派生cacheを有効とみなさない。

queryはpath／caller／callee／text／statusを組み合わせ、既定50、最大1000件で返す。全一致数・返却数・truncatedとsnapshot／raw index／派生index版を併記する。`offset`／CLIの`--offset`で`nextOffset`を辿り、同じ索引版の全ページを取得できる。原文を重複添付せず、調査には対応する原文を別に読む。機械検査は意味上の採用や実行到達性の判定ではない。

## 6. 通常D/Rへの接続

```toml
context_mode = "incremental"
semantic_project = "StudentManagement.Web.csproj"
semantic_configuration = "Release"
```

`evidence`又は`incremental`の新workで、通常のinit／run／retry／exportへ接続する。手動initは`--semantic-project PROJECT --semantic-configuration Release`を使う。fullとbehaviorの通常taskへは接続しない。設定なしの経路は.NETを起動しない。

初期化で`semanticOptions`、raw索引と派生索引のSHA・snapshotを`semantic-runtime.json`に固定する。作者、独立検証、上流handoffの受信側検証、増分子taskへ同じローカル束縛を引き継ぐ。別環境の上流索引SHAをローカル解析の代用にしない。設定・metadata・実装版の変更、索引束縛の欠落は新workを要求する。通常run／retry／exportでは原工程の現在版も一度照合し、封印後の更新を自動採用しない。

既存`query`のrequest schemaは維持する。能力を持つtaskの応答だけに、返却callに対応する`semanticBindings`、実際の正規`declarationFacts`、条件付き`registrationObservations`と正規`registrationFacts`を追加する。queryの一致数は元の検索fact数であり、補足factを件数へ混ぜない。全体のreply文字数に収まるよう同じoffset／nextOffsetでページ化し、関係のない全グラフを添付しない。

各調査・レビューの開始時、担当path又は入口pathにあるソース宣言への接続を優先し、最大2つのcallerグループから代表callの通常queryを自動実行する。初期応答と正規factの全体を正規JSONで8,000文字以内に制限し、大きすぎる項目は自動交付せず、通常queryで取得可能なまま残す。framework呼出しだけで枠を埋めない。この初期材料は部分的なナビゲーションであり、全接続の被覆ではない。

初期応答はその子task固有の交付台帳へ保存し、継続・採用時に再構築する。作者の交付を検証者へ流用しない。関係の保持窓・進展は索引SHA＋project＋call位置で重複排除し、同じqueryの繰返しを新調査としない。モデルへ不要なcompiler内部keyは省くが、正規fact・source ID・署名・位置・状態・不確実性を保持する。原文は交付せず、条件・値・業務責務・SQLに関する引用には従来のread／searchを必要とする。

モデルはホスト検査済みの静的宣言をそのまま使い、宣言先を推測し直すためだけの検索を行わない。独立検証は業務解釈・被覆・条件・未知を検査し、同じコンパイラ束縛を別モデルで再推定する工程にしない。機械束縛を実行時接続や業務上の正しさへ格上げしない。

helperの内容・SDK・metadataは意味解析索引専用の指紋で固定する。汎用Python engineのcustody形式を変えず、helper変更時は既存の意味解析query・task・再生を拒否する。既存の旧119件と意味解析を使わないcustody導入は保持するが、意味解析を使った会話のcustodyを別workへ導入する契約は未対応として明示拒否する。

## 7. 確認範囲

学生管理の削除例はWeb21・Core7のC#ファイルを同じ封印版から解析する。18のソース照合済み呼出位置を正式回帰へ固定し、完全signatureに基づくraw宣言IDと厳密な宣言位置を検査する。interface宣言は`IStudentService.DeleteAsync`、実装候補は`SqlServerStudentService.DeleteAsync`であり、旧試作の実装先期待を静的宣言の採点へ混ぜない。factory登録根拠は`Infrastructure/WebHostSetup.cs`で別に確認する。

本版の関連回帰は107件通過した。SDK 10.0.401、同じ78ファイル封印入力の最終測定では、派生索引の初回作成・検査5.28秒、cache再読込み2.36秒、現行ソース一致検査1.24秒、有界query0.88秒だった。自作helperの初期導入やSDK導入を含む時間ではない。18接続は正しい宣言18・誤った確定0、両projectの静的Compilationはerror 0。全体1373のraw呼出位置ではresolved 1308・candidates 49・unresolved 16で、rawへ未接続のcompiler観測112も別に保持した。この全体件数は機械処理の集計であり、全接続の意味正確性を人手承認した数ではない。

上記107件と時間は静的解析底層の前改訂実績であり、本改訂の正常フローの時間へ転記しない。この確認は選択した18接続の検査である。全索引の正確性、SQL列データフロー、業務上の完全性、D→R→Bの成功、モデルtoken削減、人手受入れの合格へ外挿しない。通常D/Rの接続・実行は、別の新workと今回の検証記録で確認する。旧119候補と封印入力は改訂しない。

## 8. 参照

[Roslyn SymbolInfo](https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.symbolinfo)、[CompilationReference](https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.compilation.tometadatareference)、[SDKの既定項目](https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview)、[NuGet内容hashの実装](https://github.com/NuGet/NuGet.Client/blob/dev/src/NuGet.Core/NuGet.Packaging/PackageArchiveReader.cs)を参照する。
