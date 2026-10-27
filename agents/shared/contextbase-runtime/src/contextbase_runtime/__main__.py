"""Explicit extraction steps; never falls through into draft or publication."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .controller import Session
from .contracts import STAGES


def load(path: Path) -> dict:
    if path.stat().st_size > 8_000_000:
        raise ValueError('Analysis request/response file is too large')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description='ContextBase 取得・関係構築・動作深化と独立検証（仕様書は生成しない）',
        epilog='v2: 抽出には step --stage、独立検証には verify を使用する。旧 --role は受理しない。')
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='選択範囲を封印し、新しい解析セッションを作る')
    init.add_argument('--source', type=Path, required=True)
    init.add_argument('--request', type=Path, required=True)
    step = commands.add_parser('step', help='新しい文脈で1抽出層を実行する')
    step.add_argument('--stage', choices=STAGES, required=True)
    step.add_argument('--requirements', nargs='+', help='元目標のうち今回扱う義務ID')
    step.add_argument('--feedback', help='修訂の根拠となる候補内容ハッシュ')
    step.add_argument('--prepare-only', action='store_true', help='手動引継ぎのみ。独立実行の証明にはしない')
    verify = commands.add_parser('verify', help='候補を別の文脈で原文から独立検証する')
    verify.add_argument('--candidate', required=True, help='検証する候補内容ハッシュ')
    verify.add_argument('--prepare-only', action='store_true', help='手動検証依頼のみ。独立実行の証明にはしない')
    run = commands.add_parser('run', help='前提が成立した義務を抽出・独立検証・採用し、阻害時は保存して止める')
    run.add_argument('--requirements', nargs='+', help='元目標のうち今回扱う義務ID')
    for operation in (step, verify, run):
        operation.add_argument('--timeout', type=float, default=1800, help='単独操作の秒数。総実行予算ではない')
        operation.add_argument('--inline-sources', action='store_true', help='1 MiB以下の選択原文と表示用行番号を直接渡す')
    revise = commands.add_parser('revise', help='採用済み義務と依存先を撤回し、明示的に再調査する')
    revise.add_argument('--requirements', nargs='+', required=True)
    revise.add_argument('--reason', required=True)
    submit = commands.add_parser('submit', help='手動候補・指摘を保存する（自動採用不可）')
    submit.add_argument('--task', required=True)
    submit.add_argument('--answer', type=Path, required=True)
    adopt = commands.add_parser('adopt', help='独立検証後の候補採用と範囲受入れを記録する')
    adopt.add_argument('--candidate', required=True)
    commands.add_parser('status', help='正本と未達義務・候補を確認する')
    commands.add_parser('index', help='封印済み原文の語法索引と能力制約を確認する')
    cancel = commands.add_parser('cancel', help='有効成果を保ったまま停止する')
    cancel.add_argument('--reason', default='user-cancelled')
    resume = commands.add_parser('resume', help='同じ入力・目標・権限を再照合して再開する')
    resume.add_argument('--request', type=Path, required=True)
    for command in commands.choices.values():
        command.add_argument('--work', type=Path, required=True, help='承認した専用の作業ディレクトリ')
    actual = list(sys.argv[1:] if argv is None else argv)
    if any(item == '--role' or item.startswith('--role=') for item in actual):
        parser.error('旧 --role は使用できない。v2 の抽出は step --stage、独立検証は verify を使用する。'
                     'investigation を relationship／behavior へ自動変換しない。')
    args = parser.parse_args(actual)
    try:
        if args.command == 'init':
            result = Session.create(args.source, args.work, load(args.request)).status()
        else:
            session = Session.open(args.work)
            if args.command == 'step':
                if args.prepare_only:
                    result = session.prepare(args.stage, requirements=args.requirements, feedback=args.feedback)
                else:
                    result = session.execute(args.stage, feedback=args.feedback,
                                             requirements=args.requirements, timeout=args.timeout,
                                             inline_sources=args.inline_sources)
            elif args.command == 'verify':
                if args.prepare_only:
                    result = session.prepare_verification(args.candidate)
                else:
                    result = session.verify(args.candidate, timeout=args.timeout, inline_sources=args.inline_sources)
            elif args.command == 'run':
                result = session.run(requirements=args.requirements, timeout=args.timeout,
                                     inline_sources=args.inline_sources)
            elif args.command == 'revise':
                result = session.revise(args.requirements, args.reason)
            elif args.command == 'submit':
                result = session.submit(args.task, load(args.answer))
            elif args.command == 'adopt':
                result = session.adopt(args.candidate)
            elif args.command == 'cancel':
                result = session.cancel(args.reason)
            elif args.command == 'resume':
                result = session.resume(load(args.request))
            elif args.command == 'index':
                result = {'snapshotId': session.source.snapshot_id, 'files': session.index()}
            else:
                result = session.status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == 'run' and result.get('status') not in {'complete', 'scope-complete'}:
            return 2
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1
    except KeyboardInterrupt:
        print(json.dumps({'status': 'interrupted', 'accepted': False}))
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
