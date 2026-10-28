"""Method-local npm dependencies and frontend build, including source-only ZIP use."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys

sys.dont_write_bytecode = True
F = Path(os.path.abspath(__file__)).parent
B = F.parent
sys.path.insert(0, str(B))
from build_paths import OutputPaths

parser = argparse.ArgumentParser()
parser.add_argument('command', nargs='?', choices=['build', 'typecheck', 'install', 'browser', 'dev', 'publish'], default='build')
parser.add_argument('--no-audit', action='store_true', help='Disable NuGet audit for this invocation only')
args = parser.parse_args()
paths = OutputPaths(B)
paths.preflight()
link, dependencies = paths.frontend_link()
W = paths.mkdir(B / '.tmp/frontend')
if args.command == 'publish':
    report = paths.mkdir(B / 'build/test-results')
    paths.write(report / 'results.json', json.dumps(dict(status='VERIFICATION_REQUIRED', reason='Standalone frontend publish does not run contract tests', recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat()), indent=2) + '\n')
    paths.write(report / 'README.md', '# Latest local build and path regression\n\nVERIFICATION_REQUIRED: standalone publish does not execute the contract or UI checks.\n')

npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
if not npm:
    raise SystemExit('npm is required')
env = os.environ.copy()
runtime = paths.mkdir(B / '.tmp/runtime')
env.update(TMP=str(runtime), TEMP=str(runtime), DOTNET_CLI_HOME=str(paths.output(B / '.tmp/dotnet-home')), NUGET_HTTP_CACHE_PATH=str(paths.output(B / '.tmp/nuget/http-cache')))
env['npm_config_cache'] = str(paths.output(W / 'npm-cache'))
env['PLAYWRIGHT_BROWSERS_PATH'] = str(paths.output(W / 'playwright'))
if not os.path.lexists(link):
    paths.mkdir(dependencies)
    paths.frontend_link()
    if os.name == 'nt':
        script = W / 'link.ps1'
        paths.write(script, 'param([string]$Link,[string]$Target)\n$ErrorActionPreference="Stop"\nNew-Item -ItemType Junction -Path $Link -Target $Target | Out-Null\n')
        subprocess.run(['powershell', '-NoProfile', '-File', str(script), str(link), str(dependencies)], check=True)
    else:
        link.symlink_to(dependencies, target_is_directory=True)
paths.frontend_link()
signature = hashlib.sha256(b''.join(paths.regular(F / name).read_bytes() for name in ['package.json', 'package-lock.json'])).hexdigest()
marker = paths.output(W / 'installed.sha256')
if args.command == 'install' or not dependencies.exists() or not marker.exists() or marker.read_text('ascii') != signature:
    for name in ['package.json', 'package-lock.json']:
        paths.copyfile(F / name, W / name)
    paths.preflight()
    paths.frontend_link()
    subprocess.run([npm, 'ci', '--prefix', str(W)], cwd=F, env=env, check=True)
    paths.output(dependencies, tree=True)
    paths.write(marker, signature, 'ascii')
if args.command == 'install':
    raise SystemExit(0)
paths.preflight()
paths.frontend_link()
command = ['node', 'tests/browser.mjs'] if args.command == 'browser' else [npm, 'run', 'build' if args.command == 'publish' else args.command]
subprocess.run(command, cwd=F, env=env, check=True)
if args.command == 'publish':
    stage = paths.output(B / '.tmp/frontend/publish')
    paths.remove(stage)
    paths.preflight()
    subprocess.run(['dotnet', 'publish', str(B / 'backend/StudentManagement.Api.csproj'), '-c', 'Release', '-o', str(stage), '-p:RestoreLockedMode=true', *(['-p:NuGetAudit=false'] if args.no_audit else [])], cwd=B, env=env, check=True)
    paths.replace_tree(W / 'dist', stage / 'wwwroot')
    paths.replace_tree(stage, B / 'build/publish')
    print('Published build/publish; verification is required.')
