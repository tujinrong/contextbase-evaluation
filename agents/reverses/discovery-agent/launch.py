"""Repository bootstrap for the independently installed discovery launcher.

This file uses only the standard library. It never imports source projects or
reverse-agent, and never removes or recreates an existing environment.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import venv


OWNER_SCHEMA = 'contextbase-discovery-environment/1'
PROBE = r'''
import importlib.metadata, importlib.util, json, pathlib, sys
expected = json.loads(sys.argv[1])
assert sys.version_info >= (3, 11), 'Python 3.11 or later is required'
for name, root in expected['modules'].items():
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.origin, name + ' is unavailable'
    assert pathlib.Path(spec.origin).resolve().is_relative_to(pathlib.Path(root)), name + ' uses another checkout'
for name, version in expected['versions'].items():
    assert importlib.metadata.version(name) == version, name + ' has an unexpected version'
for name in ('contextbase', 'docsite', 'specgen', 'contextbase_relationship', 'contextbase_behavior'):
    assert importlib.util.find_spec(name) is None, name + ' must not be installed in the discovery environment'
'''


class BootstrapError(RuntimeError):
    pass


class PreparationBusy(BootstrapError):
    pass


def safe_path(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink() or (item.exists() and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
            raise BootstrapError('リンクを含む起動・環境パスは使用できません: ' + str(item))
    return path.resolve()


def environment_python(directory: Path) -> Path:
    return directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


@contextmanager
def preparation_lock(path: Path):
    """The operating system releases this lock even after a crashed process."""
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open('a+b')
    acquired = False
    try:
        if os.name == 'nt':
            import msvcrt
            if stream.tell() == 0:
                stream.write(b'\0')
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise PreparationBusy('discovery の起動処理が実行中です。環境・起動ロック: ' + str(path)) from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise PreparationBusy('discovery の起動処理が実行中です。環境・起動ロック: ' + str(path)) from exc
        acquired = True
        yield
    finally:
        if acquired:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def source_binding(agent_root: Path, runtime_root: Path) -> dict:
    digest = hashlib.sha256()
    versions = {}
    for root in (runtime_root, agent_root):
        project_file = safe_path(root / 'pyproject.toml')
        document = tomllib.loads(project_file.read_text(encoding='utf-8'))
        project = document['project']
        versions[project['name']] = project['version']
        dependencies = list(project.get('dependencies', []))
        if root == runtime_root:
            dependencies.extend(project.get('optional-dependencies', {}).get('analysis', []))
        for dependency in dependencies:
            if '==' in dependency and ';' not in dependency:
                name, version = dependency.split('==', 1)
                versions[name.strip()] = version.strip()
        files = [project_file, *sorted((root / 'src').rglob('*.py'))]
        for path in files:
            path = safe_path(path)
            digest.update(str(path.relative_to(root)).replace('\\', '/').encode('utf-8'))
            digest.update(b'\0')
            digest.update(path.read_bytes())
            digest.update(b'\0')
    digest.update(OWNER_SCHEMA.encode('ascii'))
    digest.update(sys.version.encode('utf-8'))
    return {'fingerprint': digest.hexdigest(),
            'modules': {'contextbase_runtime': str(runtime_root / 'src'),
                        'contextbase_discovery': str(agent_root / 'src')},
            'versions': versions}


def probe_environment(python: Path, binding: dict) -> bool:
    if not python.is_file():
        return False
    try:
        result = subprocess.run([str(python), '-I', '-X', 'utf8', '-c', PROBE,
                                 json.dumps(binding, ensure_ascii=False)],
                                capture_output=True, text=True, encoding='utf-8', check=False)
    except OSError:
        return False
    return result.returncode == 0


def write_json(path: Path, value: dict):
    temporary = safe_path(path.with_suffix(path.suffix + '.pending'))
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(safe_path(path))


def prepare_environment(agent_root: Path) -> Path:
    agent_root = safe_path(agent_root)
    runtime_root = safe_path(agent_root.parent / 'shared/contextbase-runtime')
    directory = safe_path(agent_root / '.tmp/oneclick-environment')
    owner = {'schema': OWNER_SCHEMA, 'agentRoot': str(agent_root), 'environment': str(directory)}
    marker = safe_path(directory / 'owner.json')
    stamp = safe_path(directory / 'installed.json')
    if directory.exists():
        if not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')) != owner:
            raise BootstrapError('所有を確認できない既存環境は変更しません: ' + str(directory))
    else:
        directory.mkdir(parents=True)
        write_json(marker, owner)

    python = safe_path(environment_python(directory))
    if not python.is_file():
        print('discovery 専用 Python 環境を準備しています: ' + str(directory), flush=True)
        try:
            venv.EnvBuilder(with_pip=True, symlinks=False).create(directory)
        except (OSError, subprocess.SubprocessError) as exc:
            raise BootstrapError('専用環境の作成に失敗しました。既存成果は変更していません。') from exc

    binding = source_binding(agent_root, runtime_root)
    installed = json.loads(stamp.read_text(encoding='utf-8')) if stamp.is_file() else None
    if installed != binding or not probe_environment(python, binding):
        print('共通 runtime と discovery-agent を導入・更新しています。初回はパッケージ取得が必要です。', flush=True)
        command = [str(python), '-I', '-X', 'utf8', '-m', 'pip', 'install',
                   '--disable-pip-version-check', '--no-input',
                   '-e', str(runtime_root) + '[analysis]', '-e', str(agent_root)]
        try:
            result = subprocess.run(command, cwd=agent_root, check=False)
        except OSError as exc:
            raise BootstrapError('依存パッケージの導入を開始できませんでした。') from exc
        if result.returncode:
            raise BootstrapError('依存パッケージの導入に失敗しました。上の pip エラーを確認してください。正式成果は変更していません。')
        if not probe_environment(python, binding):
            raise BootstrapError('専用環境の検査に失敗しました。Python・依存版・ローカル package の配置を確認してください。')
        write_json(stamp, binding)
    else:
        print('準備済みの discovery 専用環境を使用します。', flush=True)
    return python


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='discovery-agent の独立環境を準備し、設定から一括起動する')
    parser.add_argument('--config', type=Path, required=True, help='プロジェクトの contextbase.toml')
    parser.add_argument('--no-pause', action='store_true', help='Windows wrapper の自動実行用（先頭で指定）')
    args, remaining = parser.parse_known_args(argv)
    try:
        if sys.version_info < (3, 11):
            raise BootstrapError('Python 3.11 以降をインストールしてください。')
        config = safe_path(args.config)
        if not config.is_file():
            raise BootstrapError('設定ファイルが見つかりません: ' + str(config))
        agent_root = safe_path(Path(__file__).parent)
        # Keep preparation serialized until the child exits, so a second click
        # cannot update this environment while its analysis process is running.
        with preparation_lock(agent_root / '.tmp/oneclick-start.lock'):
            python = prepare_environment(agent_root)
            result = subprocess.run([str(python), '-I', '-X', 'utf8', '-m',
                                     'contextbase_discovery.launch', '--config', str(config), *remaining],
                                    cwd=config.parent, check=False)
            return result.returncode
    except PreparationBusy as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 2
    except (BootstrapError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('discovery 起動失敗: ' + str(exc), file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print('discovery の起動を中断しました。成功として扱いません。', file=sys.stderr, flush=True)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
