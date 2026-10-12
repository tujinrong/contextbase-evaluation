"""Event comparison extension; only the reference side reads input sources."""
from __future__ import annotations
import json,re
from pathlib import Path
from overviewgen.core import save,digest
from .pilot import json_contract
from .spec_revision import EVENT_CONTRACT

METHODS=['txtReducePercent_LostFocus','txtDiscount_LostFocus','btnCalc_Click','chkMinus_Click','cmbBook_SelectionChanged','btnPrice_Click','txtPostalno_LostFocus','_SetDiscount','_SetSeikyuTanka','_SetOrderFromMaster','_InitOrder']


def generate_events(specs:Path,dest:Path,templates:Path):
    document=specs/'概要仕様書TKL-011_特別出版注文入力.md';contract=json_contract(document,'tested_event_ids')
    if contract!=EVENT_CONTRACT:raise ValueError('Unsupported or inconsistent event contract; update adapter and tests explicitly')
    values={'GUARDED':','.join('"'+x+'"' for x in contract['guarded_events']),'POSTAL_LEFT':contract['postal']['lengths'][0],'POSTAL_RIGHT':contract['postal']['lengths'][1]}
    for name,key in [('MINUS','true'),('PLUS','false')]:
        for token,field in [('QUANTITY','quantity'),('LENGTH','maxlength'),('STYLE','style')]:values[name+'_'+token]=contract['minus_effects'][key][field]
    source=(templates/'Events.vb.in').read_text(encoding='utf-8')
    for name,value in values.items():source=source.replace('@'+name+'@',str(value))
    if re.search('@[A-Z_]+@',source):raise ValueError('unresolved event template token')
    save(dest/'Events.vb',source)
    evidence={'source_access':'none','input':document.name,'input_sha256':digest(document.read_bytes()),'template_sha256':digest((templates/'Events.vb.in').read_bytes()),'output_sha256':digest(source),'contract_version':contract['version'],'coverage':'seven selected event bodies; mocked UI synchronization and I/O'}
    save(dest/'event-generation-manifest.json',evidence)
    return evidence


