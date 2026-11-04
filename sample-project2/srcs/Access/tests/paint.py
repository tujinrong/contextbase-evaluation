"""Rendering lifecycle regressions on a disposable copy; no native-input claims."""
from pathlib import Path
import argparse
import datetime as dt
import json
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build
import data_integrity


def call(app, name, *args):
    value = app.Run(name, *args)
    return value[0] if isinstance(value, tuple) else value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifact-sha256', required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    source = ROOT / 'build/CareerManagement.accdb'
    assert build.sha(source) == args.artifact_sha256
    work = ROOT / '.tmp/paint-check'
    work.mkdir(parents=True, exist_ok=True)
    target = work / 'CareerManagement-paint-check.accdb'
    if target.exists() or target.with_suffix('.laccdb').exists():
        raise RuntimeError('Prior owned paint copy exists; inspect its exit before replacement')
    shutil.copy2(source, target)
    before_data = data_integrity.snapshot(target)
    build.suppress_owned_startup(target)
    record = {'schemaVersion': 1, 'runId': args.run_id, 'recordedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'artifactSha256': args.artifact_sha256, 'status': 'RUNNING', 'checks': [], 'scenes': [],
              'scope': 'Actual VBA Form/navigation/error/nested-drawing lifecycle on owned copy; not video, physical input or formal acceptance',
              'formalScore': None, 'issues': []}
    before_pids = set(build.win32process.EnumProcesses())
    app = handle = component = module = None
    build.pythoncom.CoInitialize()
    try:
        app = build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
        hwnd = app.hWndAccessApp
        hwnd = int(hwnd() if callable(hwnd) else hwnd)
        pid = build.win32process.GetWindowThreadProcessId(hwnd)[1]
        assert pid not in before_pids
        handle = build.win32api.OpenProcess(0x100000 | 0x400, False, pid)
        record['ownedOffice'] = {'pid': pid, 'newInstance': True}
        print(json.dumps({'step': 'owned-paint-check', 'pid': pid}), flush=True)
        app.OpenCurrentDatabase(str(target))
        app.Visible = False
        for name, encoding in [('UiHarness', 'utf-8'), ('PaintSuite', 'cp932')]:
            component = app.VBE.ActiveVBProject.VBComponents.Add(1)
            component.Name = name
            module = component.CodeModule
            if module.CountOfLines:
                module.DeleteLines(1, module.CountOfLines)
            module.AddFromString(build.vbe_text((ROOT / 'tests' / (name + '.bas')).read_text(encoding)))
            component = module = None
        app.DoCmd.RunCommand(126)
        assert app.IsCompiled
        for line in str(call(app, 'RunPaintSuite')).splitlines():
            parts = line.split('|', 2)
            record['checks'].append({'id': parts[0], 'status': parts[1], **({'detail': parts[2]} if len(parts) > 2 else {})})
        if not record['checks'] or any(row['status'] != 'PASS' for row in record['checks']):
            raise RuntimeError('Focused drawing lifecycle suite failed')
        for scene, form_name in [('login', 'frmLogin'), ('menu', 'frmMenu'), ('search', 'frmEmployeeSearch'),
                                 ('editor-new', 'frmEmployeeEditor'), ('editor-edit', 'frmEmployeeEditor'),
                                 ('careers', 'frmEmployeeEditor'), ('code', 'frmCodeMaster')]:
            assert call(app, 'PrepareUi', scene, '' if scene == 'login' else '123')
            stable = bool(call(app, 'PaintResizeStable', form_name))
            depth = int(call(app, 'UiPaintDepth'))
            owned = bool(call(app, 'UiPaintOwnsEcho'))
            row = {'scene': scene, 'form': form_name, 'unchangedResizeNoWritesAndNoLayoutFailure': stable,
                   'paintDepth': depth, 'ownsEcho': owned}
            record['scenes'].append(row)
            assert stable and depth == 0 and not owned, row
        token = int(call(app, 'UiBeginPaint'))
        assert token > 0 and call(app, 'UiPaintDepth') == 1
        app.Run('UiRecoverPaint')
        assert call(app, 'UiPaintDepth') == 0 and not call(app, 'UiPaintOwnsEcho')
        record['checks'].append({'id': 'explicit-interruption-recovery-clears-owned-scope', 'status': 'PASS'})
        app.Run('LogoutNow')
        assert call(app, 'UiPaintDepth') == 0 and not call(app, 'UiPaintOwnsEcho')
        record['checks'].append({'id': 'logout-restores-drawing', 'status': 'PASS'})
    except Exception as error:
        record['issues'].append({'errorType': type(error).__name__, 'detail': str(error)[:1600]})
    finally:
        component = module = None
        if app is not None:
            try:
                app.Run('UiRecoverPaint')
                app.CloseCurrentDatabase()
                app.Quit(2)
            except Exception as error:
                record['issues'].append({'closeErrorType': type(error).__name__})
        app = None
        build.release()
        build.pythoncom.CoUninitialize()
        if handle is not None:
            wait = build.win32event.WaitForSingleObject(handle, 10000)
            code = build.win32process.GetExitCodeProcess(handle)
            record['ownedOffice'].update(exitWait=wait, exitCode=code)
            if wait != 0 or code != 0:
                record['issues'].append({'code': 'OWNED_OFFICE_ABNORMAL_EXIT'})
            handle.Close()
    after_data = data_integrity.snapshot(target)
    record['typedDataPreserved'] = (before_data['businessDigest'] == after_data['businessDigest'] and
                                    before_data['schemaFingerprint'] == after_data['schemaFingerprint'])
    record['finalArtifactUnchanged'] = build.sha(source) == args.artifact_sha256
    record['testSources'] = {name: build.sha(ROOT / 'tests' / name) for name in ('paint.py', 'PaintSuite.bas', 'UiHarness.bas')}
    record['unexecuted'] = ['Actual Echo setter failure injection', 'Temporal video analysis of flicker', 'Physical keyboard/IME', 'Alternate DPI/Office environments', 'Formal acceptance']
    okay = not record['issues'] and record['typedDataPreserved'] and record['finalArtifactUnchanged']
    record['status'] = 'PASS_DRAWING_LIFECYCLE_SCOPE' if okay else 'FAIL_DRAWING_LIFECYCLE_SCOPE'
    out = ROOT / 'build/test-results/drawing-control.json'
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': record['status'], 'checks': len(record['checks']), 'scenes': len(record['scenes']),
                      'issues': record['issues'], 'output': str(out)}, ensure_ascii=False), flush=True)
    return int(not okay)


if __name__ == '__main__':
    raise SystemExit(main())
