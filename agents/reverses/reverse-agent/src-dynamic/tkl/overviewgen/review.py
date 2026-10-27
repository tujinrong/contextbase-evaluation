"""Independent raw-source and rendered-document checks.

Uses ElementTree and separate regexes, not producer adapters or extracted counts.
Independent processing is not equivalent to independent human business approval.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET

VERSION='2.1.0'
TAGS={'TextBox','PasswordBox','ComboBox','DatePicker','CheckBox','RadioButton','ListBox','TreeView'}


def read(path):
    raw=path.read_bytes()
    for enc in (['utf-16'] if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else ['utf-8-sig','cp932']):
        try:return raw.decode(enc).replace('\r\n','\n')
        except UnicodeError:pass
    raise ValueError('unreadable original')


def local(tag):return tag.split('}')[-1]


def original_items(path):
    text=read(path)
    if '<!DOCTYPE' in text.upper():raise ValueError('DTD rejected')
    tree=ET.fromstring(text);baseline=[]
    for i,el in enumerate(tree.iter()):
        tag=local(el.tag);a={local(k):v for k,v in el.attrib.items()}
        col=tag.endswith('Column') and ('Header' in a or 'Binding' in a or tag=='DataGridTemplateColumn')
        dynamic=tag in {'Label','TextBlock'} and any('{Binding ' in a.get(k,'') for k in ('Text','Content'))
        if tag in TAGS or tag.endswith('Button') or col or dynamic:
            baseline.append({'key':a.get('Name') or 'node_'+str(i),'tag':tag,'attrs':a,'is_column':col,'source_order':i})
    return baseline


def raw_event_names(path):
    text=read(path)
    pattern=r'(?im)^\s*(?:(?:Private|Public|Protected|Friend|Shared|Async|Overrides|Overloads)\s+)*(?:Sub|Function)\s+(\w+)\s*\('
    starts=list(re.finditer(pattern,text));out=[]
    for i,m in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(text)
        signature=text[m.start():end].split('\n\n',1)[0]
        if re.search(r'\bHandles\s+',signature,re.I):out.append(m.group(1))
    return sorted(set(out))


def raw_db_names(path):
    strings=[]
    for line in read(path).splitlines():
        if line.lstrip().startswith("'"):continue
        strings += [m.group(1).replace('""','"') for m in re.finditer(r'"((?:""|[^"])*)"',line)]
    joined=' '.join(strings);refs=set()
    for p,op in [(r'INSERT\s+INTO','C'),(r'UPDATE','U'),(r'DELETE\s+FROM','D'),(r'FROM|JOIN','R'),(r'TRUNCATE(?:\s+TABLE)?','TRUNCATE'),(r'COPY','COPY')]:
        for m in re.finditer(r'\b(?:'+p+r')\s+([A-Za-z_]+\d{3}_\w+)\b',joined,re.I):
            if op=='R' and re.search(r'DELETE\s*$',joined[max(0,m.start()-12):m.start()],re.I):continue
            refs.add((m.group(1),op))
    return refs


def inspect_feature(root,feature):
    findings=[];fid=feature['id']
    def issue(rule,severity,detail):findings.append({'feature':fid,'rule':rule,'severity':severity,'detail':detail})
    source=root/feature['source'];items=feature['items']
    if source.suffix.lower()=='.xaml':
        expected=original_items(source);ek=[x['key'] for x in expected];ak=[x['key'] for x in items]
        if Counter(ek)!=Counter(ak):issue('ITEM-COUNT','error',{'原本項目数':len(ek),'骨子項目数':len(ak),'不足':list((Counter(ek)-Counter(ak)).elements()),'余剰':list((Counter(ak)-Counter(ek)).elements())})
        bykey={x['key']:x for x in items}
        for exp in expected:
            item=bykey.get(exp['key'])
            if not item:continue
            if exp['tag'].endswith('Button') and item['role'] not in {'operation','internal'}:issue('ITEM-ROLE','error',exp['key']+'：ボタンを値入力に誤分類')
            if item['role']=='operation' and (item.get('db') or item['required']!='対象外' or item['length']!='対象外'):issue('ITEM-BUTTON','error',exp['key']+'：操作項目にDB列・入力必須・入力長がある')
            if item['role']=='display' and item['required']!='対象外':issue('ITEM-DISPLAY','error',exp['key']+'：表示項目に入力必須を指定')
            if exp['attrs'].get('IsReadOnly','').lower()=='true' and item['role']=='input':issue('ITEM-READONLY','error',exp['key'])
            if item['label_origin']=='unresolved':issue('ITEM-LABEL','review',exp['key']+'：表示名と論理名の対応が未解決')
        if [x['order'] for x in items]!=list(range(1,len(items)+1)):issue('ITEM-ORDER','error','骨子の項目番号が不連続または重複')
        issue('ORDER-VISUAL','review','静的な宣言・階層・座標は記録済み。実際の画面配置、共通テンプレート、キーボード順の独立確認は未実施。')
    if feature.get('code'):
        ev=raw_event_names(root/feature['code']);generated={e['source_name'] for e in feature['events']}
        if set(ev)-generated:issue('EVENT-OMISSION','error',sorted(set(ev)-generated))
        expected_db=raw_db_names(root/feature['code']);actual_db={(x['object'],x['operation']) for x in feature['db']}
        if expected_db-actual_db:issue('DB-OMISSION','error',sorted(expected_db-actual_db))
    quality=feature.get('quality',{})
    if quality.get('untranslated_rules'):issue('IMPLEMENT-RULES','review',str(quality['untranslated_rules'])+'箇所の条件・設定に業務表現と期待結果の追加確認が必要')
    if quality.get('unresolved_db_items'):issue('IMPLEMENT-MAPPING','review',str(quality['unresolved_db_items'])+'項目のDB列対応が未確定')
    if quality.get('physical_schema_missing') and feature['db']:issue('IMPLEMENT-SCHEMA','review','物理DDL、関数・トリガー・制約・連動更新の定義が未取得')
    if not feature.get('example'):issue('IMPLEMENT-EXAMPLE','review','入力値と期待結果の説明用例が未記載')
    doc=root/'output'/feature['filename']
    if not doc.exists():issue('DOC-MISSING','error',feature['filename']);return findings
    text=read(doc)
    for heading in ['1. システム概要','2. 項目一覧','3. イベント仕様','4. 補足説明']:
        if '## '+heading not in text:issue('DOC-CHAPTER','error',heading)
    declared=re.search(r'合計：(\d+)項目',text)
    if not declared or int(declared.group(1))!=len(items):issue('DOC-COUNT','error','公表項目総数と骨子件数が不一致')
    section=text.split('## 2. 項目一覧',1)[-1].split('## 3. イベント仕様',1)[0]
    rows=re.findall(r'^\| (\d+)\. ',section,re.M)
    if len(rows)!=len(items) or Counter(map(int,rows))!=Counter(range(1,len(items)+1)):issue('DOC-ITEM-ROWS','error','文書の項目行と原本対応件数が不一致')
    for e in feature['events']:
        if e['id'] not in text:issue('DOC-EVENT','error',e['id'])
    diagrams='\n'.join(re.findall(r'```mermaid\n(.*?)```',text,re.S))
    for ref in feature['db']:
        if ref['object'] not in diagrams:issue('DIAGRAM-DB','error',ref['object']+'：関連図への記載なし')
    if re.search(r'\b(?:Private Sub|Public Function|sbSql\.Append|NpgsqlParameter|IsRaiseControlChanged)\b',text):issue('DOC-LANGUAGE','error','本文に実装言語の式が残っている')
    return findings


def run_review(root,data):
    findings=[]
    for f in data['features']:findings.extend(inspect_feature(root,f))
    checked=anchors=0;bad=[];diagram_count=0;line_counts={}
    paths=[root/'output'/f['filename'] for f in data['features']]
    paths += [root/'output'/name for name in ['機能一覧.md','概要仕様書COM-001_共通仕様.md','概要仕様書SYS-001_システム分析.md','メッセージ一覧.md','CRUD図.md','DB定義書.md','DBオブジェクト一覧.md']]
    paths += list((root/'report/overview').glob('根拠_*.md'))+[root/'report/overview/共通根拠.md']
    for path in paths:
        if not path.exists():bad.append(str(path));continue
        text=read(path);diagram_count+=len(re.findall(r'^```mermaid$',text,re.M))
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if re.match(r'https?://',target):continue
            checked+=1;destination=unquote(target.split('#')[0]);p=(path.parent/destination).resolve()
            if not p.is_relative_to(root) or not p.is_file():bad.append(path.name+': '+target);continue
            anchor=re.search(r'#L(\d+)(?:-L(\d+))?$',target)
            if anchor:
                anchors+=1
                if p not in line_counts:line_counts[p]=len(read(p).splitlines())
                first=int(anchor.group(1));last=int(anchor.group(2) or first)
                if not 1<=first<=last<=line_counts[p]:bad.append(path.name+': invalid source line '+target)
        if text.count('```')%2:bad.append(path.name+': unbalanced fences')
    for b in bad:findings.append({'feature':'ALL','rule':'LINK','severity':'error','detail':b})
    changed=[]
    for entry in data['inventory']:
        p=root/entry['path']
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:changed.append(entry['path'])
    if changed:findings.append({'feature':'ALL','rule':'INPUT-MUTATION','severity':'error','detail':changed})
    counts=Counter(f['severity'] for f in findings)
    result={'status':'error' if counts['error'] else 'review_required','automatic_errors':counts['error'],'review_findings':counts['review'],'features':len(data['features']),'items':sum(len(f['items']) for f in data['features']),'events':sum(len(f['events']) for f in data['features']),'links_checked':checked,'source_anchors_checked':anchors,'broken_links':len(bad),'mermaid_blocks':diagram_count,'mermaid_syntax':'not_yet_checked','input_hashes_checked':len(data['inventory']),'input_changed':changed,'independence':'生成器とは別の原本読取・評価規則。独立した人間による業務承認ではない。','implementation_readiness':'保留：DB定義・未解決条件・項目対応・実画面順の確認が必要','findings':findings}
    folder=root/'report/overview';folder.mkdir(parents=True,exist_ok=True)
    (folder/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 独立評価結果','','生成器とは別の原本読取処理で項目・イベント・DB参照を照合した。機械的一致と業務仕様の完成度は別判定とする。','','## 1. 総合判定','','**'+result['implementation_readiness']+'**','','| 項目 | 結果 |','| --- | --- |']
    for k,v in result.items():
        if k!='findings':lines.append('| '+k+' | '+str(v).replace('|','／').replace('\n',' ')+' |')
    lines+=['','## 2. 機能別判定','','| 機能ID | 自動検査エラー | 追加確認 | 再実装可否 |','| --- | --- | --- | --- |']
    for f in data['features']:
        ff=[x for x in findings if x['feature']==f['id']];lines.append('| '+f['id']+' | '+str(sum(x['severity']=='error' for x in ff))+' | '+str(sum(x['severity']=='review' for x in ff))+' | 保留 |')
    lines+=['','## 3. 指摘一覧','','| 機能ID | 規則 | 種別 | 内容 |','| --- | --- | --- | --- |']
    for f in findings:lines.append('| '+' | '.join(str(f[k]).replace('|','／').replace('\n',' ') for k in ['feature','rule','severity','detail'])+' |')
    lines+=['','## 4. 評価の範囲と制限','','自動検査は抽出漏れ・誤分類・件数不一致・根拠リンクの異常を検出するためのもの。両者が同じ未対応構文を見落とす可能性は残る。項目順は宣言・座標・階層と実画面を区別する。実画面の目視、実DB照合、独立した担当者による再実装試験、業務利用者の受入確認は未実施。','']
    (folder/'独立評価.md').write_text('\n'.join(lines),encoding='utf-8')
    return result
