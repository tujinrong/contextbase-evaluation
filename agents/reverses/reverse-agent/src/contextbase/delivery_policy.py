"""Keep provisional deliverables separate from persistent QA and incomplete reports."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path


def table(headers,rows):
    def esc(v):return html.escape(str(v),quote=False).replace('|','&#124;').replace('\n','<br>')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(esc(v) for v in row)+' |\n' for row in rows)


class ReviewLog:
    def __init__(self,root: Path):
        self.root=root
        p=root/'QA/questions.json'
        if (root/'QA').is_symlink() or p.is_symlink():raise ValueError('QA cannot be a symlink')
        old=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'questions':[]}
        self.questions={q['id']:{**q,'active':False} for q in old.get('questions',[])}
        self.incomplete=[]

    def add(self,key,target,question,assumption,evidence='',kind='specification'):
        qid='Q-'+hashlib.sha256(key.encode('utf-8')).hexdigest()[:10].upper()
        old=self.questions.get(qid,{})
        current={'id':qid,'target':target,'question':question,'assumption':assumption,
                 'evidence':evidence,'kind':kind,'active':True,
                 'impact':'対象の入力条件・データ連携・操作説明に影響する。' if kind=='specification' else '関連機能の再現範囲に影響する。',
                 'status':old.get('status','open'),'answer':old.get('answer','')}
        if old and any(old.get(k)!=current[k] for k in ('question','assumption','evidence')):
            current['status']='recheck';current['previous']=old
        self.questions[qid]={**old, **current}
        return qid

    def delivery(self,record):
        doc=deepcopy(record);source=record['path'];occurrences={}
        for row in doc.get('items',[]):
            identity=row.get('binding') or row.get('name') or 'item'
            occurrences[identity]=occurrences.get(identity,0)+1
            key=source+'|'+identity+'|'+str(occurrences[identity])
            target=source+' / '+str(row.get('name',identity))
            evidence=json.dumps(row.get('evidence',[{'path':source,'line':row.get('line')}]),ensure_ascii=False)
            role=row.get('role')
            if role in {'operation','static'}:continue
            replacements=[('db',row.get('db',row.get('data','未確認')),'画面データ連携','DBの参照・保存先と項目対応は何ですか。物理表名は根拠なしに設定しません。')]
            if role in {'input','input_output'}:
                replacements.append(('required',row.get('required','未確認'),'任意','宣言で確定できない業務上の入力必須条件はありますか。'))
            replacements.append(('length',row.get('length','未確認'),'制限指定なし','追加の形式・長さ・桁数制限はありますか。'))
            if row.get('choices')=='未確認':replacements.append(('choices','未確認','画面初期化時に取得','選択候補の取得元と絞込条件は何ですか。'))
            for field,value,assumed,question in replacements:
                if value is not None and value!='' and '未確認' not in str(value):continue
                qid=self.add(key+'|'+field,target,question,assumed,evidence)
                row[field]=assumed+'（仮定 '+qid+'）'
            if not row.get('group'):
                row['group']='表示項目' if role=='display' else '入力・選択項目'
        for i,event in enumerate(doc.get('events',[])):
            if event.get('handler') in {'未確認',None,''}:
                target=source+' / '+str(event.get('trigger','操作'))
                assumed='関連する入力補助・確認処理を起動'
                qid=self.add(source+'|event|'+str(i),target,'この操作の処理と完了後の画面状態は何ですか。',assumed,str(event.get('line','')))
                event['handler']=assumed+'（仮定 '+qid+'）'
        for warning in record.get('warnings',[]):
            code=warning.split(':',1)[0]
            self.incomplete.append({'target':source,'detail':warning})
            self.add(source+'|warning|'+code,source,warning,'現時点のソース根拠と明示した仮定で仕様書を生成する。',source,'analysis')
        return doc

    def save(self):
        qa=self.root/'QA';qa.mkdir(exist_ok=True)
        rows=sorted(self.questions.values(),key=lambda q:q['id'])
        value={'schema':'contextbase.qa.v1','questions':rows}
        (qa/'questions.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        active=[q for q in rows if q['active']]
        md='# 仕様確認QA\n\n質問待ちで生成を停止せず、暫定採用値を仕様書へ出力する。回答・状態はquestions.jsonで管理し、再生成時も保持する。\n\n'
        md+=table(['QA ID','対象','質問','暫定採用値','根拠','影響','状態','回答'],[[q[k] for k in ['id','target','question','assumption','evidence','impact','status','answer']] for q in active])
        (qa/'仕様確認.md').write_text(md,encoding='utf-8')
        report=self.root/'report/incomplete';report.mkdir(parents=True,exist_ok=True)
        (report/'analysis.json').write_text(json.dumps({'status':'partial','assumptions':len([q for q in active if q['kind']=='specification']),'details':self.incomplete},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (report/'未完成事項.md').write_text('# 未完成・未検証事項\n\n成果物はoutputに出力済み。仮定の妥当性、動的画面、DB対応、業務経路の完全性は未承認。仕様の質問・回答はQAに保存する。\n\n'+table(['対象','未完成・未検証の内容'],[[q['target'],q['detail']] for q in self.incomplete]),encoding='utf-8')
