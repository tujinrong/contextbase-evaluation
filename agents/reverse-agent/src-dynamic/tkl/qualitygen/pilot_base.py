"""Specification-only implementation generation; source access is evaluator-only."""
from __future__ import annotations
import json, re, shutil, hashlib
from pathlib import Path
from overviewgen.core import save,digest

FEATURE_METHODS=['_UpdateData','_UpdateTT302Else','_InsertTT301','_InsertTT302','_UpdateTT301','_UpdateTT302','_SetSeikyuPrice','_GetSendCopiesDefault','txtSendCopies_LostFocus','btnExec_Click','Window_Closing']


def json_contract(path,required):
    for content in re.findall(r'```json\s*\n([\s\S]*?)\n```',path.read_text(encoding='utf-8')):
        obj=json.loads(content)
        if required in obj:return obj
    raise ValueError(f'Missing implementation contract: {path.name} / {required}')


def generate_only(specs:Path,dest:Path,templates:Path):
    # This function never receives or discovers the application's source location.
    names=['概要仕様書TKL-011_特別出版注文入力.md','概要仕様書COM-001_共通仕様.md','概要仕様書COM-002_共通関数仕様.md','DB定義書.md','開発規約.md']
    docs=[specs/name for name in names]
    contract=json_contract(docs[0],'quantity');db=json_contract(docs[3],'order_columns')
    business=json_contract(docs[1],'money');functions=json_contract(docs[2],'functions');development=json_contract(docs[4],'option_strict')
    if business['money']!=contract['money'] or business['price_lookup']!=contract['price_lookup']:raise ValueError('individual/common contract conflict')
    if set(functions['functions'])!={'discount','unit_price','price_lookup','transaction_contract'} or functions['failure_state']!='unchanged':raise ValueError('unsupported shared function contract')
    if development['language']!='VB.NET' or not development['option_strict'] or development['database_access']!='evaluation_mock_only':raise ValueError('unsupported development contract')
    if contract['money']['midpoint']!='to_even' or contract['money']['clamp_zero']:raise ValueError('unsupported monetary contract; update adapter explicitly')
    if contract['workflow']['exclude_current_order']:raise ValueError('unsupported bulk scope')
    def vbarray(rows):return 'New String()() {'+', '.join('New String() {'+', '.join('"'+v.replace('"','""')+'"' for v in row)+'}' for row in rows)+'}'
    values={'ROUND_DIGITS':business['money']['round_digits'],'EDIT_LOW':contract['quantity']['edit'][0],'EDIT_HIGH':contract['quantity']['edit'][1],'NEG_LOW':contract['quantity']['add_negative'][0],'NEG_HIGH':contract['quantity']['add_negative'][1],'POS_LOW':contract['quantity']['add_positive'][0],'POS_HIGH':contract['quantity']['add_positive'][1],'ORDER_COLUMNS':vbarray(db['order_columns']),'SEND_COLUMNS':vbarray(db['send_columns']),'ORDER_TABLE':db['order_table'],'SEND_TABLE':db['send_table'],'ELIGIBILITY_TABLE':db['eligibility_table']}
    source=(templates/'Rebuilt.vb.in').read_text(encoding='utf-8')
    for k,v in values.items():source=source.replace('@'+k+'@',str(v))
    if re.search('@[A-Z_]+@',source):raise ValueError('unresolved generator token')
    save(dest/'Rebuilt.vb',source)
    manifest={'source_access':'none','inputs':[{ 'file':p.name,'sha256':digest(p.read_bytes())} for p in docs], 'output_sha256':digest(source),'independence':'Separate input interface; template and specifications authored within same assisted workflow, not independent human clean-room.'}
    save(dest/'generation-manifest.json',manifest)
    return manifest


