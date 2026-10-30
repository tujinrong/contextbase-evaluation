"""Audit current Web expectations against frozen specifications, never product source."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
OWNER = ROOT / 'sample-project2/srcs/CSharp_ASPNET'
SPEC = ROOT / 'sample-project2/spec/CSharp_ASPNET'
PREFIX = 'sample-project2/spec/CSharp_ASPNET/'
parser = argparse.ArgumentParser()
parser.add_argument('--expected-sha256', required=True)
args = parser.parse_args()
issues = []

def fail(code, detail):
    issues.append({'code': code, 'detail': detail})

def read(path):
    if path.is_symlink() or not path.is_file() or path.resolve() != path.absolute():
        raise ValueError('Nonregular/redirected file: ' + str(path))
    return path.read_bytes()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def expected_valid(value):
    if not isinstance(value, dict) or set(value) != {'op', 'value'}:
        return False
    op, item = value['op'], value['value']
    scalar = lambda v: isinstance(v, (str, bool, int, float)) and (not isinstance(v, float) or math.isfinite(v))
    number = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    return ((op == 'eq' and scalar(item)) or
            (op in ('min', 'max') and number(item)) or
            (op == 'range' and isinstance(item, list) and len(item) == 2 and all(number(n) for n in item) and item[0] <= item[1]) or
            (op == 'oneOf' and isinstance(item, list) and bool(item) and all(scalar(n) for n in item)))

contract_path = OWNER / 'tests/ui-contract.json'
contract_bytes = read(contract_path)
contract = json.loads(contract_bytes)
inputs_bytes = read(OWNER / 'build/generation/inputs.json')
inputs = json.loads(inputs_bytes)
if sha(contract_bytes) != args.expected_sha256.lower():
    fail('CONTRACT_SHA', 'Frozen notified contract differs')
if contract.get('schemaVersion') != 1 or contract.get('profileId') != 'CSharp_ASPNET':
    fail('CONTRACT_SCOPE', 'Expected schema1 and own profile')
if inputs.get('inspectionOnly') is not False or inputs.get('profileId') != contract['profileId'] or inputs.get('runId') != contract['runId']:
    fail('INPUT_SCOPE', 'Current normal own-profile preflight is required')
if contract.get('authorship', {}).get('frozenInputManifestSha256') != sha(inputs_bytes):
    fail('INPUT_SHA', 'Contract must bind current normal input manifest')
frozen = {v['file']: v for v in inputs['files']}
sources = {}
for source in contract['sources']:
    name = source['file']
    if name in sources or not name.startswith(PREFIX) or '..' in Path(name).parts:
        fail('SOURCE_SCOPE', name)
        continue
    raw = read(ROOT / name)
    meta = json.loads(re.search(r'<!--\s*spec-meta:\s*(\{.*?\})\s*-->', raw.decode('utf-8-sig'), re.S)[1])
    sources[name] = source
    if source.get('sha256') != sha(raw) or any(source.get(k) != meta.get(k) for k in ['documentId', 'version']) or any(source.get(k) != frozen.get(name, {}).get(k) for k in ['sha256', 'documentId', 'version']):
        fail('SOURCE_PROVENANCE', name)
expected_sources = {p.relative_to(ROOT).as_posix() for p in SPEC.rglob('*.md')}
if set(sources) != expected_sources:
    fail('SOURCE_COVERAGE', sorted(expected_sources.symmetric_difference(sources)))
components = {v['id']: v for v in contract['components']}
rules = {v['id']: v for v in contract['rules']}
if len(components) != len(contract['components']) or len(rules) != len(contract['rules']):
    fail('DUPLICATE_ID', 'Component or rule duplicate')
for item in list(components.values()) + list(rules.values()):
    if not re.fullmatch(r'[A-Za-z0-9_.:/-]+', item['id']):
        fail('IDENTIFIER', item['id'])
for item in components.values():
    if not item.get('selector') or not item.get('state') or not isinstance(item.get('textCapable'), bool):
        fail('COMPONENT_SHAPE', item['id'])
for rule in rules.values():
    if rule.get('target') not in components or rule.get('mandatory') is not True or not rule.get('sourceFiles') or any(v not in sources for v in rule['sourceFiles']):
        fail('RULE_REFERENCE', rule['id'])
    if not rule.get('properties') or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}', k) or not expected_valid(v) for k, v in rule['properties'].items()):
        fail('RULE_EXPECTATION', rule['id'])
    if rule.get('kind') == 'interaction' and (rule.get('requiresEvidence') is not True or not rule.get('procedure')):
        fail('INTERACTION_EVIDENCE', rule['id'])
if set(v['kind'] for v in rules.values()) != {'font', 'dimensions', 'render', 'appearance', 'interaction'}:
    fail('RULE_KINDS', 'All five measured kinds are required')

# Derive all interactive-screen item IDs and label-bearing inputs from own detailed tables.
expected_items, expected_labels = set(), set()
for path in sorted((SPEC / '詳細仕様書').glob('0*.md')):
    if path.name.startswith('05_'):
        continue  # Workbook output has its own report tests; no invented application screen.
    for line in read(path).decode('utf-8-sig').splitlines():
        if not re.match(r'\| F\d{2}-I\d+ ', line):
            continue
        row = [v.strip() for v in line.strip().strip('|').split('|')]
        expected_items.add(row[0])
        if re.match(r'(TextBox|Select|CheckBox)', row[3]):
            expected_labels.add(row[0] + '.label')
actual_items = {v for v in components if re.fullmatch(r'F\d{2}-I\d+', v)}
actual_labels = {v for v in components if re.fullmatch(r'F\d{2}-I\d+\.label', v)}
if expected_items != actual_items:
    fail('ITEM_COVERAGE', sorted(expected_items.symmetric_difference(actual_items)))
if expected_labels != actual_labels:
    fail('LABEL_COVERAGE', sorted(expected_labels.symmetric_difference(actual_labels)))
for target in ['F04.tab.basic', 'F04.tab.career', 'F04.panel.basic', 'F04.panel.career', 'F04.identity', 'F04.career.groups'] + [f'F0{n}.surface' for n in [1, 2, 3, 4, 6]]:
    if target not in components:
        fail('SURFACE_COVERAGE', target)
nontext = {v['id'] for v in components.values() if not v['textCapable']}
if nontext != {'F04-I12', 'F06-I06'}:
    fail('NONTEXT_SCOPE', sorted(nontext))
font_targets = {v['target'] for v in rules.values() if v['kind'] == 'font'}
if font_targets != set(components) - nontext:
    fail('FONT_COVERAGE', sorted(font_targets.symmetric_difference(set(components) - nontext)))
for rule in rules.values():
    if rule['kind'] != 'font':
        continue
    prop = rule['properties']
    ui_kinds = ['Label', 'Button', 'Buttons', 'Link', 'Links', 'TabButton', 'ColumnHeader', 'Breadcrumb', 'UserIdentity', 'Table', 'TableCells', 'List', 'ErrorSummary', 'FieldErrors', 'HelpText', 'SkipLink', 'Disclosure', 'ShellText']
    expected_size = 18 if rule['target'].endswith(('.groups', '.discard.title')) else 24 if components[rule['target']]['kind'] == 'Heading' else 14 if components[rule['target']]['kind'] in ui_kinds or rule['target'] == 'COMMON.getError.message' else 16
    if prop.get('fontSize') != {'op': 'eq', 'value': expected_size} or prop.get('fontUnit') != {'op': 'eq', 'value': 'px'}:
        fail('FONT_ROLE', rule['id'])
    if prop.get('fontFamily', {}).get('value') != ['"Yu Gothic UI", Meiryo, system-ui, sans-serif', 'Yu Gothic UI, Meiryo, system-ui, sans-serif']:
        fail('FONT_FAMILY', rule['id'])

# Individually adopted desktop border-box widths, not observed product rectangles.
widths = {'F03-I01': 110, 'F03-I02': 260, 'F03-I03': 180, 'F03-I04': 180, 'F04-I01': 110, 'F04-I02': 260, 'F04-I03': 330, 'F04-I06': 150, 'F06-I01': 180, 'F06-I03': 110, 'F06-I04': 340, 'F06-I05': 110}
for target, width in widths.items():
    if rules.get('WIDTH.' + target, {}).get('properties', {}).get('widthPx') != {'op': 'eq', 'value': width}:
        fail('ADOPTED_WIDTH', target)
required = ['DUI01.navigation', 'DUI04.row-edit', 'DUI05.ph05-untouched', 'DUI05.ph05-old-applied', 'DUI05.invalid-raw', 'DUI05.server-raw-diff', 'DUI05.new-save-return', 'DUI06.boundaries', 'DUI06.searched-return', 'DUI07.pending-save', 'DUI07.failure-preserve', 'DUI08.cancel', 'DUI08.code-scope', 'DUI09.keyboard', 'DUI09.search-order', 'DUI11.bfcache', 'DUI11.tabs', 'DUI11.state-expiry', 'DUI11.commit-navigation', 'DUI11.authentication', 'DUI12.export'] + ['DUI11.history.' + state for state in ['Success', 'Unsearched', 'Unapplied', 'Failed', 'LimitExceeded']]
for name in required:
    if rules.get(name, {}).get('kind') != 'interaction':
        fail('REQUIRED_SCENARIO', name)
transport = {'protectedPostContentType': 'application/json', 'navigationEnvelopeStatus': 200, 'navigationGetCount': 1, 'ticketConsumedExactlyOnce': True, 'unexpectedRedirectFollowed': False, 'failedSaveKeepsCurrentGetDocument': True, 'reloadSaveRequests': 0, 'malformedResponseKeepsRaw': True, 'automaticSaveRetries': 0}
if rules.get('DUI11.transport', {}).get('properties') != {k: {'op': 'eq', 'value': v} for k, v in transport.items()}:
    fail('TRANSPORT_EXPECTATIONS', 'DQA-UI05 requires all nine scalar expectations')
for screen in ['F01', 'F02', 'F03', 'F04', 'F06']:
    rule = rules.get('NARROW.' + screen, {})
    prop = rule.get('properties', {})
    case_value = '1366x768|1280x768|768x768|390x768|320x768|text200at1366'
    if prop.get('requiredCaseCoverage') != {'op': 'eq', 'value': case_value} or not rule.get('procedure'):
        fail('VIEWPORT_CASE_COVERAGE', screen)
    for name in ['overflowAt1366Px', 'overflowAt1280Px', 'overflowAt768Px', 'overflowAt390Px', 'overflowAt320Px', 'overflowAtText200Percent']:
        if prop.get(name) != {'op': 'eq', 'value': 0}:
            fail('VIEWPORT_INDIVIDUAL_EXPECTATION', screen + '.' + name)
    if prop.get('majorActionsReachable') != {'op': 'eq', 'value': True} or (screen != 'F01' and prop.get('navReachableAtEveryRequiredViewport') != {'op': 'eq', 'value': True}):
        fail('VIEWPORT_ACTIONS', screen)
supplemental = {screen + suffix for screen in ['F01', 'F02', 'F03', 'F04', 'F06'] for suffix in ['.help', '.skip']}
supplemental |= {screen + '.nav-toggle' for screen in ['F02', 'F03', 'F04', 'F06']}
supplemental |= {screen + suffix for screen in ['F04', 'F06'] for suffix in ['.reload', '.confirmationChoices']}
supplemental |= {'F03.exportCancel', 'F03.errors'}
supplemental |= {'COMMON.getError.' + suffix for suffix in ['surface', 'brand', 'heading', 'groups', 'message', 'body', 'actions', 'shellText']}
if len(supplemental) != 28 or not supplemental <= set(components) or not supplemental <= font_targets:
    fail('SUPPLEMENTAL_INVENTORY', sorted(supplemental - set(components)))
new_expectations = {
    'DUI09.busy-input': {'employeeInputsDisabledDuringWait': True, 'careerInputsDisabledDuringWait': True, 'codeInputsDisabledDuringWait': True, 'busyInputEditsAccepted': False, 'preRequestRawPreserved': True, 'previousDisabledAndReadonlyRestored': True, 'savedDbEqualsCapturedValues': True, 'newLinkAriaDisabledWhileBusy': True, 'rowEditLinksAriaDisabledWhileBusy': True},
    'DUI11.get-errors': {'ordinaryGetContentType': 'text/html', 'staffCodesStatus': 403, 'missingEmployeeStatus': 404, 'expiredTicketStatus': 410, 'consumedTicketStatus': 410, 'japaneseNoticeVisible': True, 'sharedShellVisible': True, 'nextActionOperable': True, 'rawJsonVisible': False, 'knownCommitNoticeIncludes14And41': True, 'unknownKeptDistinctFromKnownCommit': True},
}
for rule_id, props in new_expectations.items():
    if rules.get(rule_id, {}).get('kind') != 'interaction' or rules[rule_id]['properties'] != {k: {'op': 'eq', 'value': v} for k, v in props.items()}:
        fail('GET_BUSY_EXPECTATIONS', rule_id)
record = {'schemaVersion': 1, 'status': 'PASS_CONTRACT_STRUCTURE' if not issues else 'FAIL', 'profileId': 'CSharp_ASPNET', 'runId': contract['runId'], 'contractSha256': sha(contract_bytes), 'inputManifestSha256': sha(inputs_bytes), 'testSha256': sha(read(Path(__file__))), 'sources': len(sources), 'components': len(components), 'rules': len(rules), 'ruleKinds': dict(collections.Counter(v['kind'] for v in rules.values())), 'screenItemsDerived': len(expected_items), 'inputLabelsDerived': len(expected_labels), 'fontTargets': len(font_targets), 'individualWidths': len(widths), 'supplementalComponents': len(supplemental), 'requiredInteractionScenarios': len(required) + 1 + len(new_expectations), 'issues': issues, 'scope': 'Spec/expectation provenance, structure and selected independent scalar values only; no application source, final publish, DOM/style/geometry, HTTP/browser/native/DB/Office execution.', 'formalScore': None}
output = OWNER / 'build/test-results/independent-ui-contract-structure.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
raise SystemExit(bool(issues))
