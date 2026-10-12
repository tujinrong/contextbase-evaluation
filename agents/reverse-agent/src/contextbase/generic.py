"""Conservative starter adapter path for a different project, without previous-client prose."""
from __future__ import annotations
import json
import html
import re
from pathlib import Path
from html.parser import HTMLParser
from specgen.analyze import analyze
from specgen.common import decode_source, digest, atomic_write
from specgen.sql import sql_facts
from .itemlist import render as render_itemlist
from .markup_items import extract_markup
from .model_sources import collect_model_sources
from .delivery_policy import ReviewLog
from .pilot import load_pilot, prepare_assets, add_pilot_questions


class VueTemplate(HTMLParser):
    def __init__(self):super().__init__();self.items=[];self.events=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in {'input','textarea','select','button'}:
            self.items.append({'name':a.get('aria-label') or a.get('name') or a.get('v-model') or a.get('id') or tag,
                              'role':'operation' if tag=='button' else 'display' if 'readonly' in a or 'disabled' in a else 'input',
                              'type':a.get('type',tag),'required':'required' in a,'length':a.get('maxlength','未確認'),'line':self.getpos()[0]})
        for k,v in attrs:
            if k.startswith('@') or k.startswith('v-on:'):self.events.append({'trigger':k,'handler':v,'line':self.getpos()[0]})


def extract(text: str, path: str, language: str) -> dict:
    result={'path':path,'language':language,'status':'partial','items':[],'events':[],'symbols':[],'tables':[],'crud':[],'warnings':[]}
    ext=Path(path).suffix.lower()
    if ext in {'.cshtml','.html','.htm','.jsp','.aspx','.ascx'}:
        result.update(extract_markup(text,path));return result
    if language in {'Python','Java','C#','JavaScript','TypeScript','SQL'}:
        result.update(analyze(text,path,language));return result
    if ext=='.vue':
        template=re.search(r'<template\b[^>]*>([\s\S]*?)</template\s*>',text,re.I)
        if template:
            p=VueTemplate();p.feed(template[1]);offset=text.count('\n',0,template.start(1))
            result['items']=[dict(x,line=x['line']+offset) for x in p.items]
            result['events']=[dict(x,line=x['line']+offset) for x in p.events]
        for script in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script\s*>',text,re.I):
            lang='TypeScript' if re.search(r'lang=[\'\"]ts[\'\"]',script[1]) else 'JavaScript'
            a=analyze(script[2],path,lang);offset=text.count('\n',0,script.start(2))
            result['symbols'] += [dict(s,line=s['line']+offset,end_line=s['end_line']+offset) for s in a['symbols']]
        result['warnings']=['SFCの限定抽出。ネストしたtemplate・動的component・APIとの接続・外部CSSは完全解決していません。']
    elif ext in {'.vb','.bas','.cls','.frm'}:
        for hit in re.finditer(r'^\s*(?:(?:Public|Private|Friend|Protected|Shared|Static)\s+)*(Sub|Function|Property\s+(?:Get|Let|Set))\s+(\w+)\s*\(([^\n]*)',text,re.I|re.M):
            result['symbols'].append({'name':hit[2],'kind':hit[1],'signature':hit[0].strip(),'line':text.count('\n',0,hit.start())+1,'end_line':text.count('\n',0,hit.end())+1})
        if ext=='.frm':
            for hit in re.finditer(r'^\s*Begin\s+(?:VB\.)?(\w+)\s+(\w+)\s*$',text,re.M):
                if hit[1].lower() in {'textbox','combobox','commandbutton','label','checkbox','optionbutton'}:
                    result['items'].append({'name':hit[2],'role':'operation' if hit[1].lower()=='commandbutton' else 'display' if hit[1].lower()=='label' else 'input','type':hit[1],'required':'未確認','length':'未確認','line':text.count('\n',0,hit.start())+1})
        for hit in re.finditer(r'"(?:""|[^"\n])*"',text):
            value=hit[0][1:-1].replace('""','"')
            if re.search(r'\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE\s+TABLE)\b',value,re.I):
                tables,crud,warnings=sql_facts(value,text.count('\n',0,hit.start())+1)
                result['tables']+=tables;result['crud']+=crud;result['warnings']+=warnings
        result['warnings'].append('宣言・リテラルSQLの限定抽出。VB6とVB.NETの実行意味、COM、Access内部、動的SQLを同一視しません。')
    else:result['warnings']=['設定・構造検出のみ。業務仕様の解析器は未適用です。']
    return result


