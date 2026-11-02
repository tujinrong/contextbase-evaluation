"""One-click discovery with owned work, incremental recovery, and normal gates."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import shutil
import stat
import uuid

from contextbase_runtime import contracts
from contextbase_runtime.config import ProjectProfile, _publication_lock, read_json
from contextbase_runtime.paths import safe_path

from .agent import DiscoveryAgent
from .reporting import prepare_report


OWNER = '.discovery-launch.json'
AMENDMENT = 'amendment-operation.json'
FILES = ('target.json', 'README.md', 'review.md', 'facts/source-facts.json',
         'facts/validation.json', 'facts/facts-review.md', 'result/validation.json',
         'contextbase.json')


class LaunchBusy(RuntimeError):
    pass


def _write(path, data):
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = safe_path(path.parent / ('.launch-' + uuid.uuid4().hex))
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _json(path, value):
    _write(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def _owner(profile):
    return {'schema': 'contextbase-discovery-launch/1',
            'config': str(profile.config_path), 'target': profile.binding('discovery-agent')}


def _prepare_home(profile):
    home = safe_path(profile.work_root / 'discovery-agent-launch')
    owner = _owner(profile)
    if home.exists():
        marker = safe_path(home / OWNER)
        if not marker.is_file() or read_json(marker) != owner:
            raise ValueError('Launcher work belongs to another target or has no ownership marker: ' + str(home))
    else:
        home.mkdir(parents=True)
        # A racing first launch can only find an uninitialised home and stop.
        _json(home / OWNER, owner)
    return home, owner


@contextmanager
def _lock(home):
    path = safe_path(home / 'launch.lock')
    with path.open('a+b') as stream:
        if not path.stat().st_size:
            stream.write(b'\0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LaunchBusy('discoveryは既に実行中です。診断: ' + str(home / 'current')) from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _work_marker(owner, kind):
    return {'schema': 'contextbase-discovery-launch-work/1', 'ownerSha256': contracts.digest(owner), 'kind': kind}


def _owned(home, directory, owner):
    directory = safe_path(directory)
    if directory.parent != home or directory.name not in {
            'current', 'staging', 'amendment-current', 'amendment-staging'}:
        raise ValueError('Refusing to manage a directory outside launcher ownership')
    if not directory.is_dir() or read_json(directory / OWNER) != _work_marker(owner, directory.name):
        raise ValueError('Refusing to manage unowned launcher work: ' + str(directory))
    for path in directory.rglob('*'):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Launcher work contains a symlink or reparse point: ' + str(path))
        if not path.resolve().is_relative_to(directory):
            raise ValueError('Launcher work escapes its owned directory')


def _clean(home, directory, owner):
    if directory.exists():
        _owned(home, directory, owner)
        shutil.rmtree(directory)


def _create_owned(directory, owner):
    directory.mkdir()
    _json(directory / OWNER, _work_marker(owner, directory.name))


def _restore(profile, staging, journal):
    import hashlib
    output = profile.output('discovery-agent').parent
    if (journal.get('schema') != 'contextbase-discovery-publication/1'
            or journal.get('target') != profile.binding('discovery-agent')
            or set(journal.get('before', {})) != set(FILES)
            or set(journal.get('after', {})) != set(FILES)):
        raise ValueError('Invalid publication recovery journal')
    marker = safe_path(output / 'target.json')
    if marker.exists() and read_json(marker) != profile.binding('discovery-agent'):
        raise ValueError('Formal output ownership changed; retain publication recovery evidence')
    restored = {}
    for relative, fingerprint in journal['before'].items():
        destination = safe_path(output / relative)
        actual = hashlib.sha256(destination.read_bytes()).hexdigest() if destination.exists() else None
        if actual not in {fingerprint, journal['after'][relative]}:
            raise ValueError('Formal output changed after interrupted publication; retain recovery evidence: ' + relative)
        if fingerprint is None:
            restored[relative] = None
        else:
            data = safe_path(staging / 'rollback' / relative).read_bytes()
            if hashlib.sha256(data).hexdigest() != fingerprint:
                raise ValueError('Publication rollback backup changed')
            restored[relative] = data
    # Check every backup before changing even one final file.
    for relative, data in restored.items():
        destination = safe_path(output / relative)
        if data is None:
            destination.unlink(missing_ok=True)
        else:
            _write(destination, data)


def _recover(profile, home, staging, owner):
    if not staging.exists():
        return
    _owned(home, staging, owner)
    journal_path = staging / 'publication.json'
    if journal_path.exists():
        journal = read_json(journal_path)
        if (journal.get('schema') != 'contextbase-discovery-publication/1'
                or journal.get('target') != profile.binding('discovery-agent')
                or journal.get('status') not in {'publishing', 'committed', 'rolled-back'}
                or set(journal.get('before', {})) != set(FILES)
                or set(journal.get('after', {})) != set(FILES)):
            raise ValueError('Invalid publication recovery journal; retain staging for inspection')
        if journal.get('status') == 'publishing':
            with _publication_lock(profile.output('discovery-agent').parent):
                _restore(profile, staging, journal)
                _json(journal_path, {**journal, 'status': 'rolled-back'})
    _clean(home, staging, owner)


def _publish(profile, agent, staging):
    """Reuse export gates; publish the prepared bundle with durable rollback."""
    import hashlib
    profile.validate_workspace(agent, check_upstream=True)
    envelope = agent.export()
    profile._validate_envelope(envelope, agent.name)
    report = staging / 'report'
    if read_json(report / 'contextbase.json') != envelope:
        raise ValueError('Prepared report does not describe the accepted export')
    actual = {p.relative_to(report).as_posix() for p in report.rglob('*') if p.is_file()}
    if actual != set(FILES):
        raise ValueError('Prepared report files differ from the formal delivery contract')
    for path in report.rglob('*'):
        safe_path(path)
    target = profile.output(agent.name).parent
    with _publication_lock(target):
        marker = target / 'target.json'
        if marker.exists():
            if read_json(marker) != profile.binding(agent.name):
                raise ValueError('Formal output belongs to another source/profile/request')
        elif (target / 'contextbase.json').exists():
            raise ValueError('Existing formal output has no target ownership')
        if (target / 'contextbase.json').exists():
            profile._validate_envelope(read_json(target / 'contextbase.json'), agent.name)
        before = {}
        prepared = {relative: safe_path(report / relative).read_bytes() for relative in FILES}
        for relative in FILES:
            path = safe_path(target / relative)
            data = path.read_bytes() if path.exists() else None
            before[relative] = None if data is None else hashlib.sha256(data).hexdigest()
            if data is not None:
                _write(staging / 'rollback' / relative, data)
        journal = {'schema': 'contextbase-discovery-publication/1', 'status': 'publishing',
                   'target': profile.binding(agent.name), 'before': before,
                   'after': {relative: hashlib.sha256(data).hexdigest() for relative, data in prepared.items()},
                   'formalSha256': envelope['sha256']}
        _json(staging / 'publication.json', journal)
        try:
            # The portable JSON is the last file switched into the new version.
            for relative in FILES:
                _write(target / relative, prepared[relative])
            _json(staging / 'publication.json', {**journal, 'status': 'committed'})
        except BaseException:
            _restore(profile, staging, journal)
            _json(staging / 'publication.json', {**journal, 'status': 'rolled-back'})
            raise


def _incremental_continuation(profile, work, staging):
    """Validate an existing checkpoint against rules, profile and current input."""
    from contextbase_runtime.sources import SourceAccess

    try:
        agent = DiscoveryAgent(work)
        profile.validate_workspace(agent)
        # Use the exact acquisition rules, including additions, exclusions and
        # unsupported material states; checking old file hashes alone misses
        # new files. The comparison snapshot stays in owned ignored staging.
        observed = SourceAccess.create(profile.source, staging / 'resume-source',
            project_id=profile.request['projectId'], allowed_paths=profile.request['allowedPaths'],
            excluded_paths=profile.request['excludedPaths'])
        if observed.manifest != agent.session.source.manifest:
            raise ValueError('Current source inventory or contents changed')
        return agent, agent.status()
    except (OSError, ValueError) as exc:
        raise ValueError('Incremental checkpoint cannot be continued: ' + str(exc)
                         + '. Existing work was retained. Use --fresh for an explicitly new run '
                         'within the same owned target, or select a separate work path.') from exc


def _amendment_request(profile, home, owner, bundle, verification, findings, replace_keys, add_kinds):
    """Select the explicit operation without touching either execution workspace."""
    from contextbase_runtime import amendment_seed
    from contextbase_runtime.controller import engine_fingerprint
    import hashlib

    supplied = bundle is not None
    if not supplied and any((verification is not None, findings is not None, replace_keys, add_kinds)):
        raise ValueError('Amendment scope requires an explicit --amend-bundle')
    path = safe_path(home / AMENDMENT)
    previous = read_json(path) if path.exists() else None
    if previous is None and not supplied:
        return None
    if profile.context_mode != 'incremental':
        raise ValueError('Candidate amendment requires context_mode="incremental"')
    if supplied:
        bundle = safe_path(Path(bundle))
        if not verification:
            raise ValueError('Candidate amendment requires the source verification identity')
        for protected in (home, profile.source, profile.output_root):
            if bundle == protected or protected in bundle.parents or bundle in protected.parents:
                raise ValueError('Amendment custody input must be outside launch, source and output trees')
        selected = {'bundle': str(bundle), 'verification': verification,
                    'findings': findings, 'replaceKeys': list(replace_keys), 'addKinds': list(add_kinds)}
    else:
        selected = previous.get('selection')
        if not isinstance(selected, dict) or set(selected) != {
                'bundle', 'verification', 'findings', 'replaceKeys', 'addKinds'}:
            raise ValueError('Invalid amendment operation selection; retain the descriptor')
        bundle = safe_path(Path(selected['bundle']))
    manifest = amendment_seed.inspect_bundle(bundle)
    operation = {'schema': 'contextbase-discovery-amendment-operation/1',
                 'ownerSha256': contracts.digest(owner), 'selection': selected,
                 'work': str(home / 'amendment-current' / 'work'),
                 'engineSha256': engine_fingerprint(),
                 'agentBindingSha256': contracts.digest(DiscoveryAgent.binding()),
                 'launcherSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'bundleSha256': contracts.digest(manifest),
                 'snapshotId': manifest['sourceSnapshotId'], 'indexSha256': manifest['sourceFactsSha256']}
    if previous is not None:
        if (set(previous) not in (set(operation), set(operation) | {'seedSha256', 'specSha256', 'operationId'})
                or any(previous.get(key) != value for key, value in operation.items())):
            raise ValueError('Amendment operation changed; retain the old work and select a separate configured work path')
        return previous
    # The selection survives interruption during installation; no model starts
    # until the completed descriptor also pins the imported seed and CAS spec.
    _json(path, operation)
    return operation


def _bind_amendment(profile, home, operation, agent):
    """Install once; thereafter reject any seed/spec/source substitution."""
    from contextbase_runtime import amendment_seed
    from contextbase_runtime.amendment_runtime import operation_id
    store = agent.session.store
    selection = operation['selection']
    if not all(store.path(name).exists() for name in ('amendment-seed.json', 'amendment-spec.json')):
        amendment_seed.install(agent, Path(selection['bundle']), selection['verification'],
            selection['findings'], replace_keys=selection['replaceKeys'], add_kinds=selection['addKinds'])
    seed, spec = store.get('amendment-seed.json'), store.get('amendment-spec.json')
    bindings = {'seedSha256': contracts.digest(seed), 'specSha256': contracts.digest(spec),
                'operationId': operation_id(seed, spec),
                'snapshotId': agent.session.source.snapshot_id, 'indexSha256': agent.session.fact_index().sha256}
    if (seed['custody']['bundleSha256'] != operation['bundleSha256']
            or seed['custody']['bundlePath'] != selection['bundle']
            or seed['custody']['sourceVerificationSha256'] != selection['verification']
            or spec['replaceKeys'] != selection['replaceKeys'] or spec['addKinds'] != selection['addKinds']
            or seed['requestSha256'] != contracts.digest(profile.request)
            or seed['snapshotId'] != bindings['snapshotId'] or seed['indexSha256'] != bindings['indexSha256']):
        raise ValueError('Amendment seed no longer matches the selected input')
    if any(operation[key] != bindings[key] for key in ('snapshotId', 'indexSha256')):
        raise ValueError('Current source/index differs from the selected amendment')
    if selection['findings'] is not None and [row['finding']['id'] for row in seed['issues']] != selection['findings']:
        raise ValueError('Installed amendment findings differ from the operation selection')
    complete = {**operation, **bindings}
    if 'seedSha256' in operation and complete != operation:
        raise ValueError('Installed amendment seed/spec binding changed')
    _json(home / AMENDMENT, complete)
    return complete


def _amendment_fresh_preflight(profile, operation, staging):
    """Check the current input even when initial work creation was interrupted."""
    from contextbase_runtime.facts import FactIndex
    from contextbase_runtime.sources import SourceAccess
    from contextbase_runtime.storage import ArtifactStore
    observed = SourceAccess.create(profile.source, staging / 'fresh-source',
        project_id=profile.request['projectId'], allowed_paths=profile.request['allowedPaths'],
        excluded_paths=profile.request['excludedPaths'])
    if observed.snapshot_id != operation['snapshotId']:
        raise ValueError('Current source inventory or contents changed; amendment work was retained')
    index = FactIndex.open(observed, ArtifactStore(staging / 'fresh-index'))
    if index.sha256 != operation['indexSha256']:
        raise ValueError('Current fact index changed; amendment work was retained')


def start(config, profile_name=None, *, timeout=1800, publish_work=None, fresh=False,
          amend_bundle=None, amend_verification=None, amend_findings=None,
          replace_keys=(), add_kinds=(), emit=print):
    """Run discovery only, or finish delivery from an already-adopted local work."""
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('A positive finite per-operation timeout is required')
    if type(fresh) is not bool or (fresh and publish_work is not None):
        raise ValueError('Explicit fresh analysis cannot be combined with publish-work')
    profile = ProjectProfile.load(config, profile_name)
    try:
        home, owner = _prepare_home(profile)
    except ValueError as exc:
        if profile.context_mode != 'incremental':
            raise
        raise ValueError(str(exc) + '. Existing work was retained. Select a separate configured work path, '
                         'or restore the original target before using --fresh.') from exc
    with _lock(home):
        operation = _amendment_request(profile, home, owner, amend_bundle, amend_verification,
                                      amend_findings, replace_keys, add_kinds)
        if operation is not None and publish_work is not None:
            raise ValueError('An active amendment operation cannot be mixed with publish-work')
        current = home / ('amendment-current' if operation else 'current')
        staging = home / ('amendment-staging' if operation else 'staging')
        _recover(profile, home, staging, owner)
        # A pinned amendment cannot silently switch source even when fresh is requested.
        # Check before deleting any execution state. Custody stays outside this home.
        if operation and fresh and (current / 'work').exists():
            _create_owned(staging, owner)
            _amendment_fresh_preflight(profile, operation, staging)
            _clean(home, staging, owner)
        if publish_work is not None:
            publish_work = safe_path(Path(publish_work))
            if publish_work == current or current in publish_work.parents:
                raise ValueError('publish-work must be separate from launcher current work')
        # Only an explicit fresh request discards incremental checkpoints.
        # Full/evidence retain their existing fresh-on-click semantics.
        if profile.context_mode == 'incremental' and not fresh and current.exists():
            _owned(home, current, owner)
        else:
            _clean(home, current, owner)
            _create_owned(current, owner)
        _create_owned(staging, owner)

        def progress(phase, message, **details):
            _json(current / 'status.json', {'schema': 'contextbase-discovery-launch-status/1',
                  'phase': phase, 'message': message, **details})
            with (current / 'launch.log').open('a', encoding='utf-8') as stream:
                stream.write(message + '\n')
            emit(message)

        try:
            marker = profile.output('discovery-agent').parent / 'target.json'
            if marker.exists() and read_json(marker) != profile.binding('discovery-agent'):
                raise ValueError('Formal output belongs to another source/profile/request')
            profile._result('discovery-agent')
            progress('prepare', 'discoveryを開始します。入力: ' + str(profile.source))
            if publish_work is None:
                work = current / 'work'
                evidence_mode = profile.context_mode == 'evidence'
                incremental_mode = profile.context_mode == 'incremental'
                previous = None
                if incremental_mode and work.exists():
                    agent, previous = _incremental_continuation(profile, work, staging)
                    if previous['status'] in {'stopped', 'cancelled'}:
                        agent.session.resume(profile.request)
                        progress('resume', '保存した調査・検証を同じ入力条件で再開します。', work=str(work))
                    elif previous['status'] not in {'active', 'complete'}:
                        raise ValueError('Incremental work is not resumable; retain diagnostics and use --fresh')
                else:
                    agent = DiscoveryAgent.create(profile.source, work, profile.request,
                        evidence_mode=evidence_mode, incremental_mode=incremental_mode,
                        semantic_options=profile.semantic_options_for('discovery'))
                    profile.bind(agent)
                if operation:
                    operation = _bind_amendment(profile, home, operation, agent)
                checked = agent.session.fact_index().validate()
                progress('analysis', '索引検査pass。抽出と別文脈の独立検証を実行中です。',
                         work=str(work), sourceFactsSha256=checked['indexSha256'])
                full_mode = profile.context_mode == 'full'
                if incremental_mode and previous is not None and not previous['remainingAgentRequirements']:
                    result = {'status': 'complete', 'actions': [], 'session': previous}
                    progress('report', '採用済みのDiscovery成果を再配布します。モデルは起動しません。', work=str(work))
                else:
                    result = agent.run(timeout=timeout, inline_sources=full_mode, compact=full_mode)
                if result['status'] != 'complete':
                    progress('stopped', '未完了: ' + result['status'] + '。旧正式成果を保持しました。',
                             result=result, work=str(work))
                    return {**result, 'work': str(work), 'diagnostics': str(current), 'published': False}
            else:
                work = publish_work
                agent = DiscoveryAgent(work)
                profile.validate_workspace(agent)
                progress('report', '採用済みworkから正式レポートを作成します。モデルは起動しません。', work=str(work))
            envelope = agent.export()
            progress('report', '採用した同一版のJSON・索引・審査資料を準備しています。', work=str(work))
            summary = prepare_report(agent, envelope, staging / 'report', profile.output(agent.name).parent)
            _json(staging / 'report' / 'target.json', profile.binding(agent.name))
            progress('publish', '検査済みの正式成果を更新しています。', work=str(work))
            _publish(profile, agent, staging)
            result = {**summary, 'status': 'complete', 'published': True, 'work': str(work),
                      'output': str(profile.output(agent.name)), 'diagnostics': str(current)}
            progress('complete', '完了。確認入口: ' + str(profile.output(agent.name).parent / 'review.md'), result=result)
            _clean(home, staging, owner)
            return result
        except (Exception, KeyboardInterrupt) as exc:
            progress('interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                     '停止: ' + str(exc) + '。詳細: ' + str(current), errorType=type(exc).__name__)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description='discovery単独の新規解析・検証・正式レポート更新')
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--profile')
    parser.add_argument('--timeout', type=float, default=1800)
    parser.add_argument('--publish-work', type=Path, help='採用済みworkからの配布だけを行う。モデルは起動しない')
    parser.add_argument('--fresh', action='store_true',
                        help='incrementalの保存済み作業を、所有を確認した範囲内で明示的に作り直す')
    parser.add_argument('--amend-bundle', type=Path, help='未採用候補の封印入力。新しい改訂操作を明示選択する')
    parser.add_argument('--amend-verification', help='指摘の発生元verification SHA')
    parser.add_argument('--amend-finding', action='append', help='発生元の指摘ID。省略時は全指摘')
    parser.add_argument('--replace-key', action='append', default=[], help='置換を許す既存record key')
    parser.add_argument('--add-kind', action='append', default=[], help='追加を許すrecord kind')
    args = parser.parse_args(argv)
    try:
        result = start(args.config, args.profile, timeout=args.timeout, publish_work=args.publish_work, fresh=args.fresh,
                       amend_bundle=args.amend_bundle, amend_verification=args.amend_verification,
                       amend_findings=args.amend_finding, replace_keys=args.replace_key, add_kinds=args.add_kind,
                       emit=lambda message: print(message, flush=True))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('published') else 2
    except LaunchBusy as exc:
        print(str(exc), flush=True)
        return 3
    except KeyboardInterrupt:
        print('discoveryを中断しました。正式成果の状態は診断を確認してください。', flush=True)
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        print('discovery起動失敗: ' + str(exc), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
