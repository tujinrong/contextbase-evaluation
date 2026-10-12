"""Mode-aware AI stages: source-only by default, explicit assisted references."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from . import capsule


def main(argv=None):
    parser = argparse.ArgumentParser(description='AIによる原文解析・文書計画・執筆・独立レビュー')
    parser.add_argument('command', choices=['snapshot', 'plan', 'document', 'review', 'batch', 'iterate'])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--project-id', default='project')
    parser.add_argument('--authorized-reference-directory', action='append', default=[], type=Path,
                        help='ユーザーが訓練材料として明示許可した設計資料ディレクトリだけ指定')
    parser.add_argument('--job', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--document-id')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--document', type=Path)
    parser.add_argument('--revision-context', type=Path)
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--max-rounds', type=int, default=3)
    parser.add_argument('--deadline', help='UTC ISO8601の停止時刻。到達後に新しいAIジョブを開始しない')
    parser.add_argument('--without-independent-review', action='store_true', help='初期draftの測定用。レビュー合格とは報告しない')
    args = parser.parse_args(argv)
    try:
        if args.command == 'snapshot':
            if not args.source:
                parser.error('--source required')
            value = capsule.create(args.source, args.snapshot, project_id=args.project_id,
                                   authorized_reference_directories=tuple(args.authorized_reference_directory))
            result = {'status': 'SOURCE_SNAPSHOT_CREATED', 'files': len(value['files']), 'snapshot': str(args.snapshot)}
        else:
            from . import workflow
            if not args.job:
                parser.error('--job required')
            if args.command == 'plan':
                revision = json.loads(args.revision_context.read_text(encoding='utf-8')) if args.revision_context else None
                result = workflow.plan(args.snapshot, args.job, timeout=args.timeout,
                                       deadline=args.deadline, revision_context=revision)
            elif args.command == 'iterate':
                from .iteration import run
                if not args.plan or not args.document_id or not args.output:
                    parser.error('--plan, --document-id and --output required')
                result = run(args.snapshot, args.plan, args.document_id, args.job, args.output,
                             max_rounds=args.max_rounds, timeout=args.timeout, deadline=args.deadline)
            elif args.command == 'batch':
                from .batch import run
                if not args.plan or not args.output:
                    parser.error('--plan and --output required')
                result = run(args.snapshot, args.plan, args.job, args.output,
                             document_ids=[args.document_id] if args.document_id else None,
                             workers=args.workers, deadline=args.deadline, timeout=args.timeout,
                             independent_review=not args.without_independent_review)
            else:
                if not args.plan or not args.document_id:
                    parser.error('--plan and --document-id required')
                definition = workflow.select_document(args.plan, args.document_id)
                if args.command == 'document':
                    if not args.output:
                        parser.error('--output required')
                    revision = json.loads(args.revision_context.read_text(encoding='utf-8')) if args.revision_context else None
                    result = workflow.document(args.snapshot, definition, args.job, args.output,
                                               timeout=args.timeout, revision_context=revision,
                                               deadline=args.deadline)
                else:
                    if not args.document:
                        parser.error('--document required')
                    result = workflow.review(args.snapshot, args.document, definition, args.job,
                                             timeout=args.timeout, deadline=args.deadline)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'FAILED', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
