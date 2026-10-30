"""Read DesignView properties on an owned copy; no Form runtime or native input."""
import argparse
import datetime
import decimal
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import site
import sys

sys.dont_write_bytecode = True
OWNER = Path(__file__).resolve().parents[2]
ROOT = OWNER.parents[2]
DEPS = OWNER / '.tmp/python-deps'
site.addsitedir(str(DEPS))
if (DEPS / 'pywin32_system32').is_dir():
    os.add_dll_directory(str(DEPS / 'pywin32_system32'))
import pythoncom
import win32api
import win32com.client
import win32event
import win32process

parser = argparse.ArgumentParser()
parser.add_argument('--artifact-sha256', required=True)
parser.add_argument('--contract-sha256', required=True)
parser.add_argument('--scratch-name', choices=['independent-ui-attributes', 'independent-ui-attributes-current', 'independent-ui-attributes-final'], default='independent-ui-attributes')
args = parser.parse_args()
scratch = OWNER / '.tmp' / args.scratch_name
scratch.mkdir(parents=True, exist_ok=True)
if scratch.resolve() != scratch.absolute():
    raise RuntimeError('Redirected scratch path')
output = OWNER / 'build/test-results/independent-design-attributes.json'
contract_path = OWNER / 'tests/ui-contract.json'
artifact = OWNER / '.tmp/build/CareerManagement.accdb'
baseline = OWNER / '.tmp/build-agent/ui-regeneration/preserved-input.accdb'
candidate_copy = scratch / 'candidate.accdb'
baseline_copy = scratch / 'baseline.accdb'
TABLES = ['m_app_user', 'm_employee', 't_career', 'm_code_category', 'm_code']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def safe_copy(source, target):
    if source.resolve() != source.absolute() or source.is_symlink() or not source.is_file() or source.with_suffix('.laccdb').exists():
        raise RuntimeError('Live/nonregular/redirected input copy refused')
    if target.exists():
        raise RuntimeError('Existing audit copy preserved: ' + str(target))
    before = sha(source)
    shutil.copy2(source, target)
    if sha(source) != before or sha(target) != before:
        raise RuntimeError('Copy SHA mismatch')
    return before

def typed(value):
    if value is None: return {'kind': 'null'}
    if isinstance(value, bool): return {'kind': 'bool', 'value': value}
    if isinstance(value, datetime.datetime): return {'kind': 'datetime', 'value': value.isoformat(timespec='microseconds')}
    if isinstance(value, decimal.Decimal): return {'kind': 'decimal', 'value': str(value)}
    if isinstance(value, bytes): return {'kind': 'bytes', 'value': value.hex()}
    if isinstance(value, str): return {'kind': 'str', 'value': value}
    if isinstance(value, int): return {'kind': 'int', 'value': str(value)}
    if isinstance(value, float): return {'kind': 'float', 'value': value.hex()}
    raise TypeError('Unsupported DAO type: ' + type(value).__name__)

