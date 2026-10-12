"""Language-neutral projections of source-derived calls, stores and validations.

Names may come from a reviewed terminology file; operations/conditions never do.
Unknown predicates stay explicit instead of being paraphrased into invented rules.
"""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from contextbase.shared.store import digest, read, safe
from specgen.common import tokens, pairs

OPS={'create':'追加','read':'参照','update':'更新','delete':'削除','upsert':'追加／更新'}


def terminology(root, category="types"):
    result={}
    for p in sorted(safe(root,'src-dynamic').glob('*/terminology.json')):
        safe(root,p);data=read(p)
        if data.get('trust')=='repository-reviewed':result.update(data.get(category,{}))
    return result


def field_labels(items):
    labels={}
    for item in items:
        binding=item.get('binding','')
        if binding:
            key=binding.split('.')[-1]
            labels.setdefault(key,item['name']);labels.setdefault(key[0].lower()+key[1:],item['name'])
            labels[binding]=item['name'];labels[binding.replace('.','_')]=item['name']
    return labels


def explain(expression, labels):
    """Loss-aware expression display: labels and operators, not free inference."""
    value=str(expression).strip()
    value=re.sub(r'\bMessage\b','結果メッセージ',value)
    if value=='Input':return '画面入力'
    roles={'item':'保存データ','row':'保存データ','branch':'候補データ','Input':'画面入力','input':'画面入力','copy':'保存用データ','reservation':'受渡しデータ','entity':'処理対象データ','record':'処理対象データ'}
    for owner,role in roles.items():
        value=re.sub(r'\b'+re.escape(owner)+r'\.(\w+)',lambda m:role+'の'+labels.get(m[1],m[1]),value)
    for key in sorted(labels,key=len,reverse=True):
        value=re.sub(r'(?<![\w])'+re.escape(key)+r'(?![\w])',lambda m:labels[key],value)
    value=re.sub(r'\b(?:Input|input|item|row|copy|reservation|entity|record)\.','',value)
    replacements={'StringComparison.OrdinalIgnoreCase':'大文字小文字を区別しない',
                  'StringComparison.Ordinal':'文字単位で一致','string.IsNullOrWhiteSpace':'空欄判定',
                  'string.Equals':'一致判定','DateTime.Today':'当日','ModelState.IsValid':'入力検証が正常',
                  'HasValue':'値あり','NOT (':'次の条件ではない (','&&':' かつ ','||':' または ',' is not null':' が存在する',
                  ' is null':' が存在しない','null':'未設定','true':'はい','false':'いいえ'}
    for a,b in replacements.items():value=value.replace(a,b)
    value=re.sub(r'\s+',' ',value)
    return value[:700]+('…（詳細仕様に原文）' if len(value)>700 else '')



def public_condition(expression, event, labels):
    """Name known validations; keep unresolved predicates visibly source-derived."""
    value=str(expression)
    bymethod={}
    for rule in event.get('validation_rules',[]):
        bymethod.setdefault(rule['method'],[]).append(rule['label'])
    for method,fields in bymethod.items():
        label='・'.join(dict.fromkeys(fields))+'の入力検査'
        call=re.escape(method)+r'\(\)'
        value=re.sub(r'NOT \(!'+call+r'\)',lambda m:label+'が正常',value)
        value=re.sub(r'!'+call,lambda m:label+'が不成立',value)
        value=re.sub(call,lambda m:label+'が正常',value)
    # A FindIndex result determines whether the selected collection contains a row.
    for m in event.get('methods',[]):
        for step in m.get('steps',[]):
            expr=step.get('expression','')
            found=re.match(r'var\s+(\w+)\s*=.*\.FindIndex\(',expr)
            if found:
                test=re.escape(found[1])+r'\s*>=\s*0'
                value=re.sub(r'NOT \('+test+r'\)','照合条件に一致する既存レコードがない',value)
                value=re.sub(test,'照合条件に一致する既存レコードがある',value)
            found=re.match(r'var\s+(\w+)\s*=.*\.FirstOrDefault\(',expr)
            if found:
                test=re.escape(found[1])+r' is null'
                value=re.sub(r'NOT \('+test+r'\)','照合条件に一致するレコードがある',value)
                value=re.sub(test,'照合条件に一致するレコードがない',value)
    return explain(value,labels)


