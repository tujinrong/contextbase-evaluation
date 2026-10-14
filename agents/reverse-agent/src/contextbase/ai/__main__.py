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
    parser.add_argument('--document-contract', type=Path,
                        help='plan用の文書ID/kind/相対path/原ソース開始範囲だけを含むユーザー指定対応契約')
    parser.add_argument('--analysis-job', type=Path,
                        help='同じ封印snapshotとbound planで検証済みの解析checkpointを再利用し、新しいAI原稿だけ生成')
    parser.add_argument('--recover-analysis-job', action='store_true',
                        help='--analysis-jobの旧完了解析を原応答・provider・前後snapshotの検査後に明示的に遅延bind')
    parser.add_argument('--reuse-analysis', action='store_true',
                        help='iterateで同じ検証済み解析を明示的に再利用。既定は各稿で新規AI解析')
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--max-rounds', type=int, default=3)
    parser.add_argument('--deadline', help='UTC ISO8601の停止時刻。到達後に新しいAIジョブを開始しない')
    parser.add_argument('--without-independent-review', action='store_true', help='初期draftの測定用。レビュー合格とは報告しない')
    args = parser.parse_args(argv)
    if args.document_contract is not None and args.command != 'plan':
        parser.error('--document-contract is only valid for plan')
    if (args.analysis_job is not None or args.recover_analysis_job) and args.command != 'document':
        parser.error('--analysis-job and --recover-analysis-job are only valid for document')
    if args.recover_analysis_job and args.analysis_job is None:
        parser.error('--recover-analysis-job requires --analysis-job')
    if args.reuse_analysis and args.command != 'iterate':
        parser.error('--reuse-analysis is only valid for iterate')
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
                                       deadline=args.deadline, revision_context=revision,
                                       **({'document_contract': args.document_contract} if args.document_contract is not None else {}))
            elif args.command == 'iterate':
                from .iteration import run
                if not args.plan or not args.document_id or not args.output:
                    parser.error('--plan, --document-id and --output required')
                result = run(args.snapshot, args.plan, args.document_id, args.job, args.output,
                             max_rounds=args.max_rounds, timeout=args.timeout, deadline=args.deadline,
                             reuse_analysis=args.reuse_analysis)
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
                    if args.recover_analysis_job:
                        workflow.recover_analysis_checkpoint(args.snapshot, definition, args.analysis_job)
                    resume_options = {'analysis_job': args.analysis_job} if args.analysis_job is not None else {}
                    result = workflow.document(args.snapshot, definition, args.job, args.output,
                                               timeout=args.timeout, revision_context=revision,
                                               deadline=args.deadline, **resume_options)
                else:
                    if not args.document:
                        parser.error('--document required')
                    result = workflow.review(args.snapshot, args.document, definition, args.job,
                                             timeout=args.timeout, deadline=args.deadline)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get('status') in {'FAILED', 'NOT_RUN_TIME_LIMIT'} else 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'FAILED', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