def generate(root: Path, cfg: dict, survey: dict) -> dict:
    records=[]
    model_sources=collect_model_sources(root,cfg,survey)
    for row in survey['inventory']:
        if row['status']!='selected':continue
        path=root/cfg['input']/row['path']
        if path.suffix.lower() in {'.sln','.vbp','.csproj','.vbproj','.xaml'}:continue
        try:
            text,_=decode_source(path.read_bytes());record=extract(text,row['path'],row['language'])
            if path.suffix.lower()=='.cshtml':
                companion=Path(str(path)+'.cs')
                if companion.is_file() and not companion.is_symlink():
                    if not companion.resolve().is_relative_to((root/cfg['input']).resolve()):
                        raise ValueError('PageModel escapes input root')
                    model_text,_=decode_source(companion.read_bytes())
                    record.update(extract_markup(text,row['path'],model_text,row['path']+'.cs',model_sources))
        except Exception as exc:
            record={'path':row['path'],'status':'error','warnings':[type(exc).__name__+': '+str(exc)]}
        records.append(record)
    def put(path,value):atomic_write(root/path,value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    def cell(value):return html.escape(str(value),quote=False).replace('|','&#124;').replace('`','&#96;').replace('\n','<br>')
    def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(cell,row))+' |\n' for row in rows)
    features=[]
    review=ReviewLog(root)
    pilot, changed=load_pilot(root,cfg['input'])
    if changed:
        review.add('pilot-source-change','職員番号入力','Pilot原本が変更されました。関連仕様の再確認が必要です。','汎用解析結果に仮定を付けて出力する。',', '.join(changed),'analysis')
        put(Path('report/pilot/status.json'),{'status':'source_changed','changed':changed,'pilot_applied':False})
    if not pilot and not changed:
        put(Path('report/pilot/status.json'),{'status':'not_applicable','pilot_applied':False})
    if pilot:
        status=prepare_assets(root,cfg['input'],pilot)
        add_pilot_questions(review)
        put(Path('report/pilot/status.json'),{**status,'pilot_applied':True,'status':'reviewed_source_matched'})
    for record in records:
        if pilot and record['path'] in pilot.get('consumed',[]):continue
        if pilot and record['path']==pilot['source']:
            body=(pilot['directory']/'職員番号入力.md').read_text(encoding='utf-8')
            put(Path('output/md/基本設計書')/pilot['filename'],body)
            features.append({'id':pilot['id'],'name':pilot['name'],'filename':pilot['filename']})
            continue
        if not record.get('symbols') and not record.get('items'):continue
        fid='F-'+digest(record['path'])[:10].upper();name=record.get('title') or Path(record['path']).stem;safe_name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',name).strip(' .') or '名称未確認';filename=f'概要仕様書{fid}_{safe_name}.md'
        delivery=review.delivery(record)
        symbols=record.get('symbols',[]);items=delivery.get('items',[])
        body=f'# {cell(name)}\n\nソースから抽出した定義と、QA番号で識別した仮定を記載します。\n\n## 1. システム概要\n\n対象：{cell(record["path"])}。本機能の項目と操作を以下に示します。\n\n## 2. 項目一覧\n\n'
        body+=render_itemlist(items)
        body+=f'\n**項目定義数：{len(items)}項目**。原本の定義順に記載します。反復するデータ行は一つの項目定義として扱います。\n'
        body+='\n## 3. イベント仕様\n\n'+table(['実装単位','宣言','根拠行'],[[x['name'],x['signature'],x['line']] for x in symbols])
        body+='\n'+table(['イベント','処理表記','根拠行'],[[x['trigger'],x['handler'],x['line']] for x in delivery.get('events',[])])
        body+='\n## 4. 補足説明\n\n仮定を採用した項目は、各欄のQA番号で識別します。定義済みの入力制約を優先し、ボタン・表示項目には入力必須条件を設定しません。\n'
        put(Path('output/md/基本設計書')/filename,body);features.append({'id':fid,'name':name,'filename':filename})
    put(Path('output/md/機能一覧.md'),'# 機能一覧\n\nソースの定義単位ごとに仕様書をまとめています。\n\n'+''.join(f'- [{f["id"]} {f["name"]}](基本設計書/{f["filename"]})\n' for f in features))
    put(Path('output/md/共通/システム分析.md'),'# システム分析\n\n'+table(['検出技術','ファイル数'],list(survey['languages'].items()))+'\n検出した技術構成を基に仕様書を作成します。業務仕様は各機能の仕様書に記載します。\n')
    findings=[]
    for record in records:
        for warning in record.get('warnings',[]):
            findings.append([f'Q-{len(findings)+1:04d}',record['path'],warning,'項目定義・機能境界・業務処理の確認が必要'])
    review.save()
    put(Path('report/generic/itemlist-review.json'),{'status':'requires_review','table_schema':'v2-basic-10-columns','item_definitions':sum(len(r.get('items',[])) for r in records),'findings':findings})
    put(Path('.specgen-state/generic/index.json'),{'records':records,'features':features})
    result={'status':'partial','files_analyzed':len(records),'features':len(features),'errors':sum(r['status']=='error' for r in records),'requires_export':[i['path'] for i in survey['inventory'] if i['status']=='requires_export'],'pilot':'not_supported_for_unreviewed_profile'}
    put(Path('report/generic/evaluation.json'),result)
    return result
