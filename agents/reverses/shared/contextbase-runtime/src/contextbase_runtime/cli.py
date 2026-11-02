"""CLI mechanics shared by agent-owned entry points; no agent registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .paths import safe_path
from .sources import _json


def load(path):
    path = safe_path(Path(path))
    if path.stat().st_size > 32_000_000:
        raise ValueError('Agent JSON input exceeds the read limit')
    return _json(path)


def main(agent_type, argv=None):
    parser = argparse.ArgumentParser(description=agent_type.name + ': ソース解析と独立検証')
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='source-only入力と自身の作業先を固定する')
    init.add_argument('--source', type=Path)
    init.add_argument('--request', type=Path)
    init.add_argument('--semantic-project', help='静的呼出先を取得する封印範囲内csproj。evidence/incremental/native専用')
    init.add_argument('--semantic-configuration', choices=['Debug', 'Release'])
    init_modes = init.add_mutually_exclusive_group()
    init_modes.add_argument('--evidence', action='store_true',
                            help='新しい作業先でhost取証対話を明示利用する。設定時はcontext_mode=evidenceが必要')
    init_modes.add_argument('--incremental', action='store_true',
                            help='新しい作業先で草稿保存と分割独立検証を利用する。設定時はcontext_mode=incrementalが必要')
    init_modes.add_argument('--native', action='store_true',
                            help='役割別のCodex工具セッションで連続取証する。設定時はcontext_mode=nativeが必要')
    if agent_type.stage not in {'discovery', None}:
        init.add_argument('--handoff', type=Path, help='前層の可搬成果。runで独立再検証する')
    run = commands.add_parser('run', help='担当範囲を解析し、独立検証・採用する')
    run.add_argument('--requirements', nargs='+')
    run.add_argument('--timeout', type=float, default=1800)
    run.add_argument('--inline-sources', action='store_true')
    run.add_argument('--compact', action='store_true', help='task束縛の短縮参照を使い、検査前に正規形へ展開する')
    retry = commands.add_parser('retry', help='自層の候補への指摘を明示し、一度だけ再調査・独立検証する')
    retry.add_argument('--feedback', required=True)
    retry.add_argument('--requirements', nargs='+')
    retry.add_argument('--timeout', type=float, default=1800)
    retry.add_argument('--inline-sources', action='store_true')
    retry.add_argument('--compact', action='store_true')
    repair = commands.add_parser('repair', help='失敗草稿の指定レコードを明示修復し、全体を独立検証する')
    repair.add_argument('--from-work', type=Path, required=True)
    repair.add_argument('--task', required=True)
    repair.add_argument('--record', action='append', required=True)
    repair.add_argument('--timeout', type=float, default=1800)
    repair.add_argument('--inline-sources', action='store_true')
    repair.add_argument('--compact', action='store_true')
    amend = commands.add_parser('amend-candidate', help='未採用候補の指摘を明示改訂し、新候補全体を独立検証する')
    amend_source = amend.add_mutually_exclusive_group(required=True)
    amend_source.add_argument('--bundle', type=Path, help='discovery incremental候補の可搬bundle')
    amend_source.add_argument('--from-work', type=Path, help='native joint候補を保持する元work')
    amend.add_argument('--candidate', help='--from-workで改訂する候補ID')
    amend.add_argument('--verification', required=True)
    amend.add_argument('--finding', action='append')
    amend.add_argument('--replace-key', action='append', default=[])
    amend.add_argument('--add-kind', action='append', default=[])
    amend.add_argument('--timeout', type=float, default=1800)
    amend.add_argument('--inline-sources', action='store_true')
    amend.add_argument('--compact', action='store_true')
    commands.add_parser('status')
    commands.add_parser('index')
    query = commands.add_parser('query', help='封印ソースの構文事実を検索する。モデルを呼ばない')
    query.add_argument('--text')
    query.add_argument('--path')
    query.add_argument('--kind', choices=['symbol', 'call', 'entry', 'import'])
    query.add_argument('--caller')
    query.add_argument('--callee')
    query.add_argument('--route')
    query.add_argument('--limit', type=int)
    semantic = commands.add_parser('semantic-calls', help='封印済みC#入力の宣言呼出先を静的解決する。モデル・対象ビルドなし')
    semantic.add_argument('--snapshot', type=Path, required=True)
    semantic.add_argument('--project', required=True, help='封印inventory内の相対csprojパス')
    semantic.add_argument('--configuration', choices=['Debug', 'Release'], default='Release')
    semantic.add_argument('--frozen', action='store_true', help='元ソースの現行一致検査を省き、明示した封印版を検索する')
    semantic.add_argument('--package-root', type=Path, action='append', help='明示したローカル解析用package cache')
    semantic.add_argument('--text')
    semantic.add_argument('--path')
    semantic.add_argument('--caller')
    semantic.add_argument('--callee')
    semantic.add_argument('--status', choices=['resolved', 'candidates', 'unresolved', 'dynamic'])
    semantic.add_argument('--limit', type=int, default=50)
    semantic.add_argument('--offset', type=int, default=0)
    semantic.add_argument('--validate-only', action='store_true')
    commands.add_parser('validate-index', help='索引の内容指紋・根拠・参照を検査する。モデルを呼ばない')
    commands.add_parser('paths', help='設定から解決したパスを表示する（解析・作業先作成なし）')
    output = commands.add_parser('export', help='親のworkに依存しない可搬成果を出力する')
    output.add_argument('--output', type=Path)
    revise = commands.add_parser('revise')
    revise.add_argument('--requirements', nargs='+', required=True)
    revise.add_argument('--reason', required=True)
    cancel = commands.add_parser('cancel')
    cancel.add_argument('--reason', default='user-cancelled')
    resume = commands.add_parser('resume')
    resume.add_argument('--request', type=Path)
    for command in commands.choices.values():
        command.add_argument('--work', type=Path)
        command.add_argument('--config', type=Path, help='source/request/work/正式成果を定めるproject TOML')
        command.add_argument('--profile', help='設定内profile。省略時はdefault_profile')
    args = parser.parse_args(argv)
    try:
        if args.command == 'semantic-calls':
            if args.config or args.profile or args.work is None:
                raise ValueError('semantic-calls requires explicit --snapshot, --project and a separate --work cache')
            from .sources import SourceAccess
            from .storage import ArtifactStore
            from .facts import FactIndex
            from .semantic_calls import SemanticCallIndex
            snapshot, work = safe_path(args.snapshot), safe_path(args.work)
            source = SourceAccess.open(snapshot)
            original = safe_path(Path(source.manifest['sourceRoot']))
            if any(work == protected or protected in work.parents or work in protected.parents
                   for protected in (snapshot, original)):
                raise ValueError('Semantic cache must not overlap the frozen snapshot or original source')
            if (work / 'session.json').exists() or (work / 'state.json').exists():
                raise ValueError('Semantic cache must be separate from an existing Agent session')
            store = ArtifactStore(work)
            index = SemanticCallIndex.open(FactIndex.open(source, store), store,
                project=args.project, package_roots=args.package_root, configuration=args.configuration)
            if not args.frozen:
                index.assert_current_source()
            result = index.validate() if args.validate_only else index.query(**{key: getattr(args, key) for key in
                ('text', 'path', 'caller', 'callee', 'status', 'limit', 'offset')})
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == 'amend-candidate':
            if agent_type.stage is None:
                if args.from_work is None or not args.candidate:
                    raise ValueError('Native joint amendment requires --from-work and --candidate')
                if args.add_kind or args.compact or args.inline_sources:
                    raise ValueError('Native joint amendment does not support --add-kind, --compact or --inline-sources')
            elif agent_type.stage != 'discovery':
                raise ValueError('amend-candidate is supported only by discovery-agent or native joint analysis; R/B amendment is unsupported')
            elif args.from_work is not None or args.candidate is not None:
                raise ValueError('Discovery amendment requires --bundle; --from-work/--candidate require native joint analysis')
        profile = None
        if args.config:
            if any(getattr(args, name, None) is not None
                   for name in ('source', 'request', 'work', 'handoff', 'output')):
                raise ValueError('--config cannot be mixed with explicit source/request/work/handoff/output paths')
            if getattr(args, 'semantic_project', None) is not None or getattr(args, 'semantic_configuration', None) is not None:
                raise ValueError('--config uses its semantic_project; do not mix explicit semantic options')
            from .config import ProjectProfile
            profile = ProjectProfile.load(args.config, args.profile)
            args.work = profile.work(agent_type.name)
        elif args.profile:
            raise ValueError('--profile requires --config')
        elif args.command == 'paths':
            raise ValueError('paths requires --config')
        elif args.work is None:
            raise ValueError('--work or --config is required')
        if args.command == 'paths':
            result = profile.describe(agent_type)
        elif args.command == 'init':
            handoff = getattr(args, 'handoff', None)
            if profile:
                selected_mode = 'evidence' if args.evidence else 'incremental' if args.incremental else 'native' if args.native else None
                if selected_mode is not None and profile.context_mode != selected_mode:
                    raise ValueError('--' + selected_mode + ' requires context_mode="' + selected_mode
                                     + '" in the selected profile; the flag cannot override its configured mode')
                if agent_type.stage is None and profile.context_mode != 'native':
                    raise ValueError('Project analysis requires context_mode="native"')
                native = ({'native_mode': True, 'role_specs': profile.role_specs}
                          if profile.context_mode == 'native' else {})
                agent = agent_type.create(profile.source, args.work, profile.request,
                                          handoff=profile.upstream(agent_type),
                                          evidence_mode=profile.context_mode == 'evidence',
                                          incremental_mode=profile.context_mode == 'incremental',
                                          semantic_options=profile.semantic_options_for(agent_type.stage), **native)
                profile.bind(agent)
            else:
                if args.source is None or args.request is None:
                    raise ValueError('Manual init requires --source and --request')
                if args.semantic_configuration and not args.semantic_project:
                    raise ValueError('--semantic-configuration requires --semantic-project')
                if agent_type.stage is None and (args.evidence or args.incremental):
                    raise ValueError('Project analysis uses native role execution')
                native = {'native_mode': True} if args.native or agent_type.stage is None else {}
                agent = agent_type.create(args.source, args.work, load(args.request),
                                          handoff=load(handoff) if handoff else None,
                                          evidence_mode=args.evidence, incremental_mode=args.incremental,
                                          semantic_options={'project': args.semantic_project,
                                              'configuration': args.semantic_configuration or 'Release'}
                                              if args.semantic_project else None, **native)
            result = agent.status()
        else:
            agent = agent_type(args.work)
            if profile:
                profile.validate_workspace(agent, check_upstream=args.command in {
                    'run', 'retry', 'repair', 'amend-candidate', 'export'})
            if args.command == 'run':
                if profile:
                    profile.receive_if_ready(agent)
                result = agent.run(requirements=args.requirements, timeout=args.timeout,
                                   inline_sources=args.inline_sources, compact=args.compact)
            elif args.command == 'retry':
                result = agent.retry(args.feedback, requirements=args.requirements, timeout=args.timeout,
                                     inline_sources=args.inline_sources, compact=args.compact)
            elif args.command == 'repair':
                result = agent.repair(args.from_work, args.task, args.record, timeout=args.timeout,
                                      inline_sources=args.inline_sources, compact=args.compact)
            elif args.command == 'amend-candidate':
                if agent_type.stage is None:
                    result = agent.amend_candidate(args.from_work, args.candidate, args.verification, args.finding,
                        replace_keys=args.replace_key, timeout=args.timeout)
                else:
                    result = agent.amend_candidate(args.bundle, args.verification, args.finding,
                        replace_keys=args.replace_key, add_kinds=args.add_kind, timeout=args.timeout,
                        inline_sources=args.inline_sources, compact=args.compact)
            elif args.command == 'export':
                if profile:
                    result = profile.publish(agent)
                else:
                    if args.output is None:
                        raise ValueError('Manual export requires --output')
                    output = safe_path(args.output)
                    # Manual publication always uses a fresh path.
                    for protected in (agent.work.resolve(), Path(agent.session.source.manifest['sourceRoot'])):
                        if output == protected or protected in output.parents:
                            raise ValueError('Export must be outside the source and workspace trees')
                    if output.exists():
                        raise ValueError('Export output must be a fresh path')
                    result = agent.export()
                    output.parent.mkdir(parents=True, exist_ok=True)
                    with output.open('x', encoding='utf-8', newline='\n') as stream:
                        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                        stream.write('\n')
                    result = {'status': 'exported', 'output': str(output), 'sha256': result['sha256']}
            elif args.command == 'index':
                result = {'files': agent.session.index()}
            elif args.command == 'query':
                result = agent.session.fact_index().query(**{key: getattr(args, key) for key in
                    ('text', 'path', 'kind', 'caller', 'callee', 'route', 'limit')})
            elif args.command == 'validate-index':
                result = agent.session.fact_index().validate()
            elif args.command == 'revise':
                agent.session._select(args.requirements, agent.stage)
                result = agent.session.revise(args.requirements, args.reason)
            elif args.command == 'cancel':
                result = agent.session.cancel(args.reason)
            elif args.command == 'resume':
                if profile:
                    result = agent.session.resume(profile.request)
                else:
                    if args.request is None:
                        raise ValueError('Manual resume requires --request')
                    result = agent.session.resume(load(args.request))
            else:
                result = agent.status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command in {'run', 'retry', 'repair', 'amend-candidate'} and result.get('status') != 'complete' else 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1
    except KeyboardInterrupt:
        print(json.dumps({'status': 'interrupted', 'accepted': False}))
        return 130