def operation_summary(effect, event, labels):
    expr=effect['expression'];operation=effect['operation']
    if operation=='update' and re.search(r'\[[^]]+\]\s*=',expr):
        return '照合で特定した既存レコードを、保存用に作成したデータで置き換える。'
    if operation=='create':return '保存用に作成したデータを、対象の保持領域へ追加する。'
    if operation=='delete':
        if re.search(r'\.Clear\(',expr):return '対象の保持領域の全要素を消去する。'
        if re.search(r'\.RemoveAll\(',expr):return '指定条件に一致する要素を消去する。'
        return '照合で特定した対象レコードを保持領域から取り除く。'
    if operation=='read':
        if '.FindIndex(' in expr:return '照合条件で既存レコードの位置を検索し、結果を後続の判定に使用する。'
        if '.FirstOrDefault(' in expr:
            ts=tokens(expr);pm=pairs(ts);predicate=''
            for i,t in enumerate(ts[:-1]):
                if t['text']=='FirstOrDefault' and ts[i+1]['text']=='(' and i+1 in pm:
                    close=pm[i+1]
                    predicate=expr[ts[i+1]['end']:ts[close]['start']].strip()
                    break
            predicate=re.sub(r'^\w+\s*=>\s*','',predicate)
            pt=tokens(predicate)
            calls={t['text'] for i,t in enumerate(pt[:-1]) if pt[i+1]['text']=='('}
            result='条件に一致する先頭レコードを取得する。該当しない場合は未取得とする。'
            if predicate and not calls:result+=' 条件：'+explain(predicate,labels)+'。'
            elif any(r['target']=='レコードの照合条件' and r.get('method') in calls for r in event.get('data_rules',[])):
                result+=' 具体的な比較条件は下記の照合規則を使用する。'
            elif predicate:
                result+=' 条件式：'+explain(predicate,labels)+'（原本の条件表記）。'
            if '.Clone(' in expr:result+=' 取得結果は複製し、表示値の変更だけで保持データを書き換えない。'
            return result
    return explain(expr,labels)

def validation_rules(visits,labels):
    result=[];seen=set()
    for visit in visits:
        m=visit['method']
        for step in m['steps']:
            expr=step.get('expression','')
            match=re.search(r'AddModelError\(\s*"([^"\n]*)"\s*,\s*"([^"\n]+)"',expr)
            if not match:continue
            key=(m['path'],step['line'],match[1])
            if key in seen:continue
            seen.add(key)
            result.append({'field':match[1],'label':labels.get(match[1],match[1] or '画面全体'),
                'message':match[2],'method':m['name'],'guards':visit['guards']+step.get('guards',[]),
                'evidence':[{'path':m['path'],'line':step['line']}]})
    return result


def enrich_event(event,index,entry,visits,effects,labels):
    event['validation_rules']=validation_rules(visits,labels)
    event['storage_effects']=effects
    event['methods']=list({v['method']['id']:v['method'] for v in visits}.values())
    event['related_method_ids']=[m['id'] for m in event['methods']]
    steps=[]
    for step in entry['steps']:
        beginning=len(steps)
        expr=step.get('expression') or step.get('condition','')
        if not expr:continue
        names={c['name'].split('.')[-1] for c in step.get('calls',[])}
        checks=[r for r in event['validation_rules'] if r['method'] in names]
        if checks:
            names_text='・'.join(dict.fromkeys(r['label'] for r in checks))
            steps.append(names_text+'の入力条件を検査する。条件不成立時のメッセージと後続処理は下表に示す。')
        elif any(n in {'Save','Update','Insert','Add','Delete','Remove'} for n in names):
            matching=[r for r in effects if r['implementation'] in names]
            actions='・'.join(dict.fromkeys(OPS.get(r['operation'],r['operation']) for r in matching))
            stores='・'.join(dict.fromkeys(r['store'] for r in matching))
            if matching:steps.append(stores+'の'+actions+'処理を実施する。判定条件・照合・設定内容はデータ操作表に示す。')
        if step['kind']=='assignment' and not expr.startswith('var '):
            target=step.get('target','')
            if target and (target=='Input' or '.' in target or target in {'Message','Input'}):
                steps.append(explain(target,labels)+'に '+explain(step.get('value',''),labels)+' を設定する。')
        if step['kind']=='return':
            if 'RedirectToPage()' in expr:steps.append('処理完了後に同じ画面の初期表示へ遷移する。')
            elif 'RedirectToPage' in expr:
                m=re.search(r'RedirectToPage\(\s*"([^"]+)"',expr)
                steps.append('条件を満たす分岐では '+(m[1] if m else '指定画面')+' へ遷移する。')
            elif 'Page()' in expr:steps.append('該当分岐では同じ画面を表示する。後続の保存・削除を実行する分岐とは区別する。')
            elif 'JsonResult' in expr:steps.append('該当分岐の処理結果をJSON応答として返す。')
        for call in step.get('calls',[]):
            related=[v['method'] for v in visits if v['method']['name']==call['name'].split('.')[-1]]
            if related and not checks and not names.intersection({'Save','Delete','Add','Remove'}):
                targets=sorted({n.get('target','') for m in related for n in m['steps'] if n.get('target','').startswith('Input.')})
                if targets:steps.append('・'.join(explain(t,labels) for t in targets)+'を原本の変換条件に従って設定する。')
        if step.get('guards'):
            condition=public_condition(' / '.join(step['guards']),event,labels)
            for j in range(beginning,len(steps)):steps[j]='【条件：'+condition+'】'+steps[j]
    event['public_steps']=list(dict.fromkeys(steps or event.get('public_steps',[])))
    # Keep the derivation boundaries honest; no assertion of full path equivalence.
    event['data_rules']=data_rules(event['methods'],effects,labels)
    event['description']='画面入口から呼出先をたどり、入力検証・データ操作・応答を抽出した。条件式は項目名へ対応付けて示す。'
    return event


