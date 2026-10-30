"""Verify actual compiled Japanese text on an owned candidate copy.

This is an encoding/build check. It never declares complete UI conformance.
"""
from pathlib import Path
import argparse
import ast
import ctypes
import datetime as dt
import hashlib
import json
import re
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import build
import data_integrity
from vba_text import read_vba_source, vbe_text

WORK = ROOT / '.tmp/japanese-encoding/runtime'
FIXTURE = ROOT / 'tests/fixtures/EncodingFixture.cp932.bas'
OUT = ROOT / 'build/test-results/japanese-encoding.json'
POINTS = [
    [0x793E, 0x54E1, 0x691C, 0x7D22],
    [0x57FA, 0x672C, 0x60C5, 0x5831, 0x30FB, 0x8077, 0x52D9],
    [0x6C0F, 0x540D, 0x30AB, 0x30CA],
    [0xFF71, 0xFF72, 0xFF73],
    [34, 65, 34, 32, 79, 39, 66, 114, 105, 101, 110],
    [0xFF5E], [0x301C], [0xFF0D], [0x2212], [0x1F600],
    [103, 32, 106, 32, 112, 32, 113, 32, 121, 32, 48, 49, 50, 51],
]
CAPTIONS = {
    'frmLogin': ('社員経歴管理 — ログイン', '社員経歴管理システム — ログイン'),
    'frmMenu': ('社員経歴管理 — メニュー', '社員経歴管理システム — メニュー'),
    'frmEmployeeSearch': ('社員経歴管理 — 社員検索', '社員検索'),
    'frmEmployeeEditor': ('社員経歴管理 — 社員登録・編集', '社員登録・編集［新規］'),
    'frmCodeMaster': ('社員経歴管理 — 汎用コードマスタ', '汎用コードマスタ'),
}
MESSAGES = {
    'MSG-009': '該当する社員はいません。',
    'MSG-014': '保存しました。',
    'MSG-015': '入力内容を破棄しますか。',
    'MSG-016': '選択値が利用できません。候補を再確認してください。',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unwrap(value):
    return value[0] if isinstance(value, tuple) else value


def canonicalizer():
    path = ROOT / 'tests/independent/design_attributes.py'
    parsed = ast.parse(path.read_text('utf-8'))
    function = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == 'canonical_vba')
    env = {'re': re}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), env)
    return env['canonical_vba']


