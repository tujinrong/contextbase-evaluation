"""Stage human-readable discovery results from locally adopted artifacts only."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from html import escape
import json
import os
from pathlib import Path
from urllib.parse import quote

from contextbase_runtime import contracts
from contextbase_runtime.paths import material_path, safe_path


_KINDS = {
    'system': 'システム概要', 'function': '主機能', 'operation': '子操作',
    'common': '共通能力', 'data': 'データ対象', 'entry': '技術入口',
    'support': '運用・開発支援', 'material': '資料', 'dependency': '外部依存',
    'unclassified': '分類保留',
}
_FIELDS = {
    'scope': '集計範囲', 'area': '機能領域', 'actors': '主体',
    'businessObject': '業務対象', 'purpose': '利用目的', 'trigger': '開始契機',
    'outcome': '完了成果', 'rationale': '分類理由', 'alternative': '別案・反例',
    'entryRefs': '技術入口', 'parent': '主帰属', 'useContext': '利用文脈',
    'responsibility': '共有・集中する責務', 'consumers': '利用先',
    'tentativeKind': '候補分類', 'impact': '影響', 'reason': '保留理由',
    'unknownIds': '参照する未知ID',
}


def _md(value):
    text = escape(str(value), quote=False).replace('\\', '\\\\')
    for char in '`*_{}[]()#+-!|':
        text = text.replace(char, '\\' + char)
    return text.replace('\r\n', '\n').replace('\n', '<br>')


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def _write_markdown(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8', newline='\n')


def _accepted_artifacts(agent, status, payload, index):
    """Follow active receipts, not arbitrary last author/reviewer responses."""
    receipts = status['receipts']
    verification_ids = {receipt['verification'] for receipt in receipts.values()}
    if len(verification_ids) != 1:
        raise ValueError('Discovery reporting requires one current full-view verification')
    identifier = next(iter(verification_ids))
    verification = agent.session.store.get('verifications/' + identifier + '.json')
    if contracts.digest(verification) != identifier:
        raise ValueError('Adopted verification content binding changed')
    candidate = agent.session.store.get('candidates/' + verification['candidate'] + '.json')
    if (contracts.digest(candidate) != verification['candidate']
            or candidate['viewSha256'] != verification['viewSha256']
            or candidate['view']['records'] != payload['records']
            or set(candidate['view']['acceptedRequirements']) != set(payload['acceptedRequirements'])
            or verification['answer']['viewSha256'] != verification['viewSha256']
            or verification['answer'].get('sourceFactsSha256') != index.sha256):
        raise ValueError('Adopted report view or source-fact binding changed')
    if not any(row['candidateSha256'] == verification['candidate'] and
               any(item['sha256'] == identifier for item in row['verificationSummaries'])
               for row in payload['audit']):
        raise ValueError('Formal result does not bind its adopted verification')
    usage = {}
    for candidate_id in dict.fromkeys(receipt['candidate'] for receipt in receipts.values()):
        author = agent.session.store.get('candidates/' + candidate_id + '.json')
        if contracts.digest(author) != candidate_id or author['answer'].get('sourceFactsSha256') != index.sha256:
            raise ValueError('Adopted author content or source-fact binding changed')
        for item in author['answer'].get('factUsage', []):
            record = payload['records'].get(item['recordKey'])
            if record and receipts[record['ownerRequirement']]['candidate'] == candidate_id:
                if item['recordKey'] in usage:
                    raise ValueError('Duplicate adopted fact usage in report')
                usage[item['recordKey']] = item
    if set(usage) != set(payload['records']):
        raise ValueError('Adopted fact usage does not cover current discovery records')
    return verification, list(usage.values())


def prepare_report(agent, envelope: dict, directory: Path, final_directory: Path) -> dict:
    """Prepare a fresh publication tree; never publish or rewrite model judgments.

    ``final_directory`` controls source links, so staging can be moved without
    rewriting evidence. The caller owns publication, its lock and target marker.
    """
    if agent.stage != 'discovery':
        raise ValueError('This renderer only reports discovery')
    status = agent.status()
    own = {key for key, item in agent.session.obligations.items() if item['stage'] == agent.stage}
    if not own or not own.issubset(status['acceptedRequirements']):
        raise ValueError('All discovery requirements must be locally adopted before reporting')
    if (not isinstance(envelope, dict) or set(envelope) != {'sha256', 'payload'}
            or envelope['sha256'] != contracts.digest(envelope['payload'])
            or envelope != agent.export()):
        raise ValueError('Report envelope differs from the locally adopted export')
    payload = envelope['payload']
    if (payload['producer'] != 'discovery' or set(payload['acceptedRequirements']) != own
            or payload['records'] != status['records']):
        raise ValueError('Report must contain exactly the accepted discovery view')
    source = agent.session.source
    source.verify()
    source_root = safe_path(Path(source.manifest['sourceRoot']))
    for entry in source.manifest['files']:
        original = material_path(source_root, entry['path'])
        if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Original source changed before report: ' + entry['path'])
    directory, final_directory = safe_path(Path(directory)), safe_path(Path(final_directory))
    if (directory == source_root or source_root in directory.parents or directory in source_root.parents
            or final_directory == source_root or source_root in final_directory.parents
            or final_directory in source_root.parents):
        raise ValueError('Report directories must be outside the source tree')
    if directory == final_directory or final_directory in directory.parents or directory in final_directory.parents:
        raise ValueError('Report staging must be separate from its final publication tree')
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Report staging directory must be empty')
    index = agent.session.fact_index()
    fact_validation = index.validate()
    verification, usage = _accepted_artifacts(agent, status, payload, index)
    records, questions = payload['records'], deepcopy(payload['unknowns'])
    for key, item in questions.items():
        current = status['unknowns'].get(key)
        item['decision'] = current.get('decision') if current and current['sha256'] == item['sha256'] else None
    counts = Counter(record['kind'] for record in records.values())
    decisions = Counter((item.get('decision') or {}).get('status', '未判定') for item in questions.values())
    main = [record for record in records.values() if record['kind'] == 'function']

    def evidence(items, relative_to=final_directory):
        links = []
        for item in items:
            relative = os.path.relpath(material_path(source_root, item['path']), relative_to).replace('\\', '/')
            label = f"{item['path']}:{item['startLine']}-{item['endLine']}"
            links.append('[' + _md(label) + '](' + quote(relative, safe='/.-_') + '#L' + str(item['startLine']) + ')')
        return '<br>'.join(links) or '—'

    def value(item):
        if isinstance(item, list):
            return '、'.join(value(part) for part in item) or '—'
        if isinstance(item, str) and item in records:
            return _md(records[item]['name']) + ' (`' + records[item]['id'] + '`)'
        return _md(item)

    formal_sha = envelope['sha256']
    review = ['# discovery-agent 分類結果レビュー', '', '**ホスト採用済み・人手レビュー待ち。**', '',
              '| 項目 | 結果 |', '| --- | --- |',
              '| 対象 | ' + _md(payload['request']['projectId']) + ' / ' + _md(source_root.name) + ' |',
              '| 処理 | discoveryのみ。後続層と人手受入れの完了ではない |',
              '| 採用した要求 | ' + value(payload['acceptedRequirements']) + ' |',
              '| 分類ポリシー | ' + _md(payload.get('catalogPolicy', '未指定')) + ' |',
              '| 事実索引ポリシー | ' + _md(index.document['schema']) + ' |',
              '| 正式成果 SHA-256 | `' + formal_sha + '` |',
              '| snapshot SHA-256 | `' + source.snapshot_id + '` |',
              '| 索引 SHA-256 | `' + index.sha256 + '` |',
              '| 原文 | ' + str(len(source.manifest['files'])) + ' files |',
              '| 全記録 | ' + str(len(records)) + ' |', '',
              '[正式成果](contextbase.json) / [独立検証](result/validation.json) / '
              '[ソース事実レビュー](facts/facts-review.md)', '',
              '## 集計範囲', '', _md(payload['request']['goal']['question']), '',
              '| 分類 | 件数 |', '| --- | ---: |']
    review += ['| ' + label + ' | ' + str(counts[kind]) + ' |' for kind, label in _KINDS.items()]
    for kind, label in _KINDS.items():
        review += ['', '## ' + label, '']
        for record in records.values():
            if record['kind'] != kind:
                continue
            review += ['### ' + _md(record['name']), '', '- ID: `' + _md(record['id']) + '`',
                       '- 担当要求: ' + _md(record['ownerRequirement']), '', _md(record['statement']), '']
            for field, content in (record.get('classification') or {}).items():
                if field != 'category':
                    review.append('- ' + _FIELDS.get(field, _md(field)) + ': ' + value(content))
            review += ['- 原文根拠: ' + evidence(record['evidence']), '']
    review += ['', '## 未確認・追加調査', '']
    for key, question in questions.items():
        content, decision = question['content'], question.get('decision')
        review += ['### ' + _md(content['question']), '', '- ID: `' + _md(key) + '`',
                   '- 関連要求: ' + value(content['relatedRequirements']),
                   '- 範囲理由: ' + _md(content['scopeReason'])]
        if decision:
            review += ['- 独立判定: ' + _md(decision['status']) + ' / ' + _md(decision['reason']),
                       '- 阻害する要求: ' + value(decision['blocksRequirements']),
                       '- 判定根拠: ' + evidence(decision['evidence'])]
        else:
            review.append('- 独立判定: 未判定（解決済みとは扱わない）')
        review.append('')
    review += ['## 独立検証', '']
    for field, title, key in [('checks', '要求', 'requirement'), ('scopeChecks', '範囲', 'scope'),
                               ('classificationChecks', '分類', 'key')]:
        review += ['### ' + title, '', '| 対象 | 判定 | 理由・原文根拠 |', '| --- | --- | --- |']
        for item in verification['answer'].get(field, []):
            review.append('| ' + value(item[key]) + ' | ' + _md(item['status']) + ' | ' +
                          _md(item['reason']) + '<br>' + evidence(item['evidence']) + ' |')
        review.append('')
    fact_check = verification['answer'].get('factUsageCheck')
    if fact_check:
        review += ['### 事実利用', '', _md(fact_check['status']) + ': ' + _md(fact_check['reason']),
                   '', evidence(fact_check['evidence']), '']
    review += ['### 検証指摘', '']
    for item in verification['answer']['findings']:
        review += ['- ' + _md(item['severity']) + ' / ' + _md(item['requirement']) + ': ' +
                   _md(item['detail']), '  ' + evidence(item['evidence']), '']
    if not verification['answer']['findings']:
        review.append('指摘なし。')
    review += ['## 限界', '', '構文事実は意味上の呼出先・実行時到達性・業務機能の正解を証明しない。',
               '入力プログラム・SQL・DBを実行した結果ではない。主・子・共通の粒度と未解決事項を人手で確認する。']

    facts_root = final_directory / 'facts'
    facts = ['# ソース事実・利用証跡レビュー', '', '- 正式成果 SHA-256: `' + formal_sha + '`',
             '- 索引 SHA-256: `' + index.sha256 + '`', '',
             '[機能レビュー](../review.md) / [完全索引](source-facts.json) / [機械検査](validation.json)', '',
             '| 種別 | 件数 |', '| --- | ---: |']
    facts += ['| ' + _md(kind) + ' | ' + str(number) + ' |' for kind, number in fact_validation['counts'].items()]
    facts += ['', '## 技術入口の構文候補', '', '| 種別・名称 | route | 原文 |', '| --- | --- | --- |']
    for fact in index.by_id.values():
        if fact['kind'] == 'entry':
            data = fact['data']
            facts.append('| ' + _md(data['kind']) + ': ' + _md(data['name']) + ' | ' +
                         _md(data.get('route') or '—') + ' | ' + evidence(data['evidence'], facts_root) + ' |')
    callers = Counter(fact['data'].get('callerId') for fact in index.by_id.values() if fact['kind'] == 'call')
    facts += ['', '## 呼出位置の概観', '', '呼出は未解決の構文観測であり、確定した意味上の接続ではない。', '',
              '| 包含する宣言 | 呼出位置数 |', '| --- | ---: |']
    for caller, number in callers.items():
        data = index.by_id.get(caller, {}).get('data', {})
        facts.append('| ' + _md(data.get('qualifiedName') or caller or '宣言外') + ' | ' + str(number) + ' |')
    facts += ['', '## recordの事実利用', '', '| record | 支持するfact・原文 | 作者の説明 |', '| --- | --- | --- |']
    for item in usage:
        supports = []
        for identifier in item['factIds']:
            fact = index.by_id[identifier]
            supports.append('`' + identifier + '`<br>' + _md(fact['kind']) + ': ' +
                            _md(fact['data'].get('name') or fact['data'].get('text') or fact['kind']) +
                            '<br>' + evidence(fact['data']['evidence'], facts_root))
        facts.append('| ' + _md(records[item['recordKey']]['name']) + ' | ' +
                     ('<br>'.join(supports) or '対応factなし') + ' | ' + _md(item['reason']) + ' |')
    facts += ['', '## 制約', ''] + ['- ' + _md(item) for item in fact_validation['limitations']]

    readme = ['# discovery-agent の正式成果', '', '**ホスト採用済み・人手レビュー待ち。**', '',
              '読む入口は [review.md](review.md)。', '', '- 対象: ' + _md(payload['request']['projectId']),
              '- 採用要求: ' + value(payload['acceptedRequirements']),
              '- 分類ポリシー: ' + _md(payload.get('catalogPolicy', '未指定')),
              '- 正式成果 SHA-256: `' + formal_sha + '`', '- 全記録: ' + str(len(records)),
              '- 主機能／子操作／共通能力: ' + '/'.join(str(counts[key]) for key in ('function', 'operation', 'common')), '',
              '[正式JSON](contextbase.json) / [最終独立検証](result/validation.json) / '
              '[事実索引の案内](facts/facts-review.md)', '',
              '候補・伝送診断・テスト実行ログは正式成果へ含めない。後続層は正式JSONを受け取り、各自の原文から再検証する。',
              '本成果の採用を元目標全体・実機動作・人手受入れの完了へ広げない。']
    _write_json(directory / 'contextbase.json', envelope)
    _write_json(directory / 'result/validation.json', verification)
    _write_json(directory / 'facts/source-facts.json', {'sha256': index.sha256, 'payload': index.document})
    _write_json(directory / 'facts/validation.json', {'sha256': contracts.digest(fact_validation), 'payload': fact_validation})
    _write_markdown(directory / 'review.md', review)
    _write_markdown(directory / 'facts/facts-review.md', facts)
    _write_markdown(directory / 'README.md', readme)
    return {'files': sorted(path.relative_to(directory).as_posix() for path in directory.rglob('*') if path.is_file()),
            'recordCounts': dict(counts), 'mainFunctions': [record['name'] for record in main],
            'areas': dict(Counter(record['classification']['area'] for record in main)),
            'unknownDecisions': dict(decisions), 'factCounts': fact_validation['counts'],
            'verificationFindingCounts': dict(Counter(item['severity'] for item in verification['answer']['findings'])),
            'indexSha256': index.sha256, 'sourceSnapshot': source.snapshot_id, 'formalSha256': formal_sha,
            'classificationPolicy': payload.get('catalogPolicy'), 'sourceFactPolicy': index.document['schema'],
            'acceptedRequirements': list(payload['acceptedRequirements']), 'originalSourceUnchanged': True}
