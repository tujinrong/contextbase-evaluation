"""Build the Windows sample from generated sources without reading specifications."""
from pathlib import Path
import argparse
import ctypes
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sdk', type=Path, default=ROOT / '.tmp/toolchain/msys2/ucrt64')
parser.add_argument('--cc', type=Path, default=ROOT / '.tmp/toolchain/zig-x86_64-windows-0.14.1/zig.exe')
args = parser.parse_args()
if os.name != 'nt':
    raise SystemExit('This sample target is Windows x64.')
sdk, cc = args.sdk.resolve(), args.cc.resolve()
cobc = sdk / 'bin/cobc.exe'
def guard(path):
    path = Path(os.path.abspath(path))
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise ValueError('Generated output must stay within the sample directory')
    for item in (path, *path.parents):
        if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
            raise ValueError('Linked output path refused: ' + str(item))
    if str(path.resolve()).casefold() != str(path).casefold():
        raise ValueError('Redirected output path refused')
    return path

def directory(path):
    path = guard(path)
    if not any(path.is_relative_to(base) for base in (ROOT / 'build', ROOT / '.tmp')):
        raise ValueError('Generated directories must stay in build or .tmp')
    path.mkdir(parents=True, exist_ok=True)
    return path

work = directory(ROOT / '.tmp/windows-build')
# The resolved workspace was checked above. Recreate it so stale links cannot
# redirect a compiler's fixed intermediate output onto an authored input.
for directory_name, names, files in os.walk(work, followlinks=False):
    for name in (*names, *files):
        guard(Path(directory_name) / name)
shutil.rmtree(work)
work.mkdir()
final = directory(ROOT / 'build/app/windows')
env = os.environ.copy()
env.update(ZIG_GLOBAL_CACHE_DIR=str(directory(ROOT / '.tmp/cache/zig-global')),
           ZIG_LOCAL_CACHE_DIR=str(directory(ROOT / '.tmp/cache/zig-local')))
env['PATH'] = str(sdk / 'bin') + os.pathsep + env.get('PATH', '')
for name in ('TMPDIR', 'TEMP', 'TMP'):
    env[name] = os.path.relpath(directory(ROOT / '.tmp/compiler-temp'), ROOT)
commands, logs = [], []

def run(command):
    command = list(map(str, command))
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
    output = (result.stdout + result.stderr).decode('utf-8', 'replace')
    commands.append({'command': command, 'exitCode': result.returncode})
    logs.append(subprocess.list2cmdline(command) + '\nEXIT ' + str(result.returncode) + '\n' + output)
    print(f'[{result.returncode}] {Path(command[0]).name}', flush=True)
    if result.returncode:
        raise RuntimeError('Build command failed; see .tmp/windows-build/build.log')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compiler_path(path):
    # This GnuCOBOL runtime uses the Windows narrow CRT for configuration paths.
    try:
        candidate = os.path.relpath(path, ROOT)
    except ValueError:  # SDK on another drive
        candidate = str(path)
    if candidate.isascii():
        return candidate
    short = ctypes.create_unicode_buffer(32768)
    short_path = ctypes.WinDLL('kernel32', use_last_error=True).GetShortPathNameW
    short_path.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
    short_path.restype = ctypes.c_uint32
    if short_path(str(path), short, len(short)) and short.value.isascii():
        return short.value
    raise RuntimeError('GnuCOBOL needs an ASCII SDK path; pass --sdk with an ASCII directory.')

def write(path, data):
    path = guard(path)
    directory(path.parent)
    fd, name = tempfile.mkstemp(prefix='publish-', dir=work)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data.encode('utf-8') if isinstance(data, str) else data)
    os.replace(name, path)

sources = []
inputs = {}
success = False
staged = []
builder_hash = sha(Path(__file__))
summary = directory(ROOT / 'build/test-results') / 'summary.json'
def build_status(status):
    write(summary, json.dumps({
        'runId': os.environ.get('COBOL_RUN_ID', 'local-windows-build'),
        'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': status, 'buildSucceeded': success, 'applicationVerification': 'NOT_RUN',
        'scope': 'Compilation only. A rebuild invalidates any previous test PASS.',
        'notExecuted': ['current application tests', 'live SQL Server', 'manual acceptance', 'formal scoring'],
        'formalScore': None,
    }, ensure_ascii=False, indent=2) + '\n')
