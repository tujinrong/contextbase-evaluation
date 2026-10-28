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
    if directory.parent != home or directory.name not in {'current', 'staging'}:
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


def start(config, profile_name=None, *, timeout=1800, publish_work=None, fresh=False, emit=print):
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
    current, staging = home / 'current', home / 'staging'
    with _lock(home):
        _recover(profile, home, staging, owner)
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
                                                  evidence_mode=evidence_mode, incremental_mode=incremental_mode)
                    profile.bind(agent)
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
    args = parser.parse_args(argv)
    try:
        result = start(args.config, args.profile, timeout=args.timeout, publish_work=args.publish_work, fresh=args.fresh,
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