def prepare(root:Path,data):
    base=root/'pilot/TKL-011';specs=base/'spec-input';templates=Path(__file__).parent/'templates'
    names=['概要仕様書TKL-011_特別出版注文入力.md','概要仕様書COM-001_共通仕様.md','概要仕様書COM-002_共通関数仕様.md','DB定義書.md','開発規約.md']
    for name in names:save(specs/name,(root/'output'/name).read_text(encoding='utf-8'))
    manifest=generate_only(specs,base/'reimplementation',templates)
    # Reference-only source extraction. Whole application and real DB are never executed.
    src=next(f['code'] for f in data['features'] if f['id']=='TKL-011')
    extracted=[]
    def method(filename,name):
        matches=[m for m in data['methods'].values() if Path(m['path']).name==filename and m['name']==name]
        if len(matches)!=1:raise ValueError('Ambiguous or missing reference method '+filename+':'+name)
        m=matches[0];lines=(root/m['path']).read_text(encoding='utf-8-sig').splitlines();raw='\n'.join(lines[m['line']-1:m['end']])
        # Remove only WPF event attachment, retain all statements and branches.
        transformed=re.sub(r'\s+Handles [^\n]+','',raw)
        extracted.append({'source':m['path'],'method':name,'line':m['line'],'end':m['end'],'sha256':digest(raw),'transform':'Remove Handles attachment only; original body unchanged'})
        return transformed
    refs='Option Strict Off\nImports System\nImports System.Collections.Generic\nImports System.ComponentModel\nImports System.Text\n\nPublic Class OriginalFeature\n'
    refs+='''Public _Model As New SpecialModel()
Public Orders As New List(Of SpecialModel)()
Public CommandMode As String = "ADD"
Public IsChangedInput As Boolean = True
Private _isUpdated As Boolean = False
Public DialogResult As Boolean = False
Public Closed As Boolean = False
Public IsRaiseControlChanged As Boolean = True
Private txtSendCopies As New DummyText()
Private chkMinus As New DummyCheck()
Public Sub Close()
 Closed=True
End Sub
Public Function RunPersist() As Boolean
 Return _UpdateData()
End Function
Public Sub RunConfirm()
 btnExec_Click(Nothing,Nothing)
End Sub
Public Function RunClose() As Boolean
 Dim e=New CancelEventArgs()
 Window_Closing(Nothing,e)
 Return e.Cancel
End Function
Public Function State() As String
 Return String.Join(",",IsChangedInput,_isUpdated,DialogResult,Closed)
End Function
Public Function RunQuantity(raw As String,mode As String,minus As Boolean,price As Integer) As String
 MyMessage.Last=""
 CommandMode=mode : chkMinus.IsChecked=minus : txtSendCopies.Text=raw
 _Model.SeikyuTanka=price : _Model.SendCopies=If(raw="",0,CInt(raw)) : _Model.SeikyuPrice=-987
 txtSendCopies_LostFocus(txtSendCopies,Nothing)
 Return RebuiltRules.textResult(txtSendCopies.Text,_Model.SeikyuPrice,MyMessage.Last)
End Function
'''
    refs+='\n'.join(method(Path(src).name,n) for n in FEATURE_METHODS)+'\nEnd Class\n'
    refs+='\nPublic Class MyApp\nPublic Shared Number As Integer=100\nPublic Shared Function GetNewOrderNo() As Integer\nNumber+=1\nReturn Number\nEnd Function\nPublic Shared Sub UpdateSourceProperty(sender As Object)\nEnd Sub\n'
    refs+='\n'.join(method('MyApp.vb',n) for n in ['GetBookDiscount','GetBookPrice','ConvertDateToDb'])+'\nEnd Class\n'
    refs+='\nPublic Class MasterBookModel\nPublic Property BookCd As String\nPublic Property BookNm As String\nPublic Property UriageKbn As Integer\nPublic Property UriageKbnNm As String\nPublic Property FixedPrice As Integer\nPublic Property Discount As Integer\nPublic Property ReducePercent As Integer\n'+method('MasterBookModel.vb','FindPrice')+'\nEnd Class\n'
    # Oracle must not call any implementation utility, even for output formatting.
    refs=refs.replace('Return RebuiltRules.textResult(txtSendCopies.Text,_Model.SeikyuPrice,MyMessage.Last)','Return txtSendCopies.Text & "|" & _Model.SeikyuPrice.ToString(Globalization.CultureInfo.InvariantCulture) & "|" & MyMessage.Last')
    save(base/'reference/Oracle.vb',refs);save(base/'reference/source-manifest.json',extracted)
    for name in ['Stubs.vb','Program.vb']:save(base/'harness'/name,(templates/name).read_text())
    project='''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework><RootNamespace></RootNamespace><EnableDefaultCompileItems>false</EnableDefaultCompileItems><OptionStrict>On</OptionStrict><OptionExplicit>On</OptionExplicit><RemoveIntegerChecks>false</RemoveIntegerChecks></PropertyGroup><ItemGroup><Compile Include="reimplementation/Rebuilt.vb"/><Compile Include="reference/Oracle.vb"/><Compile Include="harness/*.vb"/></ItemGroup></Project>'''
    save(base/'Pilot.vbproj',project);save(base/'NuGet.Config','<configuration><packageSources><clear /></packageSources></configuration>')
    complexity=[]
    for f in data['features']:
        ms=[m for m in data['methods'].values() if m['path']==f['code']]
        complexity.append({'feature':f['id'],'name':f['name'],'direct_events':len(f['events']),'methods':len(ms),'db_objects':len({x['object'] for x in f['db']}),'source_lines':max([m['end'] for m in ms] or [0]),'selected':f['id']=='TKL-011'})
    save(root/'report/pilot/selection.json',{'selection':'TKL-011','reason':'多明細・価格共通関数・追加修正・複数表・一括更新・確定取消の組合せ。単純な行数最大の選定ではない。','candidates':complexity})
    assessment={'status':'prepared_not_executed','feature':'TKL-011','original_method_bodies':len(extracted),'implementation_from_specifications':True,'physical_db':False,'native_language':'VB.NET','framework_note':'net8 headless harness, not original WPF target framework','full_feature_reproduction':'not_verified','missing':['WPF binding, layout and focus','live DB transaction, constraints and sequences','all original event paths','external reports and customers screens']}
    save(root/'report/pilot/preparation.json',assessment)
    readme='''# Pilot総合検証：TKL-011 特別出版注文入力

画面・モデル・共通計算・価格取得・複数表更新・送り状一括更新・保存と確定の違いを含む高複雑度機能を選んだ。単純な画面よりも横断仕様の不足を見つけやすい一方、機能全体の再現を無条件に保証する選定ではない。

## 工程
1. 原本側の複雑度を記録し、個別・共通・DB・開発規約の版を固定する。
2. 再実装生成器にはspec-inputだけを渡す。原本の参照は評価側のOracle抽出処理だけが行う。
3. 仕様からVB.NETの業務処理ソースを生成し、原本から抽出した処理本体との同一入力比較を行う。
4. 入力境界、丸め、負数、価格の優先順位、更新順・全パラメータ、確定取消、失敗後の状態を照合する。
5. 不足を個別仕様だけで解消せず、共通規則・DB辞書・例外と取引規約へ反映する。

## 実行
```bash
dotnet run --project pilot/TKL-011/Pilot.vbproj --configuration Release -- report/pilot/native-result.json
python -m qualitygen --finalize-pilot
```

## 評価境界
原本の選択したメソッド本体を変更せず、UI・DB・採番・確認操作の境界を評価用アダプターへ置換する。実DBへの接続は一切行わない。SQLとパラメータ・呼出順は比較できるが、実DBのロールバック・制約・採番の意味は未検証。実言語でコンパイル・実行した部分と、代替した外部依存とを分けて記録する。WPFの実画面と全19イベントの動作同等性は未検証であり、テスト成功を機能全体100%の再現とは報告しない。

再実装と評価は入力経路を分離しているが、同一の支援作業内で作成しており、独立した人間によるクリーンルーム開発ではない。
'''
    save(base/'README.md',readme)
    return assessment