def attach_item_storage(items,feature,texts,index,event_effects,rules):
    companion=texts.get(feature.get('companion'),'')
    # Reverse type/property map; declarations, not matching by spelling alone.
    inputs={prop:typ.rstrip('?') for typ,prop in re.findall(r'public\s+([\w?]+)\s+(\w+)\s*\{\s*get\s*;\s*set\s*;',companion)}
    for item in items:
        binding=item.get('binding','')
        if '.' not in binding or item['io']=='‐':continue
        prop,field=binding.split('.',1);typ=inputs.get(prop)
        candidates={r['store_id']:r for r in event_effects if r.get('element_type')==typ and r['operation'] in {'create','update'}}
        if len(candidates)==1:
            effect=next(iter(candidates.values()))
            item['db']=effect['store']+'／'+item['name']+('（メモリー上のデータ）' if effect['kind']=='memory' else '（ORM対応）')
            item['storage_binding']={'store_id':effect['store_id'],'element_type':typ,'field':field,
                                     'kind':effect['kind'],'basis':'bound_model_and_resolved_store_write','evidence':effect['evidence']}
            item.setdefault('facts',{})['db']={'value':item['db'],'basis':'derived','evidence':effect['evidence']}
        applicable=[r for r in rules if r['field']==binding]
        if applicable:
            notes=' '.join(dict.fromkeys(r['message'] for r in applicable))
            item['description']=item.get('description','')+' 入力検査：'+notes
            item['validation_rules']=applicable
            for rule in applicable:
                for guard in rule['guards']:
                    limit=re.search(r'\b\w*Bytes\('+re.escape(binding)+r'\)\s*<=\s*(\d+)',guard)
                    if limit:
                        item['format']='原本のバイト換算で'+limit[1]+'以下（文字数ではない）'
                        item.setdefault('facts',{})['format']={'value':item['format'],'basis':'derived','evidence':rule['evidence']}
            if any(re.search(r'必ず入力|を入力してください',r['message']) and
                   any(re.search(re.escape(binding)+r'.*(?:HasValue|<=\s*0)|IsNullOrWhiteSpace\('+re.escape(binding),g) for g in r['guards'])
                   for r in applicable):
                item['required']='必須（保存・削除等の該当イベント）'
                item.setdefault('facts',{})['required']={'value':item['required'],'basis':'derived','evidence':[e for r in applicable for e in r['evidence']]}