def snapshot(file):
    engine = db = rs = table = field = index = relation = None
    before = sha(file)
    try:
        engine = win32com.client.DispatchEx('DAO.DBEngine.120')
        db = engine.OpenDatabase(str(file), False, True)
        names = sorted(t.Name for t in db.TableDefs if not t.Name.startswith(('MSys', '~')))
        if names != sorted(TABLES): raise RuntimeError('Unexpected actual business table inventory')
        summaries, all_schema = [], []
        for name in TABLES:
            table = db.TableDefs(name)
            fields = []
            for field in table.Fields:
                props = {}
                for key in ['Type', 'Size', 'Attributes', 'Required', 'AllowZeroLength', 'DefaultValue', 'ValidationRule']:
                    try: props[key] = typed(field.Properties(key).Value)
                    except pythoncom.com_error: props[key] = {'kind': 'absent'}
                fields.append({'name': field.Name, 'properties': props})
            indexes = []
            for index in table.Indexes:
                indexes.append({'name': index.Name, 'primary': bool(index.Primary), 'unique': bool(index.Unique), 'required': bool(index.Required), 'ignoreNulls': bool(index.IgnoreNulls), 'fields': [(f.Name, f.Attributes) for f in index.Fields]})
            schema = {'table': name, 'fields': fields, 'indexes': sorted(indexes, key=lambda i: i['name'])}
            rs = db.OpenRecordset('SELECT * FROM [' + name + ']', 4)
            rows = []
            while not rs.EOF:
                rows.append([typed(rs.Fields(i).Value) for i in range(rs.Fields.Count)])
                rs.MoveNext()
            rs.Close(); rs = None
            rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
            summaries.append({'table': name, 'rows': len(rows), 'columns': len(fields), 'typedRowsSha256': digest({'fieldNamesAndTypes': fields, 'rows': rows}), 'schemaSha256': digest(schema)})
            all_schema.append(schema)
            rows.clear()
        relations = []
        for relation in db.Relations:
            if relation.Table in TABLES or relation.ForeignTable in TABLES:
                relations.append({'name': relation.Name, 'table': relation.Table, 'foreignTable': relation.ForeignTable, 'attributes': relation.Attributes, 'fields': [(f.Name, f.ForeignName) for f in relation.Fields]})
        result = {'tables': summaries, 'schemaSha256': digest({'tables': all_schema, 'relations': sorted(relations, key=lambda r: r['name'])}), 'allTypedDataSha256': digest(summaries), 'rowValuesLogged': False}
        db.Close(); db = None
        if sha(file) != before: raise RuntimeError('Read-only DAO inspection changed input copy')
        return result
    finally:
        if rs is not None: rs.Close()
        if db is not None: db.Close()
        engine = db = rs = table = field = index = relation = None
        gc.collect(); pythoncom.CoFreeUnusedLibraries()

def suppress_startup(file):
    engine = db = rs = None
    try:
        engine = win32com.client.DispatchEx('DAO.DBEngine.120')
        db = engine.OpenDatabase(str(file))
        macros = [document.Name for document in db.Containers('Scripts').Documents]
        if any(name.casefold() == 'autoexec' for name in macros):
            raise RuntimeError('Unexpected AutoExec macro; do not execute it')
        prior = None
        if 'StartupForm' in {p.Name for p in db.Properties}:
            prior = db.Properties('StartupForm').Value
            db.Properties.Delete('StartupForm')
        db.Close(); db = None
        return {'temporaryCopyOnly': True, 'removedStartupForm': prior, 'autoExecAbsent': True, 'reason': 'Prevent runtime Form events during DesignView-only attribute review'}
    finally:
        if rs is not None: rs.Close()
        if db is not None: db.Close()
        engine = db = rs = None
        gc.collect(); pythoncom.CoFreeUnusedLibraries()

def get(obj, name):
    return getattr(obj, name)

SECTION_NAMES = {0: 'Detail', 1: 'Header', 2: 'Footer'}
AC_LABEL = 100
AC_TEXTBOX = 109
PENDING_RUNTIME_DIMENSION_RULE_IDS = frozenset({
    'PENDING-F03-LAYOUT', 'PENDING-F03-VIEWPORT-DIMENSIONS',
    'PENDING-F04-LAYOUT', 'PENDING-F04-VIEWPORT-DIMENSIONS',
    'PENDING-F06-LAYOUT', 'PENDING-F06-VIEWPORT-DIMENSIONS',
})
PROPERTY_MAP = {'designWidthTwip': 'Width', 'defaultView': 'DefaultView', 'recordSelectors': 'RecordSelectors', 'navigationButtons': 'NavigationButtons', 'dividingLines': 'DividingLines', 'autoResize': 'AutoResize', 'autoCenter': 'AutoCenter', 'popUp': 'PopUp', 'modal': 'Modal', 'scrollBars': 'ScrollBars', 'keyPreview': 'KeyPreview', 'designHeightTwip': 'Height', 'backColor': 'BackColor', 'visible': 'Visible', 'fontFamily': 'FontName', 'fontSize': 'FontSize', 'fontBold': 'FontBold', 'designLeft': 'Left', 'designTop': 'Top', 'designWidth': 'Width', 'designHeight': 'Height', 'foreColor': 'ForeColor', 'specialEffect': 'SpecialEffect', 'useTheme': 'UseTheme', 'shape': 'Shape', 'gradient': 'Gradient', 'limitToList': 'LimitToList', 'autoExpand': 'AutoExpand', 'boundColumn': 'BoundColumn', 'columnCount': 'ColumnCount', 'columnWidthsTwip': 'ColumnWidths', 'columnHeads': 'ColumnHeads', 'multiSelect': 'MultiSelect', 'rowSourceType': 'RowSourceType', 'style': 'Style', 'multiRow': 'MultiRow', 'tabFixedHeightTwip': 'TabFixedHeight', 'tabFixedWidthTwip': 'TabFixedWidth', 'enabled': 'Enabled', 'locked': 'Locked', 'tabStop': 'TabStop', 'enterKeyBehavior': 'EnterKeyBehavior'}
EMPTY_PROPS = {'recordSourceEmpty': 'RecordSource', 'controlSourceEmpty': 'ControlSource', 'inputMaskEmpty': 'InputMask', 'formatEmpty': 'Format', 'rowSourceEmpty': 'RowSource'}

