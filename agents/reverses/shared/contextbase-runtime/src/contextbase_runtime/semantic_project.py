"""Read a deliberately bounded SDK project subset, without running MSBuild.

The selected references are analysis metadata inputs, not a claim about a
previous restore or the deployed runtime. Unknown compile-affecting constructs
make the context incomplete. Nothing supplied by the project is executed.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile


_BASE_USINGS = ['System', 'System.Collections.Generic', 'System.IO', 'System.Linq',
                'System.Net.Http', 'System.Threading', 'System.Threading.Tasks']
_WEB_USINGS = ['System.Net.Http.Json', 'Microsoft.AspNetCore.Builder',
               'Microsoft.AspNetCore.Hosting', 'Microsoft.AspNetCore.Http',
               'Microsoft.AspNetCore.Routing', 'Microsoft.Extensions.Configuration',
               'Microsoft.Extensions.DependencyInjection', 'Microsoft.Extensions.Hosting',
               'Microsoft.Extensions.Logging']
_OUTPUT_ONLY = {'MethodProjectRelative', 'BaseIntermediateOutputPath',
                'MSBuildProjectExtensionsPath', 'BaseOutputPath', 'RestorePackagesPath',
                'RuntimeIdentifier', 'RuntimeIdentifiers', 'RestorePackagesWithLockFile',
                'TreatWarningsAsErrors', 'WarningsAsErrors', 'NoWarn', 'OutputPath',
                'GenerateDocumentationFile'}
_SUPPORTED = {'TargetFramework', 'Nullable', 'ImplicitUsings', 'LangVersion',
              'DefineConstants', 'EnableDefaultCompileItems', 'DefaultItemExcludes',
              'DefaultExcludesInProjectFolder', 'MethodRoot', 'AssemblyName', 'OutputType'}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _valid_package(package_id, version):
    return (re.fullmatch(r'[A-Za-z0-9_.-]+', package_id) is not None
            and re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?', version) is not None)


def _relative(base, value):
    if '\\' in value:
        value = value.replace('\\', '/')
    if re.match(r'^[A-Za-z]:|^/', value) or '$' in value:
        raise ValueError('Project path must be a literal inventory-relative path')
    parts = []
    for piece in (PurePosixPath(base) / value).parts:
        if piece == '..':
            if not parts:
                raise ValueError('Project path leaves the sealed inventory')
            parts.pop()
        elif piece != '.':
            parts.append(piece)
    return '/'.join(parts)


def _matches(path, pattern):
    """MSBuild's supported glob subset: *, ?, and recursive **/."""
    pattern = pattern.replace('\\', '/').removeprefix('./')
    tokens, i = [], 0
    while i < len(pattern):
        if pattern[i:i+3] == '**/':
            tokens.append('(?:.*/)?'); i += 3
        elif pattern[i:i+2] == '**':
            tokens.append('.*'); i += 2
        elif pattern[i] == '*':
            tokens.append('[^/]*'); i += 1
        elif pattern[i] == '?':
            tokens.append('[^/]'); i += 1
        else:
            tokens.append(re.escape(pattern[i])); i += 1
    return re.fullmatch(''.join(tokens), path, flags=re.IGNORECASE) is not None


def _covers_subtree(directory, pattern):
    """Prove coverage only for supported recursive whole-subtree patterns."""
    normalized = pattern.replace('\\', '/').removeprefix('./')
    if normalized in {'**', '**/*', '**/*.cs'}:
        return True
    suffix = next((s for s in ['/**/*.cs', '/**/*', '/**'] if normalized.endswith(s)), None)
    if suffix is None:
        return False
    prefix = normalized[:-len(suffix)]
    parts = directory.strip('/').split('/') if directory else []
    return any(_matches('/'.join(parts[:length]), prefix) for length in range(len(parts) + 1))