def save(record):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--artifact-sha256', required=True)
    parser.add_argument('--replace-closed-copy', action='store_true')
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    assert artifact.is_relative_to(ROOT.resolve()) and not artifact.is_symlink()
    assert sha(artifact) == args.artifact_sha256
    assert not artifact.with_suffix('.laccdb').exists()
    WORK.mkdir(parents=True, exist_ok=True)
    target = WORK / 'CareerManagement-encoding-check.accdb'
    if target.exists():
        if not args.replace_closed_copy:
            raise RuntimeError('Owned encoding copy already exists; inspect prior exit before replacement')
        prior = json.loads(OUT.read_text('utf-8'))
        exit_record = prior.get('officeExit', {})
        assert target.resolve().parent == WORK.resolve() and not target.is_symlink()
        assert not target.with_suffix('.laccdb').exists()
        assert exit_record.get('exitWait') == 0 and exit_record.get('exitCode') == 0
        assert exit_record['pid'] not in set(build.win32process.EnumProcesses())
        assert prior['artifact']['sha256'] == args.artifact_sha256 and prior['typedDataPreserved']
        target.unlink()  # Exact closed copy owned by this verifier, never a product/user DB.
    shutil.copy2(artifact, target)
    record = {'schemaVersion': 1, 'projectId': 'sample-project2', 'profileId': 'Access',
              'status': 'RUNNING', 'artifact': {'file': artifact.relative_to(ROOT).as_posix(), 'sha256': sha(artifact)},
              'recordedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'hostACP': ctypes.windll.kernel32.GetACP(), 'sourceEncoding': 'cp932',
              'importTransport': 'ASCII / exact UTF-16 ChrW expressions',
              'compiledSourceComparisons': [], 'fixtureRuntime': [], 'messages': [], 'forms': [], 'issues': [],
              'scope': 'Owned-copy actual VBA code/import/export/runtime strings and saved form text; no physical input, complete UI, other ACP or formal acceptance inferred',
              'measurementSources': [{'file': str(p.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(p)} for p in
                                     [Path(__file__).resolve(), FIXTURE, ROOT/'tools/vba_text.py', ROOT/'tools/build.py', ROOT/'tools/data_integrity.py', ROOT/'tests/independent/design_attributes.py']],
              'overallUiPass': False, 'formalScore': None}
    save(record)
    before_data = data_integrity.snapshot(target)
    build.suppress_owned_startup(target)
    app = handle = project = component = module = form = None
    pid = None
    build.pythoncom.CoInitialize()
    try:
        before = set(build.win32process.EnumProcesses())
        app = build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
        app.Visible = False
        raw = app.hWndAccessApp
        hwnd = int(raw() if callable(raw) else raw)
        pid = build.win32process.GetWindowThreadProcessId(hwnd)[1]
        assert pid not in before
        handle = build.win32api.OpenProcess(0x100000 | 0x400, False, pid)
        record['ownedOffice'] = {'pid': pid, 'hwnd': hwnd, 'newProcess': True}
        print(json.dumps({'step': 'owned-encoding-copy', 'pid': pid}), flush=True)
        app.OpenCurrentDatabase(str(target), False)
        try:
            record['officeUiLanguageId'] = int(app.LanguageSettings.LanguageID(2))
        except Exception as error:
            record['officeUiLanguageId'] = None
            record['officeLanguageNotMeasured'] = type(error).__name__
        record['compile'] = build.compile_gate(app)
        project = app.VBE.ActiveVBProject
        canonical = canonicalizer()
        for component in project.VBComponents:
            if component.Type not in (1, 2):
                continue
            source = ROOT/'src'/('classes' if component.Type == 2 else 'modules')/(component.Name + ('.cls' if component.Type == 2 else '.bas'))
            original = source.read_bytes().decode('cp932', errors='strict')
            assert original.encode('cp932') == source.read_bytes()
            module = component.CodeModule
            actual = module.Lines(1, module.CountOfLines) if module.CountOfLines else ''
            ascii_only = all(ord(c) < 128 for c in actual)
            equal = canonical(original) == canonical(actual)
            record['compiledSourceComparisons'].append({'component': component.Name, 'sourceSha256': sha(source), 'asciiTransportReadback': ascii_only, 'canonicalTokensEqual': equal})
            if not ascii_only or not equal:
                record['issues'].append({'code': 'COMPILED_TEXT_DIFFERENCE', 'component': component.Name})
        component = module = None
        assert len(record['compiledSourceComparisons']) == 33
        component = project.VBComponents.Add(1)
        component.Name = 'EncodingFixture'
        component.CodeModule.AddFromString(vbe_text(read_vba_source(FIXTURE)))
        app.DoCmd.RunCommand(126)
        assert app.IsCompiled
        for index, points in enumerate(POINTS):
            actual = str(unwrap(app.Run('EncodingFixtureValue', index)))
            passed = list(map(ord, actual)) == points
            record['fixtureRuntime'].append({'index': index, 'expectedCodePoints': points, 'actualCodePoints': list(map(ord, actual)), 'pass': passed})
            if not passed:
                record['issues'].append({'code': 'RUNTIME_STRING_DIFFERENCE', 'index': index})
        exported = WORK/'EncodingFixture-export.bas'
        component.Export(str(exported))
        export_text = exported.read_bytes().decode('cp932', errors='strict')
        assert export_text.encode('cp932') == exported.read_bytes()
        record['vbaExport'] = {'sha256': sha(exported), 'strictCp932Roundtrip': True, 'asciiSubset': export_text.isascii()}
        project.VBComponents.Remove(component)
        component = None
        app.LoadFromText(5, 'EncodingFixture', str(exported))
        app.DoCmd.RunCommand(126)
        assert app.IsCompiled
        record['exportReimportCodePoints'] = [list(map(ord, str(unwrap(app.Run('EncodingFixtureValue', i))))) for i in range(len(POINTS))]
        assert record['exportReimportCodePoints'] == POINTS
        for name, expected in MESSAGES.items():
            actual = str(unwrap(app.Run('MessageText', name)))
            record['messages'].append({'id': name, 'actual': actual, 'expected': expected, 'pass': actual == expected})
            if actual != expected:
                record['issues'].append({'code': 'PRODUCT_MESSAGE_DIFFERENCE', 'id': name})
        for name, expected in CAPTIONS.items():
            app.DoCmd.OpenForm(name, 1)
            form = app.Forms(name)
            actual = (str(form.Caption), str(form.Controls('lblScreenTitle').Caption))
            row = {'form': name, 'actualFormCaption': actual[0], 'actualTitleCaption': actual[1], 'pass': actual == expected,
                   'titleFontPt': form.Controls('lblScreenTitle').FontSize, 'titleHeightTwips': form.Controls('lblScreenTitle').Height}
            record['forms'].append(row)
            if actual != expected:
                record['issues'].append({'code': 'PRODUCT_FORM_TEXT_DIFFERENCE', 'form': name})
            form = None
            app.DoCmd.Close(2, name, 2)
        native = WORK/'EmployeeSearch-native.txt'
        app.SaveAsText(2, 'frmEmployeeSearch', str(native))
        assert native.read_bytes().startswith(b'\xff\xfe')
        native_text = native.read_bytes().decode('utf-16', errors='strict')
        assert '社員検索' in native_text
        record['nativeFormExport'] = {'sha256': sha(native), 'encoding': 'UTF-16LE BOM', 'japaneseCaptionPreserved': True}
        app.DoCmd.DeleteObject(5, 'EncodingFixture')
        record['finalCompile'] = build.compile_gate(app)
    except Exception as error:
        record['issues'].append({'code': 'HARNESS_OR_PRODUCT_EXCEPTION', 'type': type(error).__name__, 'detail': str(error)})
    finally:
        project = component = module = form = None
        build.release()
        if app is not None:
            try:
                app.CloseCurrentDatabase()
                app.Quit(2)
            except Exception as error:
                record['issues'].append({'code': 'OFFICE_QUIT', 'detail': str(error)})
        app = None
        build.release()
        build.pythoncom.CoUninitialize()
        if handle is not None:
            wait = build.win32event.WaitForSingleObject(handle, 10000)
            code = build.win32process.GetExitCodeProcess(handle)
            handle.Close()
            record['officeExit'] = {'pid': pid, 'exitWait': wait, 'exitCode': code}
            if wait != 0 or code != 0:
                record['issues'].append({'code': 'OWNED_OFFICE_NOT_NORMAL_EXIT'})
    after_data = data_integrity.snapshot(target)
    record['typedDataPreserved'] = before_data['businessDigest'] == after_data['businessDigest'] and before_data['schemaFingerprint'] == after_data['schemaFingerprint']
    record['artifactUnchanged'] = sha(artifact) == args.artifact_sha256
    if not record['typedDataPreserved'] or not record['artifactUnchanged']:
        record['issues'].append({'code': 'DATA_OR_ARTIFACT_CHANGED'})
    record['status'] = 'PASS_ENCODING_SCOPE_ONLY' if not record['issues'] else 'FAIL_OR_INCONCLUSIVE'
    save(record)
    print(json.dumps({'status': record['status'], 'comparisons': len(record['compiledSourceComparisons']), 'runtimeCases': len(record['fixtureRuntime']), 'issues': record['issues'], 'officeExit': record.get('officeExit')}), flush=True)
    return int(bool(record['issues']))


if __name__ == '__main__':
    raise SystemExit(main())