PROPERTY_MAP.update({'caption': 'Caption', 'controlTipText': 'ControlTipText', 'statusBarText': 'StatusBarText'})


def attached_label_names(obj):
    """Read every acLabel in the actual TextBox.Controls; never infer links from Parent/name."""
    if int(get(obj, 'ControlType')) != AC_TEXTBOX:
        raise TypeError('Attached-label measurement requires an actual TextBox')
    children = child = None
    names = []
    try:
        children = get(obj, 'Controls')
        for index in range(int(children.Count)):
            child = children.Item(index)
            if int(get(child, 'ControlType')) == AC_LABEL:
                name = get(child, 'Name')
                if not isinstance(name, str) or not name:
                    raise TypeError('Actual attached Label.Name is unavailable')
                names.append(name)
            child = None
        return sorted(names)
    finally:
        child = children = None  # Release child RCWs before owned Access shutdown.


def observed(obj, name, form, component):
    if name in PROPERTY_MAP: return get(obj, PROPERTY_MAP[name])
    if name in EMPTY_PROPS: return get(obj, EMPTY_PROPS[name]) in ('', None)
    if name == 'attachedLabelCount': return len(attached_label_names(obj))
    if name == 'attachedLabelName': return '|'.join(attached_label_names(obj))
    if name == 'fontUnit': return 'pt'  # Access FontSize property is specified in points.
    if name == 'unit': return 'twip'  # Access design coordinates are specified in twips.
    if name == 'section': return SECTION_NAMES[int(obj.Section)]
    if name == 'logicalPage':
        tag = str(obj.Tag)
        return tag[5:] if tag.startswith('PAGE:') else tag
    if name == 'pageIndex': return int(obj.PageIndex)
    if name == 'physicalParent': return form.Name + '.' + obj.Parent.Name
    if name == 'physicalInputCount': return int(obj.Controls.Count)
    if name == 'logicalInputSection':
        page = str(obj.PageIndex)
        sections = {SECTION_NAMES[int(c.Section)] for c in form.Controls if str(c.Tag) == 'PAGE:' + page}
        return next(iter(sections)) if len(sections) == 1 else '|'.join(sorted(sections))
    if name == 'pageCount': return int(obj.Pages.Count)
    if name == 'inputMaskPassword': return str(obj.InputMask) == 'Password'
    raise KeyError(name)

def passes(value, expected):
    op, wanted = expected['op'], expected['value']
    if op == 'eq': return value == wanted
    if op == 'range': return wanted[0] <= value <= wanted[1]
    if op == 'min': return value >= wanted
    if op == 'max': return value <= wanted
    if op == 'oneOf': return value in wanted
    raise ValueError(op)

