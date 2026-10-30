"""Pure isolated assembly regressions; fixture success is not product UI evidence."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile

sys.dont_write_bytecode = True
SOURCE = Path(__file__).with_name('assemble_ui_observations.py')
spec = importlib.util.spec_from_file_location('partial_assembly', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OWNER = Path(__file__).resolve().parents[2]


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    parent = OWNER / '.tmp/build-agent/ui-regeneration/assembly-fixtures'
    parent.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=parent, prefix='owned-') as temp:
        repo = Path(temp)
        owner = repo / 'sample-project2/srcs/Access'
        files = {}

        def put(relative, data):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            files[relative] = data
            return module.sha(data)

        def own(relative, data):
            return put('sample-project2/srcs/Access/' + relative, data)

        getter_hash = own(module.GETTER, b'getter actual code\n')
        own(module.ASSEMBLER, SOURCE.read_bytes())
        validator_hash = put(module.VALIDATOR, b'current validator\n')
        artifact_hash = own('build/CareerManagement.accdb', b'fixture artifact bytes\n')
        authority_file = 'sample-project2/spec/Access/detail.md'
        authority_sha = put(authority_file, b'fixture source specification\n')
        vba_file = 'sample-project2/srcs/Access/src/classes/One.cls'
        vba_sha = put(vba_file, b'Option Explicit\n')
        contract = {'projectId': 'sample-project2', 'profileId': 'Access', 'runId': 'fixture',
                    'sources': [{'file': authority_file, 'sha256': authority_sha}],
                    'components': [{'id': 'SC-F01', 'kind': 'Form', 'textCapable': False}, {'id': 'unseen', 'kind': 'Dialog', 'textCapable': False}],
                    'rules': [{'id': 'R1', 'target': 'SC-F01', 'kind': 'dimensions', 'properties': {'actualWidth': {'value': 999999, 'op': 'eq'}, 'actualFlag': {'value': True, 'op': 'eq'}}},
                              {'id': 'R2', 'target': 'unseen', 'kind': 'render', 'properties': {'unseenProperty': {'value': True, 'op': 'eq'}}}]}
        inputs = {'projectId': 'sample-project2', 'profileId': 'Access', 'runId': 'fixture', 'files': [{'file': authority_file, 'sha256': authority_sha}]}
        contract_sha = own('tests/ui-contract.json', encoded(contract))
        input_sha = own('build/generation/inputs.json', encoded(inputs))
        actual = {'projectId': 'sample-project2', 'profileId': 'Access', 'runId': 'fixture', 'artifactSha256': artifact_hash, 'contractSha256': contract_sha,
                  'inputManifestSha256': input_sha, 'testSha256': getter_hash, 'status': 'PASS_NON_UI_CHECKPOINT2', 'issues': [], 'notMeasuredProperties': [],
                  'compiledSourceComparison': [{'sourceFile': vba_file, 'sourceSha256': vba_sha, 'canonicalTokensEqual': True}],
                  'rules': [{'id': 'R1', 'target': 'SC-F01', 'kind': 'dimensions', 'status': 'PASS_DESIGN_ATTRIBUTE', 'observed': {'actualWidth': 18900, 'actualFlag': False}, 'failures': []}],
                  'inventory': [{'id': 'SC-F01', 'kind': 'Form', 'nativeName': 'frmLogin'}]}
        own(module.RECORD, encoded(actual))
        baseline = dict(files)
        bindings = {'artifact': artifact_hash, 'contract': contract_sha, 'inputs': input_sha, 'validator': validator_hash}

        def reset():
            for name, data in baseline.items():
                (repo / name).write_bytes(data)

        def measured(value):
            own(module.RECORD, encoded(value))

        def check(name, condition):
            if not condition:
                raise AssertionError(name)
            results.append({'id': name, 'status': 'PASS'})

        def rejects(name, action):
            reset()
            action()
            try:
                module.assemble(owner, repo, bindings)
            except (ValueError, FileNotFoundError):
                check(name, True)
            else:
                check(name, False)

        value = module.assemble(owner, repo, bindings)
        check('actual-differs-from-poisoned-expectation', value['observations'][0]['properties']['actualWidth'] == 18900)
        check('false-not-replaced-by-expected-true', value['observations'][0]['properties']['actualFlag'] is False)
        check('unmeasured-rule-remains-missing', [x['ruleId'] for x in value['notMeasuredRules']] == ['R2'])
        check('missing-component-not-copied-from-contract', value['notMeasuredComponentIds'] == ['unseen'])
        check('environment-not-inferred', value['environment'] is None and len(value['notMeasuredEnvironment']) == 5)
        check('record-is-evidence-not-measurement-source', all(x['file'] != module.RECORD for x in value['measurementSources']))
        altered_contract = copy.deepcopy(contract)
        altered_contract['components'][0].update(kind='Label', textCapable=True)
        altered_sha = own('tests/ui-contract.json', encoded(altered_contract))
        altered_actual = copy.deepcopy(actual)
        altered_actual['contractSha256'] = altered_sha
        measured(altered_actual)
        native_value = module.assemble(owner, repo, {**bindings, 'contract': altered_sha})
        check('native-kind-does-not-use-contract-kind', native_value['components'][0]['kind'] == 'Form'
              and native_value['components'][0]['textCapable'] is False)
        reset()
        check('validator-assembly-time-scope-explicit', 'did not record a measurement-time validator' in value['validatorBindingScope'])
        for field, relative in [('artifact', 'sample-project2/srcs/Access/build/CareerManagement.accdb'), ('contract', 'sample-project2/srcs/Access/tests/ui-contract.json'),
                                ('inputs', 'sample-project2/srcs/Access/build/generation/inputs.json'), ('validator', module.VALIDATOR),
                                ('getter', 'sample-project2/srcs/Access/' + module.GETTER), ('frozen-spec', authority_file), ('compiled-source', vba_file)]:
            rejects('reject-drift-' + field, lambda p=relative: (repo / p).write_bytes(b'drift'))
        for field in ('artifactSha256', 'contractSha256', 'inputManifestSha256', 'runId'):
            changed = copy.deepcopy(actual)
            changed[field] = 'different'
            rejects('reject-record-binding-' + field, lambda v=changed: measured(v))
        reset()
        changed = copy.deepcopy(actual)
        del changed['rules'][0]['observed']['actualFlag']
        measured(changed)
        value = module.assemble(owner, repo, bindings)
        check('missing-property-not-filled', 'actualFlag' not in value['observations'][0]['properties'] and value['notMeasuredProperties'][0]['properties'] == ['actualFlag'])
        reset()
        changed = copy.deepcopy(actual)
        changed['rules'][0]['observed']['undeclared'] = 27
        measured(changed)
        value = module.assemble(owner, repo, bindings)
        check('unknown-property-retained-as-rejected', 'undeclared' not in value['observations'][0]['properties'] and value['assemblyFindings'][0]['code'] == 'UNKNOWN_PROPERTY_OR_NONSCALAR')
        reset()
        changed = copy.deepcopy(actual)
        changed['rules'][0]['id'] = 'UNKNOWN_RULE'
        measured(changed)
        value = module.assemble(owner, repo, bindings)
        check('unknown-rule-retained-as-rejected', value['observations'] == [] and value['rejectedMeasurements'][0]['id'] == 'UNKNOWN_RULE')
        reset()
        changed = copy.deepcopy(actual)
        changed['rules'][0]['observed']['actualWidth'] = {'unmeasured': True}
        measured(changed)
        value = module.assemble(owner, repo, bindings)
        check('nonscalar-actual-not-converted-to-pass', 'actualWidth' not in value['observations'][0]['properties']
              and value['rejectedMeasurements'][0]['observed'] == {'unmeasured': True})
        reset()
        changed = copy.deepcopy(actual)
        changed['rules'][0]['target'] = 'unseen'
        measured(changed)
        value = module.assemble(owner, repo, bindings)
        check('target-mismatch-not-promoted', value['observations'] == [] and len(value['notMeasuredRules']) == 2 and bool(value['rejectedMeasurements']))
        reset()
        changed = copy.deepcopy(actual)
        changed['rules'][0]['status'] = 'FAIL'
        changed['rules'][0]['failures'] = [{'property': 'actualWidth'}]
        measured(changed)
        value = module.assemble(owner, repo, bindings)
        check('measured-failure-keeps-actual-and-finding', value['observations'][0]['properties']['actualWidth'] == 18900 and value['status'] == 'PARTIAL_WITH_SOURCE_FINDINGS')
        changed = copy.deepcopy(actual)
        changed['rules'].append(copy.deepcopy(changed['rules'][0]))
        rejects('reject-duplicate-measurement', lambda: measured(changed))
        for relative in ('../escape', '/absolute', 'C:/escape', 'a\\b', 'a/./b'):
            try:
                module.owned_path(owner, relative, must_exist=False)
            except ValueError:
                check('reject-unsafe-path-' + relative, True)
            else:
                check('reject-unsafe-path-' + relative, False)
        reset()
        formal = owner / 'build/test-results/ui-observations.json'
        formal.write_bytes(b'preserve formal sentinel')
        path = module.write_partial(owner, module.assemble(owner, repo, bindings))
        check('write-only-owned-tmp-partial', path.is_relative_to(owner / '.tmp') and formal.read_bytes() == b'preserve formal sentinel')
        old_owner, old_repo, old_argv = module.OWNER, module.REPO, sys.argv
        module.OWNER, module.REPO = owner, repo
        sys.argv = [str(SOURCE), '--artifact-sha256', '0' * 64, '--contract-sha256', contract_sha,
                    '--inputs-sha256', input_sha, '--validator-sha256', validator_hash]
        failed = False
        try:
            module.main()  # Real CLI RUNNING/except FAILED writer, with fixture-owned files.
        except ValueError:
            failed = True
        finally:
            module.OWNER, module.REPO, sys.argv = old_owner, old_repo, old_argv
        after_failure = json.loads(path.read_text('utf-8'))
        check('failed-run-removes-previous-partial-values', failed and after_failure['status'] == 'FAILED_PARTIAL_ASSEMBLY'
              and after_failure['observations'] == [] and after_failure['components'] == [])
        link = repo / 'redirect'
        try:
            link.symlink_to(repo / 'sample-project2', target_is_directory=True)
        except OSError as error:
            results.append({'id': 'redirected-ancestor', 'status': 'NOT_EXECUTED', 'reason': type(error).__name__})
        else:
            try:
                module.owned_path(repo, 'redirect/spec/Access/detail.md')
            except ValueError:
                check('redirected-ancestor', True)
            else:
                check('redirected-ancestor', False)
    print(json.dumps({'status': 'PASS_PURE_FIXTURES', 'passed': sum(x['status'] == 'PASS' for x in results), 'notExecuted': sum(x['status'] == 'NOT_EXECUTED' for x in results),
                      'scope': 'File/assembly fixture only; no Office, product execution or UI PASS', 'sourceSha256': module.sha(SOURCE.read_bytes()), 'cases': results}, ensure_ascii=False))


if __name__ == '__main__':
    main()
