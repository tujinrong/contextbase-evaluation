"""Read delivered tables and event sections rather than trusting hidden markers.
Source enumeration remains a separate XML check. This layer checks consistency
with that enumerated contract; it is not proof of business interpretation.
"""
from __future__ import annotations
import html
import re
from collections import Counter
from pathlib import Path

HEADERS=['項目名','タイプ','DB関連','必須','長さ','概要説明']
ROLES={'input':'入力・選択','display':'表示','operation':'操作','internal':'内部'}


def plain(value):
    value=html.unescape(value.strip()).replace('\r','').replace('<br>','\n')
    return re.sub(r'<!--.*?-->','',value).strip()


def item_rows(text):
    section=re.search(r'^## 2\. 項目一覧\s*$([\s\S]*?)(?=^## |\Z)',text,re.M)
    if not section:return []
    result=[];found=False
    for line in section.group(1).splitlines():
        if not line.startswith('|'):
            if found and result:break
            continue
        cells=[plain(c) for c in re.split(r'(?<!\\)\|',line)[1:-1]]
        if cells==HEADERS:found=True;continue
        if found and not all(re.fullmatch(r':?-{3,}:?',c) for c in cells):result.append(cells)
    return result


def event_sections(text):
    result={}
    for m in re.finditer(r'^### 3\.\d+ [^\n]*[（(]([^（）()\n]+-E[0-9A-F]+)[）)]\s*\n([\s\S]*?)(?=^### |^## |\Z)',text,re.M):result[m.group(1)]=m.group(2)
    return result


def logical_mapping(mapping,registry):
    obj=registry['objects'].get(mapping['object'],{})
    name=obj.get('logical_name',mapping['object'])
    col=obj.get('columns',{}).get(mapping['column'],{}).get('logical_name',mapping['column'])
    if name.startswith('用途名要確認'):name=mapping['object']
    return name+'・'+col if name!=mapping['object'] else name+'.'+mapping['column']


def inspect_feature(text,feature,registry):
    findings=[];fid=feature['id'];rows=item_rows(text);items=feature['items']
    def fail(rule,detail):findings.append({'feature':fid,'rule':rule,'detail':detail})
    if len(rows)!=len(items):fail('VISIBLE-COUNT',f'表示表{len(rows)}行、列挙した項目{len(items)}件')
    for pos,(row,item) in enumerate(zip(rows,items),1):
        if len(row)!=6:fail('VISIBLE-COLUMNS',f'{pos}行目が6列ではない');continue
        expected_name=plain(str(item['order'])+'. '+item['name'])
        if row[0]!=expected_name:fail('VISIBLE-ORDER-NAME',f'{pos}行目: {row[0]} / 定義: {expected_name}')
        if row[1]!=ROLES[item['role']]+'／'+item['type']:fail('VISIBLE-ROLE-TYPE',f'{pos}行目の役割・形式が不一致')
        if row[3]!=item['required']:fail('VISIBLE-REQUIRED',f'{pos}行目の必須条件が不一致')
        if row[4]!=item['length']:fail('VISIBLE-LENGTH',f'{pos}行目の上限・単位が不一致')
        if not row[5]:fail('VISIBLE-DESCRIPTION',f'{pos}行目の説明が空')
        if item['role']=='operation' and (not row[2].startswith('対象外') or row[3]!='対象外' or row[4]!='対象外'):fail('VISIBLE-BUTTON',f'{pos}行目: ボタンに入力必須・文字長・直接DB列を設定している')
        if item['role'] in {'display','internal'} and row[3]!='対象外':fail('VISIBLE-DISPLAY',f'{pos}行目: 非入力項目が入力必須')
        for mapping in item.get('db',[]) if item['role']!='operation' else []:
            expected=logical_mapping(mapping,registry)
            if expected not in row[2]:fail('VISIBLE-DB-MAPPING',f'{pos}行目のDB対応欠落: {expected}')
    for key,title in [('input','入力・選択'),('display','表示'),('operation','操作'),('internal','内部・非表示')]:
        actual=re.search(re.escape(title)+r' (\d+)',text.split('## 2. 項目一覧',1)[-1].split('\n\n',2)[1] if '## 2. 項目一覧' in text else '')
        if actual and int(actual.group(1))!=sum(i['role']==key for i in items):fail('VISIBLE-SUBTOTAL',title+'の小計不一致')
    sections=event_sections(text)
    for e in feature.get('events',[]):
        body=sections.get(e['id'])
        if body is None:fail('VISIBLE-EVENT',e['id']+'のイベント節がない');continue
        if not re.search(r'^- \S',body,re.M):fail('VISIBLE-EVENT-STEPS',e['id']+'の箇条書き処理がない')
        diagrams='\n'.join(re.findall(r'```mermaid\s*\n([\s\S]*?)```',body))
        if not diagrams:fail('VISIBLE-EVENT-DIAGRAM',e['id']+'の関連図がない')
        for ref in e.get('db',[]):
            logical=registry['objects'].get(ref['object'],{}).get('logical_name',ref['object'])
            if logical.startswith('用途名要確認'):logical=ref['object']
            if logical not in diagrams:fail('VISIBLE-EVENT-DB',e['id']+'の関連図から'+logical+'が欠落')
    return findings


def review(root:Path,data,registry):
    return [finding for f in data['features'] for finding in inspect_feature((root/'output'/f['filename']).read_text(encoding='utf-8'),f,registry)]