def canonical_vba(text):
    # Invert only literal concatenations introduced for VBE ANSI round-tripping.
    atom = r'(?:"(?:[^"\r\n]|"")*"|ChrW\(&H[0-9A-F]+\))'
    pattern = re.compile(r'\(' + atom + r'(?:\s*&\s*(?:_\s*)?' + atom + r')+\)', re.I)
    def decode(match):
        parts = []
        for token in re.findall(atom, match[0], re.I):
            if token.startswith('"'): parts.append(token[1:-1].replace('""', '"'))
            else: parts.append(chr(int(re.search(r'&H([0-9A-F]+)', token, re.I)[1], 16)))
        value = ''.join(parts).encode('utf-16-le', errors='surrogatepass').decode('utf-16-le')
        return '"' + value.replace('"', '""') + '"'
    text = pattern.sub(decode, text)
    # Retain literal text/case, ignore comments and nonliteral spacing/case.
    tokens = re.findall(r'"(?:[^"\r\n]|"")*"|\x27[^\r\n]*|_[ \t]*(?:\r\n|\n)|[A-Za-z_][A-Za-z_0-9]*|[^\s]', text)
    return [token if token.startswith('"') else token.casefold() for token in tokens if not token.startswith("'") and not re.fullmatch(r'_[ \t]*(?:\r\n|\n)', token)]

