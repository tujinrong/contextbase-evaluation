"""Assemble existing saved-property measurements into an explicitly incomplete record.

No Office, DB, product generation, expected-value comparison or native input runs.
The CLI writes only the fixed owned .tmp partial; final UI publication is separate.
"""
from pathlib import Path, PurePosixPath
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import stat
import tempfile

OWNER = Path(__file__).resolve().parents[2]
REPO = OWNER.parents[2]
PARTIAL = '.tmp/build-agent/ui-regeneration/ui-observations.partial.json'
RECORD = 'build/test-results/independent-design-attributes.json'
GETTER = 'tests/independent/design_attributes.py'
ASSEMBLER = 'tests/independent/assemble_ui_observations.py'
VALIDATOR = 'agents/builds/build-agent/scripts/ui-conformance.mjs'
CONTROL_TYPES = {
    100: ('Label', True), 104: ('CommandButton', True), 106: ('CheckBox', False),
    109: ('TextBox', True), 110: ('ListBox', True), 111: ('ComboBox', True),
    123: ('TabControl', True),
}
SAVED_KINDS = {'font', 'dimensions', 'appearance'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def owned_path(root, relative, must_exist=True):
    """Reject escapes, alternate Windows path spellings, and every redirected ancestor."""
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('A POSIX relative path is required')
    rel = PurePosixPath(relative)
    if rel.is_absolute() or any(p in ('', '.', '..') for p in relative.split('/')):
        raise ValueError('Unsafe relative path')
    root = Path(root).absolute()
    path = root.joinpath(*rel.parts)
    if not path.is_relative_to(root):
        raise ValueError('Path outside owner')
    for part in [root, *root.parents, *[root.joinpath(*rel.parts[:n]) for n in range(1, len(rel.parts) + 1)]]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            if must_exist:
                raise
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Redirected path refused: ' + str(part))
    return path


def valid_hash(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value):
        raise ValueError('Explicit lowercase SHA-256 required')
    return value


def scalar(value):
    return value is None or isinstance(value, (str, bool, int)) or isinstance(value, float) and math.isfinite(value)


def assemble(owner, repo, bindings):
    """Pure file reads; contract use is limited to IDs, targets, kinds and property names."""
    owner, repo = Path(owner).absolute(), Path(repo).absolute()
    anchors = {}

    def read(root, relative, expected=None):
        path = owned_path(root, relative)
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError('Regular file required: ' + relative)
        data = path.read_bytes()
        digest = sha(data)
        if expected is not None and digest != valid_hash(expected):
            raise ValueError('SHA mismatch: ' + relative)
        if path in anchors and anchors[path] != digest:
            raise ValueError('File changed between reads: ' + relative)
        anchors[path] = digest
        return data, digest

    def load(root, relative, expected=None):
        data, digest = read(root, relative, expected)
        return json.loads(data.decode('utf-8-sig')), digest

    contract, contract_sha = load(owner, 'tests/ui-contract.json', bindings['contract'])
    inputs, input_sha = load(owner, 'build/generation/inputs.json', bindings['inputs'])
    _, artifact_sha = read(owner, 'build/CareerManagement.accdb', bindings['artifact'])
    _, validator_sha = read(repo, VALIDATOR, bindings['validator'])
    actual, actual_sha = load(owner, RECORD)
    for label in ('projectId', 'profileId', 'runId'):
        if actual.get(label) != contract.get(label) or inputs.get(label) != contract.get(label):
            raise ValueError('Record identity mismatch: ' + label)
    for field, expected in [('artifactSha256', artifact_sha), ('contractSha256', contract_sha), ('inputManifestSha256', input_sha)]:
        if actual.get(field) != expected:
            raise ValueError('Measurement binding mismatch: ' + field)
    _, getter_sha = read(owner, GETTER, actual['testSha256'])
    _, assembler_sha = read(owner, ASSEMBLER)
    frozen = {}
    for item in inputs['files']:
        if item['file'] in frozen:
            raise ValueError('Duplicate frozen input')
        read(repo, item['file'], item['sha256'])
        frozen[item['file']] = item['sha256']
    for item in contract['sources']:
        if frozen.get(item['file']) != item['sha256']:
            raise ValueError('Contract source absent from frozen inputs or SHA differs')
    source_comparisons = []
    for entry in actual['compiledSourceComparison']:
        read(repo, entry['sourceFile'], entry['sourceSha256'])
        source_comparisons.append({'file': entry['sourceFile'], 'sha256': entry['sourceSha256'], 'canonicalTokensEqual': entry.get('canonicalTokensEqual')})

    # Do not import comparison results/expected literals from the contract or source record.
    descriptors = {}
    for rule in contract['rules']:
        rid = rule['id']
        if rid in descriptors:
            raise ValueError('Duplicate contract rule: ' + rid)
        descriptors[rid] = {'target': rule['target'], 'kind': rule['kind'], 'properties': set(rule['properties'])}
    expected_component_ids = {item['id'] for item in contract['components']}
    findings, observations, rejected, missing_properties, seen = [], [], [], [], set()
    for measured in actual['rules']:
        rid = measured['id']
        if rid in seen:
            raise ValueError('Duplicate measured rule: ' + rid)
        seen.add(rid)
        descriptor = descriptors.get(rid)
        if descriptor is None or measured['target'] != descriptor['target'] or measured['kind'] != descriptor['kind'] or measured['kind'] not in SAVED_KINDS:
            rejected.append(measured)
            findings.append({'code': 'UNKNOWN_OR_MISMATCHED_MEASUREMENT', 'ruleId': rid})
            continue
        properties = {}
        for name, value in measured['observed'].items():
            if name not in descriptor['properties'] or not scalar(value):
                findings.append({'code': 'UNKNOWN_PROPERTY_OR_NONSCALAR', 'ruleId': rid, 'property': name})
                rejected.append({'id': rid, 'property': name, 'observed': value})
                continue
            properties[name] = value  # Measured actual only. No value/op access to expected entries.
        absent = sorted(descriptor['properties'] - properties.keys())
        if absent:
            missing_properties.append({'ruleId': rid, 'properties': absent, 'reason': 'Absent from saved-property measurement'})
        if measured.get('failures') or measured.get('status') != 'PASS_DESIGN_ATTRIBUTE':
            findings.append({'code': 'SOURCE_MEASUREMENT_NOT_PASSED', 'ruleId': rid, 'sourceStatus': measured.get('status'), 'sourceRecord': RECORD})
        observations.append({'ruleId': rid, 'target': measured['target'], 'method': 'native-property', 'properties': properties,
                             'evidence': [{'file': RECORD, 'sha256': actual_sha}]})
    observed_ids = {item['ruleId'] for item in observations}
    not_measured = [{'ruleId': rid, 'target': desc['target'], 'kind': desc['kind'], 'properties': sorted(desc['properties']),
                     'reason': 'No saved-property measurement; runtime/visual/input/OS surface evidence remains separate'}
                    for rid, desc in descriptors.items() if rid not in observed_ids]
    components, component_ids = [], set()
    for entry in actual['inventory']:
        cid = entry['id']
        if cid in component_ids:
            raise ValueError('Duplicate native component: ' + cid)
        component_ids.add(cid)
        if 'controlType' in entry:
            classification = CONTROL_TYPES.get(entry['controlType'])
        else:
            classification = {'Form': ('Form', False), 'Section': ('Section', False), 'Page': ('Page', True)}.get(entry.get('kind'))
        if classification is None or cid not in expected_component_ids:
            findings.append({'code': 'UNKNOWN_NATIVE_COMPONENT', 'componentId': cid, 'nativeRecord': entry})
            continue
        kind, text_capable = classification
        components.append({'id': cid, 'kind': kind, 'textCapable': text_capable,
                           'evidence': [{'file': RECORD, 'sha256': actual_sha}], 'nativeProof': entry})
    source_issues = actual.get('issues', [])
    if source_issues or actual.get('notMeasuredProperties') or actual.get('status') != 'PASS_NON_UI_CHECKPOINT2':
        findings.append({'code': 'SOURCE_RECORD_INCOMPLETE_OR_FAILED', 'sourceStatus': actual.get('status'), 'issueCount': len(source_issues), 'sourceRecord': RECORD})
    for path, expected in anchors.items():
        if sha(owned_path(repo, path.relative_to(repo).as_posix()).read_bytes()) != expected:
            raise ValueError('File changed during assembly: ' + str(path))
    result = {'schemaVersion': 1, 'projectId': contract['projectId'], 'profileId': contract['profileId'], 'runId': contract['runId'],
              'status': 'PARTIAL_SAVED_PROPERTIES_ONLY' if not findings else 'PARTIAL_WITH_SOURCE_FINDINGS',
              'recordedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(), 'contractSha256': contract_sha,
              'frozenInputManifestSha256': input_sha, 'validatorSha256': validator_sha,
              'artifact': {'file': 'build/CareerManagement.accdb', 'sha256': artifact_sha}, 'environment': None,
              'components': components, 'observations': observations,
              'measurementSources': [{'file': GETTER, 'sha256': getter_sha}, {'file': ASSEMBLER, 'sha256': assembler_sha}],
              'sourceRecords': [{'file': RECORD, 'sha256': actual_sha}],
              'sourceCodeComparisons': source_comparisons, 'assemblyFindings': findings, 'rejectedMeasurements': rejected,
              'notMeasuredRules': not_measured, 'notMeasuredProperties': missing_properties,
              'notMeasuredComponentIds': sorted(expected_component_ids - {item['id'] for item in components}),
              'notMeasuredEnvironment': ['platform', 'renderer', 'dpi', 'scale', 'viewport'],
              'validatorBindingScope': 'Current assembly-time validator SHA checked at start/end. Original saved-property record did not record a measurement-time validator SHA; no retrospective claim.',
              'scope': 'Existing actual saved attributes only. No runtime/visual/native input evidence; not final UI observations. Never copies expected value/op into actual.',
              'anchors': [{'file': path.relative_to(repo).as_posix(), 'sha256': digest} for path, digest in sorted(anchors.items())],
              'formalScore': None, 'overallUiPass': False}
    return result


def write_partial(owner, value):
    target = owned_path(owner, PARTIAL, must_exist=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    owned_path(owner, PARTIAL, must_exist=False)
    if target.exists() and not target.is_file():
        raise ValueError('Non-file partial target')
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, prefix='assemble-', suffix='.tmp', delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        staged = Path(stream.name)
    os.replace(staged, target)
    return target


def main():
    parser = argparse.ArgumentParser()
    for name in ('artifact', 'contract', 'inputs', 'validator'):
        parser.add_argument('--' + name + '-sha256', required=True)
    args = parser.parse_args()
    bindings = {name: valid_hash(getattr(args, name + '_sha256')) for name in ('artifact', 'contract', 'inputs', 'validator')}
    empty = {'schemaVersion': 1, 'projectId': 'sample-project2', 'profileId': 'Access', 'status': 'RUNNING_PARTIAL_ASSEMBLY', 'components': [], 'observations': [], 'formalScore': None}
    write_partial(OWNER, empty)
    try:
        result = assemble(OWNER, REPO, bindings)
        target = write_partial(OWNER, result)
        print(json.dumps({'status': result['status'], 'observations': len(result['observations']), 'components': len(result['components']), 'notMeasuredRules': len(result['notMeasuredRules']), 'findings': len(result['assemblyFindings']), 'output': str(target), 'sha256': sha(target.read_bytes())}))
        return int(bool(result['assemblyFindings']))
    except Exception as error:
        empty.update(status='FAILED_PARTIAL_ASSEMBLY', errorType=type(error).__name__, detail=str(error))
        write_partial(OWNER, empty)
        raise


if __name__ == '__main__':
    raise SystemExit(main())
