"""Read project routing only; never infer methods or application names from a topic."""
from pathlib import Path
import json
import re


def regular_input(target: Path) -> None:
    target = target.absolute()
    if not target.is_file() or target.is_symlink() or str(target.resolve()).casefold() != str(target).casefold():
        raise RuntimeError(f'Regular input file required: {target}')


def is_test_artifact(value):
    """Recognize test directories/tokens and CamelCase test names, never substrings."""
    path = Path(value)
    if any(part.casefold() in {'test', 'tests', 'test-report', 'test-results', 'test-data', 'test-fixtures'} for part in path.parts[:-1]):
        return True
    tokens = re.split(r'[.\-_\s:]+', path.name)
    named_tests = {'test', 'tests', 'testing', 'testsuite', 'testoracle', 'testrunner', 'testharness', 'testfixture', 'testfixtures', 'testreport', 'testresults', 'conftest', 'pytest'}
    return any(token.casefold() in named_tests or re.match(r'^[Tt]est(?:s|ing)?(?=[A-Z0-9])', token) or re.search(r'(?<=[a-zA-Z0-9])Tests?$', token) for token in tokens)


def production_helpers(folder: Path):
    """Exact, selected-source-relative production files; never widen an excluded directory."""
    profile = folder / 'profile.json'
    if not profile.exists():
        return set()
    regular_input(profile)
    metadata = json.loads(profile.read_text('utf-8-sig'))
    entries = metadata.get('productionHelpers', [])
    if not isinstance(entries, list) or any(not isinstance(name, str) for name in entries):
        raise RuntimeError('productionHelpers must be an array of exact relative filenames')
    forbidden = {'.tmp', '.runtime', 'spec', 'spec-eval', 'spec-analysis', 'eval', 'tests', 'test', 'test-report', 'build', 'bin', 'obj', 'node_modules', 'dist', '.vs', '.git', '__pycache__'}
    result = set()
    folded = set()
    for name in entries:
        path = Path(name)
        if not name or '\\' in name or ':' in name or '*' in name or '?' in name or path.is_absolute() or path.as_posix() != name or any(part in {'.', '..'} or part.lower() in forbidden for part in path.parts):
            raise RuntimeError('Unsafe or excluded production helper path: ' + name)
        if name.casefold() in folded or is_test_artifact(name) or path.suffix.lower() in {'.accdb', '.accde', '.laccdb', '.exe', '.dll', '.pdb', '.pyc', '.pyo', '.o', '.so'}:
            raise RuntimeError('Duplicate, test or binary production helper refused: ' + name)
        regular_input(folder / path)
        folded.add(name.casefold())
        result.add(name)
    return result


def selected_profiles(root: Path, project: str, profile=None):
    if not re.fullmatch(r'(?:sample|test)-project[1-9]\d*', project):
        raise RuntimeError('Explicit safe project required')
    index = root / project / 'spec/README.md'
    regular_input(index)
    headers = None
    methods = []
    for line in index.read_text('utf-8-sig').splitlines():
        if not re.fullmatch(r'\s*\|.*\|\s*', line):
            headers = None
            continue
        row = [value.strip().strip('`') for value in line.strip()[1:-1].split('|')]
        if {'方式ID', 'specRoot', 'sourceRoot'}.issubset(row):
            headers = row
            continue
        if not headers or all(re.fullmatch(r':?-{3,}:?', value) for value in row):
            continue
        if len(row) != len(headers):
            raise RuntimeError('Invalid project routing row')
        method = row[headers.index('方式ID')]
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', method) or '..' in method or method.endswith('.') or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', method, re.I):
            raise RuntimeError('Invalid registered profile ID')
        if method in methods or row[headers.index('specRoot')] != f'{project}/spec/{method}/' or row[headers.index('sourceRoot')] != f'{project}/srcs/{method}/':
            raise RuntimeError('Invalid/duplicate registered profile scope')
        methods.append(method)
    if not methods or (profile is not None and profile not in methods):
        raise RuntimeError('Selected profile is not registered in the project specification index')
    return [profile] if profile else methods


def dotnet_entry(folder: Path):
    """Use an actual solution or unambiguous executable project, not a product name."""
    solutions = sorted([*folder.glob('*.slnx'), *folder.glob('*.sln')])
    if len(solutions) == 1:
        return solutions[0].relative_to(folder).as_posix()
    if len(solutions) > 1:
        raise RuntimeError('Multiple standalone solutions; select one unambiguous production entry point')
    ignored = {'.tmp', 'build', 'bin', 'obj', 'node_modules', 'tests', 'spec', 'spec-eval', 'spec-analysis', '.git'}
    projects = sorted(p for pattern in ('*.csproj', '*.vbproj') for p in folder.rglob(pattern) if not any(part.lower() in ignored for part in p.relative_to(folder).parts))
    executable = []
    for candidate in projects:
        regular_input(candidate)
        text = candidate.read_text('utf-8-sig')
        if 'Microsoft.NET.Sdk.Web' in text or re.search(r'<OutputType>\s*(?:Exe|WinExe)\s*</OutputType>|<Use(?:WPF|WindowsForms)>\s*true\s*</Use', text, re.I):
            executable.append(candidate)
    choices = executable or projects
    if len(choices) > 1:
        raise RuntimeError('Multiple .NET projects without one executable entry point')
    return choices[0].relative_to(folder).as_posix() if choices else None


def build_instruction(folder: Path):
    entry = dotnet_entry(folder)
    if entry:
        return f'dotnet build "{entry}" -c Release --nologo -p:RestoreLockedMode=true'
    for entry in ('Build-Access.ps1', 'build.py', 'Makefile', 'frontend/build.py', 'cl/BUILD.clle'):
        if (folder / entry).is_file():
            return f'Use the included {entry} and its local deployment instructions for this source tree.'
    for entry in sorted(production_helpers(folder)):
        if Path(entry).name.lower() == 'build.py':
            return f'Use the included {entry} and its local deployment instructions for this source tree.'
    return 'Use the included production entry points and local deployment instructions; no build command is inferred.'