record = {'schemaVersion': 1, 'projectId': 'sample-project2', 'profileId': 'Access', 'runId': 'sp2-ui-regenerate-20261029', 'checkpoint': 2, 'status': 'RUNNING', 'scope': 'Owned-copy DesignView saved attributes / normal VBA class initialization / read-only typed data only; no Form runtime, native input, viewport, drawing, Dialog behavior or acceptance.', 'formalScore': None, 'issues': [], 'rules': [], 'skippedRuntimeRules': [], 'inventory': [], 'compiledSourceComparison': [], 'unexecuted': ['Runtime Form rendering/viewport/initial focus', 'Physical keyboard/IME/clipboard and all Dialog actions', 'F03 top-visible-row capture/restore', 'F05 Excel/full-text/print/response interruption', 'Final published product and user acceptance']}
app = process_handle = project = probe = module = form = obj = None
record['notMeasuredProperties'] = []
pid = None
pythoncom.CoInitialize()
try:
    if sha(artifact) != args.artifact_sha256 or sha(contract_path) != args.contract_sha256:
        raise RuntimeError('Notified current artifact/contract SHA mismatch')
    record['artifactSha256'] = safe_copy(artifact, candidate_copy)
    record['baselineSha256'] = safe_copy(baseline, baseline_copy)
    record['contractSha256'] = sha(contract_path)
    contract = json.loads(contract_path.read_text(encoding='utf-8-sig'))
    record['inputManifestSha256'] = sha(OWNER / 'build/generation/inputs.json')
    record['baselineData'] = snapshot(baseline_copy)
    record['candidateDataBefore'] = snapshot(candidate_copy)
    if record['baselineData'] != record['candidateDataBefore']:
        record['issues'].append({'code': 'DATA_PRESERVATION', 'detail': 'Baseline and candidate typed data/schema differ'})
    record['startupSuppression'] = suppress_startup(candidate_copy)
    before_pids = set(win32process.EnumProcesses())
    app = win32com.client.DispatchEx('Access.Application')
    app.Visible = False
    hwnd = app.hWndAccessApp
    if callable(hwnd): hwnd = hwnd()
    pid = win32process.GetWindowThreadProcessId(hwnd)[1]
    if pid in before_pids: raise RuntimeError('New owned Access process required')
    process_handle = win32api.OpenProcess(0x100000 | 0x400, False, pid)
    record['ownedOffice'] = {'pid': pid, 'newProcess': True, 'nativeInputUsed': False}
    print(json.dumps({'step': 'owned-access-copy', 'pid': pid}), flush=True)
    app.OpenCurrentDatabase(str(candidate_copy), True)
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('Initial RunCommand126 did not establish IsCompiled')
    project = app.VBE.ActiveVBProject
    for component in project.VBComponents:
        if component.Type not in (1, 2): continue
        suffix = '.cls' if component.Type == 2 else '.bas'
        folder = 'classes' if component.Type == 2 else 'modules'
        source_file = OWNER / 'src' / folder / (component.Name + suffix)
        code_module = component.CodeModule
        compiled_text = code_module.Lines(1, code_module.CountOfLines) if code_module.CountOfLines else ''
        source_text = source_file.read_text(encoding='cp932')
        equal = canonical_vba(compiled_text) == canonical_vba(source_text)
        record['compiledSourceComparison'].append({'component': component.Name, 'sourceFile': source_file.relative_to(ROOT).as_posix(), 'sourceSha256': sha(source_file), 'compiledCodeTextSha256': hashlib.sha256(compiled_text.encode()).hexdigest(), 'canonicalTokensEqual': equal})
        if not equal: record['issues'].append({'code': 'COMPILED_SOURCE_DIFFERENCE', 'component': component.Name})
    component = code_module = None
    classes = sorted(c.Name for c in project.VBComponents if c.Type == 2)
    expected_classes = sorted(p.stem for p in (OWNER / 'src/classes').glob('*.cls'))
    if classes != expected_classes: raise RuntimeError('Compiled normal class inventory differs from source')
    probe = project.VBComponents.Add(1); probe.Name = 'IndependentClassAudit'
    module = probe.CodeModule
    if module.CountOfLines: module.DeleteLines(1, module.CountOfLines)
    lines = ['Option Explicit', 'Public Function IndependentClassSmoke() As Boolean']
    for n, name in enumerate(classes): lines += [f' Dim c{n} As New {name}', f' If TypeName(c{n}) <> "{name}" Then Err.Raise 5']
    lines += [' IndependentClassSmoke = True', 'End Function']
    module.AddFromString('\r\n'.join(lines))
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('Probe compilation failed')
    if not app.Run('IndependentClassSmoke'): raise RuntimeError('Normal-class initialization smoke failed')
    module = None; project.VBComponents.Remove(probe); probe = None
    app.DoCmd.RunCommand(126)
    if not app.IsCompiled: raise RuntimeError('Post-removal compilation failed')
    record['compile'] = {'runCommand': 126, 'initialIsCompiled': True, 'classes': classes, 'initializationSmoke': True, 'probeRemoved': True, 'finalIsCompiled': True, 'formRuntimeNewExecuted': False}
    components = {c['id']: c for c in contract['components']}
    form_components = [c for c in components.values() if c['kind'] == 'Form']
    actual_forms = sorted(f.Name for f in app.CurrentProject.AllForms)
    if actual_forms != sorted(c['nativeName'] for c in form_components):
        record['issues'].append({'code': 'FORM_INVENTORY', 'actual': actual_forms})
    for form_component in form_components:
        name = form_component['nativeName']
        app.DoCmd.OpenForm(name, 1, '', '', 0, 1)  # DesignView, Hidden; never Normal view.
        form = app.Forms(name)
        record['inventory'].append({'id': form_component['id'], 'kind': 'Form', 'nativeName': form.Name})
        for section_no, section_name in SECTION_NAMES.items():
            section = form.Section(section_no)
            record['inventory'].append({'id': name + '.' + section_name, 'kind': 'Section', 'nativeIndex': section_no, 'height': int(section.Height), 'visible': bool(section.Visible)})
        section = None
        actual = {}
        for ctl in form.Controls:
            if ctl.ControlType == 124: continue  # Native Pages are inventoried separately below.
            key = name + '.' + ctl.Name
            actual[key] = {'id': key, 'controlType': int(ctl.ControlType), 'nativeParent': str(ctl.Parent.Name), 'section': SECTION_NAMES[int(ctl.Section)], 'tag': str(ctl.Tag)}
        expected_controls = {c['id'] for c in components.values() if c['id'].startswith(name + '.') and c['kind'] != 'Section'}
        if set(actual) != expected_controls:
            record['issues'].append({'code': 'CONTROL_INVENTORY', 'form': name, 'missing': sorted(expected_controls - set(actual)), 'unexpected': sorted(set(actual) - expected_controls)})
        record['inventory'] += list(actual.values())
        relevant = {form_component['id']}
        relevant |= {c['id'] for c in components.values() if c['id'].startswith(name + '.')}
        if name == 'frmEmployeeEditor': relevant |= {'SC-F04-BASIC', 'SC-F04-CAREER'}
        for rule in contract['rules']:
            if rule['target'] not in relevant or rule['kind'] not in ['font', 'dimensions', 'appearance']:
                continue
            runtime_properties = {'groupsDoNotOverlap', 'actionsAssociatedWithScope', 'measuredClientAndDpi', 'mainActionsReachable', 'headerTabFooterRemainVisible', 'detailScrollDoesNotHideParent'}
            if rule['id'] in PENDING_RUNTIME_DIMENSION_RULE_IDS or runtime_properties.intersection(rule['properties']):
                record['skippedRuntimeRules'].append({'id': rule['id'], 'reason': 'Requires runtime drawing/viewport/meaning inspection; DesignView properties cannot establish it'})
                continue
            component = components[rule['target']]
            if component['kind'] == 'Form': obj = form
            elif component['kind'] == 'Section': obj = form.Section({'Detail': 0, 'Header': 1, 'Footer': 2}[component['nativeName']])
            elif component['kind'] == 'Page': obj = form.Controls('tabEmployee').Pages(component['nativeName'])
            else: obj = form.Controls(component['nativeName'])
            font_obj = form.Controls('tabEmployee') if component['kind'] == 'Page' and rule['kind'] == 'font' else obj
            values, failures = {}, []
            for prop, expected in rule['properties'].items():
                try:
                    value = observed(font_obj, prop, form, component)
                    values[prop] = value
                    if not passes(value, expected): failures.append({'property': prop, 'actual': value, 'expected': expected})
                except Exception as error:
                    failures.append({'property': prop, 'status': 'NOT_MEASURED', 'error': str(error)})
                    record['notMeasuredProperties'].append({'ruleId': rule['id'], 'target': rule['target'], 'property': prop, 'reason': str(error)})
            record['rules'].append({'id': rule['id'], 'target': rule['target'], 'kind': rule['kind'], 'status': 'FAIL' if failures else 'PASS_DESIGN_ATTRIBUTE', 'observed': values, 'failures': failures})
            if failures: record['issues'].append({'code': 'SAVED_ATTRIBUTE', 'rule': rule['id'], 'failures': failures})
        if name == 'frmEmployeeEditor':
            for page in form.Controls('tabEmployee').Pages:
                record['inventory'].append({'id': 'SC-F04-BASIC' if page.PageIndex == 0 else 'SC-F04-CAREER', 'nativeName': page.Name, 'kind': 'Page', 'physicalNativeParent': page.Parent.Name, 'nativeChildControls': int(page.Controls.Count)})
        obj = form = None
        app.DoCmd.Close(2, name, 2)  # Close form without saving DesignView.
    record['isCompiledAfterDesignRead'] = bool(app.IsCompiled)
    app.CloseCurrentDatabase()