build_status('BUILD_RUNNING')
try:
    env['COB_CONFIG_DIR'] = compiler_path(sdk / 'share/gnucobol/config')
    for required in (cobc, cc, sdk / 'include/libcob.h', ROOT / 'bridge/windows_terminal.c'):
        if not required.is_file():
            raise RuntimeError('Required build input is absent: ' + str(required))
    sources = sorted((ROOT / 'cobol').glob('*.cob'))
    inputs = {p.relative_to(ROOT).as_posix(): sha(guard(p))
              for folder in ('cobol', 'copy', 'bridge') for p in sorted((ROOT / folder).rglob('*'))
              if p.is_file() and p.suffix in ('.cob', '.cpy', '.c', '.h')}
    run([cobc, '-V'])
    run([cc, 'version'])
    for source in sources:
        run([cobc, '-free', '-fsyntax-only', '-Wall', '-I', 'copy', source.relative_to(ROOT)])
        run([cobc, '-C', '-free', '-fstatic-call', '-I', 'copy',
             *(['-x'] if source.stem in ('STMAIN', 'STMAINT') else []),
             '-o', (work / (source.stem + '.c')).relative_to(ROOT), source.relative_to(ROOT)])
    flags = [cc, 'cc', '-std=c11', '-Wno-deprecated-non-prototype', '-target', 'x86_64-windows-gnu',
             '-DST_WINDOWS_SAMPLE=1', '-I', 'bridge', '-I', sdk / 'include']
    for name in ('student_bridge', 'windows_terminal'):
        run(flags + ['-Wall', '-Wextra', '-Werror', '-c', 'bridge/' + name + '.c', '-o', work / (name + '.o')])
    libs = [sdk / 'lib/libcob.dll.a', sdk / 'lib/libicuuc.dll.a', sdk / 'lib/libicudt.dll.a',
            sdk / 'lib/libcrypto.dll.a', '-lodbc32', '-luser32']
    common = [work / (p.stem + '.c') for p in sources if p.stem not in ('STMAIN', 'STMAINT')]
    for main, name in (('STMAIN', 'student-text.exe'), ('STMAINT', 'student-maint.exe')):
        destination = work / name
        run(flags + [work / (main + '.c'), *common, work / 'student_bridge.o', work / 'windows_terminal.o',
                     *libs, '-o', destination])
        staged.append((destination, final / name))
    if builder_hash != sha(Path(__file__)) or any(sha(guard(ROOT / name)) != digest for name, digest in inputs.items()):
        raise RuntimeError('Source changed during compilation; binaries were not published')
    # Publish only after both executables link successfully. Intermediates stay in .tmp.
    for source, target in staged:
        if target.is_symlink():
            raise ValueError('Linked executable output refused')
        write(target, source.read_bytes())
    runtime = {
        'profile': 'Windows x64 native Console / GnuCOBOL 3.2 sample',
        'authentication': 'none; user-requested sample',
        'actor': 'sample-user', 'fixedSampleRole': 'Administrator',
        'application': 'student-text.exe',
        'runtimeDirectory': str(sdk / 'bin'),
        'runtimeLibrariesIncluded': False,
        'runtimeRequirements': ['GnuCOBOL 3.2 UCRT x64 runtime', 'ICU 78.3 x64', 'OpenSSL 3.6.5 x64',
                                'Microsoft ODBC Driver 18 for SQL Server x64'],
        'databaseConfiguration': 'STUDENT_ODBC_DSN; Encrypt=Yes; TrustServerCertificate=No; no database setup is performed',
        'binaries': {target.name: sha(target) for _, target in staged},
        'formalScore': None,
    }
    write(final / 'runtime.json', json.dumps(runtime, ensure_ascii=False, indent=2) + '\n')
    success = True
finally:
    build_status('BUILD_SUCCEEDED_VERIFICATION_REQUIRED' if success else 'BUILD_FAILED')
    write(work / 'build.log', '\n'.join(logs))
    write(work / 'build.json', json.dumps({
        'succeeded': success, 'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'profile': 'Windows x64 native no-auth sample', 'compiledInputs': inputs, 'builderSha256': builder_hash,
        'commands': commands,
        'binaries': {target.name: sha(target) for _, target in staged if target.is_file()} if success else {},
        'scope': 'source-only Windows compilation/link; no database or acceptance test',
        'formalScore': None,
    }, ensure_ascii=False, indent=2) + '\n')