def prepare_extension(root:Path,data,base:Path):
    templates=Path(__file__).parent/'templates'
    generate_events(base/'spec-input',base/'reimplementation',templates)
    manifest=json.loads((base/'reference/source-manifest.json').read_text())
    def extract(filename,name):
        hits=[m for m in data['methods'].values() if Path(m['path']).name==filename and m['name']==name]
        if len(hits)!=1:raise ValueError('Missing/ambiguous reference method '+name)
        m=hits[0];raw='\n'.join((root/m['path']).read_text(encoding='utf-8-sig').splitlines()[m['line']-1:m['end']])
        transformed=re.sub(r'\s+Handles [^\n]+','',raw)
        manifest.append({'source':m['path'],'method':name,'line':m['line'],'end':m['end'],'sha256':digest(raw),'transform':'Remove Handles attachment only; body unchanged'})
        return transformed
    src=next(f['code'] for f in data['features'] if f['id']=='TKL-011')
    text='''Option Strict Off
Imports System
Imports System.Collections.Generic
Public Partial Class OriginalFeature
    Private btnPrice As New DummyButton()
    Private cmbBook As New DummySelection()
    Public Function RunEvent(name As String,model As SpecialModel,active As Boolean,mode As String,minus As Boolean,selected As Boolean) As String
        _Model=model : CommandMode=mode : IsRaiseControlChanged=active : chkMinus.IsChecked=minus
        cmbBook.SelectedItem=If(selected,New Object(),Nothing)
        btnPrice.IsEnabled=False : txtSendCopies.MaxLength=4 : txtSendCopies.Style="initial"
        Dim failure=""
        Try
            Select Case name
                Case "rate" : txtReducePercent_LostFocus(Nothing,Nothing)
                Case "discount" : txtDiscount_LostFocus(Nothing,Nothing)
                Case "calculate" : btnCalc_Click(Nothing,Nothing)
                Case "minus" : chkMinus_Click(Nothing,Nothing)
                Case "book" : cmbBook_SelectionChanged(Nothing,Nothing)
                Case "price" : btnPrice_Click(Nothing,Nothing)
                Case "postal" : txtPostalno_LostFocus(Nothing,Nothing)
                Case Else : Throw New ArgumentOutOfRangeException(NameOf(name))
            End Select
        Catch ex As Exception
            failure=ex.GetType().FullName
        End Try
        Return EventCases.Snapshot(_Model,btnPrice.IsEnabled,txtSendCopies.MaxLength,CStr(txtSendCopies.Style),failure)
    End Function
'''
    text+='\n'.join(extract(Path(src).name,n) for n in METHODS)+'\nEnd Class\n'
    text+='\nPublic Partial Class MyApp\n'+extract('MyApp.vb','NullToString')+'''
Public Shared Function GetAddressFromPostalno(leftValue As String,rightValue As String) As String
    Return EventPorts.ReadPostal(leftValue,rightValue)
End Function
End Class
'''
    save(base/'reference/OracleEvents.vb',text);save(base/'reference/source-manifest.json',manifest)
    old=(base/'reference/Oracle.vb').read_text()
    old=old.replace('Public Class OriginalFeature','Public Partial Class OriginalFeature').replace('Public Class MyApp','Public Partial Class MyApp')
    old=old.replace('Public Shared Sub UpdateSourceProperty(sender As Object)\nEnd Sub','Public Shared Sub UpdateSourceProperty(sender As Object)\nEventPorts.SourceUpdates+=1\nEnd Sub')
    old=old.replace('Public Property UriageKbn As Integer','Public Property UriageKbn As Short?')
    save(base/'reference/Oracle.vb',old)
    stubs=(base/'harness/Stubs.vb').read_text()
    stubs=stubs.replace('Public Class DummyText\n','Public Class DummyText\n    Public Property MaxLength As Integer\n    Public Property Style As Object\n')
    stubs=stubs.replace('Queries += 1\n','Queries += 1\n        EventPorts.ObserveQuery(sql,parameters)\n')
    stubs=stubs.replace('Public Property ReducePercent As Integer','Public Property ReducePercent As Single').replace('Public Property UriageKbn As Integer','Public Property UriageKbn As Short?')
    save(base/'harness/Stubs.vb',stubs)
    program=(base/'harness/Program.vb').read_text()
    program=program.replace('{{"status",If(failed=0,"subset_pass","failed")}', '{{"run_id",Environment.GetEnvironmentVariable("PILOT_RUN_ID")},{"status",If(failed=0,"subset_pass","failed")}')
    program=program.replace('        Dim failed=Results.Where','        Results.AddRange(EventCases.Run())\n        Dim failed=Results.Where')
    save(base/'harness/Program.vb',program)
    save(base/'harness/EventHarness.vb',(templates/'EventHarness.vb').read_text())
    project=(base/'Pilot.vbproj').read_text().replace('reimplementation/Rebuilt.vb','reimplementation/*.vb').replace('reference/Oracle.vb','reference/*.vb')
    save(base/'Pilot.vbproj',project)
    family_counts={'discount_rounding':40,'unit_price':4,'quantity_and_abort':32,'sql_order_parameters_and_state':72,'price_priority':4,**{'event_'+name:40 for name in ['rate','discount','calculate','minus','book','price']},'event_postal':24}
    save(base/'harness/test-plan.json',{'family_counts':family_counts,'cases':sum(family_counts.values()),'scope':'selected method bodies; WPF and live database excluded'})
    tested={'Window_Closing','btnExec_Click','txtSendCopies_LostFocus'}|set(EVENT_CONTRACT['tested_event_ids'])
    f=next(f for f in data['features'] if f['id']=='TKL-011')
    coverage={'denominator':'19 directly declared handlers, not all inherited/routed UI events','selected_handlers':len(tested),'declared_handlers':len(f['events']),'events':[{'id':e['id'],'source_name':e['source_name'],'selected_body_comparison':e['source_name'] in tested,'wpf_routing_tested':False} for e in f['events']],'native_method_bodies':len(manifest),'full_feature_equivalence':'not_verified','note':'Selection is not proof of every branch; actual execution results reported separately.'}
    save(root/'report/pilot/event-coverage.json',coverage)
    preparation=json.loads((root/'report/pilot/preparation.json').read_text());preparation['original_method_bodies']=len(manifest);preparation['selected_handlers']=len(tested)
    save(root/'report/pilot/preparation.json',preparation)
    readme=(base/'README.md').read_text()+'''\n## イベント比較の追加

直接宣言された19イベントのうち10イベントの選択した処理本体を比較対象とした。入力値の受渡し呼出し回数、価格照会のキーと優先段階、変更対象と変更しない値、NULL・0を含む型、監視中／監視停止中を記録する。WPFのイベント発火・バインディング更新そのものを実行したわけではない。小数の率はモデルへ注入する試験であり、画面がその入力を受け付けることを意味しない。
'''
    save(base/'README.md',readme)