def finalize(root:Path):
    path=root/'report/pilot/native-result.json'
    if not path.exists():raise ValueError('Native execution results are absent; cannot finalize as passed')
    result=json.loads(path.read_text());failed=int(result['failed'])
    rows=['# Pilot総合検証結果','','## 1. 実行結果','',f"VB.NET実行：{result['cases']}件中{result['passed']}件一致、{failed}件不一致。",'', '**判定：選択した業務処理の比較結果。機能全体の再実装可能性は保留。**','','## 2. 仕様書に反映した不足','', '| 不足 | 修正した仕様 |','| --- | --- |','| 数量のモード別範囲と修正時の0許容 | 個別仕様・データ例・Pilot契約 |','| 偶数丸めと負単価を0に補正しない点 | 共通業務仕様・共通関数仕様 |','| 条件別価格から基本価格への切替・未取得時・NULL | 個別価格イベント・共通価格仕様・DB定義 |','| 一括送り状更新の顧客・送付先・計上対象条件 | 個別確定イベント・DB定義 |','| 複数更新の順序・1回の共通実行・失敗時の状態 | 個別仕様・共通更新仕様・開発規約 |','','## 3. 未検証範囲','','WPFのデータ受渡し・フォーカス・実画面、全イベント、実DBの制約・取引・シーケンス・トリガー、他機能との総合動作。これらを一致件数の分母から隠して総合再現率を示すことはしない。','', '## 4. 独立性と証跡','','再実装の入力ハッシュはpilot/TKL-011/reimplementation/generation-manifest.json。原本抽出位置はreference/source-manifest.json。比較は文字列の類似度ではなく処理結果・SQL構造・値・状態を対象とする。','']
    if failed:rows+=['## 5. 不一致','']+[str(r) for r in result['results'] if not r['passed']]
    save(root/'report/pilot/Pilot総合検証.md','\n'.join(rows)+'\n')
    save(root/'.specgen-state/quality/pilot-checkpoint.json',{'stage':'native_comparison_completed','cases':result['cases'],'passed':result['passed'],'failed':failed,'full_feature':'not_verified','result_sha256':digest(path.read_bytes())})
    return result