except Exception as error:
    record['issues'].append({'code': 'FATAL', 'error': str(error)})
finally:
    obj = form = module = probe = project = ctl = page = font_obj = section = component = code_module = None
    if app is not None:
        try: app.Quit(2)
        except Exception as error: record['issues'].append({'code': 'QUIT', 'error': str(error)})
    app = None
    gc.collect(); pythoncom.CoFreeUnusedLibraries()
    if process_handle is not None:
        waited = win32event.WaitForSingleObject(process_handle, 10000)
        record['ownedOffice'].update(exitWait=waited, exitCode=win32process.GetExitCodeProcess(process_handle))
        if waited != 0: record['issues'].append({'code': 'OWNED_PROCESS_STILL_RUNNING', 'pid': pid})
        win32api.CloseHandle(process_handle)
    try:
        if candidate_copy.exists():
            record['candidateDataAfter'] = snapshot(candidate_copy)
            if record.get('candidateDataBefore') != record['candidateDataAfter']: record['issues'].append({'code': 'AUDIT_DATA_MUTATION'})
        record['originalArtifactStillSameSha'] = sha(artifact) == args.artifact_sha256
        if not record['originalArtifactStillSameSha']: record['issues'].append({'code': 'ORIGINAL_ARTIFACT_CHANGED'})
    except Exception as error: record['issues'].append({'code': 'POST_DATA_CHECK', 'error': str(error)})
    pythoncom.CoUninitialize()
    record['status'] = 'PASS_NON_UI_CHECKPOINT2' if not record['issues'] else 'FAIL_NON_UI_CHECKPOINT2'
    record['testSha256'] = sha(Path(__file__))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': record['status'], 'designAttributeRules': len(record['rules']), 'issues': len(record['issues']), 'output': str(output)}, ensure_ascii=False), flush=True)
raise SystemExit(bool(record['issues']))