def _may_include_subtree(directory, pattern):
    normalized = pattern.replace('\\', '/').removeprefix('./')
    if not any(c in normalized for c in '*?'):
        return normalized.casefold().startswith(directory.casefold().rstrip('/') + '/')
    # Literal prefixes can prove disjointness. Otherwise retain uncertainty.
    literal = re.split(r'[*?]', normalized, maxsplit=1)[0]
    prefix = literal.rstrip('/') if literal.endswith('/') else str(PurePosixPath(literal).parent)
    if prefix == '.':
        prefix = ''
    prefix, directory = prefix.casefold(), directory.casefold().rstrip('/')
    return not prefix or prefix == directory or prefix.startswith(directory + '/') or directory.startswith(prefix + '/')


def _dotnet_root():
    executable = shutil.which('dotnet')
    if executable:
        return Path(executable).resolve().parent
    raise ValueError('Installed dotnet SDK reference packs are required')


def _version_key(value):
    return tuple(int(p) for p in re.findall(r'\d+', value))


def _framework_references(root, tfm, web):
    result, missing = [], []
    major = tfm[3:].split('.')[0]
    for pack in ['Microsoft.NETCore.App.Ref'] + (['Microsoft.AspNetCore.App.Ref'] if web else []):
        directory = root / 'packs' / pack
        versions = sorted((p for p in directory.glob('*') if p.is_dir() and p.name.startswith(major + '.')),
                          key=lambda p: _version_key(p.name), reverse=True)
        found = next((p / 'ref' / tfm for p in versions if (p / 'ref' / tfm).is_dir()), None)
        if found is None:
            missing.append('Missing reference pack ' + pack + '/' + tfm)
        else:
            assemblies = sorted(found.glob('*.dll'))
            if not assemblies:
                missing.append('Empty reference pack ' + pack + '/' + tfm)
            result.extend({'path': str(p.resolve()), 'sha256': _sha(p.read_bytes()),
                           'origin': 'sdk-reference-pack', 'pack': pack,
                           'version': found.parent.parent.name, 'tfm': tfm}
                          for p in assemblies)
    return result, missing


def _package_metadata(package_id, version, tfm, roots, lock, content_hashes):
    if not _valid_package(package_id, version):
        return [], 'Unsupported package identity/version: ' + package_id
    compatible = ['net' + str(n) + '.0' for n in range(int(tfm[3:].split('.')[0]), 7, -1)] + ['netstandard2.1', 'netstandard2.0']
    for root in roots:
        package = root / package_id.lower() / version.lower()
        archive = package / (package_id.lower() + '.' + version.lower() + '.nupkg')
        if not archive.is_file():
            continue
        archive_data = archive.read_bytes()
        expected = lock.get('contentHash')
        signed_hash = content_hashes.get(str(archive.resolve()))
        if signed_hash and signed_hash[1] != _sha(archive_data):
            return [], 'Package archive changed during metadata access: ' + package_id
        stable_hash = signed_hash[0] if signed_hash else base64.b64encode(hashlib.sha512(archive_data).digest()).decode()
        if expected and stable_hash != expected:
            return [], 'Package archive hash differs from source lock: ' + package_id
        try:
            with zipfile.ZipFile(io.BytesIO(archive_data)) as z:
                names = set(z.namelist())
                for folder in ['ref', 'lib']:
                    for selected in compatible:
                        prefix = folder + '/' + selected + '/'
                        # NuGet's explicit-empty compile group is a selected
                        # asset group, not permission to fall back to lib/.
                        if prefix + '_._' in names:
                            return [], None if expected else 'Package lacks source-lock hash: ' + package_id
                        dlls = sorted(n for n in names if n.startswith(prefix) and n.endswith('.dll') and '/' not in n[len(prefix):])
                        if not dlls:
                            continue
                        result = []
                        for name in dlls:
                            local = package / name
                            local_data = local.read_bytes() if local.is_file() else None
                            if local_data is None or local_data != z.read(name):
                                return [], 'Package metadata differs from archive: ' + package_id
                            result.append({'path': str(local.resolve()), 'sha256': _sha(local_data),
                                           'origin': 'local-package-analysis-metadata', 'packageId': package_id,
                                           'version': version, 'tfm': selected, 'archiveSha256': _sha(archive_data),
                                           'lockVerified': bool(expected)})
                        return result, None if expected else 'Package lacks source-lock hash: ' + package_id
                # Runtime-only/native packages intentionally contribute no compiler metadata.
                if not any(n.endswith('.dll') and n.startswith(('ref/', 'lib/')) for n in names):
                    return [], None if expected else 'Package lacks source-lock hash: ' + package_id
        except (OSError, zipfile.BadZipFile) as exc:
            return [], 'Unreadable package metadata: ' + package_id + ': ' + str(exc)
        return [], 'No supported package reference TFM: ' + package_id
    return [], 'Missing local package metadata: ' + package_id + '/' + version