def client_events(markup,path):
    """Statically inspect callback spans. No execution or arbitrary JS evaluation."""
    soup=BeautifulSoup(markup,'html.parser');ts=tokens(markup);pm=pairs(ts);result=[]
    variables={}
    for name,selector in re.findall(r'\b(?:const|let|var)\s+(\w+)\s*=\s*document\.querySelector\(\s*"([^"]+)"\s*\)',markup):variables[name]=selector
    for i,t in enumerate(ts[:-1]):
        if t['text']!='addEventListener' or ts[i+1]['text']!='(' or i+1 not in pm:continue
        end=pm[i+1];arrow=next((k for k in range(i+2,end) if ts[k]['text']=='=>'),None)
        if arrow is None or arrow+1>=end or ts[arrow+1]['text']!='{':continue
        body_end=pm.get(arrow+1)
        if body_end is None:continue
        start=ts[arrow+1]['start'];body=markup[start:ts[body_end]['end']]
        prefix=markup[max(0,t['start']-150):t['start']]
        selector_match=re.search(r'document\.querySelector\("([^"]+)"\)\?\.$',prefix)
        receiver=re.search(r'(\w+)\??\.$',prefix)
        selector=selector_match[1] if selector_match else variables.get(receiver[1]) if receiver else None
        if not selector:continue
        try:tag=soup.select_one(selector)
        except Exception:continue
        if not tag:continue
        caption=tag.get('aria-label') or tag.get_text(' ',strip=True)
        if tag.name=='form':caption='フォーム内のキー操作'
        if not caption:continue
        messages=list(dict.fromkeys(re.findall(r'\b(?:message\s*:|message\s*=)\s*"([^"\n]+)"',body)))
        conditions=[]
        for k in range(arrow+2,body_end):
            if ts[k]['text']=='if' and k+1 in pm:
                close=pm[k+1];conditions.append(markup[ts[k+1]['end']:ts[close]['start']])
        if not messages and not conditions:continue
        result.append({'id':'CLI-'+str(len(result)+1).zfill(3),'name':caption,'selector':selector,
                       'conditions':conditions,'messages':messages,
                       'request_submit':'requestSubmit(' in body,'cancellation_return':bool(re.search(r'if\s*\(\s*!confirmed\s*\)\s*\{\s*return',body)),
                       'confirmation':bool(re.search(r'mode\s*:\s*"confirm"',body)),
                       'evidence':[{'path':path,'line':t['line']}]})
    return result


def data_rules(methods, effects, labels):
    """Resolve pure matcher/normalizer and stored-field assignments as readable rules."""
    result=[];seen=set();byname={m['name']:m for m in methods}
    saved_assignments={(r['evidence'][0]['path'],a['line']) for r in effects for a in r.get('assignments',[])}
    meanings={}
    for m in methods:
        text=' '.join(n.get('expression','') for n in m['steps'])
        if '.Where(char.IsDigit)' in text:
            meanings[m['name']]='数字だけを抽出'
        elif '.Trim()' in text and re.search(r'\.Replace\("　",\s*" "',text):
            meanings[m['name']]='前後空白を除去し全角空白を半角空白に変換'
    def display(value):
        for name,meaning in meanings.items():value=re.sub(r'\b'+re.escape(name)+r'\(',meaning+'(',value)
        return explain(value,labels)
    for m in methods:
        for n in m['steps']:
            expr=n.get('expression','');target=n.get('target','')
            if (m['path'],n['line']) in saved_assignments:
                desc=display(n.get('value',''))
                if 'DateTime.Today' in expr:desc='処理当日を '+('yyyy-MM-dd' if 'yyyy-MM-dd' in expr else '原本指定形式')+' で設定する'
                for c in n.get('calls',[]):
                    helper=byname.get(c['name'].split('.')[-1])
                    if helper:
                        returns=' '.join(x.get('expression','') for x in helper['steps'])
                        choices=re.findall(r'(\d+)\s*=>\s*"([^"]*)"',returns)
                        if choices:desc=' / '.join(k+'→'+v for k,v in choices)+'。その他は '+('空欄' if '_ => ""' in returns else '原本の既定値')
                        adds=[x for x in helper['steps'] if re.search(r'\.Add\("[^"\n]+"\)',x.get('expression',''))]
                        if adds and 'string.Join(' in returns:
                            values=[re.search(r'\.Add\("([^"\n]+)"\)',x['expression'])[1] for x in adds]
                            separator=re.search(r'string.Join\("([^"\n]*)"',returns)
                            desc='選択条件に対応する名称（'+'、'.join(values)+'）を「'+(separator[1] if separator else '指定区切り')+'」で連結する。'
                            if re.search(r'\.Count\s*==\s*0\s*\?',returns):desc+='選択対象がない場合は入力の値を使用する。'
                key=(m['path'],n['line'])
                if key not in seen:
                    seen.add(key);result.append({'target':display(target),'rule':desc,'evidence':[{'path':m['path'],'line':n['line']}]})
            elif n['kind']=='return' and 'string.Equals(' in expr and ('Normalize(' in expr or 'Digits(' in expr or '.Trim(' in expr):
                key=(m['path'],n['line'])
                if key not in seen:
                    seen.add(key);result.append({'target':'レコードの照合条件','method':m['name'],'rule':display(expr.removeprefix('return').strip()),'evidence':[{'path':m['path'],'line':n['line']}]})
    for name,meaning in meanings.items():
        m=byname[name];result.append({'target':'照合前の文字列整形','rule':meaning,'evidence':[{'path':m['path'],'line':m['line']}]})
    return result
