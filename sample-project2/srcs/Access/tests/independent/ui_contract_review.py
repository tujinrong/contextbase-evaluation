"""Review frozen Access expectations from specifications only; never open an ACCDB."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
OWNER = ROOT / 'sample-project2/srcs/Access'
SPEC = ROOT / 'sample-project2/spec/Access'
PREFIX = 'sample-project2/spec/Access/'
UI = SPEC / '共通/方式別/02_UI部品・状態・検査契約.md'
FORMS = {'F01': 'frmLogin', 'F02': 'frmMenu', 'F03': 'frmEmployeeSearch', 'F04': 'frmEmployeeEditor', 'F06': 'frmCodeMaster'}
parser = argparse.ArgumentParser()
parser.add_argument('--expected-sha256', required=True)
args = parser.parse_args()
issues = []

def fail(code, detail):
    issues.append({'code': code, 'detail': detail})

def data(path):
    if path.is_symlink() or not path.is_file() or path.resolve() != path.absolute():
        raise ValueError('Nonregular/redirected file: ' + str(path))
    return path.read_bytes()

def sha(value):
    return hashlib.sha256(value).hexdigest()

def metadata(value):
    return json.loads(re.search(r'<!-- spec-meta: (.*?) -->', value.decode('utf-8-sig')).group(1))

def expectation_valid(value):
    if not isinstance(value, dict) or 'value' not in value:
        return False
    op, item = value.get('op'), value['value']
    scalar = isinstance(item, (str, bool, int, float)) and item is not None
    number = lambda n: isinstance(n, (int, float)) and not isinstance(n, bool) and float('-inf') < n < float('inf')
    if op == 'eq':
        return scalar and (not isinstance(item, (int, float)) or isinstance(item, bool) or number(item))
    if op in ['min', 'max']:
        return number(item)
    if op == 'range':
        return isinstance(item, list) and len(item) == 2 and all(number(n) for n in item) and item[0] <= item[1]
    if op == 'oneOf':
        return isinstance(item, list) and bool(item) and all(isinstance(n, (str, bool, int, float)) and n is not None for n in item)
    return False

contract_path = OWNER / 'tests/ui-contract.json'
contract_bytes = data(contract_path)
contract_sha = sha(contract_bytes)
contract = json.loads(contract_bytes.decode('utf-8-sig'))
if contract_sha != args.expected_sha256.lower():
    fail('CONTRACT_SHA', 'Contract differs from the builder-notified frozen SHA')
if contract.get('schemaVersion') != 1:
    fail('SCHEMA_VERSION', 'Existing schema1 is required')
inputs_path = OWNER / 'build/generation/inputs.json'
input_bytes = data(inputs_path)
inputs = json.loads(input_bytes.decode('utf-8-sig'))
if inputs.get('inspectionOnly') is not False or inputs.get('profileId') != 'Access' or inputs.get('runId') != contract.get('runId'):
    fail('INPUT_SCOPE', 'Current normal preflight of this profile/run is required')
if contract.get('adoption', {}).get('frozenInputManifestSha256') != sha(input_bytes):
    fail('INPUT_SHA', 'Contract input manifest SHA differs')
frozen = {item['file']: item for item in inputs['files']}
sources = {}
for item in contract.get('sources', []):
    name = item['file']
    if name in sources or not name.startswith(PREFIX) or '..' in Path(name).parts:
        fail('SOURCE_SCOPE', name)
        continue
    sources[name] = item
    raw = data(ROOT / name)
    meta = metadata(raw)
    if item.get('sha256') != sha(raw) or any(item.get(k) != meta.get(k) for k in ['documentId', 'version']) or any(item.get(k) != frozen.get(name, {}).get(k) for k in ['sha256', 'documentId', 'version']):
        fail('SOURCE_PROVENANCE', name)
components = contract.get('components', [])
rules = contract.get('rules', [])
component_by_id = {item['id']: item for item in components}
rule_by_id = {item['id']: item for item in rules}
if len(component_by_id) != len(components) or len(rule_by_id) != len(rules):
    fail('DUPLICATE_ID', 'Components/rules contain duplicate IDs')

# Derive all application control names independently from frozen specification tables.
expected_controls = set()
for path in sorted((SPEC / '詳細仕様書').glob('0*.md')):
    function = 'F' + path.name[:2]
    if function not in FORMS:
        continue
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not re.match(r'\| F\d{2}-I\d+ ', line):
            continue
        row = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if not re.fullmatch(r'(?:txt|cbo|cmd|lst|lbl|tab|chk)[A-Z][A-Za-z0-9_]*', row[11]):
            fail('SPEC_CONTROL', str(path) + ' ' + row[0])
        expected_controls.add(FORMS[function] + '.' + row[11])
if len(expected_controls) != 73:
    fail('SPEC_PRIMARY_COUNT', str(len(expected_controls)))
expected_controls.add('frmEmployeeSearch.txtSelectedDetails')
ui_text = UI.read_text(encoding='utf-8-sig')
attached = set()
for line in ui_text.splitlines():
    match = re.match(r'^\| (frm[A-Za-z]+)/[^|]+\|([^|]+)\|', line)
    if match:
        for name in re.findall(r'\b(?:txt|cbo|chk)[A-Z][A-Za-z0-9_]*', match[2]):
            attached.add(match[1] + '.lbl_' + name)
expected_controls |= attached
heads_line = next(line for line in ui_text.splitlines() if line.startswith('一覧見出しは'))
headings = set()
for function, names in re.findall(r'F(03|04|06) `([^`]+)`', heads_line):
    headings |= {FORMS['F' + function] + '.' + name for name in names.split('/')}
expected_controls |= headings
supplement_line = next(line for line in ui_text.splitlines() if line.startswith('追加の独立Labelは'))
match = re.search(r'F01の(.*?)、F02の(.*?)、F04の(.*?)を用いる', supplement_line)
supplements = set()
for function, names in zip(['F01', 'F02', 'F04'], match.groups()):
    supplements |= {FORMS[function] + '.' + name for name in re.findall(r'\blbl[A-Z][A-Za-z0-9_]*', names)}
expected_controls |= supplements
primary_control_count = len(expected_controls)
# DQA-UI10 auxiliary inventory comes from its explicit specification table,
# not the form definitions or a generated ACCDB. Normal fields remain73.
pending_controls = {}
for line in ui_text.splitlines():
    if not re.match(r'^\| AUX-F(?:03|04|06)-', line):
        continue
    row = [cell.strip() for cell in line.strip().strip('|').split('|')]
    if len(row) != 5 or not re.fullmatch(r'frm[A-Za-z]+\.(?:txtPending_cbo[A-Za-z]+|lbl_txtPending_cbo[A-Za-z]+)', row[1]):
        fail('PENDING_SPEC_ROW', line)
        continue
    coordinates = row[3].split('/')
    if len(coordinates) != 4 or not all(n.isdigit() for n in coordinates):
        fail('PENDING_SPEC_GEOMETRY', row[0])
        continue
    page = re.search(r'論理Page([01])', row[2])
    pending_controls[row[1]] = {'auxiliaryId': row[0], 'section': 'Header' if 'FormHeader' in row[2] else 'Detail',
                               'logicalPage': int(page[1]) if page else None,
                               'rectangle': tuple(map(int, coordinates)), 'kind': 'Label' if 'Label' in row[2] else 'TextBox'}
pending_inputs = {name for name, value in pending_controls.items() if value['kind'] == 'TextBox'}
pending_labels = set(pending_controls) - pending_inputs
expected_controls |= set(pending_controls)
if (len(attached), len(headings), len(supplements), primary_control_count, len(pending_inputs), len(pending_labels), len(expected_controls)) != (32, 13, 8, 127, 6, 6, 139):
    fail('SPEC_AUXILIARY_COUNT', str((len(attached), len(headings), len(supplements), primary_control_count, len(pending_inputs), len(pending_labels), len(expected_controls))))
for name, item in pending_controls.items():
    component = component_by_id.get(name, {})
    if component.get('kind') != item['kind'] or component.get('auxiliaryId') != item['auxiliaryId'] or component.get('physicalParent') != name.split('.')[0] + '.' + item['section'] or component.get('logicalPage') != item['logicalPage']:
        fail('PENDING_COMPONENT_MAPPING', name)
expected_surfaces = set(re.findall(r'^\| (SC-F[A-Z0-9-]+|DLG-F[A-Z0-9-]+) \|', ui_text, re.M))
expected_sections = {form + '.' + section for form in FORMS.values() for section in ['Header', 'Detail', 'Footer']}
expected_components = expected_controls | expected_surfaces | expected_sections
if len(expected_surfaces) != 16 or len(expected_components) != 170:
    fail('SPEC_SURFACE_COUNT', str((len(expected_surfaces), len(expected_components))))
if expected_components != set(component_by_id):
    fail('COMPONENT_COVERAGE', {'missing': sorted(expected_components - set(component_by_id)), 'unexpected': sorted(set(component_by_id) - expected_components)})

# Coordinates are independently parsed from the specification, never from generated source.
spec_geometry = {}
for line in ui_text.splitlines():
    row = re.match(r'^\| (F0[1-6][^|]*)\|([^|]+)\|', line)
    if not row or row[1][:3] not in FORMS:
        continue
    form = FORMS[row[1][:3]]
    for match in re.finditer(r'((?:txt|cbo|cmd|lst|lbl|tab|chk)[A-Z][A-Za-z0-9_]*)\((\d+),(\d+),(\d+),(\d+)\)', row[2]):
        section = 'Footer' if 'Footer' in row[2][:match.start()] else 'Detail'
        spec_geometry[form + '.' + match[1]] = (section, tuple(int(match[n]) for n in range(2, 6)))
for label in attached:
    form, native_label = label.split('.', 1)
    native_input = native_label[len('lbl_'):]
    own = spec_geometry.get(form + '.' + native_input)
    if not own:
        continue
    section, (left, top, width, height) = own
    if form == 'frmLogin':
        rectangle = (6345, top, 1200, 330)
    elif native_input == 'chkEnabled':
        rectangle = (left + 420, top, 8000, 330)
    else:
        rectangle = (left, top - 330, 2580 if native_input == 'txtEndMonth' else width, 330)
    spec_geometry[label] = (section, rectangle)
spec_geometry['frmCodeMaster.lbl_cboCategory'] = ('Header', (360, 1740, 480, 480))
spec_geometry.update({name: (item['section'], item['rectangle']) for name, item in pending_controls.items()})
for target, (section, rectangle) in spec_geometry.items():
    rule = rule_by_id.get('GEOMETRY-' + target)
    props = rule.get('properties', {}) if rule else {}
    if props.get('section') != {'op': 'eq', 'value': section} or props.get('unit') != {'op': 'eq', 'value': 'twip'}:
        fail('SPEC_GEOMETRY_SECTION', target)
    for property_name, expected_value in zip(['designLeft', 'designTop', 'designWidth', 'designHeight'], rectangle):
        expected = props.get(property_name, {})
        exact = property_name == 'designWidth' and target in {'frmEmployeeEditor.txtEmployeeName', 'frmEmployeeEditor.txtEmployeeKana', 'frmEmployeeEditor.txtJoinDate'}
        valid = expected == {'op': 'eq', 'value': expected_value}
        if not exact and expected.get('op') == 'range':
            value = expected.get('value')
            valid = isinstance(value, list) and len(value) == 2 and expected_value - 30 <= value[0] <= expected_value <= value[1] <= expected_value + 30
        if not valid:
            fail('SPEC_GEOMETRY_VALUE', target + '/' + property_name)

# The UI10 caption table is a separate source-level check, including the
# navigation-label exception: F06 uses 分類 without a required marker.
pending_captions = {}
for line in ui_text.splitlines():
    match = re.match(r'^\| (F(?:03|04|06))(?: Page[01])? (cbo[A-Za-z]+) \| [0-9/]+ \| [0-9/]+・([^|]+) \|$', line)
    if match:
        pending_captions[(FORMS[match[1]], match[2])] = match[3].strip().split('（')[0]
if len(pending_captions) != 6 or pending_captions.get(('frmCodeMaster', 'cboCategory')) != '分類':
    fail('PENDING_CAPTION_SOURCE', str(pending_captions))
for target, item in pending_controls.items():
    form, native_name = target.split('.', 1)
    owner_name = re.search(r'cbo[A-Za-z]+', native_name)[0]
    props = rule_by_id.get('STYLE-' + target, {}).get('properties', {})
    if props.get('visible') != {'op': 'eq', 'value': False}:
        fail('PENDING_INITIAL_VISIBILITY', target)
    if item['kind'] == 'Label':
        if props.get('caption') != {'op': 'eq', 'value': pending_captions[(form, owner_name)]}:
            fail('PENDING_LABEL_CAPTION', target)
    else:
        values = {'controlSourceEmpty': True, 'inputMaskEmpty': True, 'formatEmpty': True, 'enterKeyBehavior': False,
                  'scrollBars': 0, 'enabled': False, 'locked': True, 'tabStop': False,
                  'attachedLabelCount': 1, 'attachedLabelName': 'lbl_' + native_name}
        for key, expected_value in values.items():
            if props.get(key) != {'op': 'eq', 'value': expected_value}:
                fail('PENDING_SAVED_ATTRIBUTE', target + '/' + key)
for item in rules:
    if item['id'].startswith('PENDING-F03-'):
        forbidden = {'noRetainsAllRawPendingAndTarget', 'yesDiscardsOnlyConfirmedScope', 'declineRestoresVisibleRawAndFocus', 'declineStillAllowsEditing'}
        if any(any(key.endswith('_' + suffix) for suffix in forbidden) for key in item.get('properties', {})):
            fail('F03_CONFIRMATION_INVENTED', item['id'])

font_targets = {item['target'] for item in rules if item.get('kind') == 'font'}
amendment_expectations = [
    ('SECTION-03-Detail', 'designHeightTwip', 7500),
    ('SECTION-04-Header', 'designHeightTwip', 2400),
    ('SECTION-04-Detail', 'designHeightTwip', 7920),
    ('SC-F03-NAVIGATION', 'cancelRestoresTopVisibleEmployeeId', True),
    ('F05-PRINT-PH07', 'bodyFontPoint', 10.5),
    ('F05-PRINT-PH07', 'headingFontPoint', 11),
    ('F05-PRINT-PH07', 'titleFontPoint', 18),
    ('F05-PRINT-PH07', 'footerNominalFontPoint', 11),
    ('F05-PRINT-PH07', 'footerNumericLeadingNameLiteral', True),
    ('F05-PRINT-PH07', 'footerFullName40ScalarsOnFirstLine', True),
]
for rule_id, property_name, value in amendment_expectations:
    if rule_by_id.get(rule_id, {}).get('properties', {}).get(property_name) != {'op': 'eq', 'value': value}:
        fail('DQA_UI08_UI09_EXPECTATION', rule_id + '/' + property_name)
expected_font_targets = (expected_controls - {'frmCodeMaster.chkEnabled'}) | {'SC-F04-BASIC', 'SC-F04-CAREER'}
if font_targets != expected_font_targets:
    fail('FONT_COVERAGE', {'missing': sorted(expected_font_targets - font_targets), 'unexpected': sorted(font_targets - expected_font_targets)})
for item in rules:
    target = item.get('target')
    if not isinstance(item.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', item['id']):
        fail('RULE_ID', str(item.get('id')))
    if item.get('mandatory') is not True or target not in component_by_id or not item.get('sourceFiles') or any(name not in sources for name in item['sourceFiles']):
        fail('RULE_SCOPE', item['id'])
    if not item.get('properties'):
        fail('EMPTY_EXPECTATIONS', item['id'])
    for key, value in item.get('properties', {}).items():
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}', key) or not expectation_valid(value):
            fail('EXPECTED_INVALID', item['id'] + '/' + key)
    if item.get('kind') == 'font':
        for key, expected in [('fontFamily', 'Yu Gothic UI'), ('fontSize', 11), ('fontUnit', 'pt')]:
            if item['properties'].get(key) != {'op': 'eq', 'value': expected}:
                fail('FONT_VALUE', item['id'] + '/' + key)
    if item.get('kind') == 'interaction' and any('oneOf' == value.get('op') for key, value in item.get('properties', {}).items() if 'state' in key.lower() or 'path' in key.lower()):
        fail('STATE_WEAKENING', item['id'])
if set(item.get('kind') for item in rules) != {'font', 'dimensions', 'appearance', 'render', 'interaction'}:
    fail('RULE_KINDS', 'All five existing kinds required')
for component in components:
    if not isinstance(component.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', component['id']) or not isinstance(component.get('kind'), str) or not component['kind'] or type(component.get('textCapable')) is not bool:
        fail('COMPONENT_SHAPE', str(component.get('id')))
    own_rules = [rule for rule in rules if rule.get('target') == component['id']]
    if not own_rules or (component.get('textCapable') and component['id'] not in font_targets):
        fail('COMPONENT_UNCOVERED', component['id'])
    if component['id'] in expected_controls and component.get('textCapable') is False and not component.get('fontScopeReason'):
        fail('FONT_EXCLUSION_REASON', component['id'])

category_kinds = {'identity': {'render'}, 'layout': {'dimensions'}, 'content': {'render'}, 'selection': {'interaction'}, 'saveCancel': {'interaction'}, 'navigation': {'interaction'}, 'keyboard': {'interaction'}, 'states': {'render'}, 'viewport': {'dimensions', 'render'}}
screens = contract.get('accessScreenChecks', [])
if {item['target'] for item in screens} != expected_surfaces or len(screens) != 16:
    fail('SCREEN_COVERAGE', 'All16 real surfaces require independent screen checks')
used_categories = {}
for screen in screens:
    if screen.get('screenType') not in {'AUTH', 'HOME', 'SEARCH_LIST', 'DETAIL', 'EDIT_FORM', 'MASTER_DETAIL', 'WIZARD', 'DASHBOARD_REPORT', 'SETTINGS', 'DIALOG', 'CUSTOM'} or (screen.get('screenType') == 'CUSTOM' and not screen.get('purpose', '').strip()):
        fail('SCREEN_TYPE', screen['target'])
    if set(screen.get('checks', {})) != set(category_kinds):
        fail('CATEGORY_KEYS', screen['target'])
    for category, required in category_kinds.items():
        check = screen.get('checks', {}).get(category, {})
        must_apply = category not in ['selection', 'saveCancel'] or (category == 'selection' and screen.get('screenType') in ['SEARCH_LIST', 'MASTER_DETAIL']) or (category == 'saveCancel' and screen.get('screenType') in ['EDIT_FORM', 'MASTER_DETAIL', 'WIZARD', 'SETTINGS'])
        ids = check.get('ruleIds', [])
        if check.get('applicable') is False:
            if must_apply or not check.get('reason', '').strip() or ids:
                fail('CATEGORY_EXCLUSION', screen['target'] + '/' + category)
            continue
        if check.get('applicable') is not True or not ids or len(ids) != len(set(ids)):
            fail('CATEGORY_SHAPE', screen['target'] + '/' + category)
        present = set()
        for rule_id in ids:
            rule = rule_by_id.get(rule_id)
            if not rule or rule.get('mandatory') is not True:
                fail('CATEGORY_RULE', rule_id)
                continue
            present.add(rule['kind'])
            if rule_id in used_categories and used_categories[rule_id] != category:
                fail('CROSS_CATEGORY_REUSE', rule_id)
            used_categories[rule_id] = category
        if not required <= present:
            fail('CATEGORY_KIND', screen['target'] + '/' + category)
if data(contract_path) != contract_bytes:
    fail('CONTRACT_CHANGED', 'Contract changed during inspection')
result = {'schemaVersion': 1, 'projectId': 'sample-project2', 'profileId': 'Access', 'runId': contract.get('runId'), 'checkpoint': '1-expectation-contract-structure', 'status': 'PASS_CONTRACT_STRUCTURE' if not issues else 'FAIL_CONTRACT_STRUCTURE', 'scope': 'Frozen specifications and UI contract only. No application/ACCDB/DB/UI execution and no runtime acceptance.', 'contract': {'file': 'tests/ui-contract.json', 'sha256': contract_sha, 'version': contract.get('version')}, 'inputs': {'file': 'build/generation/inputs.json', 'sha256': sha(input_bytes), 'files': len(frozen)}, 'sources': len(sources), 'components': len(components), 'specDerivedApplicationControls': len(expected_controls), 'specDerivedGeometryTargets': len(spec_geometry), 'sections': len(expected_sections), 'surfaces': len(screens), 'fontTargets': len(font_targets), 'rulesByKind': dict(collections.Counter(item['kind'] for item in rules)), 'findings': issues, 'testSource': {'file': 'tests/independent/ui_contract_review.py', 'sha256': sha(data(Path(__file__).resolve()))}, 'formalScore': None}
out = OWNER / 'build/test-results/independent-ui-contract-structure.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: result[key] for key in ['status', 'sources', 'components', 'specDerivedApplicationControls', 'sections', 'surfaces', 'fontTargets', 'rulesByKind', 'findings']}, ensure_ascii=False))
raise SystemExit(1 if issues else 0)