def build_project_context(texts, *, project, dotnet_root=None, package_roots=None,
                          configuration='Release', omitted=None):
    """Create a hash-bound, explicit compilation request from sealed text only."""
    root = Path(dotnet_root) if dotnet_root is not None else _dotnet_root()
    if configuration not in {'Release', 'Debug'}:
        raise ValueError('Analysis configuration must be explicitly Release or Debug')
    roots = [Path(p) for p in package_roots] if package_roots is not None else [Path.home() / '.nuget/packages']
    omitted = list(omitted or [])
    config, reference_binding, package_binding, projects, visiting = {}, {}, {}, {}, set()

    def read_xml(path):
        if path not in texts:
            raise ValueError('Project configuration is outside sealed inventory: ' + path)
        config[path] = {'path': path, 'sha256': _sha(texts[path].encode('utf-8'))}
        return ET.fromstring(texts[path])

    def load(path):
        if path in projects:
            return projects[path]
        if path in visiting:
            raise ValueError('Cyclic ProjectReference: ' + path)
        visiting.add(path)
        directory = str(PurePosixPath(path).parent)
        if directory == '.':
            directory = ''
        xml = read_xml(path)
        sdk = xml.get('Sdk', '')
        diagnostics = []
        complete = True

        def issue(message):
            nonlocal complete
            complete = False
            diagnostics.append({'code': 'incomplete-project-context', 'message': message, 'path': path})

        properties = {'TargetFramework': '', 'ImplicitUsings': 'disable', 'Nullable': 'disable',
                      'EnableDefaultCompileItems': 'true', 'DefaultItemExcludes': '',
                      'DefaultExcludesInProjectFolder': '', 'DefineConstants': ''}
        compile_items, refs, packages = [], [], []
        # Nearest Directory.Build.props only: no parent outside the sealed boundary.
        parents = [directory] if directory else ['']
        while parents[-1]:
            parent = str(PurePosixPath(parents[-1]).parent)
            parents.append('' if parent == '.' else parent)
        props = next((p + '/Directory.Build.props' if p else 'Directory.Build.props'
                      for p in parents if (p + '/Directory.Build.props' if p else 'Directory.Build.props') in texts), None)
        documents = [(props, read_xml(props))] if props else []
        documents.append((path, xml))
        for ancestor in parents:
            for filename in ['Directory.Build.targets', 'Directory.Packages.props', 'global.json']:
                extra = ancestor + '/' + filename if ancestor else filename
                if extra in texts:
                    config[extra] = {'path': extra, 'sha256': _sha(texts[extra].encode('utf-8'))}
                    issue('Unsupported compilation configuration: ' + extra)

        def expand(value, document):
            local = str(PurePosixPath(document).parent)
            prefix = '' if local == '.' else local + '/'
            known = {**properties, 'MSBuildThisFileDirectory': prefix, 'MSBuildProjectName': PurePosixPath(path).stem}
            return re.sub(r'\$\(([^)]+)\)', lambda m: known.get(m.group(1), m.group(0)), value)

        for document, tree in documents:
            if set(tree.attrib) - ({'Sdk'} if document == path else set()):
                issue('Unsupported project-root attributes: ' + document)
            for group in tree:
                tag = group.tag.rsplit('}', 1)[-1]
                if tag not in {'PropertyGroup', 'ItemGroup'}:
                    issue('Unsupported project construct: ' + tag); continue
                for item in group:
                    name = item.tag.rsplit('}', 1)[-1]
                    if tag == 'PropertyGroup':
                        if name in _OUTPUT_ONLY:
                            diagnostics.append({'code': 'output-only-property', 'message': 'Not evaluated: ' + name, 'path': document})
                            continue
                        if name not in _SUPPORTED or group.get('Condition') or item.get('Condition'):
                            issue('Unsupported compile-affecting property/condition: ' + name); continue
                        value = expand(item.text or '', document)
                        if '$' in value:
                            issue('Unevaluated compile-affecting property: ' + name)
                        properties[name] = value
                    else:
                        if name in {'Content', 'None'}:
                            continue
                        if group.get('Condition') or item.get('Condition'):
                            issue('Unsupported item condition: ' + name); continue
                        if name == 'Compile':
                            if list(item) or item.get('Update') or item.get('Exclude'):
                                issue('Unsupported Compile metadata/Update/Exclude'); continue
                            for key in ['Remove', 'Include']:
                                for value in item.get(key, '').split(';'):
                                    if value:
                                        expanded = expand(value, document)
                                        if ('$' in expanded or re.match(r'^[A-Za-z]:|^/', expanded)
                                                or '..' in PurePosixPath(expanded.replace('\\', '/')).parts):
                                            issue('Unsupported Compile pattern outside the project-local subset')
                                        compile_items.append((key, expanded.replace('\\', '/')))
                        elif name == 'ProjectReference' and set(item.attrib) == {'Include'} and not list(item):
                            refs.append(_relative(directory, item.get('Include')))
                        elif name == 'PackageReference' and set(item.attrib) <= {'Include', 'Version'} and not list(item):
                            packages.append((item.get('Include', ''), item.get('Version', '')))
                        else:
                            issue('Unsupported compiler item: ' + name)
        if sdk not in {'Microsoft.NET.Sdk', 'Microsoft.NET.Sdk.Web'}:
            issue('Unsupported SDK: ' + sdk)
        output_type = properties.get('OutputType', 'Exe' if sdk.endswith('.Web') else 'Library').lower()
        if output_type not in {'exe', 'winexe', 'library'}:
            issue('Unsupported OutputType: ' + output_type)
        tfm = properties['TargetFramework']
        if tfm not in {'net8.0', 'net9.0', 'net10.0'}:
            issue('Unsupported TargetFramework: ' + tfm)
            tfm = 'net10.0'
        default_excludes = ['**/bin/**', '**/obj/**', '**/.tmp/**', '**/.vs/**', '**/node_modules/**']
        for key in ['DefaultItemExcludes', 'DefaultExcludesInProjectFolder']:
            default_excludes.extend(p for p in properties[key].split(';') if p)
        files = []
        prefix = directory + '/' if directory else ''
        if properties['EnableDefaultCompileItems'].lower() not in {'true', 'false'}:
            issue('Unsupported EnableDefaultCompileItems value')
        for operation, pattern in compile_items:
            if operation == 'Include' and not any(c in pattern for c in '*?'):
                try:
                    included = _relative(directory, pattern)
                except ValueError:
                    issue('Explicit Compile Include leaves the sealed inventory: ' + pattern)
                else:
                    if included not in texts:
                        issue('Explicit Compile Include is absent from sealed inventory: ' + included)

        def selected_file(candidate):
            local = candidate[len(prefix):]
            excluded = any(_matches(local, p) or _matches(candidate, p) for p in default_excludes)
            selected = properties['EnableDefaultCompileItems'].lower() == 'true' and not excluded
            for operation, pattern in compile_items:
                if _matches(local, pattern):
                    if operation == 'Include' and selected:
                        issue('Duplicate Compile Include: ' + candidate)
                    selected = operation == 'Include'
            return selected

        for entry in omitted:
            candidate = entry.get('path', '').replace('\\', '/').rstrip('/')
            try:
                if _relative('', candidate) != candidate:
                    raise ValueError('Noncanonical omission')
            except ValueError:
                issue('Invalid omitted inventory path: ' + candidate)
                continue
            if not candidate.startswith(prefix):
                continue
            reason = entry.get('reason', '')
            is_cs_file = candidate.lower().endswith('.cs') and reason != 'excluded-directory'
            # Scope-pruning records do not state whether the path was a file or
            # directory. A suffix alone cannot prove that it was a file.
            potential_directory = reason not in {'unsupported-text-material', 'unsupported-encoding-or-binary'}
            if is_cs_file and selected_file(candidate):
                issue('Possible compiler input omitted from sealed inventory: ' + candidate)
            if potential_directory:
                local = candidate[len(prefix):]
                excluded = any(_covers_subtree(local, p) or _covers_subtree(candidate, p) for p in default_excludes)
                selected = properties['EnableDefaultCompileItems'].lower() == 'true' and not excluded
                for operation, pattern in compile_items:
                    if operation == 'Remove' and _covers_subtree(local, pattern):
                        selected = False
                    elif operation == 'Include' and _may_include_subtree(local, pattern):
                        selected = True
                if selected:
                    issue('Possible C# subtree omitted without proven project exclusion: ' + candidate)
        for candidate, text in sorted(texts.items()):
            if not candidate.startswith(prefix) or not candidate.lower().endswith('.cs'):
                continue
            if selected_file(candidate):
                files.append({'path': candidate, 'text': text})
        metadata, missing = _framework_references(root, tfm, sdk.endswith('.Web'))
        for message in missing:
            issue(message)
        # A source lock is inherited only from the nearest ancestor, never another project.
        lock_path = next((p + '/packages.lock.json' if p else 'packages.lock.json'
                          for p in parents if (p + '/packages.lock.json' if p else 'packages.lock.json') in texts), None)
        locked = {}
        if lock_path:
            config[lock_path] = {'path': lock_path, 'sha256': _sha(texts[lock_path].encode('utf-8'))}
            locked = json.loads(texts[lock_path]).get('dependencies', {}).get(tfm, {})
        pending, package_requests = list(packages), []
        seen = set()
        while pending:
            package_id, version = pending.pop(0)
            identity = package_id.lower()
            if identity in seen:
                continue
            seen.add(identity)
            lock = next((v for k, v in locked.items() if k.lower() == identity), {})
            if lock and lock.get('resolved') != version:
                issue('Declared package differs from source lock: ' + package_id)
                continue
            package_requests.append((package_id, version, lock))
            for dependency in lock.get('dependencies', {}):
                dependency_lock = next((v for k, v in locked.items() if k.lower() == dependency.lower()), {})
                if dependency_lock.get('resolved'):
                    pending.append((dependency, dependency_lock['resolved']))
                else:
                    issue('Missing transitive package lock: ' + dependency)
        archives = []
        for package_id, version, lock in package_requests:
            if not _valid_package(package_id, version):
                continue
            for package_root in roots:
                archive = package_root / package_id.lower() / version.lower() / (package_id.lower() + '.' + version.lower() + '.nupkg')
                if archive.is_file():
                    # Signed NuGet package contentHash is signature-independent.
                    # Use the installed SDK's reader, never execute package code.
                    if zipfile.is_zipfile(archive):
                        with zipfile.ZipFile(archive) as z:
                            if '.signature.p7s' in z.namelist():
                                archives.append(str(archive.resolve()))
                    break
        content_hashes = {}
        if archives:
            from .dotnet_host import package_content_hashes
            raw_hashes = {p: _sha(Path(p).read_bytes()) for p in sorted(set(archives))}
            try:
                content_hashes = {p: (value, raw_hashes[p]) for p, value in package_content_hashes(sorted(raw_hashes)).items()}
            except (OSError, ValueError, RuntimeError) as exc:
                issue('Could not verify package content hash: ' + str(exc))
        for package_id, version, lock in package_requests:
            additions, problem = _package_metadata(package_id, version, tfm, roots, lock, content_hashes)
            metadata.extend(additions)
            if problem:
                issue(problem)
            record = {'packageId': package_id, 'version': version,
                      'compileReferenceCount': len(additions),
                      'declaredContentHash': lock.get('contentHash'),
                      'lockVerified': not problem and bool(lock.get('contentHash')),
                      'origin': 'explicit-local-analysis-cache', 'archive': None}
            for package_root in roots if _valid_package(package_id, version) else []:
                archive = package_root / package_id.lower() / version.lower() / (package_id.lower() + '.' + version.lower() + '.nupkg')
                if archive.is_file():
                    record['archive'] = {'path': str(archive.resolve()), 'sha256': _sha(archive.read_bytes())}
                    break
            package_binding[package_id.lower() + '/' + version] = record
        # Framework metadata wins for platform assemblies; preserve every selected input in binding.
        unique = {}
        reference_hashes = {}
        for ref in metadata:
            reference_binding[ref['path']] = ref
            filename = Path(ref['path']).name.lower()
            if filename in reference_hashes and reference_hashes[filename] != ref['sha256']:
                issue('Conflicting compiler metadata filenames: ' + filename)
            reference_hashes[filename] = ref['sha256']
            unique.setdefault(filename, ref['path'])
        language = properties.get('LangVersion', str(int(tfm[3:].split('.')[0]) + 4))
        if language not in {'12', '12.0', '13', '13.0', '14', '14.0'}:
            issue('Unsupported language version: ' + language)
            language = str(int(tfm[3:].split('.')[0]) + 4)
        if properties['Nullable'] not in {'enable', 'disable', 'warnings', 'annotations'}:
            issue('Unsupported Nullable value: ' + properties['Nullable'])
        if properties['ImplicitUsings'].lower() not in {'true', 'false', 'enable', 'disable'}:
            issue('Unsupported ImplicitUsings value: ' + properties['ImplicitUsings'])
        implicit = properties['ImplicitUsings'].lower() in {'true', 'enable'}
        defines = ['TRACE'] + (['DEBUG'] if configuration == 'Debug' else [])
        defines.extend(x.strip() for x in properties['DefineConstants'].split(';') if x.strip())
        major = int(tfm[3:].split('.')[0])
        defines.extend(['NET', 'NETCOREAPP', 'NET' + str(major) + '_0'] + ['NET' + str(n) + '_0_OR_GREATER' for n in range(5, major + 1)])
        defines.extend('NETCOREAPP' + version + '_OR_GREATER' for version in ['1_0', '1_1', '2_0', '2_1', '2_2', '3_0', '3_1'])
        result = {'id': path, 'assemblyName': properties.get('AssemblyName', PurePosixPath(path).stem),
                  'outputKind': 'console' if output_type == 'exe' else 'winexe' if output_type == 'winexe' else 'library',
                  'analysisConfiguration': configuration,
                  'files': files, 'references': sorted(unique.values()),
                  'projectReferences': refs, 'languageVersion': language,
                  'defines': sorted(set(defines)), 'nullable': properties['Nullable'],
                  'globalUsings': (_BASE_USINGS + (_WEB_USINGS if sdk.endswith('.Web') else [])) if implicit else [],
                  'configurationComplete': complete, 'diagnostics': diagnostics}
        for dependency in refs:
            upstream = load(dependency)
            for reference in upstream['references']:
                filename = Path(reference).name.lower()
                if filename in unique and unique[filename] != reference and _sha(Path(unique[filename]).read_bytes()) != _sha(Path(reference).read_bytes()):
                    issue('Conflicting referenced-project metadata filenames: ' + filename)
                unique.setdefault(filename, reference)
            if not upstream['configurationComplete']:
                issue('Referenced project context incomplete: ' + dependency)
        result['references'] = sorted(unique.values())
        result['configurationComplete'] = complete
        projects[path] = result
        visiting.remove(path)
        return result

    normalized_project = _relative('', project)
    load(normalized_project)
    return {'rootProject': normalized_project, 'projects': list(projects.values()),
            'binding': {'schema': 'contextbase-csharp-project-context/1',
                        'analysisConfiguration': configuration,
                        'omitted': sorted(omitted, key=lambda x: x.get('path', '')),
                        'config': sorted(config.values(), key=lambda x: x['path']),
                        'references': sorted(reference_binding.values(), key=lambda x: x['path']),
                        'packages': sorted(package_binding.values(), key=lambda x: (x['packageId'], x['version'])),
                        'boundary': 'sealed inventory only; no MSBuild, restore, analyzers or generators',
                        'limitations': ['Static supported SDK project subset, not full MSBuild evaluation.',
                                        'Project configuration above the sealed inventory boundary is not observed or evaluated.',
                                        'No generated Razor or source-generator trees are inferred.',
                                        'Package hash verification confirms locked content, not signer trust.',
                                        'Selected package metadata is an explicit analysis input, not proof of deployed assemblies.']}}
