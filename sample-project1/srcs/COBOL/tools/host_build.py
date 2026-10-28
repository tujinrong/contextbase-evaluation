"""Compile the Windows no-auth sample and its independent native boundary probes."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
from output_paths import result_dir, reset_work, guard, ensure_directory, write_latest, write_json
from evidence import compiled_inputs, binary_hashes

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
out = reset_work(ROOT / '.tmp/host')
work = ROOT / '.tmp/windows-build'
sdk = ROOT / '.tmp/toolchain/msys2/ucrt64'
zig = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / '.tmp/toolchain/zig-x86_64-windows-0.14.1/zig.exe'
run_id = os.environ.get('COBOL_RUN_ID', 'local-cobol')
report = result_dir('host-build', os.environ.get('COBOL_TEST_REPORT_DIR'))
prefix = report / 'host-build'
env = os.environ.copy()
env.update(COB_CONFIG_DIR=os.path.relpath(sdk / 'share/gnucobol/config', ROOT),
           ZIG_GLOBAL_CACHE_DIR=str(ensure_directory(ROOT / '.tmp/cache/zig-global')),
           ZIG_LOCAL_CACHE_DIR=str(ensure_directory(ROOT / '.tmp/cache/zig-local')))
env['PATH'] = str(sdk / 'bin') + os.pathsep + env.get('PATH', '')
temporary = ensure_directory(ROOT / '.tmp/compiler-temp')
for name in ('TMPDIR', 'TEMP', 'TMP'):
    env[name] = os.path.relpath(temporary, ROOT)
results, logs = [], []
succeeded = False
evidence_file = out / 'build-evidence.json'
write_json(evidence_file, {'succeeded': False, 'status': 'BUILD_RUNNING'})
write_json(ROOT / 'build/test-results/summary.json', {
    'runId': run_id, 'status': 'BUILD_RUNNING', 'buildSucceeded': False,
    'applicationVerification': 'NOT_RUN', 'formalScore': None,
})
host_inputs = compiled_inputs()

def run(command):
    command = list(map(str, command))
    result = subprocess.run(command, env=env, capture_output=True)
    output = (result.stdout + result.stderr).decode('utf-8', 'replace')
    results.append({'command': command, 'exitCode': result.returncode})
    logs.append(subprocess.list2cmdline(command) + '\nEXIT ' + str(result.returncode) + '\n' + output)
    print(f'[{result.returncode}] {Path(command[0]).name}', flush=True)
    if result.returncode:
        raise RuntimeError('Windows build failed; see build/test-results/host-build/host-build.raw.log')

try:
    run([sys.executable, 'tools/input_lock.py'])
    run([sys.executable, 'build.py', '--sdk', sdk, '--cc', zig])
    cobc = sdk / 'bin/cobc.exe'
    for source in sorted((ROOT / 'tests').glob('*.cob')):
        run([cobc, '-free', '-fsyntax-only', '-Wall', '-I', 'copy', source.relative_to(ROOT)])
        run([cobc, '-C', '-free', '-fstatic-call', '-I', 'copy', '-x',
             '-o', (out / (source.stem + '.c')).relative_to(ROOT), source.relative_to(ROOT)])
    flags = [zig, 'cc', '-std=c11', '-Wno-deprecated-non-prototype', '-target', 'x86_64-windows-gnu',
             '-DST_WINDOWS_SAMPLE=1', '-I', 'bridge', '-I', sdk / 'include']
    libs = [sdk / 'lib/libcob.dll.a', sdk / 'lib/libicuuc.dll.a', sdk / 'lib/libicudt.dll.a',
            sdk / 'lib/libcrypto.dll.a', '-lodbc32', '-luser32']
    common = [work / (p.stem + '.c') for p in sorted((ROOT / 'cobol').glob('*.cob'))
              if p.stem not in ('STMAIN', 'STMAINT')]
    bridge = work / 'student_bridge.o'
    terminal = work / 'windows_terminal.o'
    run(flags + [out / 'date-probe.c', work / 'STDATE.c', bridge, *libs, '-o', out / 'date-probe.exe'])
    run(flags + [out / 'abi-probe.c', 'tests/abi-helper.c', sdk / 'lib/libcob.dll.a', '-o', out / 'abi-probe.exe'])
    run(flags + ['tests/boundary-probe.c', bridge, *libs, '-o', out / 'boundary-probe.exe'])
    run(flags + [out / 'validation-probe.c', *common, bridge, terminal, *libs, '-o', out / 'validation-probe.exe'])
    run(flags + [out / 'text-probe.c', *common, bridge, 'tests/text-terminal-fixture.c',
                 *libs, '-o', out / 'text-probe.exe'])
    run(flags + ['-Wall', '-Wextra', '-Werror', 'tests/sample-session-probe.c',
                 *libs, '-o', out / 'sample-session-probe.exe'])
    if (ROOT / 'tests/windows-terminal-test.c').is_file():
        run(flags + ['-Wall', '-Wextra', '-Werror', 'tests/windows-terminal-test.c',
                     '-luser32', '-o', out / 'windows-terminal-test.exe'])
    # A CGI executable is an obsolete delivery for this explicitly selected target.
    obsolete = ROOT / 'build/app/windows/student.cgi.exe'
    if obsolete.is_file():
        destination = ROOT / '.tmp/legacy-work/old-cgi/student.cgi.exe'
        ensure_directory(destination.parent)
        os.replace(guard(obsolete), guard(destination))
    if host_inputs != compiled_inputs():
        raise RuntimeError('Compilation inputs changed during probe build')
    succeeded = True
    write_json(evidence_file, {
        'succeeded': True, 'buildRecord': prefix.name + '.json',
        'compiledInputs': compiled_inputs(), 'binaries': binary_hashes(),
    })
finally:
    if not succeeded:
        write_json(ROOT / 'build/test-results/summary.json', {
            'runId': run_id, 'status': 'BUILD_FAILED', 'buildSucceeded': False,
            'applicationVerification': 'NOT_RUN', 'formalScore': None,
        })
    write_latest(prefix.with_suffix('.raw.log'), '\n'.join(logs))
    write_json(prefix.with_suffix('.json'), {
        'runId': run_id, 'succeeded': succeeded, 'compiledInputs': compiled_inputs(),
        'binaryHashes': binary_hashes(), 'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'inputManifest': 'build/input-manifest.json',
        'inputManifestSha256': hashlib.sha256((ROOT / 'build/input-manifest.json').read_bytes()).hexdigest(),
        'profile': 'Windows x64 native Console, authentication-free sample',
        'legacyHttpProbes': 'Preserved source; CGI/HTML is not the selected target and is not counted as Text acceptance.',
        'results': results, 'formalScore': None,
    })
